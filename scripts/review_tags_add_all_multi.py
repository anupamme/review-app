import json
import sys
import re
sys.path.insert(0, 'scripts/lib/')
import multiprocessing as mp
import random
import googlemaps
import gc

import language_functions as text_p

count_so_far = -1
hotels_so_far = -1
elastic_count = 0
review_count = 0
output_hotel_id_review_id = {}      #hotel_id -> review_id -> review_object
address_delim = ', '

seed_file = 'data/tree-data/percolate_10.json'
adjective_file = 'data/antonyms/reverse_adj_2.json'
hotel_id_file = 'data/hotel/city_hotel_details.json'
gmaps = googlemaps.Client(key='AIzaSyAXQ2pGkeUBhRZG4QNqy2t1AbzA6O3ToUU') 

def get_hotel_id(hotel_name, hotel_id_map):
    for key in hotel_id_map:
        if hotel_name == hotel_id_map[key]['name']:
            return key
    return -1

def get_review_details(attribute_seed, attribute_adjective_map, sent):
    try:
        res_obj = text_p.find_attribute_2(attribute_seed['root'], sent)
        path_with_score = res_obj['path']
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

def parse_review(attribute_seed, attribute_adjective_map, raw_review, city_id, hotel_id, item):
    global elastic_count
    global review_count
    address = None
    location = None
    if 'address' in item:
        address = item['address']
    if 'location' in item:
        location = item['location']
    #global output_hotel_id_review_id
#    if 'description' not in raw_review:
#        print 'description not present in review: ' + str(raw_review)
#        return None
#    complete_review = ''.join(raw_review['description']).encode('utf-8')
#    if raw_review == None:
#        print 'raw review is none: '
#        return None
    try:
        complete_review = raw_review
        review_sentences = re.split('\.|\?| !', complete_review)
    except Exception, e:
        print 'exception: ' + str(e)
    review_sentences_encode = []
    for sent in review_sentences:
        try: 
            review_sentences_encode.append(sent.encode('utf-8'))
        except UnicodeDecodeError:
            print 'error 01: ' + city_id + ' ; ' + str(hotel_id) + ' ; ' + str(review_count)
            continue
    result = []
    for sent in review_sentences_encode:
        sent = sent.strip().lower()
        if sent == None or sent == '':
            continue
        else:
            print '###looking for: ' + str(sent)
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
    
    # handle address:
    if location == None or location == {}:
        if address != None and address != []:
            if address['street'] != '' and address['street'] != None:
                street_address = address['street'] + address_delim + city_id + address_delim + address['country']
                geocode_result = gmaps.geocode(street_address)
                if geocode_result == None or len(geocode_result) == 0:
                    print 'geo code not found for street address: ' + str(street_address)
                else:
                    location = {}
                    location['lat'] = geocode_result[0]['geometry']['location']['lat']
                    location['lon'] = geocode_result[0]['geometry']['location']['lng']
            else:
                print 'parsing error 00: neither address nor location is present: ' + city_id + ' ; ' + str(hotel_id)
        else:
            print 'parsing error 01: neither address nor location is present: ' + city_id + ' ; ' + str(hotel_id)
    
    formed_object = {
        "city_id": city_id,
        "id": elastic_count,
        "hotel_id": hotel_id,
        "review_id": review_count,
        "attribute_list": attr_to_insert_2,
        "sentiment": sentiment_map,
        "adjective_list": adj_list_map,
        "attribute_line": sentence_map,
        "score": score_map,
        "complete_review": complete_review,
        "location": location
    }
    print 'elastic_count, review_count: ' + str(elastic_count) + ' ; ' + str(review_count)
    elastic_count += 1
    review_count += 1
    return formed_object

if __name__ == "__main__":
    attribute_seed = load_json(seed_file)
    attribute_adjective_map = load_json(adjective_file)
    #global output_hotel_id_review_id
    #output_hotel_id_review_id = {}
    text_p.load_for_adjectives()
    # read the data
    hotel_id_map = load_json(hotel_id_file)
    output = []
    prev_count = 0
    next_count = 0
    hotel_count = 0
    
    if len(sys.argv) == 1:
        user_input = raw_input("Some input please: ")
        while user_input != 'stop':
            formed_object = parse_review(attribute_seed, attribute_adjective_map, user_input, 'NA', -1, {})
            print 'elastic obj: ' + str(formed_object)
            user_input = raw_input("Some input please: ")
    else:
        pool = mp.Pool(processes=int(sys.argv[2]))
        meta_review_data = json.loads(open(sys.argv[1], 'r').read())
        for city_id in meta_review_data:
            city_id = city_id.encode('utf-8')
            review_data = meta_review_data[city_id]
            #output_hotel_id_review_id[city_id] = {}
            for val in review_data:
                if hotel_count < hotels_so_far:
                    hotel_count += 1
                    continue

                hotel_count += 1
                hotel_name = val['name']
                hotel_id = get_hotel_id(hotel_name, hotel_id_map[city_id])
                if hotel_id == -1:
                    print 'error 11: hotel_id not found for ' + hotel_name
                    continue
                #output_hotel_id_review_id[city_id][hotel_id] = {}
                reviews = val['reviews']
                try: 
                    result = [pool.apply(parse_review, args=(attribute_seed, attribute_adjective_map, ''.join(x['description']).encode('utf-8'), city_id.encode('utf-8'), hotel_id, val)) for x in reviews if 'description' in x]
                except TypeError, e:
                    print type(city_id)
                    print type(hotel_id)
                    print 'type error: ' + str(e) + ' ; ' + city_id.encode('utf-8') + ' ; ' + str(hotel_id)
                
                next_count += len(result)
                for obj in result:
                    if obj == None or obj == {}:
                        continue
                    #output_hotel_id_review_id[obj['city_id']][obj['hotel_id']] = obj['complete_review']
                    output.append(obj)
                
                if next_count - prev_count > 1000:
                    f = open('hotel_review_elastic_' + str(next_count) + '.json', 'w')
                    f.write(json.dumps(output))
                    f.close()
                    prev_count = next_count
                    gc.collect()

        f = open('hotel_review_id.json', 'w')
        f.write(json.dumps(output_hotel_id_review_id))
        f.close()

        f = open('hotel_review_elastic.json', 'w')
        f.write(json.dumps(output))
        f.close()