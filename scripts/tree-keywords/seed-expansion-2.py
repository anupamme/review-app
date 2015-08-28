import json
from gensim.models import word2vec
from nltk import word_tokenize
import nltk
import sys

'''
0. load the attribute tree
1. read subset of array of sentences.
2. for each sentence do pos tag and extract nouns
3. for each noun, see if there is an exact match with any word for any child:
4. If yes, go down the tree and note down the path.
5. If not, find distance of the noun with all the keywords and find avg of top 3 values. 
6. Pick the child which has max of it. Add this word in the keywords list. Go down the tree and continue the same operations.
7. Keep record of exact match and approx match.
'''

attribute_tree_file = 'data/keywords-filled.json'
model_file = '../code/word2vec-all/word2vec/trunk/vectors-phrase.bin'

attribute_tree = None
model = None
possibleNounTags = ['NN', 'NNP', 'NNS', 'NNPS']
numIterations = 5

def normalize(word):
    return word.lower().replace(' ', '_').encode('utf-8')

def loadModelFile():
    global model
    global model_file
    model = word2vec.Word2Vec.load_word2vec_format(model_file, binary=True)

def findMaxDistance(tag, keywords):
    max_distance = -1
    #print 'keywords in findMaxDistance: ' + str(keywords)
    for word in keywords:
        try:
            distance = model.similarity(tag, word)
        except KeyError:
            #print 'Key Error for key: ' + tag
            continue
        if distance > max_distance:
            max_distance = distance
    return max_distance

def findMaxAvgDistance(tag, keywords):
    distance_arr = []
    #print 'keywords in findMaxDistance: ' + str(keywords)
    for word in keywords:
        try:
            distance = model.similarity(tag, word)
            distance_arr.append(distance)
        except KeyError:
            #print 'Key Error for key: ' + tag
            continue
    length = len(distance_arr)
    if length == 0:
        #print 'zero length array for tag, keyword: ' + tag + str(keywords)
        return -1
    else:
        distance_arr_sorted = sorted(distance_arr, reverse=True)
        return (sum(distance_arr_sorted[0:length])/length)

def findNextBest(word, map_val, path_so_far, isRoot):
    if map_val['next'] == {}:
        map_val['keywords'][word] = 1
        return True
    else:
        max_distance = -1
        max_node = None
        for node in map_val['next']:
            local_distance = findMaxAvgDistance(word, map_val['keywords'])
            if local_distance < 0.2:
                print 'max distance too low: ' + str(local_distance)
                continue
            if local_distance > max_distance:
                max_distance = local_distance
                max_node = node
        if max_node == None:
            print 'max node is none for word: ' + word
            return False
        path_so_far.append(max_node)
        return findNextBest(word, map_val['next'][max_node], path_so_far, False)
    
def findNext(word, node, path):
    if len(node['next']) == 0:
        return
    for inner in node['next']:
        if word in node['next'][inner]['keywords']:
            path.append(inner)
            findNext(word, node['next'][inner], path)

'''
takes a word as argument and returns path to the leaf node. And true or false depending on whether the word was already present or it was added.

'''
def findPositionOfTag(word):
    # init process
    node = attribute_tree['root']
    path = ['root']
    
    if word in node['keywords']:
        findNext(word, node, path)
        return path, False
    else:
        val = findNextBest(word, node, path, True)
        if val == False:
            print 'Could not find word for word: ' + word
        return path, True

def takeUnionOfAllKeywordsMap(map_val):
    result = {}
    if map_val['next'] == {}:
        for key in map_val['keywords']:
            result[key] = map_val['keywords'][key]
    else:
        for key in map_val['next']:
            interim = takeUnionOfAllKeywordsMap(map_val['next'][key])
            for minor in interim:
                if minor in result:
                    result[minor] = max(result[minor], interim[minor])
                else:
                    result[minor] = interim[minor]
        map_val['keywords'] = result
    return result
    
'''
The output of keywords-fill.py becomes input to this file.

'''
if __name__ == "__main__":
    loadModelFile()
    #print 'model file loaded ...'
    datalinesMeta = json.loads(open(sys.argv[1], 'r').read())
    length_data_lines = len(datalinesMeta)
    #datalinesMetaSub = datalinesMeta[0:(len/10)]
    attribute_tree = json.loads(open(sys.argv[2], 'r').read())
    iteration_count = 0
    numLinesForEachIteration = (len(datalinesMeta)/20) / numIterations
    while iteration_count < numIterations:
        print 'iteration_count: ' + str(iteration_count)
        num_found = 0
        num_added = 0
        datalines = datalinesMeta[numLinesForEachIteration * iteration_count : (numLinesForEachIteration * (iteration_count + 1))]
        iteration_count += 1
        for line in datalines:
            tokens = word_tokenize(line)
            pos_tags = nltk.pos_tag(tokens)
            #print 'pos tags: ' + str(pos_tags)
            for word, tag in pos_tags:
                word = normalize(word)
                if tag in possibleNounTags:
                    #print 'in possible noun tags'
                    path, isNewAddition = findPositionOfTag(word)
                    #print 'res: ' + str(path) + ' : ' + str(isNewAddition)
                    if isNewAddition:
                        num_added += 1
                        #print 'Added new element: ' + word + ' -> ' + str(path)
                    else:
                        num_found += 1
                        #print 'Found existing element: ' + tag + ' -> ' + str(path)
        takeUnionOfAllKeywordsMap(attribute_tree['root'])
        print 'num_found: ' + str(float(num_found))
        print 'num_added: ' + str(float(num_added))
        print 'percentage val: ' + str(float(num_found / (num_found + num_added)))
    f = open(sys.argv[3], 'w')
    f.write(json.dumps(attribute_tree))
    f.close()