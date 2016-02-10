import json
import sys

def print_nodes(node_name, node):
#  for key in node:
#    print key
  if node['next'] == {}:
    print node_name
  else:
    for inner in node['next']:
#      print inner + ';'
      print_nodes(inner, node['next'][inner])
      
      
if __name__ == "__main__":
  data = json.loads(open(sys.argv[1], 'r').read())
  print_nodes('root', data['root'])