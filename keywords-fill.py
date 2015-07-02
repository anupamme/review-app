import json
from gensim.models import word2vec


'''
read the attribute tree.
traverse to leaves. 
fill the keywords at the leaf level: use word2vec to find nearest words. And filter which are not nouns.
Then traverse up and percolate those keywords one level up. Till you reach root node.
output the populated tree.
'''

tree_file = 'attribute-tree.json'
model_file = '../word2vec-all/word2vec/trunk/vectors-phrase.bin'
model = None
pickFirst = lambda (x,y): x
    
def loadModelFile():
    global model
    global model_file
    model = word2vec.Word2Vec.load_word2vec_format(model_file, binary=True)

def findNearestNouns(word, current_keywords):
    if current_keywords != []:
        print 'current keywords are not empty: ' + str(current_keywords)
        return current_keywords
    try:
        result = map(pickFirst, model.most_similar(word))
        print 'current keywords calculated: ' + str(result)
    except KeyError:
        print 'key not found for key: ' + word
        result = []
    return result

def takeUnionOfAllKeywords(node):
    result = []
    for key in node:
        next_node = node[key]
        #print 'checking: ' + str(next_node) + str(key)
        val = next_node['next']
        if val == {}:
            print 'val is empty'
            current_keywords = next_node['keywords']
            keywords = findNearestNouns(key, current_keywords)
        else :
            keywords = takeUnionOfAllKeywords(val)
        next_node['keywords'] = keywords
        if keywords == None:
            print 'No key words found for: ' + str(key)
            continue
        result = result + keywords
    return result

if __name__ == "__main__":
    att_tree = json.loads(open(tree_file, 'r').read())
    loadModelFile()
    print 'model loaded...'
    keywords = takeUnionOfAllKeywords(att_tree['root']['next'])
    att_tree['root']['keywords'] = keywords
    f = open('keywords-filled.json', 'w')
    f.write(json.dumps(att_tree))
    f.close()