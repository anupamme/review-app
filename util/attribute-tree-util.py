import json
import sys

def delete_path_keyword(attribute_tree, path, keyword):
    search_node = path[0]
    assert(search_node in attribute_tree['next'])
    attribute_tree['next']['keywords'].remove(keyword)
    val = attribute_tree['next'][search_node]
    delete_path_keyword(val, path[1:], keyword)

if __main__ == "__main__":
    att_tree = json.loads(open(sys.argv[1], 'r').read())
    