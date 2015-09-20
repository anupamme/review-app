import json
import sys

if __name__ == "__main__":
    output = {}
    count = 1
    while count < len(sys.argv):
        json_obj = json.loads(open(sys.argv[count], 'r').read())
        for key in json_obj:
            output[key] = json_obj[key]
        count += 1
    f = open('merge.json', 'w')
    f.write(json.dumps(output))
    f.close()