import sys
import json
import ast
sys.path.insert(0, 'scripts/lib/')

import language_functions as i_map

'''
input: list of files (which are output of clarifai program)
output: data which can be inserted in elastic search server.

input data format: 

output data format:

'''

def write(data, file_name):
    f = open(file_name, 'w')
    f.write(json.dumps(data))
    f.close()

def merge(count):
    output = {}
    while count < len(sys.argv):
        json_obj = json.loads(open(sys.argv[count], 'r').read())
        for key in json_obj:
            output[key] = json_obj[key]
        count += 1
    return output

if __name__ == "__main__":
    i_map.load_model_files()
    attribute_seed = json.loads(open(sys.argv[1], 'r').read())
    city_hotel_images_map = merge(2)
    hotel_attr_image = {}
    print 'finding hotel attribute image map...'
    for city_name in city_hotel_images_map:
        hotel_attr_image[city_name] = {}
        for hotel_name in city_hotel_images_map[city_name]:
            hotel_attr_image[city_name][hotel_name] = {}
            if 'results' not in city_hotel_images_map[city_name][hotel_name]:
                print 'not_results: ' + city_name + ' ; ' + hotel_name
                if '0' not in city_hotel_images_map[city_name][hotel_name]:
                    print 'no index found: ' + city_name + ' ; ' + hotel_name
                    continue
                else:
                    print 'index found for the hotel.'
                    images_arr = city_hotel_images_map[city_name][hotel_name]['0']['results']
            else: 
                images_arr = city_hotel_images_map[city_name][hotel_name]['results']
            for image in images_arr:
                if 'tag' in image['result']:
                    path_with_score = []
                    i_map.findBestCategory_2(image['result']['tag']['classes'], image['result']['tag']['probs'], attribute_seed['root'], path_with_score)
                    assert(path_with_score != None)
                    assert(path_with_score != [])
                    path = map(lambda x: x[0], path_with_score)
                    str_path = str(path)
#                    if path_str not in result[hotel_name]:
#                        result[hotel_name][path_str] = []
                    final_score = path_with_score[len(path_with_score) - 1][1]
                    
                    if str_path not in hotel_attr_image[city_name][hotel_name]:
                        hotel_attr_image[city_name][hotel_name][str_path] = []
                    hotel_attr_image[city_name][hotel_name][str_path].append([image['url'], final_score])
            
    write(hotel_attr_image, 'data/images/hotel_attr_image.json')
    print 'converting the data to elastic search data format...'
    # convert this data into elastic search input format.
    hotel_id = 0
    output_arr = []
    output_hotel = {}
    count = 0
    for city_name in hotel_attr_image:
        output_hotel[city_name] = {}
        for hotel_name in hotel_attr_image[city_name]:
            output_hotel[city_name][hotel_id] = hotel_name
            attr_url_map = hotel_attr_image[city_name][hotel_name]
            for attr_path_str in attr_url_map:
                image_arr = attr_url_map[attr_path_str]
                attr_path = ast.literal_eval(attr_path_str)
                attr_to_insert = map(lambda x: {"value": x}, attr_path)
                #print 'image_arr: ' + str(image_arr)
                for image_url, image_score in image_arr:
                    obj = {
                        "id": count,
                        "hotel_id": hotel_id,
                        "attributes": attr_to_insert,
                        "url": image_url,
                        "score": image_score,
                        "city_id": city_name
                    }
                    count += 1
                    output_arr.append(obj)
            hotel_id += 1
            
    write(output_arr, 'data/images/hotel_image_elastic.json')
    write(output_hotel, 'data/images/hotel_id.json')