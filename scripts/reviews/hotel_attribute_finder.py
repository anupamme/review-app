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
sys.path.insert(0, '../scripts/lib/')
import pprint

import elastic_search as es

def find_path(item):
    path_obj = {}
    for attr_root in item['attribute_list']:
        leaf_name = attr_root['value']
        path = find_path(leaf_name)
        score = item['score'][leaf_name]
        path_obj[str(path)] = score
    return path_obj

def find_sentiment(item):
    result = {}
    for leaf_attr in item['sentiment']:
        path = find_path(leaf_attr)
        result[str(path)] = item['sentiment'][leaf_attr]
    return result

def find_adjective(item):
    result = {}
    for leaf_attr in item['adjective_list']:
        path = find_path(leaf_attr)
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
        out[path][sent] += 1
        
def insert_or_increment_adjective(out, path_dict, adjective_dict):
    for path in path_dict:
        if path not in out:
            out[path] = {}
        score = path_dict[path]
        adj, adj_score = adjective_dict[path]
        if adj in out[path:
            out[path][adj] += adj_score
        else:
            out[path][adj] = adj_score
        

if __name__ == "__main__":
    city_name = sys.argv[1]
    hotel_id = sys.argv[2]
    elastic_results = es.find_city_hotel_reviews(city_name, hotel_id)
    output_sentiment = {}   # format is: 
    output_adjective = {}   # format is: 
    for item in elastic_results:
        path_dict = find_path(item)
        sentiment_dict = find_sentiment(item)
        adjective_dict = find_adjective(item)
        insert_or_increment(output_sentiment, path_dict, sentiment_dict)
        insert_or_increment_adjective(output_adjective, path_dict, adjective_dict)
        
    pp = pprint.PrettyPrinter(depth=3)
    pp.print(output_sentiment)
    pp.print(output_adjective)
        