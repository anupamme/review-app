import sys
import json
sys.path.insert(0, 'scripts/reviews/')
import pprint

import hotel_attribute_finder as finder
hash_tag_delim = '_'

if __name__ == "__main__":
    res = finder.find_city_hotel_attributes(sys.argv[1], sys.argv[2])
    # most talked about items:
    sentiment_map = res[0]
    most_talked_about = {}
    for attr in sentiment_map:
        s = sum(sentiment_map[attr].values())
        most_talked_about[attr] = s
    most_talked_about_arr = most_talked_about.items()
    most_talked_about_arr.sort(key=lambda x: x[1], reverse=True)
    
    # print_hashtags
    hash_tag_map = {}
    adjective_map = res[1]
    for attr in adjective_map:
        adjective_values = adjective_map[attr]
        for adj in adjective_values:
            adj_weight = adjective_values[adj]
            hash_tag = adj + hash_tag_delim + attr
            hash_tag_map[hash_tag] = adj_weight
    hash_tag_arr = hash_tag_map.items()
    hash_tag_arr.sort(key=lambda x: x[1], reverse=True)
    
    print 'most talked about:'
    pp = pprint.PrettyPrinter(depth=2)
    pp.pprint(most_talked_about_arr)
    
    print 'hash_tags:'
    pp.pprint(hash_tag_arr)
    
    most_hash_tags = []
    for attr, attr_score in most_talked_about_arr:
        adjective_values = adjective_map[attr].items()
        if adjective_values == []:
            print 'No adjective found for: ' + str(attr)
            continue
        adj, adj_score = adjective_values[0]
        hash_tag = adj + hash_tag_delim + attr
        hash_score = attr_score * adj_score
        most_hash_tags.append((hash_tag, hash_score))
    most_hash_tags.sort(key=lambda x: x[1], reverse=True)
    
    print 'for most talked about:'
    pp.pprint(most_hash_tags)