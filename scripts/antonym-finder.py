import textwrap
from nltk.corpus import wordnet as wn
import sys
import json

POS = {
    'v': 'verb', 'a': 'adjective', 's': 'satellite adjective', 
    'n': 'noun', 'r': 'adverb'}

def info(word, pos=None):
    antonym_list = {}
    for i, syn in enumerate(wn.synsets(word, pos)):
        #print 'synonyms: ' + str(syn.lemma_names) + '; ' + str(type(syn.lemma_names))
        #syns = [n for n in syn.lemma_names]
        #syns = [n.replace('_', ' ') for n in syn.lemma_names()]
        ants = [a for m in syn.lemmas() for a in m.antonyms()]
        #ind = ' '*12
        #defn= textwrap.wrap(syn.definition(), 64)
#        if syn.pos() != 'a':
#            continue
        #print 'sense %d (%s)' % (i + 1, POS[syn.pos()])
#        print 'definition: ' + ('\n' + ind).join(defn)
#        print '  synonyms:', ', '.join(syns)
        pos_tag = POS[syn.pos()]
        if ants:
            for ant in ants:
                if pos_tag not in antonym_list:
                    antonym_list[pos_tag] = a.name()
            #print '  antonyms:', ', '.join(a.name() for a in ants)
#        if syn.examples():
#            print '  examples: ' + ('\n' + ind).join(syn.examples())
#        print
    return antonym_list

#info('near')

if __name__ == "__main__":
#    antonym_list = info(sys.argv[1])
#    print sys.argv[1] + ': ' + str(antonym_list)
    data = json.loads(open(sys.argv[1], 'r').read())
    output = {}
    for key in data:
        adj_list = data[key]
        print 'key: ' + str(key)
        for item in adj_list:
            adj_pos = item[0]
            adj_map = info(adj_pos)
            if adj_map == {}:
                continue
            output[adj_pos] = adj_map
    f = open('data/antonym_map.json', 'w')
    f.write(json.dumps(output))
    f.close()