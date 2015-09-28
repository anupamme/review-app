
import sys
import json
from elasticsearch import Elasticsearch
client = Elasticsearch()
'''
Input: 
    type: review, images, distance
    value: attribute (for review or images), (lat, long) and radius for distance
    ranking: ?
    return: set of results which satisfy the criterion

'''

def find_reviews_for_attribute(search_attribute):
    response = client.search(
                index="hn_reviews",
                size=10000,
                pretty=True,
                body={
                    "query": {
                        "nested": {
                            "path": "attribute_list",
                            "query": {
                                "bool": {
                                    "must": [
                                        { "match": {"attribute_list.value": search_attribute}}
                                    ]
                                }
                            }
                        }
                    }
                }
            )
    return response

def find_images_for_attribute(search_attribute):
    response = client.search(
            index="hn",
            size=10000,
            body={
                "query": {
                    "nested": {
                        "path": "attributes",
                        "query": {
                            "bool": {
                                "must": [
                                    { "match": {"attributes.value": search_attribute}}
                                ]
                            }
                        }
                    }
                }
            }
        )
    return response



def find_city_hotel_reviews(city_name, hotel_id):
    response = {}
    response = client.search(
            index="hn_reviews",
            size=10000,
            body={
                "query" : {
                    "bool": {
                        "must": [
                            { "match": { "hotel_id":  hotel_id }},
                            { "match": { "city_id": city_name }}
                        ]
                    }
                }
            }
        )
    return response

def find_location_hotels(lat, lon):
    response = {}
    response = client.search(
        index="hn_distance",
        size=10000,
        body={
        "query":{
            "filtered":{
                    "query":{
                        "match_all":{}
                    },  
                    "filter":{
                        "geo_distance":{
                            "distance":"10km",
                            "location":{
                                "lat":lat,
                                "lon":lon
                            }
                        }
                    }
                }
            }
        }
    )
    return response
    

def find_city_reviews(city_name):
    response = {}
    response = client.search(
            index="hn_reviews",
            size=100000,
            body={
                "query" : {
                    "bool": {
                        "must": [
                            { "match": { "city_id": city_name }}
                        ]
                    }
                }
            }
        )
    return response

if __name__ == "__main__":
    search_type = sys.argv[1]
    response = {}
    if search_type == 'image':
        search_val = sys.argv[2]
        response = client.search(
            index="hn",
            size=10000,
            body={
                "query": {
                    "nested": {
                        "path": "attributes",
                        "query": {
                            "bool": {
                                "must": [
                                    { "match": {"attributes.value": search_val}}
                                ]
                            }
                        }
                    }
                }
            }
        )
    else:
        if search_type == 'review':
            search_val = sys.argv[2]
            response = client.search(
                index="hn_reviews",
                size=10000,
                pretty=True,
                body={
                    "query": {
                        "nested": {
                            "path": "attribute_list",
                            "query": {
                                "bool": {
                                    "must": [
                                        { "match": {"attribute_list.value": search_val}}
                                    ]
                                }
                            }
                        }
                    }
                }
            )
        else:
            if search_type == 'distance':
                radius = float(sys.argv[2])
                lat = float(sys.argv[3])
                lon = float(sys.argv[4])
                response = client.search(
                    index="hn_distance",
                    size=100000,
                    pretty=True,
                    body={
                        "query":{
                            "filtered":{
                                    "query":{
                                        "match_all":{}
                                    },  
                                    "filter":{
                                        "geo_distance":{
                                            "distance": str(radius) + "km",
                                            "location":{
                                                "lat":lat,
                                                "lon":lon
                                            }
                                        }
                                    }
                                }
                            }
                        }
                )
            else:
                if search_type == 'hotel_id':
                    response = find_city_hotel_reviews(sys.argv[2], int(sys.argv[3]))
    print str(response)

    
        