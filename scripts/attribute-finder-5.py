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
model_file = "../code/word2vec-all/word2vec/trunk/vectors-phrase.bin"
stanford_jars = "/Volumes/anupam work/code/stanford-jars/3.5/*"
model = None
proc = None
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

def loadModelFile():
    global model
    global model_file
    global proc
    model = word2vec.Word2Vec.load_word2vec_format(model_file, binary=True)
    proc = sockwrap.SockWrap("parse", corenlp_jars=[stanford_jars])

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
    return sub, adj_list, verb_list, obj, noun_arr

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
    
def find_attribute(line, attribute_seed):
    try:
        line = line.encode('utf-8').strip()
    except UnicodeDecodeError:
        print 'Error: UnicodeDecodeError for line no: ' + str(count)
        return None, None, None
    if line == '':
        return None, None, None
    print 'line: ' + line
    path = []
    sub, adj_list, verb_list, obj, noun_arr = find_subject_object(line)
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
            return None, adj_list, verb_list
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
                    return None, adj_list, verb_list
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
                        return None, adj_list, verb_list
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
                            return None, adj_list, verb_list
    return path, adj_list, verb_list

            
    
if __name__ == "__main__":
    reverse_map = {}
    forward_map = {}
    reverse_map_adj = {}
    reverse_map_verb = {}
    loadModelFile()
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
            path, adj_list, verb_list = find_attribute(line, attribute_seed)
            if path == None:
                continue
            assert(path != [])
            str_path = str(path)
            print 'path: ' + str_path
            if str_path not in reverse_map:
                reverse_map[str_path] = []
                reverse_map_adj[str_path] = {}
                reverse_map_verb[str_path] = {}
            for adj in adj_list:
                if adj in reverse_map_adj[str_path]:
                    reverse_map_adj[str_path][adj] = reverse_map_adj[str_path][adj] + 1
                else:
                    reverse_map_adj[str_path][adj] = 1
            for vb in verb_list:
                if vb in reverse_map_verb[str_path]:
                    reverse_map_verb[str_path][vb] = reverse_map_verb[str_path][vb] + 1
                else:
                    reverse_map_verb[str_path][vb] = 1
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
    f = open('reverse_verb.json', 'w')
    f.write(json.dumps(sorted_list_verb))
    f.close()