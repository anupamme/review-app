import json
import sys

def merge_trees(new_tree, dirty_tree, merge_tree):
    if new_tree['next'] == {}:
        merge_tree['keywords'] = dirty_tree['keywords']
        merge_tree['next'] = {}
        return
    
    merge_tree['next'] = {}
    merge_tree['keywords'] = []
    
    for node in new_tree['next']:
        merge_tree['next'][node] = {}
        if node in dirty_tree['next']:
            merge_trees(new_tree['next'][node], dirty_tree['next'][node], merge_tree['next'][node])
        else:
            merge_tree['next'][node] = new_tree['next'][node]

if __name__ == "__main__":
    new_tree = json.loads(open(sys.argv[1], 'r').read())
    dirty_tree = json.loads(open(sys.argv[2], 'r').read())
    
    merge_tree = {}
    merge_tree['root'] = {}
    merge_trees(new_tree['root'], dirty_tree['root'], merge_tree['root'])
    
    f = open('merge_tree.json', 'w')
    f.write(json.dumps(merge_tree))
    f.close()