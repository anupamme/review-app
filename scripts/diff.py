import json
import sys

if __name__ == "__main__":
    a = json.loads(open(sys.argv[1], 'r').read())
    b = json.loads(open(sys.argv[2], 'r').read())
    c_f = 0
    c_nf = 0
    for item_b in b:
        found = False
        for item_a in a:
            if a[item_a]['name'] == b[item_b]['name']:
                found = True
                break
        if found:
            c_f += 1
            print 'found:' + b[item_b]['name'].encode('utf-8')
        else:
            c_nf += 1
            print 'not found:' + b[item_b]['name'].encode('utf-8')
    print 'stats: ' + str(c_f) + ' ; ' + str(c_nf)
        