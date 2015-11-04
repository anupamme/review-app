import cgi
import webapp2

import json
import re
from os import path
import sys
import urllib2
import elasticsearch
#import urllib3
from elasticsearch import Elasticsearch
from google.appengine.api import urlfetch
import requests

url = 'http://104.197.70.181:9200/hn_reviews/'
client = elasticsearch.Elasticsearch(host='104.197.70.181', port=9200)
#search_url = 'http://104.197.70.181:9200/hn_reviews/'

def do_search():
    response = client.search(
        index="hn_reviews",
            size=100000,
            body={
                "query" : {
                    "bool": {
                        "must": [
                            { "match": { "city_id": 'marrakech' }}
                        ]
                    }
                }
            }
    )
    return response

class MainPage(webapp2.RequestHandler):

    def get(self):
        print 'before reading elastic search data:'
        #data = json.loads(urllib2.urlopen(search_url).read())
        #data = json.loads(urlfetch.fetch(search_url).content)
        data = json.loads(do_search())
        print 'data: ' + str(data)
        html = open('index.html', 'r').read()
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")
        self.response.headers['Content-Type'] = 'text/html'
    	self.response.write(html)

application = webapp2.WSGIApplication([('/', MainPage)], debug=True)