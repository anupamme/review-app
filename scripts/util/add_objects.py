import json
import sys

if __name__ == "__main__":
    output = []
    count = 1
    while count < len(sys.argv):
        print 'opening...: ' + str(sys.argv[count])
        json_arr = json.loads(open(sys.argv[count], 'r').read())
        print 'length: ' + str(len(json_obj))
        output = output + json_arr
        count += 1
    
    print 'total_length: ' + str(len(output))
    f = open('append.json', 'w')
    f.write(json.dumps(output))
    f.close()