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

import elastic_search as es

def find_path(item):
    return ['']

def find_sentiment(item):
    return ''

def find_adjective(item):
    return ''

if __name__ == "__main__":
    city_name = sys.argv[1]
    hotel_id = sys.argv[2]
    elastic_results = es.find_city_hotel_reviews(city_name, hotel_id)
    output_sentiment = {}
    output_adjective = {}
    for item in elastic_results:
        path = find_path(item)
        sentiment = find_sentiment(item)
        adjective = find_adjective(item)
        insert_or_increment(output_sentiment, path, sentiment)
        insert_or_increment(output_adjective, path, adjective)
        
    
    pretty_print(output_sentiment)
    pretty_print(output_adjective)
        