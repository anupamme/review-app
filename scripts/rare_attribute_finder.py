'''
input:  list of reviews.
        rare_decision tree.
output: rare_attribute, frequency
        rare_attribute_sentiment_map
        rare_attribute_sentences_map
'''

import json
import sys
sys.path.insert(0, '/Volumes/anupam_work/code/nlp-code/scripts/')
import language_functions as text_p
import re

rare_decision_tree = '/Volumes/anupam_work/code/showup-code/holidayiq/data/unique_3.json'

min_threshhold = 4.0
min_elements = 8

if __name__ == "__main__":
    #load models
    text_p.load_for_adjectives()
    # read decision tree as well.
    decision_tree = json.loads(open(rare_decision_tree, 'r').read())
    review_data = json.loads(open(sys.argv[1], 'r').read())
    output = {}
    for hotel_id in review_data:
        output[hotel_id] = {}
        review_list = review_data[hotel_id]
        for review_item in review_list:
            review_arr = re.split('\.|\?|!|\\r|\\n|;', review_item)
            for sent in review_arr:
                try:
                    sent_e = sent.encode('latin-1')
                except UnicodeEncodeError as e:
                    print 'UnicodeEncodeError: ' + str(e)
                    continue
                print('looking for: ' + str(sent))
                res_obj = text_p.find_attribute_2(decision_tree['root'], sent)
                if res_obj == None:
                    print 'nlp output is null for: ' + str(len)
                    continue
                path_with_score = res_obj['path']
                if path_with_score == None or path_with_score == []:
                    print 'path is none for line: ' + str(sent)
                    continue
                path = map(lambda x: x[0], path_with_score)
                score = map(lambda x: x[1], path_with_score)
                score_to_use = score[-1]
                attr = path[len(path) - 1]
                print 'attr, sent: ' + str(attr) + ' ; ' + str(sent)
                if attr in output[hotel_id]:
                    output[hotel_id][attr].append([sent, score_to_use])
                else:
                    output[hotel_id][attr] = [[sent, score_to_use]]
    
    output_sorted = {}
    for hotel_id in output:
        output_sorted[hotel_id] = {}
        for attr in output[hotel_id]:
            output_sorted[hotel_id][attr] = output[hotel_id][attr]
            output_sorted[hotel_id][attr].sort(key=lambda x: x[1], reverse=True)
    
    output_sorted_sorted = {}
    for hotel_id in output_sorted:
        output_arr = list(output_sorted[hotel_id].items())
        output_arr.sort(key=lambda x: len(x[1]), reverse=True)
        output_sorted_sorted[hotel_id] = output_arr
    #print('output_arr: ' + str(output_arr))
    output_filtered = {}
    global min_threshhold
    for hotel_id in output_sorted_sorted:
        output_filtered[hotel_id] = []
        for item in output_sorted_sorted[hotel_id]:
            attr = item[0]
            sentences = item[1]
            if len(sentences) < min_elements:
                continue
            if sentences[min_elements - 1][1] < min_threshhold:
                continue
            #print('#adding item: ' + str(sentences[min_elements - 1]))
            output_filtered[hotel_id].append(item)
            
    f = open('output_sorted_4.json', 'w')
    f.write(json.dumps(output_filtered))
    f.close()