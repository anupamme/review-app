import os
import json
import sys
import re

if __name__ == "__main__":
    inpDir = sys.argv[1]
    result = []
    for file1 in os.listdir(inpDir):
        path = os.path.join(inpDir, file1)
        data = open(path, 'r').read()
        result = result + re.split('\n|\.', data)
    f = open('total.json', 'w')
    f.write(json.dumps(result))
    f.close()