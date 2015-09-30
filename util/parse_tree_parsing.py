import json
from stanford_corenlp_pywrapper import CoreNLP
from ast import literal_eval

stanford_jars = "/Volumes/anupam work/code/stanford-jars/3.5/*"

def parse_phrase(child_node, phrase):
    index = 0
    print 'child_node: ' + str(child_node)
    while index < len(child_node):
        node = child_node[index]
        #print 'node: ' + str(node)
        if type(node) == tuple:
            parse_phrase(node, phrase)
        else:
            if index == 0:
                index += 1
                continue    # skip the first word
            assert(type(node) == str)
            phrase.append(node)
        index += 1
    
def parse_from_parse_tree(parse_tree, tag_name, result):
    print 'parse tree: ' + str(parse_tree)
    assert(type(parse_tree) == tuple)
    root_node = parse_tree[0]
    assert(type(root_node) == str)
    if root_node == tag_name:
        phrase_arr = []
        parse_phrase(parse_tree[1:], phrase_arr)
        assert(phrase_arr != [])
        phrase_str = ' '.join(phrase_arr)
        result.append(phrase_str)
    index = 1
    while index < len(parse_tree):
        node = parse_tree[index]
        index += 1
        node_type = type(node)
        if node_type == tuple:
            parse_from_parse_tree(node, tag_name, result)
        else:
            assert(node_type == str)

if __name__ == "__main__":
    proc = CoreNLP("parse", corenlp_jars=[stanford_jars])
    user_input = raw_input("Some input please: ")
    while user_input != 'stop':
        processed = proc.parse_doc(user_input)
        parse_tree_str = str(processed['sentences'][0]['parse']).replace(' ', ' ,').replace(' ', '\' ').replace('(', '(\'').replace(')', '\')').replace(',', ',\'').replace('\'(', '(').replace(')\'', ')').replace(')\')', '))').replace(')\')', '))')
        
        print 'parse tree: ' + parse_tree_str
        parse_tree = literal_eval(parse_tree_str)
        result_np = []
        parse_from_parse_tree(parse_tree, 'NP', result_np)
        print 'result_np: ' + str(result_np)
        user_input = raw_input("Some input please: ")