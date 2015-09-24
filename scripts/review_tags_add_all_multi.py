import json
import sys
import re
sys.path.insert(0, 'scripts/lib/')
import multiprocessing as mp
import random

import language_functions as text_p

count_so_far = -1
hotels_so_far = -1
elastic_count = 0
review_count = 0
output_hotel_id_review_id = {}      #hotel_id -> review_id -> review_object

seed_file = 'data/tree-data/percolate_6.json'
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

def find_to_insert(obj):
    if 'adjective' in obj:
        return obj['adjective']
    if 'noun' in obj:
        return obj['noun']
    if 'adverb' in obj:
        return obj['adverb']
    print 'warn: unknown type: ' + str(obj)
    return None

def parse_review(attribute_seed, attribute_adjective_map, raw_review, city_id, hotel_id):
    global elastic_count
    global review_count
    global output_hotel_id_review_id
    if 'description' not in raw_review:
        print 'description not present in review: ' + str(raw_review)
        return None
    complete_review = ''.join(raw_review['description']).encode('utf-8')
    review_sentences = re.split('\.|\?| !', complete_review)
    review_sentences_encode = []
    for sent in review_sentences:
        try: 
            review_sentences_encode.append(sent.encode('utf-8'))
        except UnicodeDecodeError:
            print 'error 01: ' + city_id + ' ; ' + hotel_name.encode('utf-8') + ' ; ' + str(review_count)
            continue
    result = []
    for sent in review_sentences_encode:
        result.append(get_review_details(attribute_seed, attribute_adjective_map, sent))
    
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
        if len(obj['adj_list']) > 0 and obj['adj_list'][0] != None:
            val = obj['adj_list'][0]
            val_to_insert = []
            adj_to_insert = None
            print 'val: ' + str(val)
            val_type = type(val[0])
            if val_type == dict:
                adj_to_insert = find_to_insert(val[0])
                assert(adj_to_insert != None)
            else:
                assert(val_type == str or val_type == unicode)
                adj_to_insert = val[0]

            val_to_insert.append(adj_to_insert)
            val_to_insert.append(val[1])
            adj_list_map[attr] = val_to_insert # only the first element
        else:
            adj_list_map[attr] = []
        sentence_map[attr] = sentence_count
        score_map[attr] = score
        sentence_count += 1

    attr_to_insert_2 = map(lambda x: {"value": x}, adj_list_map)
    formed_object = {
        "city_id": city_id,
        "id": elastic_count,
        "hotel_id": hotel_id,
        "review_id": review_count,
        "attribute_list": attr_to_insert_2,
        "sentiment": sentiment_map,
        "adjective_list": adj_list_map,
        "attribute_line": sentence_map,
        "score": score_map
    }
    output_hotel_id_review_id[city_id][hotel_id][review_count] = complete_review
    elastic_count += 1
    review_count += 1
    return formed_object

if __name__ == "__main__":
    attribute_seed = load_json(seed_file)
    attribute_adjective_map = load_json(adjective_file)
    global review_count
    global output_hotel_id_review_id
    
    text_p.load_for_adjectives()
    # read the data
    hotel_id_map = load_json(hotel_id_file)
    output = []
    count = count_so_far + 1
    hotel_count = 0
    
    if len(sys.argv) == 1:
        user_input = raw_input("Some input please: ")
        while user_input != 'stop':
            formed_object = parse_review(attribute_seed, attribute_adjective_map, user_input, 'NA', -1, -1)
            print 'elastic obj: ' + str(formed_object)
            user_input = raw_input("Some input please: ")
    else:
        pool = mp.Pool(processes=int(sys.argv[2]))
        meta_review_data = json.loads(open(sys.argv[1], 'r').read())
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
                review_count = 0
                result = [pool.apply(parse_review, args=(attribute_seed, attribute_adjective_map, x, city_id, hotel_id)) for x in reviews]
                for obj in result:
                    if obj == None or obj == {}:
                        continue
                    output.append(formed_object)
                
#                if elastic_count % 1000 == 0:
#                    f = open('hotel_review_elastic_' + str(count) + '.json', 'w')
#                    f.write(json.dumps(output))
#                    f.close()
#                    output = []
#                    f = open('hotel_review_id_' + str(count) + '.json', 'w')
#                    f.write(json.dumps(output_hotel_id_review_id))
#                    f.close()
#                    output_hotel_id_review_id = {}
#                    output_hotel_id_review_id[city_id] = {}
#                    output_hotel_id_review_id[city_id][hotel_id] = {}


        f = open('hotel_review_id.json', 'w')
        f.write(json.dumps(output_hotel_id_review_id))
        f.close()

        f = open('hotel_review_elastic.json', 'w')
        f.write(json.dumps(output))
        f.close()