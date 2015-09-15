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

import language_functions as text_p
text_p.load_for_adjectives()

def get_review_details(attribute_seed, attribute_adjective_map, sent):
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
    #print 'path: ' + str(path)
    #print 'sentiment: ' + str(sentiment)
    #print 'adj_list: ' + str(adj_list)
    print 'sent, path: ' + sent + ' ; ' + str(path)
    obj = {'sent': sent, 'path': path, 'sentiment': sentiment, 'adj_list': adj_list }
    #result.append(obj)
    return obj

if __name__ == '__main__':
    attribute_seed = json.loads(open(sys.argv[1], 'r').read())
    attribute_adjective_map = json.loads(open(sys.argv[2], 'r').read())
    print 'initing...'
    print 'finished initing...'
    # read the data
    #review_data = json.loads(open(sys.argv[3], 'r').read())
    #hotel_id_map = json.loads(open(sys.argv[4], 'r').read())
    
    pool = mp.Pool(processes=4)
    
    print 'init results...'
    stamp_init = time.time()
    results = [pool.apply_async(get_review_details, args=(attribute_seed, attribute_adjective_map, x,)) for x in [ "wine was the best", "service was lousy"]]
    stamp_end = time.time()
    print 'end results...' + str(stamp_end - stamp_init)
#    result = []
#    for sent in ['food was awesome', 'service was lousy', 'room was disgusting']:
#        item = pool.apply_async(get_review_details, args=(attribute_seed, attribute_adjective_map, sent, result))
#    print 'results: ' + str(result)
    #print 'results: ' + str(results)
    print 'all done!'
    for item in results:
        print 'item: ' + str(item.get())
    print 'all done done!'
    output = [p.get() for p in results]
    print 'all done done done!'
    print(output)