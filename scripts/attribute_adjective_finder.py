import nltk
from gensim.models import word2vec
import json
import sys
from nltk import word_tokenize
import re
from stanford_corenlp_pywrapper import sockwrap
from ast import literal_eval
import operator

'''
algorithm:

for each line find:
1. noun_list = [noun]
2. subject, object and any other part of sentence.
3. breaking steps:
    3.1. if subject is present in tree we use subject.
    3.2. if object is present in tree we use object
    3.3. Otherwise we check for each of the nouns and pick the path which has maximum number of nouns.
    3.4. If none of the above in the sense neighter is present in tree then:
        3.4.1 if subject is prp then ignore 
        3.4.2 if object is prp ignore.
        3.4.3. from list of nouns, subject and object: find which has lowest distance with avg of max 3.
        
    3.5. 
'''

possibleNounTags = ['NN', 'NNP', 'NNS', 'NNPS']
possibleAdjTags = ['JJ', 'JJR', 'JJS', 'RB', 'RBS', 'RBR']
possibleVerbTags = ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']

antonym_file = 'data/antonym_map.json'
positive_file = 'data/positives.json'
negative_file = 'data/negatives.json'
attribute_adjective_file = 'data/reverse_adj.json'
model_file = "../code/word2vec-all/word2vec/trunk/vectors-phrase.bin"
stanford_jars = "../code/stanford-jars/3.5/*"
model = None
proc = None
attribute_adjective_map = {}
positive_array = []
negative_array = []
antonym_map = {}
exclude_noun = ["day", "hotel", "july", "ones", "years", "guest", "night", "year", "room"]


def findExact(attribute_seed, word, word_val, path):
    if attribute_seed['next'] == {}:
        assert(word in attribute_seed['keywords'])
        assert(word_val == attribute_seed['keywords'][word])
        return
    else:
        for node in attribute_seed['next']:
#            if 'others' == node:
#                continue
            if word in attribute_seed['next'][node]['keywords'] and word_val == attribute_seed['next'][node]['keywords'][word]:
                path.append(node)
                findExact(attribute_seed['next'][node], word, word_val, path)
                break
        return

def findBestDistance(keywords, word):
    winner_keyword = None
    max_distance = -1
    global model
    for key in keywords:
        if key == '' or key == None:
            continue
        val = keywords[key]
        if val == 1 or val == 2:
            key = normalize(key)
            try:
                local_distance = model.similarity(key, word)
            except KeyError:
                print 'word2vec error: word not found: ' + key + ' ; ' + word
                continue
            if local_distance > max_distance:
                max_distance = local_distance
                winner_keyword = key
    return max_distance, winner_keyword

def findAndInsert(attribute_seed, word, path):
    #print 'word, path: ' + word + ' ; ' + str(path)
    if len(word) <= 2:
        return False
    max_distance = -1
    winner_node = None
    if attribute_seed['next'] == {}:
        #attribute_seed['keywords'][word] = 1
        return True
    for node in attribute_seed['next']:
        #print 'checking node: ' + node
        local_distance, local_keyword = findBestDistance(attribute_seed['next'][node]['keywords'], word)
        #print 'dist, keyword: ' + str(local_distance) + ' ; ' + str(local_keyword)
        if local_distance < 0.1:
            continue
        if local_distance > max_distance:
            max_distance = local_distance
            winner_node = node
    if winner_node == None:
        print 'winner node is none for: ' + word
        return False
    if winner_node == 'yoga':
        print 'yoga distance: ' + str(max_distance)
    path.append(winner_node)
    #attribute_seed['next'][winner_node]['keywords'][word] = 1
    return findAndInsert(attribute_seed['next'][winner_node], word, path)

def normalize(word):
    if word == None:
        return None
    return word.lower().replace(' ', '_').replace('-','_')

def init():
    global model
    global model_file
    global proc
    global attribute_adjective_map
    global positive_array
    global negative_array
    global antonym_map
    model = word2vec.Word2Vec.load_word2vec_format(model_file, binary=True)
    print 'stanford-jars: ' + stanford_jars
    proc = sockwrap.SockWrap("parse", corenlp_jars=[stanford_jars])
    attribute_adjective_map = json.loads(open(attribute_adjective_file, 'r').read())
    print 'length of attribute_adjective_map: ' + str(len(attribute_adjective_map))
    positive_array = json.loads(open(positive_file, 'r').read())
    negative_array = json.loads(open(negative_file, 'r').read())
    antonym_map = json.loads(open(antonym_file, 'r').read())

def find_subject_object(line):
    global proc
    parsed_c = proc.parse_doc(line)
    #tuple_v = convert_to_tuple(parsed_c['sentences'][0]['parse'])
    tokens = parsed_c['sentences'][0]['tokens']
    deps = parsed_c['sentences'][0]['deps_basic']
    subj_details = None
    obj_details = None
    mod_details = None
    for val in deps:
        #print 'checking: ' + str(val)
        if 'subj' in val[0]:
            subj_details = val
        if 'obj' in val[0]:
            obj_details = val
        if 'mod' in val[0]:
            mod_details = val
    print 'details: ' + str(subj_details) + ' ; ' + str(obj_details) + ' ; ' + str(mod_details)
    pos_tags = parsed_c['sentences'][0]['pos']
    obj = None
    if obj_details == None:
        if mod_details != None:
            obj = tokens[mod_details[2]]
    else:
        obj = tokens[obj_details[2]]
    sub = None
    adj_list = []
    verb_list = []
    pos_count = 0
    for tag in pos_tags:
        if tag in possibleAdjTags:
            adj_list.append(normalize(tokens[pos_count]))
        if tag in possibleVerbTags:
            verb_list.append(normalize(tokens[pos_count]))
        pos_count += 1
    
    noun_arr = []
    index = 0
    for tag in pos_tags:
        if tag in possibleNounTags:
            noun = normalize(tokens[index])
            if noun not in exclude_noun:
                noun_arr.append(noun)
        index += 1
    print 'nouns: ' + str(noun_arr)
    return sub, adj_list, verb_list, obj, noun_arr, parsed_c['sentences'][0]['sentiment']

def checkIfDone(user_controlled, user_input, reviewArr, current_count):
    if user_controlled:
        return user_input == 'stop'
    else:
        return (len(reviewArr) == current_count + 1)

def is_present(word, map_val):
    if word in map_val:
        if map_val[word] == 1 or map_val[word] == 2:
            return True
    return False

def is_any_noun_present(map_val, noun_arr):
    path = []
    for noun in noun_arr:
        noun = normalize(noun)
        if is_present(noun, map_val['keywords']):
            word_val = map_val['keywords'][noun]
            print 'found noun: ' + noun
            findExact(map_val, noun, word_val, path)
            break
    return path

def search_noun_array(map_val, noun_arr):
    if len(noun_arr) == 0:
        print 'Not Found: Subject and object are none and no noun present: ' + line
        return []
    path = is_any_noun_present(map_val, noun_arr)
    if path == []:
        print 'No noun is present in tree. So finding best bet...'
        max_distance = -1
        winner_noun = None
        for noun in noun_arr:
            noun = normalize(noun)
            local_distance = findBestDistance(map_val['keywords'], noun)
            if local_distance > max_distance:
                max_distance = local_distance
                winner_noun = noun
        assert(winner_noun != None)
        path = []
        if findAndInsert(map_val, winner_noun, path):
            assert(path != [])
        else:
            print 'Unknown: Not able to insert line and noun: ' + line + ' ; ' + winner_noun
    return path
    
def convert_sentiment_to_int(sentiment):
    sentiment_lower = sentiment.lower()
    if 'positive' in sentiment_lower:
        if 'very' in sentiment_lower:
            return 5
        else:
            return 4
    else:
        if 'negative' in sentiment_lower:
            if 'very' in sentiment_lower:
                return 1
            else:
                return 2
    return 3

def find_max_adjective(adj, candidate_adjectives):
    max_adj = None
    max_distance = -1
    for candidate, frequency in candidate_adjectives:
        try:
            dist = model.similarity(adj, candidate) * frequency
            if dist > max_distance:
                max_adj = candidate
                max_distance = dist
        except KeyError:
            print 'Key error for: ' + adj + '; ' + candidate
    return max_adj, max_distance
    
def find_correct_adjective(adj_list, candidate_adjectives, sentiment):
    global antonym_map
    global positive_array
    global negative_array
    selected_adj = []
    final_adj = []
    for adj in adj_list:
        if adj in positive_array or adj in negative_array:
            max_candidate_adj, max_candidate_distance = find_max_adjective(adj, candidate_adjectives)
            print 'max adj match: ' + str(max_candidate_adj) + ' ; ' + str(max_candidate_distance)
            if max_candidate_adj == None:
                continue
            selected_adj.append(max_candidate_adj)
        else:
            print 'error: invalid adjective: ' + adj
        
    # figure whether positive or negative.
    print 'sentiment: ' + sentiment
    if selected_adj == []:
        print 'max adjective is none for adj_list: ' + str(adj_list)
        return None, -1
    
    if convert_sentiment_to_int(sentiment) >= 3:
        for max_adj in selected_adj:
            if max_adj in positive_array:
                final_adj.append(max_adj)
            else:
                if max_adj in negative_array:
                    if max_adj in antonym_map:
                        print 'returning antonym for: ' + max_adj
                        final_adj.append(antonym_map[max_adj])
                    else:
                        print 'error 00: ' + str(max_adj)
                else:
                    print 'error 01: ' + max_adj
    else:
        for max_adj in selected_adj:
            if max_adj in negative_array:
                final_adj.append(max_adj)
            else:
                if max_adj in positive_array:
                    if max_adj in antonym_map:
                        print 'returning antonym for: ' + max_adj
                        final_adj.append(antonym_map[max_adj])
                    else:
                        print 'error 11: ' + max_adj
                else:
                    print 'error 10: ' + max_adj
    return final_adj
    
def find_meta_data(line, attribute_seed, attribute_adjective_map):
    try:
        line = line.encode('utf-8').strip()
    except UnicodeDecodeError:
        print 'Error: UnicodeDecodeError for line no: ' + str(count)
        return None, None, None, None
    if line == '':
        return None, None, None, None
    print 'line: ' + line
    path = []
    sub, adj_list, verb_list, obj, noun_arr, sentiment = find_subject_object(line)
    try:
        print 'sub, obj: ' + str(sub) + ' ; ' + str(obj)
    except UnicodeEncodeError:
        print 'UnicodeEncodeError. So setting sub and obj none.'
        sub = None
        obj = None

    sub = normalize(sub)
    obj = normalize(obj)
    if sub == None and obj == None:
        # play with noun_arr
        path = search_noun_array(attribute_seed['root'], noun_arr)
        if path == []:
            print 'Not Found: For line: ' + line
            return None, sentiment, None, None
    else:
        if sub == None:
            # if object is present.
            if is_present(obj, attribute_seed['root']['keywords']):
                word_val = attribute_seed['root']['keywords'][obj]
                print 'found obj: ' + obj
                path = []
                findExact(attribute_seed['root'], obj, word_val, path)
            else:
                path = search_noun_array(attribute_seed['root'], noun_arr)
                if path == []:
                    print 'Not Found: For line: ' + line
                    return None, sentiment, None, adj_list
        else:
            # if subject is present
            if is_present(sub, attribute_seed['root']['keywords']):
                word_val = attribute_seed['root']['keywords'][sub]
                print 'found sub: ' + sub
                path = []
                findExact(attribute_seed['root'], sub, word_val, path)
            else:
                if obj == None:
                    path = search_noun_array(attribute_seed['root'], noun_arr)
                    if path == []:
                        print 'Not Found: For line: ' + line
                        return None, sentiment, None, adj_list
                else:
                    if is_present(obj, attribute_seed['root']['keywords']):
                        word_val = attribute_seed['root']['keywords'][obj]
                        print 'found: ' + obj
                        path = []
                        findExact(attribute_seed['root'], obj, word_val, path)
                    else:
                        path = search_noun_array(attribute_seed['root'], noun_arr)
                        if path == []:
                            print 'Not Found: For line: ' + line
                            return None, sentiment, None, adj_list
    assert(path != None and path != [])
    print 'adj_list: ' + str(adj_list)
    str_path = str(path)
    if len(adj_list) > 0:
        if str_path in attribute_adjective_map:
            candidate_adjectives = attribute_adjective_map[str_path]
            correct_adjective_list = find_correct_adjective(adj_list, candidate_adjectives, sentiment)
    return path, sentiment, correct_adjective_list, adj_list
    
if __name__ == "__main__":
    reverse_map = {}
    forward_map = {}
    reverse_map_adj = {}
    reverse_map_verb = {}
    forward_adj_map = {}
    global attribute_adjective_map
    init()
    attribute_seed = json.loads(open(sys.argv[1], 'r').read())
    
    user_controlled = False
    data = None
    user_input = None
    if len(sys.argv) == 2:
        user_controlled = True
        user_input = raw_input("Some input please: ")
        input_arg = 'default'
    else:
        input_arg = sys.argv[2]
        input_file = input_arg + '.json'
        data = json.loads(open(input_file, 'r').read())
    
    count = 0
    while not checkIfDone(user_controlled, user_input, data, count):
        if user_controlled:
            review = user_input
        else:
            review = data[count].encode('utf-8')
            count = count + 1
        
        lineArr = re.split('\n|\.', review)
        for line in lineArr:
            path, sentiment, correct_adjective_list, adj_list = find_meta_data(line, attribute_seed, attribute_adjective_map)
            if path == None or path == []:
                continue
            if correct_adjective_list != None and correct_adjective_list != []:
                forward_adj_map[line] = str(correct_adjective_list)
                print 'found adjective: ' + str(correct_adjective_list)
            else:
                print 'error attribute adjective map key error: ' + str_path + '; ' + str(len(attribute_adjective_map))
            assert(path != [])
            str_path = str(path)
            print 'path: ' + str_path
            if str_path not in reverse_map:
                reverse_map[str_path] = []
                reverse_map_adj[str_path] = {}
                reverse_map_verb[str_path] = {}
            # calculate correct set of adjectives
            
            
            for adj in adj_list:
                if adj in reverse_map_adj[str_path]:
                    reverse_map_adj[str_path][adj] = reverse_map_adj[str_path][adj] + 1
                else:
                    reverse_map_adj[str_path][adj] = 1
#            for vb in verb_list:
#                if vb in reverse_map_verb[str_path]:
#                    reverse_map_verb[str_path][vb] = reverse_map_verb[str_path][vb] + 1
#                else:
#                    reverse_map_verb[str_path][vb] = 1
            reverse_map[str_path].append(line)
            forward_map[line] = str_path
        if user_controlled:
            user_input = raw_input("Some input please: ")
#    f = open('reverse_review.json', 'w')
#    f.write(json.dumps(reverse_map))
#    f.close()
#    f = open('forward_review.json', 'w')
#    f.write(json.dumps(forward_map))
#    f.close()
    sorted_list = {}
    for key in reverse_map_adj:
        sorted_list[key] = sorted(reverse_map_adj[key].items(), key=operator.itemgetter(1), reverse=True)
    sorted_list_verb = {}
    for key in reverse_map_verb:
        sorted_list_verb[key] = sorted(reverse_map_verb[key].items(), key=operator.itemgetter(1), reverse=True)
    f = open('reverse_adj.json', 'w')
    f.write(json.dumps(sorted_list))
    f.close()
#    f = open('reverse_verb.json', 'w')
#    f.write(json.dumps(sorted_list_verb))
#    f.close()
    f = open('forward_adj.json', 'w')
    f.write(json.dumps(forward_adj_map))
    f.close()