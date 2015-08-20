'''
input: image url
output: path
'''

import sys
import json
import time
import clarifai

from clarifai.client import ClarifaiApi
import image_attribute_map as i_map

if __name__ == "__main__":
    api = ClarifaiApi()
    i_map.loadModelFile()
    attribute_seed = json.loads(open(sys.argv[1], 'r').read())
    user_input = raw_input("Some image url please: ")
    while user_input != 'stop':
        response = api.tag_image_urls([user_input])
        output = response['results'][0]['result']['tag']
        print 'keywords: ' + str(output['classes'])
        path = []
        i_map.findBestCategory(output['classes'], output['probs'], attribute_seed['root'], path)
        print 'path: ' + str(path)
        user_input = raw_input("Some image url please: ")