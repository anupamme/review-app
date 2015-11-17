import json
import sys

if __name__ == '__main__':
    input_data = json.loads(open(sys.argv[1], 'r').read())
    output = {}
    index = 0
    for item in input_data:
        sub = {}
        sub['name'] = item['name']
        sub['address'] = item['address']
        if 'location' in item:
            sub['location'] = item['location']
        else:
            sub['location'] = None
        output[index] = sub
        index += 1
    f = open(sys.argv[2], 'w')
    f.write(json.dumps(output))
    f.close()