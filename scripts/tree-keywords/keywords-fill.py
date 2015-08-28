import json
from gensim.models import word2vec
import sys

'''
read the attribute tree.
traverse to leaves.
fill the keywords at the leaf level: use word2vec to find nearest words. And filter which are not nouns.
Then traverse up and percolate those keywords one level up. Till you reach root node.
output the populated tree.
'''

model_file = '../code/word2vec-all/word2vec/trunk/vectors-phrase.bin'
model = None

def normalize(word):
    return word.lower().replace('-', '_').replace(' ', '_')
    
def loadModelFile():
    global model
    global model_file
    model = word2vec.Word2Vec.load_word2vec_format(model_file, binary=True)

def findNearestNouns(word, current_keywords):
    result = None
    if current_keywords != []:
        #print 'current keywords are not empty: ' + str(current_keywords)
        result = current_keywords
    else:
        try:
            normalized_noun = normalize(word)
            result = map(lambda (x,y): x, model.most_similar(word))
            result.append(word)
            #print 'current keywords calculated: ' + str(result)
        except KeyError:
            print 'key not found for key: ' + word
            result = []
    
    result_map = {}
    
    for val in result:
        result_map[val] = 1
    
    return result_map

'''
each node returns the dict of the keywords it has. Its parent collects the keywords of its children and form a collective collection.

'''
def takeUnionOfAllKeywordsMap(map_val):
    result = {}
    if map_val['next'] == {}:
        for key in map_val['keywords']:
            result[key] = map_val['keywords'][key]
    else:
        for key in map_val['next']:
            interim = takeUnionOfAllKeywords(map_val['next'][key])
            for minor in interim:
                if minor in result:
                    result[minor] = max(result[minor], interim[minor])
                else:
                    result[minor] = interim[minor]
        map_val['keywords'] = result
    return result

def takeUnionOfAllKeywords(map_val):
    result = {}
    if 'next' not in map_val:
        print 'next_error: ' + str(map_val)
        return result
    if map_val['next'] == {}:
        for key in map_val['keywords']:
            result[key] = 1
    else:
        for key in map_val['next']:
            interim = takeUnionOfAllKeywords(map_val['next'][key])
            for minor in interim:
                if minor in result:
                    result[minor] = max(result[minor], interim[minor])
                else:
                    result[minor] = interim[minor]
    map_val['keywords'] = result
    return result

if __name__ == "__main__":
    tree_file = sys.argv[1]
    att_tree = json.loads(open(tree_file, 'r').read())
    loadModelFile()
    print 'model loaded...'
    keywords = takeUnionOfAllKeywords(att_tree['root'])
    att_tree['root']['keywords'] = keywords
    output_file = sys.argv[2]
    f = open(output_file, 'w')
    f.write(json.dumps(att_tree))
    f.close()