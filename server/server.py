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
city_hotel_id_file = 'data/city_hotel_id.json'

a = reqparse.RequestParser()
a.add_argument('search_str', type=str)

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

def do_attribute_query(city, attr_path):
    results = []
    if city == None or attr_path == None or len(attr_path) == 0:
        return None
    attr = attr_path[-1]
    return finder.find_city_attribute_top_hotels(city, attr)

def combine_results(attr_results, loc_results):
    if attr_results == None:
        return loc_results
    if loc_results == None:
        return attr_results
    if len(attr_results) >  len(loc_results):
        return attr_results
    return loc_results

class HelloHandler(restful.Resource):
    def get(self):
        args = a.parse_args()
        search_criterion = args.get('search_str')
        result_1 = text_p.find_attribute_2(app.attr_seed['root'], search_criterion)
        result = qp.process_request(result_1, app.hotel_name_data.keys(), app.attr_seed, search_criterion)
        print 'processed results: ' + str(result)
        loc_results = None
        if 'loc' in result:
            loc_arr = result['loc'] # array of {lat, lng} objects
            loc_results = do_location_query(loc_arr)
        attr_results = None
        if 'attr' in result:
            attr_path = result['attr']
            assert('city' in result)
            attr_results = do_attribute_query(result['city'], map(lambda x: x[0], attr_path))
        print 'loc_results: ' + str(loc_results)
        print 'attr_results: ' + str(attr_results)
        final_results = combine_results(attr_results, loc_results)
        return final_results, 200
        
if __name__ == "__main__":
    cors = CORS(app)
    app.config['CORS_HEADERS'] = 'Content-Type'
    api = restful.Api(app)
    api.add_resource(HelloHandler, '/hello')
    print 'running server...'
    app.run(debug=True, port=8080, host="localhost")