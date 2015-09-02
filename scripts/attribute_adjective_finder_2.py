import json
import sys
sys.path.insert(0, '/Volumes/anupam work/review-app-local/scripts/lib/')

import language_functions as text_p

if __name__ == "__main__":
    attribute_seed = json.loads(open(sys.argv[1], 'r').read())
    attribute_adjective_map = json.loads(open(sys.argv[2], 'r').read())
    text_p.load_for_adjectives()
    user_input = raw_input("Some input please: ")
    while user_input != 'stop':
        path = text_p.find_attribute_2(attribute_seed, user_input)
        adj_list = text_p.find_sentiment_adjective(attribute_adjective_map, path, user_input)
        print 'path: ' + str(path)
        print 'adjective list: ' + str(adj_list)
        user_input = raw_input("Some input please: ")