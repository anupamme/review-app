import json
import sys

default_delim = '\t'

if __name__=="__main__":
    input_file = sys.argv[1]
    delim_to_use = default_delim
    if len(sys.argv) > 2:
        delim_to_use = sys.argv[2]
    input_data = json.loads(open(input_file, 'r').read())
    output = ""
    for key in input_data:
        str_to_write = key + delim_to_use + input_data[key] + '\n'
        output = output + str_to_write
    f = open('json_str.txt', 'w')
    f.write(output)
    f.close()