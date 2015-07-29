import nltk
from gensim.models import word2vec
import json
import sys
from nltk import word_tokenize
import re
from stanford_corenlp_pywrapper import CoreNLP
from ast import literal_eval

'''
algorithm: 
1. read the attribute tree.
2. read the candidate line or review:
    2.1. do pos tagging on the line or review.
    2.2. find subject of the line by using stanford parser.
        2.2.1. do tuple to string/tree conversion and use the dependency parser.
    2.3. find the nearest/exact category for the subject.
    2.4. If new keyword is added then log it.
    2.5. store the line to subject/category in a map.
3. store this map.
'''


possibleNounTags = ['NN', 'NNP', 'NNS', 'NNPS']
model_file = "../code/word2vec-all/word2vec/trunk/vectors-phrase.bin"
stanford_jars = "/Volumes/anupam work/code/stanford-jars/3.5/*"
model = None
proc = None

def is_present(word, map_val):
    if word in map_val:
        if map_val[word] == 1 or map_val[word] == 2:
            return True
    return False

def normalize(word):
    if word == None:
        return None
    return word.lower().replace(' ', '_').replace('-','_')

def loadModelFile():
    global model
    global model_file
    global proc
    model = word2vec.Word2Vec.load_word2vec_format(model_file, binary=True)
    proc = CoreNLP("parse", corenlp_jars=[stanford_jars])

def findBestDistance(keywords, word):
    winner_keyword = None
    max_distance = -1
    global model
    for key in keywords:
        if key == '' or key == None:
            continue
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
        attribute_seed['keywords'][word] = 1
        return True
    for node in attribute_seed['next']:
        #print 'checking node: ' + node
        local_distance, local_keyword = findBestDistance(attribute_seed['next'][node]['keywords'], word)
        #print 'dist, keyword: ' + str(local_distance) + ' ; ' + str(local_keyword)
        if local_distance > max_distance:
            max_distance = local_distance
            winner_node = node
    if winner_node == None:
        print 'winner node is none for: ' + word
        return False
    path.append(winner_node)
    attribute_seed['next'][winner_node]['keywords'][word] = 1
    return findAndInsert(attribute_seed['next'][winner_node], word, path)
    
def findExact(attribute_seed, word, word_val, path):
    if attribute_seed['next'] == {}:
        assert(word in attribute_seed['keywords'])
        assert(word_val == attribute_seed['keywords'][word])
        return
    else:
        for node in attribute_seed['next']:
            if 'others' == node:
                continue
            if word in attribute_seed['next'][node]['keywords'] and word_val == attribute_seed['next'][node]['keywords'][word]:
                path.append(node)
                findExact(attribute_seed['next'][node], word, word_val, path)
                break
        return
        
    
def checkIfDone(user_controlled, user_input, reviewArr, current_count):
    if user_controlled:
        return user_input == 'stop'
    else:
        return (len(reviewArr) == current_count + 1)

def convert_to_tuple(unicode_str):
    # return the tuple version of the unicode.
    a = a + 1
    
    
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
    sub_pos = None
    if subj_details != None:
        sub = tokens[subj_details[2]]
        sub_pos = pos_tags[subj_details[2]]
    noun_arr = []
    index = 0
    for tag in pos_tags:
        if tag in possibleNounTags:
            noun_arr.append(tokens[index])
        index += 1
    print 'nouns: ' + str(noun_arr)
    return sub, sub_pos, obj


if __name__ == "__main__":
    final_map = {}
    training_map = {}
    reverse_map = {}
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
            try:
                line = line.encode('utf-8').strip()
            except UnicodeDecodeError:
                print 'Error: UnicodeDecodeError for line no: ' + str(count)
                continue
            if line == '':
                continue
            sub, sub_pos, obj = find_subject_object(line)
            sub = normalize(sub)
            obj = normalize(obj)
            try:
                print 'line, subject, object: ' + str(line) + ' ; ' + str(sub) + ' ; ' + str(sub_pos) + ' ; ' + str(obj)
            except UnicodeEncodeError:
                print 'cannot print one of line, subject or object'
                continue
            if sub == None:
                subject = None
            else:
                subject = normalize(sub)
            path = []
            if subject == None:
                if obj == None:
                    print 'Both None: ' + line
                    continue
                else:
                    obj = normalize(obj)
                    if is_present(obj, attribute_seed['root']['keywords']):
                        word_val = attribute_seed['root']['keywords'][obj]
                        print 'found: ' + obj
                        path = []
                        findExact(attribute_seed['root'], obj, word_val, path)
                    else:
                        attribute_seed['root']['keywords'][obj] = 1
                        path = []
                        findAndInsert(attribute_seed['root'], obj, path)
            else:
                if is_present(subject, attribute_seed['root']['keywords']):
                    word_val = attribute_seed['root']['keywords'][subject]
                    print 'found: ' + subject
                    path = []
                    findExact(attribute_seed['root'], subject, word_val, path)
                else:
                    if obj == None:
                        attribute_seed['root']['keywords'][subject] = 1
                        path = []
                        findAndInsert(attribute_seed['root'], subject, path)
                    else:
                        obj = normalize(obj)
                        if is_present(obj, attribute_seed['root']['keywords']):
                            word_val = attribute_seed['root']['keywords'][obj]
                            print 'found: ' + obj
                            path = []
                            findExact(attribute_seed['root'], obj, word_val, path)
                        else:
                            try:
                                print 'not found: ' + subject + ' ; ' + obj
                            except UnicodeEncodeError:
                                print 'cannot print one of the not found subject and object'
                                continue
                            # check pos tag and work
                            if 'PRP' in sub_pos:
                                # use object
                                attribute_seed['root']['keywords'][obj] = 1
                                path = []
                                findAndInsert(attribute_seed['root'], obj, path)
                            else:
                                attribute_seed['root']['keywords'][subject] = 1
                                path = []
                                findAndInsert(attribute_seed['root'], subject, path)
            str_path = str(path)
            print 'path: ' + str_path
            if str_path not in final_map:
                final_map[str_path] = []
            final_map[str_path].append(line)
            training_map[line] = str_path
            if str_path not in reverse_map:
                reverse_map[str_path] = []
            reverse_map[str_path].append(line)
        if user_controlled:
            user_input = raw_input("Some input please: ")
    f = open('data/expanded-seed-2.json', 'w')
    f.write(json.dumps(attribute_seed))
    f.close()
    output_file = input_arg + '-out.json'
    f = open(output_file, 'w')
    f.write(json.dumps(final_map))
    f.close()
    f = open('data/training_data.json', 'w')
    f.write(json.dumps(training_map))
    f.close()
    f = open('data/reverse_data.json', 'w')
    f.write(json.dumps(reverse_map))
    f.close()