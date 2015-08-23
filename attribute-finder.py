import nltk
import gensim
from gensim.models import word2vec
import json
from nltk import word_tokenize
import operator
import sys

foodAssists = ['food', 'ambience', 'taste', 'breakfast', 'lunch', 'dinner', 'drinks']

foodMeta = {'nounList': ["food", "lunch", "dinner", "drinks", 'restaurant'], "descList": ["taste", "presentation", "service"]}

breakfastMeta = {'nounList': ['breakfast', 'cereals', 'breads', 'cuts', 'fruits', 'yoghurt', 'coffee', 'buffet', 'eggs', 'sausage', 'bacon', 'spread'], 'descList': ['cold', 'hygienic']}

serviceAssists = ['service', 'politeness', 'accommodating', 'speed', 'friendly']

serviceMeta = {'nounList': ['owner', 'staff', 'service', 'lady', 'gentleman', 'embarrassment', 'service', 'reception', 'desk', 'suggestions', 'welcome', 'luggage', 'manager', 'members', 'rude', 'course', 'english', 'helping', 'front'], 'descList': ['polite', 'friendly', 'accommodating', 'personal', 'welcoming', 'helpful', 'inflexible', 'standard', 'rudely']}

viewAssists = ['view', 'breathtaking', 'vista', 'sea', 'forest', 'skyline', 'desert', 'valley', 'beach', 'sunset']

viewMeta = {'nounList': ['view', 'balcony', 'balconies', 'watch', 'stars', 'mountains', 'river', 'look'], 'descList': ['breathtaking', 'sea', 'forest', 'skyline', 'desert', 'valley', 'beach', 'sunset', 'rainy']}

roomAssists = ["room", "size", "linen", "furniture", "bathroom"]

roomMeta = {'nounList': ['room', 'balconies', 'bell', 'floor'], 'descList': ['size', 'linen', 'furniture', 'bathroom', 'lovely', 'spacious', 'clean', 'top', 'luxurious', 'comfortable', 'generous']}

livingareaMeta = {'nounList': ['living', 'area'], 'descList': ['dining']}

petMeta = {'nounList': ['pet', 'dog'], 'descList': ['leash']}

bathroomMeta = {'nounList': ['shower', 'cubicle', 'water'], 'descList': ['modern']}

purposeMeta = {'nounList': ['honeymoon', 'business', 'family', 'group', 'friends'], 'descList': ['business']}

overallMeta = {'nounList': ['time', 'hotel', 'experience', 'customer','hotels', 'world', 'impression', 'misfortune', 'home', 'stay', 'chore', 'amenities', 'place', 'stairs', 'complaints', 'building', 'annex', 'chalet', 'trip', 'overall', 'charm', 'information', 'welcoming', 'sofa', 'library', 'details', 'attention'], 'descList': ['wonderful', 'fantastic', 'just', 'rustic', 'pet_friendly', 'professional']}

locationMeta = {'nounList': ['location', 'shops', 'walk', 'range', 'airport', 'train', 'mins', 'station', 'minute', 'door', 'place', 'center', 'city', 'grassy', 'walking'], 'descList': ['excellent', 'ideal', 'close', 'approachable', 'quiet', 'noisy', 'walkable', 'next']}

feelMeta = {'nounList': ["feelings"], 'descList': ['business', 'romantic', 'family', 'quirky', 'formal', 'casual', 'dated']}

wifiMeta = {'nounList': ['wifi', 'internet', 'skype', 'movies', 'bandwidth', 'facetime'], 'descList': ['speed', 'fast', 'freely']}

pickupMeta = {'nounList': ['shuttle', 'taxi', 'stop', 'drop'], 'descList': ['free']}

sleepMeta = {'nounList': ['sleep'], 'descList': ['quiet']}

priceMeta = {'nounList': ['budget', 'option', 'price'], 'descList': ['expensive', 'cheap', 'high', 'quite']}

poolMeta = {'nounList': ['pool', 'swimming', 'spa', 'infinity', 'jacuzzi', 'wet', 'sauna', 'temperature', 'gym', 'swim', 'indoor', 'robe'], 'descList': ['dry']}

reverseNounMap = {}
reverseAdjMap = {}

modelFile = "../../word2vec-all/word2vec/trunk/vectors-phrase.bin"
possibleNounTags = ['NN', 'NNP', 'NNS', 'NNPS']
possibleAdjTags = ['JJ', 'JJR', 'JJS', 'RB', 'RBS']
model = None

'''
algorithm:
    1. read the input from file. 
    2. do pos tagging.
    3. from nouns figure out whether it talks about food by using foodAssists
    4. If yes, figure what it talks about in food meaning which foodAssists have the highest probability
    5. if it is indeed food, then figure which kind of food is present.
        
'''

def buildWordCloud(valueArr):
    result = {}
    for val in valueArr:
        result[val] = model.most_similar(val)
    return result

def loadModelFile():
    global model
    global modelFile
    model = word2vec.Word2Vec.load_word2vec_format(modelFile, binary=True)

def findMaxMatch(destination, nounList, prospectiveMap):
    result = {}
    for prosKey in prospectiveMap:
        listOfNearWords = prospectiveMap[prosKey]
        for word, distanceFromRoot in listOfNearWords:
            for nounChild, nounDistance in nounList:
                mid_distance = model.similarity(word, nounChild)
                totalDistance = distanceFromRoot * mid_distance * nounDistance
                if prosKey not in result:
                    result[prosKey] = []
                result[prosKey].append((totalDistance, (prosKey, word, nounChild, destination)))
    sortedResult = {}
    for prosKey in result:
        sortedResult[prosKey] = sorted(result[prosKey], key=operator.itemgetter(0), reverse=True)
    sortedMeta = sorted(sortedResult.items(), key=operator.itemgetter(1), reverse=True)
    return sortedMeta[0][0], sortedMeta[0][1][0]
    

if __name__ == "__main__":
    loadModelFile()
#    reviewData = json.loads(open(sys.argv[1], 'r').read())
#    reviewArr = reviewData['review']
    reviewArr = json.loads(open(sys.argv[1], 'r').read())
    # build word clouds:
    # check for food.
    foodNounCloud = buildWordCloud(foodMeta['nounList'])
    foodAdjCloud = buildWordCloud(foodMeta['descList'])
    serviceNounCloud = buildWordCloud(serviceMeta['nounList'])
    serviceAdjCloud = buildWordCloud(serviceMeta['descList'])
    viewNounCloud = buildWordCloud(viewMeta['nounList'])
    viewAdjCloud = buildWordCloud(viewMeta['descList'])
    locNounCloud = buildWordCloud(locationMeta['nounList'])
    locAdjCloud = buildWordCloud(locationMeta['descList'])
#    serviceCloud = buildWordCloud(serviceAssists)
#    viewCloud = buildWordCloud(viewAssists)
    count = 0
    for review in reviewArr:
        count = count + 1
        if count == 10:
            break
        tokens = word_tokenize(review)
        pos_tags = nltk.pos_tag(tokens)
        print 'pos tags: ' + str(pos_tags)
        res_noun = []
        res_adj = []
        for word,pos in pos_tags:
            word = word.encode('utf-8')
            for nounTag in possibleNounTags:
                if nounTag == pos:
                    print 'checking for noun word: ' + word
                    try: 
                        similar_words = model.most_similar(word)
                    except KeyError:
                        print('not found word: ' + word)
#                        if pos == 'NNP':
#                            max_match = 'service'
#                            max_val = [1.0, ('service', 'service')]
#                            res_noun.append((max_val[0], max_match, max_val[1]))
                        continue
                    max_match, max_val = findMaxMatch(word, similar_words, foodNounCloud)
#                    print 'max food-noun match: ' + max_match
#                    print 'max food-noun val: ' + str(max_val)
                    res_noun.append((max_val[0], max_match, max_val[1]))
#                    if pos == 'NNP':
#                        max_match = 'service'
#                        max_val = [1.0, ('service', 'service')]
#                    else:
                    max_match, max_val = findMaxMatch(word, similar_words, serviceNounCloud)
                    res_noun.append((max_val[0], max_match, max_val[1]))
#                    print 'max service-noun match: ' + max_match
#                    print 'max service-noun val: ' + str(max_val)
                    max_match, max_val = findMaxMatch(word, similar_words, viewNounCloud)
                    res_noun.append((max_val[0], max_match, max_val[1]))
                    max_match, max_val = findMaxMatch(word, similar_words, locNounCloud)
                    res_noun.append((max_val[0], max_match, max_val[1]))
#                    print 'max view-noun match: ' + max_match
#                    print 'max view-noun val: ' + str(max_val)
            for adjTag in possibleAdjTags:
                if adjTag == pos:
                    print 'checking for adj word: ' + word
                    try: 
                        similar_words = model.most_similar(word)
                    except KeyError:
                        print('not found word: ' + word)
                        continue
                    max_match, max_val = findMaxMatch(word, similar_words, foodAdjCloud)
                    res_adj.append((max_val[0], max_match, max_val[1]))
#                    print 'max food-adj match: ' + max_match
#                    print 'max food-adj val: ' + str(max_val)
                    max_match, max_val = findMaxMatch(word, similar_words, serviceAdjCloud)
                    res_adj.append((max_val[0], max_match, max_val[1]))
    #                print 'max service-adj match: ' + max_match
    #                print 'max service-adj val: ' + str(max_val)
                    max_match, max_val = findMaxMatch(word, similar_words, viewAdjCloud)
                    res_adj.append((max_val[0], max_match, max_val[1]))
                    max_match, max_val = findMaxMatch(word, similar_words, locAdjCloud)
                    res_adj.append((max_val[0], max_match, max_val[1]))
#                    print 'max view-adj match: ' + max_match
#                    print 'max view-adj val: ' + str(max_val)
        #print 'unsorted: ' + str(res_noun)
        sorted_res_noun = sorted(res_noun, key=operator.itemgetter(0), reverse=True)
        for val in sorted_res_noun:
            print 'noun val: ' + str(val)
        sorted_res_adj = sorted(res_adj, key=operator.itemgetter(0), reverse=True)
        for val in sorted_res_adj:
            print 'adj val: ' + str(val)