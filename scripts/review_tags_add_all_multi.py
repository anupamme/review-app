import json
import sys
import re
sys.path.insert(0, 'scripts/lib/')
import multiprocessing as mp
import random

import language_functions as text_p

count_so_far = -1
hotels_so_far = -1

seed_file = 'data/tree-data/percolate_4.json'
adjective_file = 'data/antonyms/reverse_adj.json'
hotel_id_file = 'data/images/hotel_id.json'

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
    return {'path': path, 'sentiment': sentiment, 'adj_list': adj_list, 'cumulative_score': cumulative_score}

def load_json(file_name):
    return json.loads(open(file_name, 'r').read())

if __name__ == "__main__":
    attribute_seed = load_json(seed_file)
    attribute_adjective_map = load_json(adjective_file)
    
    text_p.load_for_adjectives()
    # read the data
    meta_review_data = json.loads(open(sys.argv[1], 'r').read())
    hotel_id_map = load_json(hotel_id_file)
    output = []
    output_hotel_id_review_id = {}      #hotel_id -> review_id -> review_object
    count = count_so_far + 1
    hotel_count = 0
    
    pool = mp.Pool(processes=int(sys.argv[2]))
    
    for city_id in meta_review_data:
        print 'city_id: ' + str(city_id)
        review_data = meta_review_data[city_id]
        output_hotel_id_review_id[city_id] = {}
        for val in review_data:
            if hotel_count < hotels_so_far:
                hotel_count += 1
                continue

            hotel_count += 1
            hotel_name = val['name']
            print 'hotel_name: ' + hotel_name
            hotel_id = get_hotel_id(hotel_name, hotel_id_map[city_id])
            if hotel_id == -1:
                print 'hotel_id not found for ' + hotel_name
                hotel_id = random.randint(100, 1000)
                #continue
            output_hotel_id_review_id[city_id][hotel_id] = {}
            reviews = val['reviews']
            rev_id = 0
            for rev in reviews:
                #rev['description'] = rev['description'].encode('utf-8')
                output_hotel_id_review_id[city_id][hotel_id][rev_id] = rev
                complete_review = ''.join(rev['description'])
                complete_review = complete_review.encode('utf-8')
                review_sentences = re.split('\.|\?| !', complete_review)
                review_sentences_encode = []
                for sent in review_sentences:
                    try: 
                        review_sentences_encode.append(sent.encode('utf-8'))
                    except UnicodeDecodeError:
                        print 'error 01: ' + city_id + ' ; ' + hotel_name.encode('utf-8') + ' ; ' + str(rev_id)
                        continue
                #result = []
                result = [pool.apply(get_review_details, args=(attribute_seed, attribute_adjective_map, x,)) for x in review_sentences_encode]
    #            for sent in review_sentences:
    #                sent = sent.encode('utf-8')
    #                item = get_review_details(attribute_seed, attribute_adjective_map, sent)
    #                
    #                if item != None:
    #                    result.append(item)
                #print 'result: ' + str(result)
                sentiment_map = {}
                adj_list_map = {}
                sentence_map = {}
                score_map = {}
                sentence_count = 0
                for obj in result:
                    if obj == None or obj['path'] == None or obj['path'] == []:
                        sentence_count += 1
                        continue
                    attr = obj['path'][len(obj['path']) - 1]
                    score = obj['cumulative_score']
                    sentiment_map[attr] = obj['sentiment']
                    adj_list_map[attr] = obj['adj_list'][0] # only the first element
                    sentence_map[attr] = sentence_count
                    score_map[attr] = score
                    sentence_count += 1

                attr_to_insert_2 = map(lambda x: {"value": x}, adj_list_map)
                formed_object = {
                    "city_id": city_id,
                    "id": count,
                    "hotel_id": hotel_id,
                    "review_id": rev_id,
                    "attribute_list": attr_to_insert_2,
                    "sentiment": sentiment_map,
                    "adjective_list": adj_list_map,
                    "attribute_line": sentence_map,
                    "score": score_map
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
                    output_hotel_id_review_id[city_id] = {}
                    output_hotel_id_review_id[city_id][hotel_id] = {}
    
    
    f = open('hotel_review_id.json', 'w')
    f.write(json.dumps(output_hotel_id_review_id))
    f.close()
    
    f = open('hotel_review_elastic.json', 'w')
    f.write(json.dumps(output))
    f.close()