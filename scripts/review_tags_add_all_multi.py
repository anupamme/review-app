import json
import sys
import re
sys.path.insert(0, '/Volumes/anupam work/review-app-local/scripts/lib/')
import multiprocessing as mp

import language_functions as text_p

count_so_far = -1
hotels_so_far = -1

def get_hotel_id(hotel_name, hotel_id_map):
    for key in hotel_id_map:
        if hotel_name == hotel_id_map[key]:
            return key
    return -1

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
    return {'path': path, 'sentiment': 1, 'adj_list': [] }

if __name__ == "__main__":
    attribute_seed = json.loads(open(sys.argv[1], 'r').read())
    attribute_adjective_map = json.loads(open(sys.argv[2], 'r').read())
    
    text_p.load_for_adjectives()
    # read the data
    review_data = json.loads(open(sys.argv[3], 'r').read())
    hotel_id_map = json.loads(open(sys.argv[4], 'r').read())
    output = []
    output_hotel_id_review_id = {}      #hotel_id -> review_id -> review_object
    count = count_so_far + 1
    hotel_count = 0
    
    pool = mp.Pool(processes=int(sys.argv[3]))
    
    for val in review_data:
        if hotel_count < hotels_so_far:
            hotel_count += 1
            continue
        
        hotel_count += 1
        hotel_name = val['name']
        hotel_id = get_hotel_id(hotel_name, hotel_id_map)
        if hotel_id == -1:
            print 'hotel_id not found for ' + hotel_name
            continue
        output_hotel_id_review_id[hotel_id] = {}
        reviews = val['reviews']
        rev_id = 0
        for rev in reviews:
            output_hotel_id_review_id[hotel_id][rev_id] = rev
            complete_review = ''.join(rev['description'])
            review_sentences = re.split('\.|\?| !', complete_review)
            result = []
            for sent in review_sentences:
                sent = sent.encode('utf-8')
                item = get_review_details(attribute_seed, attribute_adjective_map, sent)
                item = pool.apply_async(get_review_details, args=(attribute_seed, attribute_adjective_map, sent))
                if item != None:
                    result.append(item)
            print 'result: ' + str(result)
            attr_to_insert = []
            sentiment_map = {}
            adj_list_map = {}
            sentence_map = {}
            sentence_count = 0
            for obj in result:
                if obj['path'] == None or obj['path'] == []:
                    sentence_count += 1
                    continue
                attr = obj['path'][len(obj['path']) - 1]
                attr_to_insert.append(attr)
                sentiment_map[attr] = obj['sentiment']
                adj_list_map[attr] = obj['adj_list']
                sentence_map[attr] = sentence_count
                sentence_count += 1
            
            attr_to_insert_2 = map(lambda x: {"value": x}, adj_list_map)
            formed_object = {
                "id": count,
                "hotel_id": hotel_id,
                "review_id": rev_id,
                "attribute_list": attr_to_insert_2,
                "sentiment": sentiment_map,
                "adjective_list": adj_list_map,
                "attribute_line": sentence_map
            }
            count += 1
            rev_id += 1
            output.append(formed_object)
            
            if count % 1000 == 0:
                f = open('hotel_review_elastic_' + str(count) + '.json', 'w')
                f.write(json.dumps(output))
                f.close()
                output = []
                f = open('hotel_review_id_' + str(count) + '.json', 'w')
                f.write(json.dumps(output_hotel_id_review_id))
                f.close()
                output_hotel_id_review_id = {}
                output_hotel_id_review_id[hotel_id] = {}
    
    
    f = open('hotel_review_id.json', 'w')
    f.write(json.dumps(output_hotel_id_review_id))
    f.close()
    
    f = open('hotel_review_elastic.json', 'w')
    f.write(json.dumps(output))
    f.close()