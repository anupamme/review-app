import json
from stanford_corenlp_pywrapper import CoreNLP
from gensim.models import word2vec
import sys

'''
Algo:
Step 1: Read the attribute_adjective_map.
step 2: read the positive adjective list.
step 3: read the negative adjective list.
step 4: read the positive_antonym map.
step 5: read the negative_antonym map.
step 6: read the file of sentences and for each sentence do following:
step 7: break line into attribute, [adjective], sentiment
step 8: candidate_adjectives = attribute_adjective_map[attribute]
step 9: from candidate_adjectives, find the adjective which has highest similarity with one of the adjective, do this for all adjectives.
step 10: pick the candidate adjective which has the max similarity in step 9.
step 11: if sentiment is +ve, and adjective is positive, return it else find its opposite from the negative_antonym. Similarly, if sentiment is -ve, do appropriate.
'''

anotnym_file = '/Volumes/anupam work/review-app-local/data/antonym_map.json'
positive_file = '/Volumes/anupam work/review-app-local/data/positives.json'
negative_file = '/Volumes/anupam work/review-app-local/data/negatives.json'
attribute_adjective_file = '/Volumes/anupam work/review-app-local/data/reverse_adj.json'
model_file = '/Volumes/anupam work/code/word2vec-all/word2vec/trunk/vectors-phrase.bin'
stanford_jars = '/Volumes/anupam work/code/stanford-jars/3.5/*'
review_attribute_file = '/Volumes/anupam work/review-app-local/data/forward_review.json'

attribute_adjective_map = {}
positive_array = []
negative_array = []
antonym_map = {}
model = None
proc = None

def init():
    attribute_adjective_map = json.loads(open(attribute_adjective_file, 'r').read())
    positive_array = json.loads(open(positive_file, 'r').read())
    negative_array = json.loads(open(negative_file, 'r').read())
    antonym_map = json.loads(open(antonym_map, 'r').read())
    model = word2vec.Word2Vec.load_word2vec_format(model_file, binary=True)
    proc = CoreNLP("parse", corenlp_jars=[stanford_jars])

if __name__ == "__main__":
    init()
    data = json.loads(open(review_attribute_file, 'r').read())
    for line in data:
        attribute = data[line]
        