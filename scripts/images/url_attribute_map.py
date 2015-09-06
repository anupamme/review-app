import json
import sys
sys.path.insert(0, '/Volumes/anupam work/review-app-local/scripts/lib/')
import operator

from clarifai.client import ClarifaiApi
import language_functions as image_p

if __name__ == "__main__":
    attribute_seed = json.loads(open(sys.argv[1], 'r').read())
    image_p.load_model_files()
    if len(sys.argv) == 2:
        api = ClarifaiApi()
        user_input_url = raw_input("Some url please: ")
        while user_input_url != 'stop':
            arrToUse = [user_input_url]
            res = api.tag_image_urls(arrToUse)
            print 'clarifai result: ' + str(res)
            classes = res['results'][0]['result']['tag']['classes']
            probs = res['results'][0]['result']['tag']['probs']
            # now find the perfect category.
            path = []
            image_p.findBestCategory_2(classes, probs, attribute_seed['root'], path)
            print 'path: ' + str(path)
            user_input_url = raw_input("Some url please: ")
    else:
        assert(len(sys.argv) == 3)
        result = {}
        input_data = json.loads(open(sys.argv[2], 'r').read())
        for hotel_name in input_data:
            for image_item in input_data[hotel_name]['results']:
                if 'tag' not in image_item['result']:
                    print 'error 01: No tag item in item: ' + str(image_item['result'])
                    continue
                classes = image_item['result']['tag']['classes']
                probs = image_item['result']['tag']['probs']
                path_with_score = []
                image_p.findBestCategory_2(classes, probs, attribute_seed['root'], path_with_score)
                assert(path_with_score != None)
                assert(path_with_score != [])
                path = map(lambda x: x[0], path_with_score)
                path_str = str(path)
                if path_str not in result:
                    result[path_str] = []
                final_score = path_with_score[len(path_with_score) - 1][1]
                url = image_item['url']
                result[path_str].append([url, final_score])
        sorted_result = {}
        for path_key in result:
            sorted_result[path_key] = sorted(result[path_key], key=operator.itemgetter(1), reverse=True)
        f = open('path_image_score.json', 'w')
        f.write(json.dumps(sorted_result))
        f.close()