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

if __name__ == "__main__":
    city_name = sys.argv[1]
    hotel_name = sys.argv[2]
    hotel_id = get_hotel_id_name(city_name, hotel_name)
    elastic_results = get_elastic_results(city_name, hotel_id)
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
        