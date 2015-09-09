import multiprocessing as mp
import urllib2
import json
import sys
import re
sys.path.insert(0, '/Volumes/anupam work/review-app-local/scripts/lib/')

import language_functions as text_p

def get_review_details(attribute_seed, attribute_adjective_map, sent):
    try:
        print 'before call find_attribute_2'
        path_with_score = text_p.find_attribute_2(attribute_seed, sent)
        if path_with_score == None or path_with_score == []:
            'path is none for line: ' + str(sent)
            return None
        #print 'path_with_score: ' + str(path_with_score)
        path = map(lambda x: x[0], path_with_score)
        score = map(lambda x: x[1], path_with_score)
        #print 'score: ' + str(score)
        cumulative_score = reduce(lambda x, y: x * y, score, 1.0)
        print 'before call find_sentiment_adjective'
        adj_list, sentiment = text_p.find_sentiment_adjective(attribute_adjective_map, path, sent)
    except TypeError:
        print 'Type Error in attribute_adjective_finder for line: ' + str(sent)
        return None
    print 'path: ' + str(path)
    print 'sentiment: ' + str(sentiment)
    print 'adj_list: ' + str(adj_list)
    return {'path': path, 'sentiment': sentiment, 'adj_list': adj_list }

if __name__ == '__main__':
    attribute_seed = json.loads(open(sys.argv[1], 'r').read())
    attribute_adjective_map = json.loads(open(sys.argv[2], 'r').read())
    print 'initing...'
    text_p.load_for_adjectives()
    print 'finished initing...'
    # read the data
    #review_data = json.loads(open(sys.argv[3], 'r').read())
    #hotel_id_map = json.loads(open(sys.argv[4], 'r').read())
    
    pool = mp.Pool(processes=1)
    
    results = [pool.apply_async(get_review_details, args=(attribute_seed, attribute_adjective_map, x,)) for x in ['food was awesome', 'service was lousy', 'room was disgusting']]
    output = [p.get() for p in results]
    print(output)