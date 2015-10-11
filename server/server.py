import flask
from flask import Flask
from flask.ext import restful
from flask.ext.restful import reqparse
from flask.ext.cors import CORS, cross_origin

import json
from elasticsearch import Elasticsearch
import re
from os import path
import sys

sys.path.insert(0, 'scripts/lib/')

import language_functions as text_p
import query_parser as qp
import hotel_attribute_finder as finder

client = Elasticsearch()

app = Flask(__name__)

attribute_seed_file = 'data/tree-data/percolate_8.json'
city_hotel_id_file = 'data/city_hotel_details.json'
default_image = 'https://scontent.cdninstagram.com/hphotos-xaf1/t51.2885-15/e15/11240355_1446634575634173_545669914_n.jpg'

a = reqparse.RequestParser()
a.add_argument('search_str', type=str)
a.add_argument('city', type=str)
a.add_argument('hotel_id', type=str)
a.add_argument('hash_tag', type=str)

app.attr_seed = json.loads(open(attribute_seed_file, 'r').read())
app.hotel_name_data = json.loads(open(city_hotel_id_file, 'r').read())
text_p.load_model_files()

def do_location_query(loc_array):
    max_results = []
    if loc_array == None:
        return None
    for loc in loc_array:
        loc_results = finder.find_city_location_hotels(loc['lat'], loc['lng'])
        if loc_results != None and len(loc_results) > len(max_results):
            max_results = loc_results
    return max_results

def do_attribute_query(city, attr):
    if city == None or attr == None:
        return None
    image_result = finder.find_city_all_hotels_images(city)
    #print 'image_result: ' + str(image_result)
    review_result, output_sentiment, output_adj = finder.find_city_attribute_top_hotels(city, attr)
    output = {}
    for hotel_id, hotel_score in review_result:
        #hotel_id_int = int(hotel_id)
        hotel_id_int = int(hotel_id)
        #print 'hotel_id: ' + hotel_id
        output[hotel_id] = {}
        output[hotel_id]['score'] = hotel_score
        #output[hotel_id_int] = review_result[(hotel_id, hotel_score)]
        output[hotel_id]['attribute_details'] = {}
        map_to = output[hotel_id]['attribute_details']
        for path in output_sentiment[hotel_id]:
            map_to[path] = {}
            map_to[path]['sentiment_graph'] = output_sentiment[hotel_id][path]
            map_to[path]['adjective_graph'] = output_adj[hotel_id][path]
        
        
        if hotel_id in image_result:
            for path in image_result[hotel_id]:
                if path not in map_to:
                    map_to[path] = {}
                map_to[path]['images'] = image_result[hotel_id][path]    
    return output

def combine_results(attr_results, loc_results):
    if attr_results == None:
        return loc_results
    if loc_results == None:
        return attr_results
    if len(attr_results) >  len(loc_results):
        return attr_results
    return loc_results

def insert_hotel_details(city, final_results):
    #output = []
    #print 'city: ' + str(city)
    map_to = app.hotel_name_data[city]
    for hotel_id in final_results:
        assert(hotel_id in app.hotel_name_data[city])
        hotel_name = map_to[hotel_id]['name']
        obj = {}
        obj['id'] = hotel_id
        obj['name'] = hotel_name
        obj['score'] = final_results[hotel_id]['score']
        obj['address'] = map_to[hotel_id]['address']
        if 'location' in map_to[hotel_id]:
            obj['location'] = map_to[hotel_id]['location']
        final_results[hotel_id]['details'] = obj

def merge_results(images, hashtags, sentiment, adjectives):
    out = {}
    print 'len of images: ' + str(len(images))
    for attr in sentiment:
        out[attr] = {}
        out[attr]['sentiment'] = sentiment[attr]
        #sort on total sentiment value.
        out[attr]['sum_sentiment'] = sum(sentiment[attr].values())
        if attr in images:
            print 'in images: ' + str(attr)
            out[attr]['images'] = images[attr]
        if attr in hashtags:
            out[attr]['hashtags'] = hashtags[attr]
        if attr in adjectives:
            out[attr]['adjectives'] = adjectives[attr]
    return out
 
def convert_into_presentation_format(final_results, search_city, search_attr):
    presentation_json = []
    
    for hotel_id in final_results:
        obj = {}
        obj['hotel_id'] = hotel_id
        obj['city'] = search_city
        obj['name'] = final_results[hotel_id]['details']['name']
        obj['address'] = final_results[hotel_id]['details']['address']
        if 'location' in final_results[hotel_id]['details']:
            obj['location'] = final_results[hotel_id]['details']['location']
        else:
            obj['location'] = None
        assert(search_attr in final_results[hotel_id]['attribute_details'])
        sentiment_graph = final_results[hotel_id]['attribute_details'][search_attr]['sentiment_graph']
        adjective_graph = final_results[hotel_id]['attribute_details'][search_attr]['adjective_graph']
        if 'images' in final_results[hotel_id]['attribute_details'][search_attr]:
            image_arr = final_results[hotel_id]['attribute_details'][search_attr]['images']
            if len(image_arr) > 0:
                obj['image'] = image_arr[0][0]
        else:
            for in_attr in final_results[hotel_id]['attribute_details']:
                if 'images' in final_results[hotel_id]['attribute_details'][in_attr]:
                    image_arr = final_results[hotel_id]['attribute_details'][in_attr]['images']
                    if len(image_arr) > 0:
                        obj['image'] = image_arr[0][0]
            if 'image' not in obj:
                print 'error 11: using default image for hotel: ' + str(obj['name'])
                obj['image'] = default_image
        #attribute summary
        sentiment_arr = sentiment_graph.items()
        sentiment_arr.sort(key=lambda x: x[1], reverse=True)
        popular_sentiment = sentiment_arr[0][0]
        popular_percent = (sentiment_arr[0][1]*100)/sum(sentiment_graph.values())
        obj['sentiment_percent'] = round(popular_percent)
        obj['attribute_summary'] = 'Most popular sentiment about: ' + search_attr + ' is: ' + str(popular_sentiment)
        presentation_json.append(obj)
    return presentation_json

def create_sentiment_graph(output_sentiment):
    output = {}
    for path in output_sentiment:
        max_sentiment = None
        max_val = -1
        for sentiment in output_sentiment[path]:
            if output_sentiment[path][sentiment] > max_val:
                max_sentiment = sentiment
                max_val = output_sentiment[path][sentiment]
        if max_sentiment not in output:
            output[max_sentiment] = 0
        output[max_sentiment] = output[max_sentiment] + 1
    return output

def create_attribute_graph(output_sentiment, output_adj, output_images):
    output = []
    for path in output_sentiment:
        #print 'path: ' + str(path)
        attr = path
        image_arr = None
        if attr in output_images:
            image_arr = output_images[attr]
        else:
            continue
        sentiment_map = output_sentiment[path]
        sentiment_arr = sentiment_map.items()
        sentiment_arr.sort(key=lambda x: x[1], reverse=True)
        sentiment_len = len(sentiment_arr)
        if sentiment_len > 0:
            most = sentiment_arr[0][0]
        else:
            most = 'None'
        if sentiment_len > 1:
            few = sentiment_arr[1][0]
        else:
            few = 'None'
        if sentiment_len > 2:
            less = sentiment_arr[2][0]
        else:
            few = 'None'
        obj = {
            "title": attr,
            "images": image_arr,
            "details": [
                'Most people had ' + most.lower() + ' experience.',
                'Some people had ' + few.lower() + ' experience.',
                'Less people had ' + less.lower() + ' experience.'
            ]
        }
        output.append(obj)
    output.sort(key=lambda x: len(x['images']), reverse=True)
    return output

'''
output:
    {
        'title': 'beautiful_view',
        'city': 'marrakech',
        'hotels': [
            {
                'hotel_id': '123',
                'score': 12121,
                'name': 'my hotel',
                'image': 'my url'
            },
        ]
    }
'''
def convert_into_presentation_format_hashtags(city, hash_tags_map, output_images):
    output = {}
    output['city']  = city
    results = []
    for hash_tag in hash_tags_map:
        first_index = hash_tag.index(finder.hash_tag_delim)
        attr = hash_tag[first_index + 1:]
        adj = hash_tag[:first_index]
        hotel_results = hash_tags_map[hash_tag]
        out_hotel_list = []
        sum_score = 0
        for hotel_id, hash_score in hotel_results:
            obj = {}
            hotel_id = str(hotel_id)
            #print 'hotel_id type: ' + str(type(hotel_id))
            obj['hotel_id'] = hotel_id
            obj['score'] = hash_score
            sum_score += hash_score
            obj['name'] = app.hotel_name_data[city][hotel_id]['name']
            #print 'obj: ' + str(obj)
            if hotel_id not in output_images:
                print 'error 00: ' + str(hotel_id) + ' ; ' + str(city)
                continue
            if attr in output_images[hotel_id]:
                obj['image'] = output_images[hotel_id][attr][0][0]
            else:
#                for in_attr in output_images[hotel_id]:
#                    if len(output_images[hotel_id][in_attr]) > 0:
#                        obj['image'] = output_images[hotel_id][in_attr][0][0]
#                if 'image' not in obj:
#                    print 'error 10: image not found for hash_tag and hotel_id: ' + str(hash_tag) + ' ; ' + str(hotel_id) + ' ; ' + str(city)
                obj['image'] = default_image
            out_hotel_list.append(obj)
        out_hotel_list.sort(key=lambda x: x['score'], reverse=True)
        meta_obj = {}
        meta_obj['title'] = hash_tag
        meta_obj['hotels'] = out_hotel_list
        meta_obj['sum_score'] = sum_score
        results.append(meta_obj)
    results.sort(key=lambda x: x['sum_score'], reverse=True)
    output['results'] = results[:20]
    return output
        
            

'''
possible outputs:
1. [hash_tags]
2. [attribute -> [images]]
3. [sentiment -> [attributes]]
4. [attribute -> (sentiment, adjective)]
5. [attribute -> [hash_tags]]
'''

class HashTagSearchHandler(restful.Resource):
    def get(self):
        args = a.parse_args()
        search_city = args.get('city')
        search_hash_tag = args.get('hash_tag')
        search_attr = search_hash_tag[search_hash_tag.index(finder.hash_tag_delim) + 1:]
        attr_results = do_attribute_query(search_city, search_attr)
        insert_hotel_details(search_city, attr_results)
        presentation_json = convert_into_presentation_format(attr_results, search_city, search_attr)
        return presentation_json, 200
        

class HashTagHandler(restful.Resource):
    def get(self):
        args = a.parse_args()
        search_city = args.get('city').lower()
        hash_tags = finder.find_city_hashtags(search_city)  # format is hash_tag -> [(hotel_id, score)]
        output_images = finder.find_city_all_hotels_images(search_city)
        output_format = convert_into_presentation_format_hashtags(search_city, hash_tags, output_images)
        return output_format, 200
        
        

class DetailHandler(restful.Resource):
    def get(self):
        args = a.parse_args()
        search_city = args.get('city').lower()
        search_hotel_id = args.get('hotel_id')
        hotel_details = app.hotel_name_data[search_city][search_hotel_id]
        output_images = finder.find_city_hotel_images(search_city, search_hotel_id)
        output_sentiment, output_adj, output_hashtags = finder.find_hotel_hashtags(search_city, search_hotel_id)
        sentiment_graph = create_sentiment_graph(output_sentiment)
        attribute_graph = create_attribute_graph(output_sentiment, output_adj, output_images)
        obj = {
            'city': search_city,
            'hotel_id': search_hotel_id,
            'name': hotel_details['name'],
            'address': hotel_details['address'],
            'sentiment_graph': sentiment_graph,
            'attribute_graph': attribute_graph
        }
#        final_results = merge_results(output_images, output_hashtags, output_sentiment, output_adj)
#        final_results_arr = final_results.items()
#        final_results_arr.sort(key=lambda x: x[1]['sum_sentiment'], reverse=False)
        return obj, 200
        
        

class HelloHandler(restful.Resource):
    def get(self):
        args = a.parse_args()
        search_city = args.get('city').lower()
        #print 'city_parsed: ' + search_city
        search_criterion = args.get('search_str')
        result_1 = text_p.find_attribute_2(app.attr_seed['root'], search_criterion)
        result = qp.process_request(result_1, app.hotel_name_data.keys(), app.attr_seed, search_criterion)
        #print 'processed results: ' + str(result)
        loc_results = None
        search_attr = None
        if 'loc' in result:
            loc_arr = result['loc'] # array of {lat, lng} objects
            loc_results = do_location_query(loc_arr)
            search_attr = 'beach'
        attr_results = None
        if 'attr' in result:
            attr_path = result['attr']
            attr_path_pure = map(lambda x: x[0], attr_path)
            search_attr = attr_path_pure[len(attr_path_pure) - 1]
            attr = attr_path_pure[-1]
            attr_results = do_attribute_query(search_city, attr)
        #print 'loc_results: ' + str(loc_results)
        #print 'attr_results: ' + str(attr_results)
        #final_results = combine_results(attr_results, loc_results)
        final_results = attr_results
        insert_hotel_details(search_city, final_results)
        presentation_json = convert_into_presentation_format(final_results, search_city, search_attr)
        return presentation_json, 200
        
if __name__ == "__main__":
    cors = CORS(app)
    app.config['CORS_HEADERS'] = 'Content-Type'
    api = restful.Api(app)
    api.add_resource(HelloHandler, '/listing')
    api.add_resource(DetailHandler, '/detail')
    api.add_resource(HashTagHandler, '/hashtag')
    api.add_resource(HashTagSearchHandler, '/hashtag_listing')
    print 'running server...'
    app.run(debug=True, port=8080, host="0.0.0.0")