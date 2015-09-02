import nltk
from gensim.models import word2vec
import json
import sys
from nltk import word_tokenize
import re
from stanford_corenlp_pywrapper import sockwrap
from ast import literal_eval
import operator
import time

model = None
proc = None

# data
possibleNounTags = ['NN', 'NNP', 'NNS', 'NNPS']
possibleAdjTags = ['JJ', 'JJR', 'JJS', 'RB', 'RBS', 'RBR']
possibleVerbTags = ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']

model_file = "../code/word2vec-all/word2vec/trunk/vectors-phrase.bin"
stanford_jars = "/Volumes/anupam work/code/stanford-jars/3.5/*"

antonym_file = 'data/antonyms/antonym_map.json'
positive_file = 'data/antonyms/positives.json'
negative_file = 'data/antonyms/negatives.json'
attribute_adjective_file = 'data/antonyms/reverse_adj.json'

positive_array = []
negative_array = []
antonym_map = {}

def normalize(word):
    if word == None:
        return None
    return word.lower().replace(' ', '_').replace('-','_')

def load_for_adjectives():
    load_model_files()
    attribute_adjective_map = json.loads(open(attribute_adjective_file, 'r').read())
    print 'length of attribute_adjective_map: ' + str(len(attribute_adjective_map))
    positive_array = json.loads(open(positive_file, 'r').read())
    negative_array = json.loads(open(negative_file, 'r').read())
    antonym_map = json.loads(open(antonym_file, 'r').read())

def load_model_files():
    global model
    global model_file
    global proc
    global stanford_jars
    model = word2vec.Word2Vec.load_word2vec_format(model_file, binary=True)
    proc = sockwrap.SockWrap("parse", corenlp_jars=[stanford_jars])
    
def find_best_score(word, keywords_map):
    best_score = -1
    for key in keywords_map:
        try:
            score = model.similarity(word, key) * keywords_map[key]
        except KeyError:
            #print 'word2vec error: word not found: ' + word + ' ; ' + key
            continue
        if score > best_score:
            best_score = score
    return best_score
    
def find_score(data_map, map_val):
    score_sum = 0
    for key in data_map:
        if key in map_val['keywords'] and map_val['keywords'][key] >= 1:
            score_sum += 1 * data_map[key]
        else:
            best = find_best_score(key, map_val['keywords']) * data_map[key]
            if best > 0:
                score_sum += best
    return score_sum
    
def find_best_attribute_multi_2(data_map, map_val, path):
    if len(data_map) == 0:
        return None
    max_score = -1
    max_node = None
    for node in map_val['next']:
        score = find_score(data_map, map_val['next'][node])
        if score > max_score:
            print 'win: max_score, new_score: ' + str(max_score) + ' ; ' + str(score) + ' ; ' + node
            max_score = score
            max_node = node
    assert(max_node != None)
    path.append(max_node)
    if len(map_val['next'][max_node]['next']) == 0:
        return
    else:
        find_best_attribute_multi_2(data_map, map_val['next'][max_node], path)

def find_sub_obj(processed):
    deps = processed['sentences'][0]['deps_basic']
    subj_details = None
    obj_details = None
    mod_details = None
    for val in deps:
        if 'subj' in val[0]:
            subj_details = val
        if 'obj' in val[0]:
            obj_details = val
        if 'mod' in val[0]:
            mod_details = val
    #print 'details: ' + str(subj_details) + ' ; ' + str(obj_details) + ' ; ' + str(mod_details)
    #pos_tags = parsed_c['sentences'][0]['pos']
    tokens = processed['sentences'][0]['tokens']
    obj = None
    if obj_details == None:
        if mod_details != None:
            obj = tokens[mod_details[2]]
    else:
        obj = tokens[obj_details[2]]
    sub = None
    if subj_details is not None:
        sub = tokens[subj_details[2]]
    return sub, obj        
        
def filter_array(processed, possibleTags):
    count = 0
    pos_count = len(processed['sentences'][0]['pos'])
    print 'pos: ' + str(processed['sentences'][0]['pos'])
    print 'tokens: ' + str(processed['sentences'][0]['tokens'])
    res_arr = []
    while count < pos_count:
        if processed['sentences'][0]['pos'][count] in possibleTags:
            res_arr.append(processed['sentences'][0]['tokens'][count])
        count = count + 1
    return res_arr        
        
def find_attribute_2(attribute_seed, user_input):
    processed = proc.parse_doc(user_input)
    if len(processed['sentences']) == 0:
        return None
    nouns = filter_array(processed, possibleNounTags)
    sub, obj = find_sub_obj(processed)
    data = {}
    for noun in nouns:
        n_noun = normalize(noun)
        if n_noun in data:
            data[n_noun] += 1
        else:
            data[n_noun] = 1
    if sub != None:
        if sub in possibleNounTags or sub in possibleAdjTags or sub in possibleVerbTags:
            n_sub = normalize(sub)
            if n_sub in data:
                data[n_sub] += 1.10
            else:
                data[n_sub] = 1.10
    if obj != None:
        if obj in possibleNounTags or sub in possibleAdjTags or sub in possibleVerbTags:
            n_obj = normalize(obj)
            if n_obj in data:
                data[n_obj] += 1.01
            else:
                data[n_obj] = 1.01
    print 'data: ' + str(data)
    path = []
    find_best_attribute_multi_2(data, attribute_seed['root'], path)
    print 'path: ' + str(path)
    return path

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

def find_correct_adjective(adj_list, candidate_adjectives, sentiment):
    global antonym_map
    global positive_array
    global negative_array
    selected_adj = []
    final_adj = []
    print 'candidate_adjectives: ' + str(candidate_adjectives)
    for adj in adj_list:
        #if adj in positive_array or adj in negative_array:
        print 'looking for adjective: ' + str(adj)
        max_candidate_adj, max_candidate_distance = find_max_adjective(adj, candidate_adjectives)
        print 'max adj match: ' + str(max_candidate_adj) + ' ; ' + str(max_candidate_distance)
        if max_candidate_adj == None:
            continue
        selected_adj.append(max_candidate_adj)
#        else:
#            print 'error: invalid adjective: ' + adj
        
    # figure whether positive or negative.
    print 'sentiment: ' + sentiment
    if selected_adj == []:
        print 'max adjective is none for adj_list: ' + str(adj_list)
        return None, -1
    
    if convert_sentiment_to_int(sentiment) >= 3:
        for max_adj in selected_adj:
            print 'checking for max_adj: ' + str(max_adj)
            print 'positive_array: ' + str(positive_array)
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
    
def find_sentiment_adjective(attribute_adjective_map, attribute_path, user_input):
    assert(attribute_path != None and attribute_path != [])
    processed = proc.parse_doc(user_input)
    adj_list = filter_array(processed, possibleAdjTags)
    sentiment = processed['sentences'][0]['sentiment']
    print 'adj_list: ' + str(adj_list)
    str_path = str(attribute_path)
    correct_adjective_list = []
    if len(adj_list) > 0:
        if str_path in attribute_adjective_map:
            candidate_adjectives = attribute_adjective_map[str_path]
            correct_adjective_list = find_correct_adjective(adj_list, candidate_adjectives, sentiment)
        else:
            print 'Not found in path: ' + str_path
    return correct_adjective_list
