import json
import sys

if __name__ == "__main__":
    output = {}
    count = 1
    while count < len(sys.argv):
        print 'opening...: ' + str(sys.argv[count])
        json_obj = json.loads(open(sys.argv[count], 'r').read())
        print 'length: ' + str(len(json_obj))
        for key in json_obj:
            if key in output:
                print 'key already present: ' + key.encode('utf-8')
            output[key] = json_obj[key]
        count += 1
    
    print 'total_length: ' + str(len(output))
    f = open('merge.json', 'w')
    f.write(json.dumps(output))
    f.close()