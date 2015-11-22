from __future__ import division
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
import pdb

sys.path.insert(0, 'scripts/lib/')

import language_functions as text_p
import query_parser_2 as qp
import hotel_attribute_finder as finder

client = Elasticsearch()

app = Flask(__name__)

attribute_seed_file = 'data/tree-data/percolate_11.json'
city_hotel_id_file = 'data/hotel/city_hotel_details.json'
positive_file = 'data/antonyms/positives.json'
negative_file = 'data/antonyms/negatives.json'
default_image = 'https://scontent.cdninstagram.com/hphotos-xaf1/t51.2885-15/e15/11240355_1446634575634173_545669914_n.jpg'

a = reqparse.RequestParser()
a.add_argument('search_str', type=str)
a.add_argument('city', type=str)
a.add_argument('hotel_id', type=str)
a.add_argument('hash_tag', type=str)

app.attr_seed = json.loads(open(attribute_seed_file, 'r').read())
app.hotel_name_data = json.loads(open(city_hotel_id_file, 'r').read())
app.positives = json.loads(open(positive_file, 'r').read())
app.negatives = json.loads(open(negative_file, 'r').read())
text_p.load_model_files()

def do_location_query(loc_array):
    max_results = []
    if loc_array == None:
        return None
    for loc in loc_array:
        print 'querying for: ' + str(loc)
        loc_results = finder.find_city_location_hotels(loc['lat'], loc['lon'])
        #print 'loc_results: ' + str(loc_results)
        if loc_results != None and len(loc_results) > len(max_results):
            max_results = loc_results
    max_results_obj = {}
    for res in max_results:
        res['type'] = 'loc'
        max_results_obj[res['hotel_id']] = res
    return max_results_obj

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
        output[hotel_id]['type'] = 'attr'
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
    return output, output_adj

def combine_results(attr_results, loc_results):
#    if loc_results != None and len(loc_results) > 0:
#        print 'returning loc results'
#        return loc_results
#    print 'returning attr results.'
#    return attr_results
    if attr_results == None:
        return loc_results
    if loc_results == None:
        return attr_results
    print 'length of attr and loc results: ' + str(len(attr_results)) + ' ; ' + str(len(loc_results))
    output = {}
    for hotel_id in attr_results:
        output[hotel_id] = attr_results[hotel_id]
    for hotel_id in loc_results:
        if hotel_id in output:
            output[hotel_id]['type'] = 'both'
        else:
            print 'loc result not found in attr: ' + str(hotel_id)
            output[hotel_id] = loc_results[hotel_id]
#    if len(attr_results) >  len(loc_results):
#        print 'returning attr results'
#        return attr_results
#    print 'returning loc results'
    return output

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
        obj['type'] = final_results[hotel_id]['type']
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
 
def convert_into_presentation_format(final_results, search_city, search_attr, output_adj):
    presentation_json = []
    
    for hotel_id in final_results:
        obj = {}
        obj['hotel_id'] = hotel_id
        obj['city'] = search_city
        obj['name'] = final_results[hotel_id]['details']['name']
        #if final_results[hotel_id]['details']['address']
        obj['address'] = final_results[hotel_id]['details']['address']
        if obj['address']['country'] == None:
            obj['address']['country'] = ''
        if obj['address']['street'] == None:
            obj['address']['street'] = ''
        if 'location' in final_results[hotel_id]['details']:
            obj['location'] = final_results[hotel_id]['details']['location']
        else:
            obj['location'] = None
        search_type = final_results[hotel_id]['details']['type']
        if 'attribute_details' not in final_results[hotel_id]:
            assert( search_type == 'loc')
            continue
        else:
            assert(search_type == 'attr' or search_type == 'both')
        #assert(search_attr in final_results[hotel_id]['attribute_details'])
        sentiment_graph = final_results[hotel_id]['attribute_details'][search_attr]['sentiment_graph']
        adjective_graph = final_results[hotel_id]['attribute_details'][search_attr]['adjective_graph']
        if 'images' in final_results[hotel_id]['attribute_details'][search_attr]:
            image_arr = final_results[hotel_id]['attribute_details'][search_attr]['images']
            if len(image_arr) > 0:
                obj['image'] = image_arr[0][0]
                obj['score'] = len(image_arr) * 10
        else:
            for in_attr in final_results[hotel_id]['attribute_details']:
                if 'images' in final_results[hotel_id]['attribute_details'][in_attr]:
                    image_arr = final_results[hotel_id]['attribute_details'][in_attr]['images']
                    if len(image_arr) > 0:
                        obj['image'] = image_arr[0][0]
                        obj['score'] = len(image_arr) / 2
            if 'image' not in obj:
                try:
                    print 'error 11: using default image for hotel: ' + obj['name'].encode('utf-8')
                except UnicodeDecodeError:
                    print 'UnicodeDecodeError for hotel_id: ' + str(hotel_id)
                obj['image'] = default_image
                obj['score'] = -1
        #attribute summary
        sentiment_arr = sentiment_graph.items()
        sentiment_arr.sort(key=lambda x: x[1], reverse=True)
        popular_sentiment = sentiment_arr[0][0].lower()
        #print 'popular sentiment: ' + str(popular_sentiment)
        sum_val = sum(sentiment_graph.values())
        if sum_val == 0:
            popular_percent = -1
        else:
            popular_percent = (sentiment_arr[0][1]*100)/sum_val
        if 'negative' in popular_sentiment:
            popular_percent = -popular_percent
        obj['sentiment_percent'] = round(popular_percent)
        adj_list = output_adj[hotel_id][search_attr].items()
        popular_adjective = None
        if adj_list == None or len(adj_list) == 0:
            popular_adjective = popular_sentiment.lower()  # XXX: Some handling here.
            try:
                obj['attribute_summary'] = 'Most popular sentiment around ' + search_attr + ' is ' + str(popular_adjective)
            except UnicodeEncodeError:
                print 'UnicodeDecodeError error for hotel_id: ' + str(hotel_id)
            obj['score'] = 0
        else:
            positive, negative, neutral = filter_adjectives(adj_list)
            if 'positive' in popular_sentiment:
                popular_adjective = finder.find_random_positive(search_attr)
            else:
                if 'negative' in popular_sentiment:
                    popular_adjective = finder.find_random_negative(search_attr)
                else:
                    if len(neutral) == 0:
                        popular_adjective = finder.find_random_neutral()
                    else:
                        neutral.sort(key=lambda x: x[1], reverse=True)
                        popular_adjective = neutral[0][0]
            try:
                obj['attribute_summary'] = 'Most popular sentiment around ' + search_attr + ' is ' + str(popular_adjective)
            except UnicodeEncodeError:
                print 'Encoding error for hotel_id: ' + str(hotel_id)
        if final_results[hotel_id]['details']['type'] == 'both':
            obj['score'] = 2 * obj['score']
        presentation_json.append(obj)
    presentation_json.sort(key=lambda x: x['sentiment_percent'] * x['score'], reverse=True)
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

def filter_adjectives(output_adj):
    positive_list = []
    negative_list = []
    neutral_list = []
    if output_adj != None:
        for adj, adj_score in output_adj:
            if adj in app.positives:
                positive_list.append((adj, adj_score))
            else:
                if adj in app.negatives:
                    negative_list.append((adj, adj_score))
                else:
                    neutral_list.append((adj, adj_score))
    return positive_list, negative_list, neutral_list

def create_inner_sentiment_graph(attr, output_sentiment, output_adj):
    #entry 1:
    count_positive = 0
    count_negative = 0
    count_neutral = 0
    total = 0
    for sentiment in output_sentiment:
        total += output_sentiment[sentiment]
        if 'positive' in sentiment.lower():
            count_positive += output_sentiment[sentiment]
        else:
            if 'negative' in sentiment.lower():
                count_negative += output_sentiment[sentiment]
            else:
                count_neutral += output_sentiment[sentiment]
    positive, negative, neutral = filter_adjectives(output_adj.items())
    
    output = []
#    obj = {}
#    obj['status'] = 'awesome'
#    obj['description'] = str(round((count_positive * 100) / total )) + '% had positive experience with ' + str(attr) + '.'
#    obj['hash_tags'] = []
#    for adj, adj_score in positive:
#        obj['hash_tags'].append(finder.create_hash_tag(attr, adj))
#    output.append(obj)
#    obj = {}
#    obj['status'] = 'ok'
#    obj['description'] = str(round((count_neutral * 100) / total )) + '% had so so experience with ' + str(attr) + '.'
#    obj['hash_tags'] = []
#    for adj, adj_score in neutral:
#        obj['hash_tags'].append(finder.create_hash_tag(attr, adj))
#    output.append(obj)
#    obj = {}
#    obj['status'] = 'bad'
#    obj['description'] = str(round((count_negative * 100) / total )) + '% had bad experience with ' + str(attr) + '.'
#    obj['hash_tags'] = []
#    for adj, adj_score in negative:
#        obj['hash_tags'].append(finder.create_hash_tag(attr, adj))
#    output.append(obj)
    return output

def create_attribute_graph(output_sentiment, output_adj, output_images, output_raw_reviews):
    output = []
    for path in output_sentiment:
        #print 'path: ' + str(path)
        attr = path
        
        raw_reviews = []
        if attr in output_raw_reviews:
            raw_reviews_raw = output_raw_reviews[attr]
            raw_reviews_raw.sort(key=lambda x: (x[1] * x[2]), reverse=True)
            raw_reviews = map(lambda x: x[0], raw_reviews_raw)
            
        image_arr = None
        if attr in output_images:
            image_arr = output_images[attr]
        else:
            if len(raw_reviews) < 5:
                # no image and no raw reviews means pass.
                continue
            image_arr = []
            image_arr.append([default_image])
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
            less = 'None'
        obj = {
            "title": attr,
            "images": image_arr,
            "details": [
                'Most people had ' + most.lower() + ' experience.',
                'Some people had ' + few.lower() + ' experience.',
                'Less people had ' + less.lower() + ' experience.'
            ],
            "sentiment_graph": create_inner_sentiment_graph(attr, output_sentiment[attr], output_adj[attr]),
            "raw_reviews": raw_reviews
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
        adj = hash_tag[1:first_index]
        hotel_results = hash_tags_map[hash_tag]
        out_hotel_list = []
        sum_score = 0
        for hotel_id, hash_score in hotel_results:
            obj = {}
            hotel_id = str(hotel_id)
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
                obj['score'] = -1
            out_hotel_list.append(obj)
        out_hotel_list.sort(key=lambda x: x['score'], reverse=True)
        meta_obj = {}
        adj, attr = finder.break_hash_tag(hash_tag)
        if attr not in finder.attr_title_map:
            'error 21: ' + str(attr)
            continue
        title = finder.attr_title_map[attr]
        meta_obj['title'] = title
        meta_obj['hash_tag'] = hash_tag
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
    def post(self):
        args = a.parse_args()
        search_city = args.get('city')
        search_hash_tag = args.get('hash_tag')
        index = search_hash_tag.index(finder.hash_tag_delim)
        search_attr = search_hash_tag[ index + 1:]
        attr_results, output_adj = do_attribute_query(search_city, search_attr)
        insert_hotel_details(search_city, attr_results)
        presentation_json = convert_into_presentation_format(attr_results, search_city, search_attr, output_adj)
        return presentation_json, 200
        

class HashTagHandler(restful.Resource):
    def post(self):
        args = a.parse_args()
        search_city = args.get('city').lower()
        hash_tags = finder.find_city_hashtags(search_city)  # format is hash_tag -> [(hotel_id, score)]
        output_images = finder.find_city_all_hotels_images(search_city)
        output_format = convert_into_presentation_format_hashtags(search_city, hash_tags, output_images)
        return output_format, 200
        
        

class DetailHandler(restful.Resource):
    def post(self):
        args = a.parse_args()
        search_city = args.get('city').lower()
        search_hotel_id = args.get('hotel_id')
        print 'search_criterion: ' + search_city + ' ; ' + search_hotel_id
        hotel_details = app.hotel_name_data[search_city][search_hotel_id]
        output_images = finder.find_city_hotel_images(search_city, search_hotel_id)
        output_sentiment, output_adj, output_hashtags, output_raw_reviews = finder.find_hotel_hashtags(search_city, search_hotel_id)
        sentiment_graph = create_sentiment_graph(output_sentiment)
        attribute_graph = create_attribute_graph(output_sentiment, output_adj, output_images, output_raw_reviews)
        
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
 
base_questions = ['hotels with good restaurants', 'hotels with sumptuous breakfast', 'hotels with awesome swimming pool']
specific_questions = {
    'bali': ['hotels near sea beach', 'hotels with infinity pool'],
    'marrakech': ['hotels with great patios to relax', 'hotels with lush green gardens'],
    'goa': ['hotels near sea beach', 'family friendly hotels']
}    
    
class CityTagHandler(restful.Resource):
    def post(self):
        args = a.parse_args()
        search_city = args.get('city').lower()
        assert(search_city in specific_questions)
        return base_questions + specific_questions[search_city], 200
        

class HelloHandler(restful.Resource):
    def post(self):
        args = a.parse_args()
        search_city = args.get('city').lower()
        search_criterion = args.get('search_str')
        assert(search_criterion != None)
        print 'search_criterion: ' + search_criterion
        result_1 = text_p.find_attribute_2(app.attr_seed['root'], search_criterion, True)
        result = qp.process_request(result_1, app.attr_seed, search_city, search_criterion)
        print 'processed results: ' + str(result)
        loc_results = None
        search_attr = None
        if 'loc' in result:
            loc_arr = result['loc'] # array of {lat, lng} objects
            loc_results = do_location_query(loc_arr)
        attr_results = None
        output_adj = None
        if 'attr' in result:
            attr_path = result['attr']
            attr_path_pure = map(lambda x: x[0], attr_path)
            search_attr = attr_path_pure[len(attr_path_pure) - 1]
            attr = attr_path_pure[-1]
            attr_results, output_adj = do_attribute_query(search_city, attr)
        final_results = combine_results(attr_results, loc_results)
        insert_hotel_details(search_city, final_results)
        presentation_json = convert_into_presentation_format(final_results, search_city, search_attr, output_adj)
        return presentation_json, 200
        
if __name__ == "__main__":
    cors = CORS(app)
    app.config['CORS_HEADERS'] = 'Content-Type'
    api = restful.Api(app)
    api.add_resource(HelloHandler, '/listing')
    api.add_resource(DetailHandler, '/detail')
    api.add_resource(HashTagHandler, '/hashtag')
    api.add_resource(HashTagSearchHandler, '/hashtag_listing')
    api.add_resource(CityTagHandler, '/search_str')
    print 'running server...'
    app.run(debug=True, port=8181, host="0.0.0.0")