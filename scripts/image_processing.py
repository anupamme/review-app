import sys
import json
import time

import image_attribute_map as i_map

if __name__ == "__main__":
    i_map.loadModelFile()
    attribute_seed = json.loads(open(sys.argv[1], 'r').read())
    hotel_images_map = json.loads(open(sys.argv[2], 'r').read())
    hotel_attr_image = {}
    for hotel_name in hotel_images_map:
        hotel_attr_image[hotel_name] = {}
        images_arr = hotel_images_map[hotel_name]['results']
        for image in images_arr:
            if 'tag' in image['result']:
                path = []
                i_map.findBestCategory(image['result']['tag']['classes'], image['result']['tag']['probs'], attribute_seed['root'], path)
                assert(path != [])
                filtered_path = map(lambda x: x[0], path)
<<<<<<< HEAD
                str_path = json.dumps(filtered_path)
=======
                str_path = str(filtered_path)
>>>>>>> origin/master
                
                if str_path not in hotel_attr_image[hotel_name]:
                    hotel_attr_image[hotel_name][str_path] = []
                hotel_attr_image[hotel_name][str_path].append(image['url'])
    
<<<<<<< HEAD
    f = open('data/hotel_attr_image.json', 'w')
=======
    f = open('hotel_attr_image.json', 'w')
>>>>>>> origin/master
    f.write(json.dumps(hotel_attr_image))
    f.close()