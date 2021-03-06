import json
sys.path.insert(0, '/Volumes/anupam work/review-app-local/scripts/lib/')
import sys
import re
import threading

def get_hotel_id(hotel_name, hotel_id_map):
    for key in hotel_id_map:
        if hotel_name == hotel_id_map[key]:
            return key
    return -1

def get_review_details(text_p, attribute_seed, attribute_adjective_map, sent, result):
    try:
        path_with_score = text_p.find_attribute_2(attribute_seed, sent)
        if path_with_score == None or path_with_score == []:
            'path is none for line: ' + str(line)
            continue
        #print 'path_with_score: ' + str(path_with_score)
        path = map(lambda x: x[0], path_with_score)
        score = map(lambda x: x[1], path_with_score)
        #print 'score: ' + str(score)
        cumulative_score = reduce(lambda x, y: x * y, score, 1.0)
        adj_list = text_p.find_sentiment_adjective(attribute_adjective_map, path, sent)
    except TypeError:
        print 'Type Error in attribute_adjective_finder for line: ' + str(sent)
        return
    result.append({'path': path, 'sentiment': sentiment, 'adj_list': adj_list })

if __name__ == "__main__":
    attribute_seed = json.loads(open(sys.argv[1], 'r').read())
    attribute_adjective_map = json.loads(open(sys.argv[2], 'r').read())
    text_p.load_for_adjectives()
    # read the data
    review_data = json.loads(open(sys.argv[3], 'r').read())
    hotel_id_map = json.loads(open(sys.argv[4], 'r').read())
    output = []
    output_hotel_id_review_id = {}      #hotel_id -> review_id -> review_object
    count = 0
    for val in review_data:
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
                t = threading.Thread(target=get_review_details, args = (text_p, attribute_seed, attribute_adjective_map, sent, result))
                t.daemon = True
                t.start()
                
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
    
    f = open('hotel_review_id.json', 'w')
    f.write(json.dumps(output_hotel_id_review_id))
    f.close()
    
    f = open('hotel_review_elastic.json', 'w')
    f.write(json.dumps(output))
    f.close()