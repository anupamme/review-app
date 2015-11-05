import multiprocessing as mp
import urllib2
import json
import sys
import re
sys.path.insert(0, '/Volumes/anupam work/review-app-local/scripts/lib/')
import time
'''
to run: python multi_process.py data/tree-data/percolate_4.json data/antonyms/reverse_adj.json
'''

attribute_seed = None
attribute_adjective_map = None

import language_functions as text_p
text_p.load_for_adjectives()
    
def get_review_details(sent):
    try:
        path_with_score = text_p.find_attribute_2(attribute_seed, sent)
        if path_with_score == None or path_with_score == []:
            'path is none for line: ' + str(sent)
            return None
        #print 'path_with_score: ' + str(path_with_score)
        path = map(lambda x: x[0], path_with_score)
        score = map(lambda x: x[1], path_with_score)
        #print 'score: ' + str(score)
        cumulative_score = reduce(lambda x, y: x * y, score, 1.0)
        adj_list, sentiment = text_p.find_sentiment_adjective(attribute_adjective_map, path, sent)
    except TypeError:
        print 'Type Error in attribute_adjective_finder for line: ' + str(sent)
        return None
    obj = {'sent': sent, 'path': path, 'sentiment': sentiment, 'adj_list': adj_list }
    return obj

if __name__ == '__main__':
    global attribute_seed
    global attribute_adjective_map
    attribute_seed = json.loads(open(sys.argv[1], 'r').read())
    attribute_adjective_map = json.loads(open(sys.argv[2], 'r').read())
    print 'initing...'
    print 'finished initing...'
    # read the data
    #review_data = json.loads(open(sys.argv[3], 'r').read())
    #hotel_id_map = json.loads(open(sys.argv[4], 'r').read())
    
    pool = mp.Pool(processes=2)
    print 'init results...'
    stamp_init = time.time()
#    results = poo.map(get_review_details, [0, 1, 2])
    results = [pool.apply(get_review_details, args=(x,)) for x in ["wine was the best", "service was lousy", "pool was unclean", "gym was big and functional", "view from the room was fantastic", "we really enjoyed having brunch in their lobby with breeze and awesome view", "we were greeted so warmly by their staff that we felt at home"]]
    stamp_end = time.time()
    print 'end results...' + str(stamp_end - stamp_init)
#    result = []
#    for sent in ['food was awesome', 'service was lousy', 'room was disgusting']:
#        item = pool.apply_async(get_review_details, args=(attribute_seed, attribute_adjective_map, sent, result))
#    print 'results: ' + str(result)
    #print 'results: ' + str(results)
    print 'all done!'
    for item in results:
        print 'item: ' + str(item)
    print 'all done done!'
#    output = [p.get() for p in results]
#    print 'all done done done!'
#    print(output)