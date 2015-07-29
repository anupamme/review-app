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
model_file = "../code/word2vec-all/word2vec/trunk/vectors-phrase.bin"
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
        attribute_seed['keywords'][word] = 1
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
    attribute_seed['next'][winner_node]['keywords'][word] = 1
    findAndInsert(attribute_seed['next'][winner_node], word, path)
    
def findExact(attribute_seed, word, word_val, path):
    if attribute_seed['next'] == {}:
        assert(word in attribute_seed['keywords'])
        assert(word_val == attribute_seed['keywords'][word])
        return
    else:
        for node in attribute_seed['next']:
            if word in attribute_seed['next'][node]['keywords'] and word_val == attribute_seed['next'][node]['keywords'][word]:
                path.append(node)
                findExact(attribute_seed['next'][node], word, word_val, path)
                break
        
    
def checkIfDone(user_controlled, user_input, reviewArr, current_count):
    if user_controlled:
        return user_input == 'stop'
    else:
        return (len(reviewArr) == current_count + 1)
    
if __name__ == "__main__":
    final_map = {}
    training_map = {}
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
            print 'line: ' + line
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
                    res_noun.append(word)
                    path = []
                    if word in attribute_seed['root']['keywords']:
                        word_val = attribute_seed['root']['keywords'][word]
                        print 'found: ' + word
                        findExact(attribute_seed['root'], word, word_val, path)
                    else:
                        print 'not found: ' + word
                        attribute_seed['root']['keywords'][word] = 1
                        try:
                            similar = model.most_similar(word)
                        except KeyError:
                            print 'Key Error for word: ' + word
                            continue
                        findAndInsert(attribute_seed['root'], word, path)
                    str_path = str(path)
                    #print 'path: ' + str_path
                    if str_path not in final_map:
                            final_map[str_path] = []
                    final_map[str_path].append(line)
                    training_map[line] = str_path
            print 'nouns: ' + str(res_noun)
        if user_controlled:
            user_input = raw_input("Some input please: ")
    print 'count: ' + str(count)       
    f = open('expanded-seed-2.json', 'w')
    f.write(json.dumps(attribute_seed))
    f.close()
    output_file = input_arg + '-out.json'
    f = open(output_file, 'w')
    f.write(json.dumps(final_map))
    f.close()
    f = open('training_data.json', 'w')
    f.write(json.dumps(training_map))
    f.close()