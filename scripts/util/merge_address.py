import json
import sys

def find_id(hotel_name_data, name):
    for hotel_id in hotel_name_data:
        if hotel_name_data[hotel_id] == name:
            return hotel_id
    return -1

if __name__ == "__main__":
    crawler_data = json.loads(open(sys.argv[1], 'r').read())
    hotel_name_data = json.loads(open(sys.argv[2], 'r').read())
    output = {}
    for hotel_item in crawler_data:
        hotel_id = find_id(hotel_name_data['marrakech'], hotel_item['name'])
        obj = {}
        obj['name'] = hotel_item['name']
        obj['address'] = hotel_item['address']
        if 'location' in hotel_item:
            obj['location'] = hotel_item['location']
        output[hotel_id] = obj
    f = open(sys.argv[3], 'w')
    f.write(json.dumps(output))
    f.close()