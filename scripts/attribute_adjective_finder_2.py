import json
import sys
sys.path.insert(0, '/Volumes/anupam work/review-app-local/scripts/lib/')
import operator

import language_functions as text_p

if __name__ == "__main__":
    attribute_seed = json.loads(open(sys.argv[1], 'r').read())
    attribute_adjective_map = json.loads(open(sys.argv[2], 'r').read())
    input_data = None
    if len(sys.argv) > 3:
        input_data = json.loads(open(sys.argv[3], 'r').read())
    text_p.load_for_adjectives()
    reverse_map = {}
    if input_data == None:
        user_input = raw_input("Some input please: ")
        while user_input != 'stop':
            path_with_score = text_p.find_attribute_2(attribute_seed, user_input)
            if path_with_score == None:
                'path is none for line: ' + str(line)
                continue
            print 'path_with_score: ' + str(path_with_score)
            path = map(lambda x: x[0], path_with_score)
            score = map(lambda x: x[1], path_with_score)
            adj_list = text_p.find_sentiment_adjective(attribute_adjective_map, path, user_input)
            print 'path: ' + str(path)
            print 'adjective list: ' + str(adj_list)
            user_input = raw_input("Some input please: ")
    else:
        for line in input_data:
            line = line.encode('utf-8')
            path_with_score = text_p.find_attribute_2(attribute_seed, line)
            if path_with_score == None or path_with_score == []:
                'path is none for line: ' + str(line)
                continue
            path = map(lambda x: x[0], path_with_score)
            score = map(lambda x: x[1], path_with_score)
            adj_list, sentiment = text_p.find_sentiment_adjective(attribute_adjective_map, path, line)
#            adj = adj_list[0][0]
#            adj_score = adj_list[0][1]
            
            cumulative_score = reduce(lambda x, y: x * y, score, 1.0)
            str_path = str(path)
            if str_path not in reverse_map:
                reverse_map[str_path] = []
            reverse_map[str_path].append([line, cumulative_score, adj_list])
    sorted_reverse_map = {}
    for key in reverse_map:
        sorted_reverse_map[key] = sorted(reverse_map[key], key=operator.itemgetter(1), reverse=True)
    f = open('sorted_reverse_map.json', 'w')
    f.write(json.dumps(sorted_reverse_map))
    f.close()
            