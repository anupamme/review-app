'''
Input: city_name, hotel_name

Output: what is a map: {attribute -> {0 -> %, 1 -> %, 2 -> %, 3 -> %, 4 -> %}}

process: city_name and hotel_name are part of elastic search attributes.
query: elastic search query results in [elastic_search_obj]

processing: 
    Input: [elastic search object]
    output: attribute_path -> sentiment -> number of people
    output: attribute_path -> adjective -> number of people
    for each object:
        find attribute path
        for that path, update the sentiment.

'''

import sys
import json
sys.path.insert(0, 'scripts/lib/')
import pprint
import operator
import elastic_search as es

hash_tag_delim = '_'

attribute_seed = json.loads(open('data/tree-data/percolate_8.json', 'r').read())

def find_abs_path(search_node):
#    if root_node['next'] == {}:
#        return False
#    for node in root_node['next']:
#        if node == search_node:
#            path.append(search_node)
#            return True
#        if find_abs_path(search_node, root_node['next'][node], path):
#            path.append(node)
#            return True
    return search_node

def find_path(item):
    path_obj = {}
    for attr_root in item['attribute_list']:
        leaf_name = attr_root['value']
        path = find_abs_path(leaf_name)
        score = item['score'][leaf_name]
        path_obj[str(path)] = score
    return path_obj

def find_sentiment(item):
    result = {}
    for leaf_attr in item['sentiment']:
        path = find_abs_path(leaf_attr)
        result[str(path)] = item['sentiment'][leaf_attr]
    return result

def find_adjective(item):
    result = {}
    for leaf_attr in item['adjective_list']:
        path = find_abs_path(leaf_attr)
        result[str(path)] = item['adjective_list'][leaf_attr]
    return result

def insert_or_increment(out, path_dict, sentiment_dict):
    for path in path_dict:
        if path not in out:
            out[path] = {}
        score = path_dict[path]
        sent = sentiment_dict[path]
        if sent not in out[path]:
            out[path][sent] = 0
        out[path][sent] += score
        
def insert_or_increment_adjective(out, path_dict, adjective_dict):
    for path in path_dict:
        if path not in out:
            out[path] = {}
        #score = path_dict[path]
        if len(adjective_dict[path]) > 0:
            adj = adjective_dict[path][0]
            adj_score = adjective_dict[path][1]
            if adj in out[path]:
                out[path][adj] = out[path][adj] + adj_score
            else:
                out[path][adj] = adj_score

'''
input: city_name, hotel_id
output: 
    output_sentiment: path -> sentiment -> score
    output_adjective: path -> adjective -> score
'''
def find_city_hotel_attributes(city_name, hotel_id):
    elastic_results = es.find_city_hotel_reviews(city_name, hotel_id)
    output_sentiment = {}   # format is: 
    output_adjective = {}   # format is: 
    for item in elastic_results['hits']['hits']:
        item = item['_source']
        path_dict = find_path(item)
        #print 'path_dict: ' +  str(path_dict)
        sentiment_dict = find_sentiment(item)
        #print 'sentiment_dict: ' + str(sentiment_dict)
        adjective_dict = find_adjective(item)
        #print 'adjective_dict: ' + str(adjective_dict)
        insert_or_increment(output_sentiment, path_dict, sentiment_dict)
        insert_or_increment_adjective(output_adjective, path_dict, adjective_dict)
        
    return output_sentiment, output_adjective

def find_city_all_hotels_attributes(city_name):
    elastic_results = es.find_city_reviews(city_name)
    output_sentiment = {}   # format is: hotel_id -> path -> sentiment -> score
    output_adjective = {}   # format is: hotel_id -> path -> adjective -> score
    for item in elastic_results['hits']['hits']:
        item = item['_source']
        hotel_id = item['hotel_id']
        if hotel_id not in output_sentiment:
            output_sentiment[hotel_id] = {}
        if hotel_id not in output_adjective:
            output_adjective[hotel_id] = {}
        path_dict = find_path(item)
        #print 'path_dict: ' +  str(path_dict)
        sentiment_dict = find_sentiment(item)
        #print 'sentiment_dict: ' + str(sentiment_dict)
        adjective_dict = find_adjective(item)
        #print 'adjective_dict: ' + str(adjective_dict)
        insert_or_increment(output_sentiment[hotel_id], path_dict, sentiment_dict)
        insert_or_increment_adjective(output_adjective[hotel_id], path_dict, adjective_dict)

    return output_sentiment, output_adjective

def find_sum_over_sentiment(output_sentiment):
    output_sentiment_sum = {}
    for hotel_id in output_sentiment:
        output_sentiment_sum[hotel_id] = {}
        for attribute in output_sentiment[hotel_id]:
            sentiment_dist = output_sentiment[hotel_id][attribute]
            sentiment_values = map(lambda x: x[1], sentiment_dist.items())
            sentiment_values_sum = reduce(lambda x, y: x+y, sentiment_values)
            output_sentiment_sum[hotel_id][attribute] = sentiment_values_sum
    return output_sentiment_sum

def sort(output_sentiment_sum, candidate_attribute):
    hotel_sentiment_map = {}
    for hotel_id in output_sentiment_sum:
        for attr in output_sentiment_sum[hotel_id]:
            if attr == candidate_attribute:
                hotel_sentiment_map[hotel_id] = output_sentiment_sum[hotel_id][attr]
    return sorted(hotel_sentiment_map.items(), key=operator.itemgetter(1), reverse=True)
                
def find_city_attribute_top_hotels(city_name, attribute):
    print 'finder:: ' + city_name + ' ; ' + attribute
    output_sentiment, output_adjective = find_city_all_hotels_attributes(city_name)
    output_sentiment_sum = find_sum_over_sentiment(output_sentiment)
    output_sentiment_sort = sort(output_sentiment_sum, attribute)
    return output_sentiment_sort

def find_city_location_hotels(lat, lon):
    print 'finder:: ' + str(lat) + ' ; ' + str(lon)
    elastic_results = es.find_location_hotels(lat, lon)
    output = []
    for item in elastic_results['hits']['hits']:
        item = item['_source']
        output.append(item)
    return output

'''
input: city_name
level 1: 
output: hashtag -> [hotel_id]
'''
def find_city_hashtags(city_name):
    output = {} # hashtag -> [(hotel_id, score)]
    most_talked_about = {}
    most_talked_about_arr = {}
    output_sentiment, output_adjective = find_city_all_hotels_attributes(city_name)
    for hotel_id in output_sentiment:
        if hotel_id not in most_talked_about:
            most_talked_about[hotel_id] = {}
        for path in output_sentiment[hotel_id]:
            s = sum(output_sentiment[hotel_id][path].values())
            most_talked_about[hotel_id][path] = s
        most_talked_about_arr[hotel_id] = most_talked_about[hotel_id].items()
        #print 'most: ' + str(most_talked_about_arr[hotel_id])
        most_talked_about_arr[hotel_id].sort(key=lambda x: x[1], reverse=True)
    
    for hotel_id in most_talked_about_arr:
        #print 'most: ' + str(most_talked_about_arr[hotel_id])
        for attr, attr_score in most_talked_about_arr[hotel_id]:
            adjective_values = output_adjective[hotel_id][attr].items()
            if adjective_values == []:
                print 'No adjective found for: ' + str(attr)
                continue
            adj, adj_score = adjective_values[0]
            hash_tag = adj + hash_tag_delim + attr
            hash_score = attr_score * adj_score
            if hash_tag not in output:
                output[hash_tag] = []
            output[hash_tag].append((hotel_id, hash_score))
    for hash_tag in output:
        output[hash_tag].sort(key=lambda x: x[1], reverse=True)
    return output

    
if __name__ == "__main__":
    result = {}
    search_type = sys.argv[1]
    if search_type == 'city_hotel':
        assert(len(sys.argv) >= 4)
        result = find_city_hotel_attributes(sys.argv[2], sys.argv[3])
    else:
        if search_type == 'city_attribute':
            assert(len(sys.argv) >= 4)
            result = find_city_attribute_top_hotels(sys.argv[2], sys.argv[3])
        else:
            if search_type == 'loc':
                assert(len(sys.argv) >= 4)
                result = find_city_location_hotels(sys.argv[2], sys.argv[3])
            else:
                if search_type == 'city_hash':
                    result = find_city_hashtags(sys.argv[2])
                else:
                    raise Exception('invalid search type: ' + search_type)
    pp = pprint.PrettyPrinter(depth=2)
    pp.pprint(result)