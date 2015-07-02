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

attribute_tree_file = 'keywords-filled.json'
dataFile = "review-lines.txt"
model_file = '../word2vec-all/word2vec/trunk/vectors-phrase.bin'

attribute_tree = None
model = None
possibleNounTags = ['NN', 'NNP', 'NNS', 'NNPS']
numIterations = 2

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
            print 'Key Error for key: ' + tag
            break
        if distance > max_distance:
            max_distance = distance
    return max_distance

def findNextBest(tag, node, path):
    node['keywords'].append(tag)
    path.append(node)
    max_distance = -1
    max_node = None
    distance = []
    index = 0
    if len(node['next']) == 0:
        return
    for inner in node['next']:
        #print 'inner: ' + inner
        #print 'tag: ' + tag
        dist = findMaxDistance(tag, node['next'][inner]['keywords'])
        #print 'distance: ' + str(dist)
        if dist == -1:
            return
        if dist > max_distance:
            max_node = inner
        index += 1
    winner_node = node['next'][max_node]
    findNextBest(tag, winner_node, path)

def findNext(word, node, path):
    path.append(node)
    if len(node['next']) == 0:
        return
    for inner in node['next']:
        if word in node['next'][inner]['keywords']:
            findNext(word, node['next'][inner], path)
    
def findPositionOfTag(word):
    node = attribute_tree['root']
    path = []
    if word in node['keywords']:
        findNext(word, node, path)
        return path, False
    else:
        findNextBest(word, node, path)
        return path, True

if __name__ == "__main__":
    loadModelFile()
    #print 'model file loaded ...'
    datalines = open(sys.argv[1], 'r').read().split('.')
    attribute_tree = json.loads(open(attribute_tree_file, 'r').read())
    for line in datalines:
        tokens = word_tokenize(line)
        pos_tags = nltk.pos_tag(tokens)
        #print 'pos tags: ' + str(pos_tags)
        for word, tag in pos_tags:
            if tag in possibleNounTags:
                #print 'in possible noun tags'
                path, isNewAddition = findPositionOfTag(word)
                #print 'res: ' + str(path) + ' : ' + str(isNewAddition)
                if isNewAddition:
                    print 'Added new element: ' + tag + ' -> ' + str(path)
                else:
                    print 'Found existing element: ' + tag + ' -> ' + str(path)
    f = open('expanded-seed.json', 'w')
    f.write(json.dumps(attribute_tree))
    f.close()