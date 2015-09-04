import json
import sys
sys.path.insert(0, '/Volumes/anupam work/review-app-local/scripts/lib/')

from clarifai.client import ClarifaiApi
import language_functions as image_p

if __name__ == "__main__":
    attribute_seed = json.loads(open(sys.argv[1], 'r').read())
    api = ClarifaiApi()
    user_input_url = raw_input("Some url please: ")
    image_p.load_model_files()
    while user_input_url != 'stop':
        arrToUse = [user_input_url]
        res = api.tag_image_urls(arrToUse)
        print 'clarifai result: ' + str(res)
        classes = res['results'][0]['result']['tag']['classes']
        probs = res['results'][0]['result']['tag']['probs']
        # now find the perfect category.
        path = []
        image_p.findBestCategory(classes, probs, attribute_seed['root'], path)
        print 'path: ' + str(path)
        user_input_url = raw_input("Some url please: ")
        