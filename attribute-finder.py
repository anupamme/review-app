import nltk
import gensim
from gensim.models import word2vec
import json
from nltk import word_tokenize
import operator
import sys
import re

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

modelFile = "../trunk/vectors-phrase.bin"
possibleNounTags = ['NN', 'NNP', 'NNS', 'NNPS']
possibleAdjTags = ['JJ', 'JJR', 'JJS', 'RB', 'RBS', 'RBR']

'''
algorithm for noun parsing: 

1. Parse noun phrases rather than just nouns
2. 
'''

grammar_noun = r""" NP: {<NN>+}
                      : {<NNP>+}
                      : {<NNS>+}
                      : {<NNPS>+}"""

grammar_adj = r""" """

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
    
def buildReverseMaps():
    nounArr = foodMeta["nounList"]
    for val in nounArr:
        reverseNounMap[val] = "food"
    adjArr = foodMeta["descList"]
    for val in adjArr:
        reverseAdjMap[val] = "food"
    
    nounArr = serviceMeta["nounList"]
    for val in nounArr:
        reverseNounMap[val] = "service"
    adjArr = serviceMeta["descList"]
    for val in adjArr:
        reverseAdjMap[val] = "service"
        
    nounArr = locationMeta["nounList"]
    for val in nounArr:
        reverseNounMap[val] = "location"
    adjArr = locationMeta["descList"]
    for val in adjArr:
        reverseAdjMap[val] = "location"
        
    nounArr = viewMeta["nounList"]
    for val in nounArr:
        reverseNounMap[val] = "view"
    adjArr = viewMeta["descList"]
    for val in adjArr:
        reverseAdjMap[val] = "view"
        
    nounArr = overallMeta["nounList"]
    for val in nounArr:
        reverseNounMap[val] = "overall"
    adjArr = overallMeta["descList"]
    for val in adjArr:
        reverseAdjMap[val] = "overall"
        
    nounArr = roomMeta["nounList"]
    for val in nounArr:
        reverseNounMap[val] = "room"
    adjArr = roomMeta["descList"]
    for val in adjArr:
        reverseAdjMap[val] = "room"
        
    nounArr = feelMeta["nounList"]
    for val in nounArr:
        reverseNounMap[val] = "feel"
    adjArr = feelMeta["descList"]
    for val in adjArr:
        reverseAdjMap[val] = "feel"
        
    nounArr = wifiMeta["nounList"]
    for val in nounArr:
        reverseNounMap[val] = "wifi"
    adjArr = wifiMeta["descList"]
    for val in adjArr:
        reverseAdjMap[val] = "wifi"
        
    nounArr = pickupMeta["nounList"]
    for val in nounArr:
        reverseNounMap[val] = "pickup"
    adjArr = pickupMeta["descList"]
    for val in adjArr:
        reverseAdjMap[val] = "pickup"
        
    nounArr = sleepMeta["nounList"]
    for val in nounArr:
        reverseNounMap[val] = "sleep"
    adjArr = sleepMeta["descList"]
    for val in adjArr:
        reverseAdjMap[val] = "sleep"
        
    nounArr = priceMeta["nounList"]
    for val in nounArr:
        reverseNounMap[val] = "price"
    adjArr = priceMeta["descList"]
    for val in adjArr:
        reverseAdjMap[val] = "price"
        
    nounArr = purposeMeta["nounList"]
    for val in nounArr:
        reverseNounMap[val] = "purpose"
    adjArr = purposeMeta["descList"]
    for val in adjArr:
        reverseAdjMap[val] = "purpose"
        
    nounArr = breakfastMeta["nounList"]
    for val in nounArr:
        reverseNounMap[val] = "breakfast"
    adjArr = breakfastMeta["descList"]
    for val in adjArr:
        reverseAdjMap[val] = "breakfast"
        
    nounArr = bathroomMeta["nounList"]
    for val in nounArr:
        reverseNounMap[val] = "bathroom"
    adjArr = bathroomMeta["descList"]
    for val in adjArr:
        reverseAdjMap[val] = "bathroom"
        
    nounArr = poolMeta["nounList"]
    for val in nounArr:
        reverseNounMap[val] = "pool"
    adjArr = poolMeta["descList"]
    for val in adjArr:
        reverseAdjMap[val] = "pool"

def checkIfDone(user_controlled, user_input, reviewArr, current_count):
    if user_controlled:
        return user_input == 'stop'
    else:
        return (len(reviewArr) == current_count + 1)
        
if __name__ == "__main__":
    loadModelFile()
    foodNounCloud = buildWordCloud(foodMeta['nounList'])
    foodAdjCloud = buildWordCloud(foodMeta['descList'])
    serviceNounCloud = buildWordCloud(serviceMeta['nounList'])
    serviceAdjCloud = buildWordCloud(serviceMeta['descList'])
    viewNounCloud = buildWordCloud(viewMeta['nounList'])
    viewAdjCloud = buildWordCloud(viewMeta['descList'])
    locNounCloud = buildWordCloud(locationMeta['nounList'])
    locAdjCloud = buildWordCloud(locationMeta['descList'])
    overallNounCloud = buildWordCloud(overallMeta['nounList'])
    overallAdjCloud = buildWordCloud(overallMeta['descList'])
    roomNounCloud = buildWordCloud(roomMeta['nounList'])
    roomAdjCloud = buildWordCloud(roomMeta['descList'])
    feelNounCloud = buildWordCloud(feelMeta['nounList'])
    feelAdjCloud = buildWordCloud(feelMeta['descList'])
    wifiNounCloud = buildWordCloud(wifiMeta['nounList'])
    wifiAdjCloud = buildWordCloud(wifiMeta['descList'])
    pickupNounCloud = buildWordCloud(pickupMeta['nounList'])
    pickupAdjCloud = buildWordCloud(pickupMeta['descList'])
    sleepNounCloud = buildWordCloud(sleepMeta['nounList'])
    sleepAdjCloud = buildWordCloud(sleepMeta['descList'])
    priceNounCloud = buildWordCloud(priceMeta['nounList'])
    priceAdjCloud = buildWordCloud(priceMeta['descList'])
    purposeNounCloud = buildWordCloud(purposeMeta['nounList'])
    purposeAdjCloud = buildWordCloud(purposeMeta['descList'])
    bathroomNounCloud = buildWordCloud(bathroomMeta['nounList'])
    bathroomAdjCloud = buildWordCloud(bathroomMeta['descList'])
    breakfastNounCloud = buildWordCloud(breakfastMeta['nounList'])
    breakfastAdjCloud = buildWordCloud(breakfastMeta['descList'])
    poolNounCloud = buildWordCloud(poolMeta['nounList'])
    poolAdjCloud = buildWordCloud(poolMeta['descList'])
    buildReverseMaps()
    user_controlled = False
    reviewArr = None
    user_input = None
    if len(sys.argv) == 1:
        user_controlled = True
        user_input = raw_input("Some input please: ")
    else:
        reviewArr = json.loads(open(sys.argv[1], 'r').read())
    
    count = 0
    result = []
    while not checkIfDone(user_controlled, user_input, reviewArr, count):
        if user_controlled:
            review = user_input
        else:
            review = reviewArr[count]
            count = count + 1

        review = review.encode('utf-8')
        #print '\nsentence: ' + review
        tokens = word_tokenize(review)
        try:
            pos_tags = nltk.pos_tag(tokens)
        except UnicodeDecodeError:
            print 'cannot decode: ' + str(tokens)
        if len(pos_tags) == 0:
            print 'pos tags are empty for: ' + review
            continue
        #print 'pos tags: ' + str(pos_tags)
        res_noun = []
        res_adj = []
        noun_tags = []
        adj_tags = []
        for word,pos in pos_tags:
            word = word.lower()
            # experimental to decide on prp.
            if pos == 'PRP':
                max_match = 'service'
                max_val = [0.4, (word, 'service', 'service')]
                res_noun.append((max_val[0], max_match, max_val[1]))
                continue
            # nounTag is used to determine attribute.
            if pos in possibleNounTags:
                noun_tags.append(word)
                try: 
                    similar_words = model.most_similar(word)
                except KeyError:
                    print('not found word: ' + word)
                    if pos == 'NNP':
                        max_match = 'service'
                        max_val = [0.4, (word, 'service', 'service')]
                        res_noun.append((max_val[0], max_match, max_val[1]))
                    continue
                max_match, max_val = findMaxMatch(word, similar_words, foodNounCloud)
                res_noun.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, serviceNounCloud)
                res_noun.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, viewNounCloud)
                res_noun.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, locNounCloud)
                res_noun.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, overallNounCloud)
                res_noun.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, roomNounCloud)
                res_noun.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, feelNounCloud)
                res_noun.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, wifiNounCloud)
                res_noun.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, pickupNounCloud)
                res_noun.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, sleepNounCloud)
                res_noun.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, priceNounCloud)
                res_noun.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, purposeNounCloud)
                res_noun.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, breakfastNounCloud)
                res_noun.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, bathroomNounCloud)
                res_noun.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, poolNounCloud)
                res_noun.append((max_val[0], max_match, max_val[1]))
            # adjTag is used to figure why that attribute is selected.
            if pos in possibleAdjTags:
                adj_tags.append(word)
                try: 
                    similar_words = model.most_similar(word)
                except KeyError:
                    print('not found word: ' + word)
                    continue
                max_match, max_val = findMaxMatch(word, similar_words, foodAdjCloud)
                res_adj.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, serviceAdjCloud)
                res_adj.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, viewAdjCloud)
                res_adj.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, locAdjCloud)
                res_adj.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, overallAdjCloud)
                res_adj.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, roomAdjCloud)
                res_adj.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, feelAdjCloud)
                res_adj.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, wifiAdjCloud)
                res_adj.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, pickupAdjCloud)
                res_adj.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, sleepAdjCloud)
                res_adj.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, priceAdjCloud)
                res_adj.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, purposeAdjCloud)
                res_adj.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, breakfastAdjCloud)
                res_adj.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, bathroomAdjCloud)
                res_adj.append((max_val[0], max_match, max_val[1]))
                max_match, max_val = findMaxMatch(word, similar_words, poolAdjCloud)
                res_adj.append((max_val[0], max_match, max_val[1]))

        sorted_res_noun = sorted(res_noun, key=operator.itemgetter(0), reverse=True)
        if len(sorted_res_noun) == 0:
            continue
        top_noun_data = sorted_res_noun[0]
        top_noun = top_noun_data[1]
        top_noun_root = reverseNounMap[top_noun]
        element = {}
        element['sentence'] = review
        element ['nouns'] = noun_tags
        element['adjectives'] = adj_tags
        #print 'possible nouns: ' + str(noun_tags)
        #print 'possible adjectives: ' + str(adj_tags)
        element['top_noun'] = [top_noun_root, top_noun_data]
        print 'top noun root and val: ' + top_noun_root + ' : ' + str(top_noun_data)
        sorted_res_adj = sorted(res_adj, key=operator.itemgetter(0), reverse=True)
        for val in sorted_res_adj:
    #        print 'considering adj: ' + str(val)
            adj_val = val[1]
            adj_val_root = reverseAdjMap[adj_val]
            if top_noun_root == adj_val_root:
                print 'Found! adj val: ' + str(val)
                element['top_adj'] = val
                break
        result.append(element)
        if user_controlled:
            user_input = raw_input("Some input please: ")
    f = open('output.json', 'w')
    f.close(json.dumps(result))
    f.close()