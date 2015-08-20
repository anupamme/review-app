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

'''
algo:
    start from parse tree:
    1. if you can find NP -> JJ, NN, parse JJ and NN. Look for NN as attribute.
    2. if you can find NP -> *, NN, NN, parse NN_1 and NN_2. Look for NN_1 and NN_2 as attributes.
    3. if you can find NP -> * , NN. Look for NN as attribute.
    4. PP -> TO, NN. This is location attribute most prob. So look for NN in Location.
    5. PP -> IN, NN. This could be either location or purpose. e.g. for honeymoon, from station.
    6. Make JJ indexable in elastic search.
'''

possibleNounTags = ['NN', 'NNP', 'NNS', 'NNPS', 'NP']
possibleAdjTags = ['JJ', 'JJR', 'JJS', 'RB', 'RBS', 'RBR']
possibleVerbTags = ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']
model_file = "../code/word2vec-all/word2vec/trunk/vectors-phrase.bin"
stanford_jars = "/Volumes/anupam work/code/stanford-jars/3.5/*"
model = None
proc = None
exclude_noun = ["day", "hotel", "july", "ones", "years", "guest", "night", "year", "room"]

def loadModelFile():
    global model
    global model_file
    global proc
    model = word2vec.Word2Vec.load_word2vec_format(model_file, binary=True)
    proc = sockwrap.SockWrap("parse", corenlp_jars=[stanford_jars])

def find_lowest_subtree(tree, tag):
    if tree[0] == tag:
        print 'returning: ' + str(tree)
        return tree
    tree_len = len(tree)
    print 'tree: ' + str(tree)
    time.sleep(1)
    if tree == None or tree_len == 0:
        return None
    count = tree_len - 1
    final_val = None
    while count >= 0:
        print 'calling tree: ' + str(tree[count])
        val = find_lowest_subtree(tree[count], tag)
        if val != None:
            final_val = val
        count = count - 1
    return None

def find_lowest_subtree_2(tree, tag):
    if tree == None:
        return None
    tree_len = len(tree)
    if tree_len == 0:
        return None
    count = tree_len - 1
    print 'tree: ' + str(tree)
    while count >= 0:
        if type(tree[count]) == str:
            if tree[count] == tag:
                print 'returning: ' + str(tree)
                return tree
            else:
                return None
        val = find_lowest_subtree_2(tree[count], tag)
        if val != None:
            return val
        count = count - 1

def find_noun_array(processed):
    count = 0
    pos_count = len(processed['sentences'][0]['pos'])
    noun_arr = []
    while count < pos_count:
        if processed['sentences'][0]['pos'][count] in possibleNounTags:
            noun_arr.append(processed['sentences'][0]['tokens'][count])
        count = count + 1
    return noun_arr

def normalize(word):
    if word == None:
        return None
    return word.lower().replace(' ', '_').replace('-','_')

def is_present(word, map_val):
    if word in map_val:
        if map_val[word] == 1 or map_val[word] == 2:
            return True
    return False

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

def find_best_attribute(noun_arr, map_val):
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
            print 'Unknown: Not able to insert line and noun: ' + str(noun_arr) + ' ; ' + winner_noun
    return path

def find_all(sub_tree, tags_list, nouns):
    tree_len = len(sub_tree)
    count = 0
    #print 'tree first: ' + str(sub_tree)
    while count < tree_len:
        if type(sub_tree[count]) == str:
            count = count + 1
            continue
        #print 'tree_next first: ' + str(sub_tree[count][0])
        if type(sub_tree[count][0]) == tuple:
            find_first(sub_tree[count], tags_list, nouns)
        if sub_tree[count][0] in tags_list:
            nouns.append(sub_tree[count][1])
        count = count + 1
    return

if __name__ == "__main__":
    loadModelFile()
    attribute_seed = json.loads(open(sys.argv[1], 'r').read())
    user_input = raw_input("Some input please: ")
    while user_input != 'stop':
        processed = proc.parse_doc(user_input)
        if len(processed['sentences']) == 0:
            user_input = raw_input("Some input please: ")
            continue
        parse_tree_str = str(processed['sentences'][0]['parse']).replace(' ', ' ,').replace(' ', '\' ').replace('(', '(\'').replace(')', '\')').replace(',', ',\'').replace('\'(', '(').replace(')\'', ')').replace(')\')', '))').replace(')\')', '))')
        
        print 'parse tree str: ' + str(parse_tree_str)
        parse_tree = literal_eval(parse_tree_str)
        print 'parse tree: ' + str(parse_tree)
        
        # find last PP or NP.
        path = []
        pp_tree = find_lowest_subtree_2(parse_tree, 'PP')
        if pp_tree == None:
            print 'NULL: pp_tree is null'
            np_tree = find_lowest_subtree_2(parse_tree, 'NP')
            if np_tree == None:
                print 'NULL: np_tree is null'
                noun_arr = find_noun_array(processed)
                path = find_best_attribute(noun_arr, attribute_seed['root'])
            else:
                assert(np_tree[0] == 'NP')
                tree_len = len(np_tree)
                if np_tree[1][0] == 'JJ' and np_tree[2][0] in possibleNounTags:
                    adj = np_tree[1][1]
                    noun = np_tree[2][1]
                    path = find_best_attribute([noun], attribute_seed['root'])
                else:
                    if np_tree[tree_len - 1][0] == 'NN':
                        # find all nouns:
                        tree_count = 0
                        noun_arr = []
                        while tree_count < tree_len:
                            if np_tree[tree_count][0] == 'NN':
                                noun_arr.append(np_tree[tree_count][1])
                            tree_count += 1
                        # off all the nouns find the nearest attribute.
                        print 'noun arr: ' + str(noun_arr)
                        path = find_best_attribute(noun_arr, attribute_seed['root'])
        else:
            print 'pp_tree: ' + str(pp_tree)
            assert(pp_tree[0] == 'PP')
            # mostly location attribute.
            tree_len = len(pp_tree)
            assert(pp_tree[2][0] in possibleNounTags)
            noun_val_arr = []
            find_all(pp_tree[2], ['NN', 'NNS'], noun_val_arr)
            if pp_tree[1][0] == 'TO':
                #only location attribute.
                # find location target for noun_val
                path = find_best_attribute(noun_val_arr, attribute_seed['root']['next']['location'])
            else:
                if pp_tree[1][0] == 'IN':
                    # either purpose or location.
                    # choose between purpose and location.
                    path = find_best_attribute(noun_val, attribute_seed['root']['next']['location'])
        print 'path found: ' + str(path)
        user_input = raw_input("Some input please: ")