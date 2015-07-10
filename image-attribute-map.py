import json
import sys
from gensim.models import word2vec

'''
1. read the attribute tree in memory.
2. for each list of (key, prob) as pair:
    start from root: for each child:
        weighted distance of each keyword with the key*prob then sort. Take the sum of top 3 or max.
    like this we have sum for each key, child.
    Similarly take the sum over top three keys.

'''
model_file = '../code/word2vec-all/word2vec/trunk/vectors-phrase.bin'
model = None

top_number_of_items = 3
excludedCategories = ['services', 'others', 'price-value']

def normalize(word):
    return word.lower().replace(' ', '_')

def loadModelFile():
    global model
    global model_file
    model = word2vec.Word2Vec.load_word2vec_format(model_file, binary=True)

def findMaxForEachSource(classes, probs, keywords):
    index = 0
    result = []
    while index < len(classes):
        source_word = normalize(classes[index])
        source_prob = probs[index]
        index += 1
        interim = []
        for word in keywords:
            word = normalize(word)
            try:
                interim.append(model.similarity(source_word, word))
            except KeyError:
                #print 'key error for: ' + source_word + ' ; ' + word
                continue
        if len(interim) == 0:
            #print 'No similar word found for word, keywords: ' + source_word + ' ; ' + str(keywords)
            continue
        interim.sort(reverse=True)
        result.append((source_word, source_prob*interim[0]))
    return result


def findBestCategory(classes, probs, attribute_seed, path):
    nextNode = attribute_seed['next']
    if nextNode == {}:
        return
    result_node = {}
    for key in nextNode:
        keywords = nextNode[key]['keywords']
        source_max = findMaxForEachSource(classes, probs, keywords)
        source_max.sort(key=lambda k: k[1], reverse=True)
        sum_val = sum(map(lambda x: x[1], source_max[:top_number_of_items]))
        result_node[key] = sum_val
    result_items = result_node.items()
    result_items.sort(key=lambda k: k[1], reverse=True)
    index = 0
    winner_node, winner_val = result_items[index]
    while winner_node in excludedCategories:
        index += 1
        winner_node, winner_val = result_items[index]
    path.append(result_items[index])
    return findBestCategory(classes, probs, nextNode[winner_node], path)


if __name__ == '__main__':
    loadModelFile()
    attribute_seed = json.loads(open(sys.argv[1], 'r').read())
    image_tree = json.loads(open(sys.argv[2], 'r').read())
    output = []
    for index in image_tree:
        tree = image_tree[index]
        for res in tree['results']:
            url = res['url']
            classes = res['result']['tag']['classes']
            probs = res['result']['tag']['probs']
            # now find the perfect category.
            path = []
            findBestCategory(classes, probs, attribute_seed['root'], path)
            element = {}
            element['classes'] = classes
            element['url'] = url
            element['path'] = path
            output.append(element)
    f = open('output.json', 'w')
    f.write(json.dumps(output))
    f.close()