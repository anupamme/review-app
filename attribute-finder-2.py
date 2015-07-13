import nltk
from gensim.models import word2vec
import json
import sys
from nltk import word_tokenize
import re

'''
algorithm: 
1. Read the attribute tree and the word2vec model.
2. Read the candidate line:
    1. do pos tagging
    2. pick nouns (and adjectives) and find where it fits in the attribute_tree. Insert a new or match with existing.
    3. pick the top noun. (use subject-object logic to boost weights)
    4. pick the correct noun and adjective.

'''
model_file = "../trunk/vectors-phrase.bin"
possibleNounTags = ['NN', 'NNP', 'NNS', 'NNPS']
possibleAdjTags = ['JJ', 'JJR', 'JJS', 'RB', 'RBS', 'RBR']
model = None

def normalize(word):
    return word.lower().replace(' ', '_')

def loadModelFile():
    global model
    global model_file
    model = word2vec.Word2Vec.load_word2vec_format(model_file, binary=True)

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
    max_distance = -1
    winner_node = None
    if attribute_seed['next'] == {}:
        attribute_seed['keywords'].append(word)
        return
    for node in attribute_seed['next']:
        #print 'checking node: ' + node
        local_distance, local_keyword = findBestDistance(attribute_seed['next'][node]['keywords'], word)
        #print 'dist, keyword: ' + str(local_distance) + ' ; ' + str(local_keyword)
        if local_distance > max_distance:
            max_distance = local_distance
            winner_node = node
    assert(winner_node != None)
    path.append(winner_node)
    attribute_seed['next'][winner_node]['keywords'].append(word)
    findAndInsert(attribute_seed['next'][winner_node], word, path)
    
def findExact(attribute_seed, word, path):
    if attribute_seed['next'] == {}:
        assert(word in attribute_seed['keywords'])
        return
    else:
        for node in attribute_seed['next']:
            if word in attribute_seed['next'][node]['keywords']:
                path.append(node)
                findExact(attribute_seed['next'][node], word, path)
                break
        
    
if __name__ == "__main__":
    final_map = {}
    loadModelFile()
    attribute_seed = json.loads(open(sys.argv[1], 'r').read())
    input_arg = sys.argv[2]
    input_file = input_arg + '.json'
    data = json.loads(open(input_file, 'r').read())
    for review in data:
        lineArr = re.split('\n|\.', review)
        for line in lineArr:
            line = line.encode('utf-8').strip()
            if line == '':
                continue
            tokens = word_tokenize(line)
            try:
                pos_tags = nltk.pos_tag(tokens)
            except UnicodeDecodeError:
                print 'cannot decode: ' + str(tokens)
            if len(pos_tags) == 0:
                print 'pos tags are empty for: ' + line
                continue
            res_noun = []
            res_adjectives = []
            for word, pos in pos_tags:
                if word == '' or word == None:
                    continue
                if pos in possibleNounTags:
                    #print 'checking out word: ' + word
                    word = normalize(word)
                    path = []
                    if word in attribute_seed['root']['keywords']:
                        findExact(attribute_seed['root'], word, path)
                    else:
                        attribute_seed['root']['keywords'].append(word)
                        try:
                            similar = model.most_similar(word)
                        except KeyError:
                            print 'Key Error for word: ' + word
                            continue
                        findAndInsert(attribute_seed['root'], word, path)
                    str_path = str(path)
                    if str_path not in final_map:
                            final_map[str_path] = []
                    final_map[str_path].append(line)
        f = open('expanded-seed-2.json', 'w')
        f.write(json.dumps(attribute_seed))
        f.close()
        output_file = input_arg + '-out.json'
        f = open(output_file, 'w')
        f.write(json.dumps(final_map))
        f.close()