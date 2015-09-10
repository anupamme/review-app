'''
input: hotel_name -> attribute -> [(image_url, image_score)]
output: [{
    "id": count,
    "hotel_id": hotel_id,
    "attributes": [
        "value": "amenity",
        "value": "gym"
    ],
    "url": "my_url"
}]
'''

import sys
import json
import ast

if __name__ == "__main__":
    image_data = json.loads(open(sys.argv[1]).read())
    hotel_id = 0
    count = 0
    output_arr = []
    output_hotel = {}
    for hotel_name in image_data:
        output_hotel[hotel_id] = hotel_name
        attr_url_map = image_data[hotel_name]
        for attr_path_str in attr_url_map:
            image_arr = attr_url_map[attr_path_str]
            attr_path = ast.literal_eval(attr_path_str)
            attr_to_insert = map(lambda x: {"value": x}, attr_path)
            for image_url, image_score in image_arr:
                obj = {
                    "id": count,
                    "hotel_id": hotel_id,
                    "attributes": attr_to_insert,
                    "url": image_url,
                    "score": image_score
                }
                count += 1
                output_arr.append(obj)
        hotel_id += 1
        
    f = open('data/hotel_id.json', 'w')
    f.write(json.dumps(output_hotel))
    f.close()
    
    f = open('data/image_elastic.json', 'w')
    f.write(json.dumps(output_arr))
    f.close()