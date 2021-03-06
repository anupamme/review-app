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

def merge(city_name, count):
    output = {}
    output[city_name] = {}
    while count < len(sys.argv):
        file_name = sys.argv[count]
        print 'opening file_name: ' + file_name
        json_obj = json.loads(open(file_name, 'r').read())
        for hotel_name in json_obj:
            output[city_name][hotel_name] = json_obj[hotel_name]
        count += 1
    return output

city_hotel_details_map = {}

def is_equal(name1, name2):
    if name1.lower() == name2.lower():
        return True
    return False
    
def is_subset(name1, name2):
    name1_lower = name1.lower()
    name2_lower = name2.lower()
    if name1_lower in name2_lower:
        return True
    if name2_lower in name1_lower:
        return True
    return False

def get_hotel_id(name):
    for hotel_id in city_hotel_details_map:
        if is_equal(city_hotel_details_map[hotel_id]['name'], name):
            return hotel_id
    for hotel_id in city_hotel_details_map:
        if is_subset(name, city_hotel_details_map[hotel_id]['name']):
            print 'Approx Value: ' + city_hotel_details_map[hotel_id]['name']
            return hotel_id
    print 'warn: no hotel id found for: ' + name
    return -1

if __name__ == "__main__":
    i_map.load_model_files()
    attribute_seed = json.loads(open(sys.argv[1], 'r').read())
    city_name = sys.argv[2]
    global city_hotel_details_map
    city_hotel_details_map = json.loads(open(sys.argv[3], 'r').read())
    city_hotel_images_map = merge(city_name, 4)
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
    output_arr = []
    output_hotel = {}
    count = 0
    for city_name in hotel_attr_image:
        output_hotel[city_name] = {}
        for hotel_name in hotel_attr_image[city_name]:
            try:
                print 'searching for: ' + hotel_name.encode('utf-8')
            except UnicodeEncodeError:
                print 'unicode error.'
            hotel_id = get_hotel_id(hotel_name)
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
            
    write(output_arr, 'data/images/' + city_name + '_image_elastic.json')
    write(output_hotel, 'data/images/hotel_id.json')