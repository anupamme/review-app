import json
import attribute_adjective_finder as finder
import sys

if __name__ == "__main__":
    attribute_seed = json.loads(open(sys.argv[1], 'r').read())
    attribute_adjective_map = json.loads(open(sys.argv[2], 'r').read())
    
    finder.init()
    user_input = raw_input("Some input please: ")
    while user_input != 'stop':
        path, sentiment, correct_adj_list, adj_list = finder.find_meta_data(user_input, attribute_seed, attribute_adjective_map)
        print 'path: ' + str(path)
        user_input = raw_input("Some input please: ")