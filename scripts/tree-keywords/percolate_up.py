import json
import sys

def takeUnionOfAllKeywordsMap(map_val):
    result = {}
    if map_val['next'] == {}:
        for key in map_val['keywords']:
            result[key] = map_val['keywords'][key]
    else:
        for key in map_val['next']:
            interim = takeUnionOfAllKeywordsMap(map_val['next'][key])
            for minor in interim:
                if minor in result:
                    result[minor] = max(result[minor], interim[minor])
                else:
                    result[minor] = interim[minor]
        map_val['keywords'] = result
    return result

if __name__ == "__main__":
    data = json.loads(open(sys.argv[1], 'r').read())
    map_ret = takeUnionOfAllKeywordsMap(data['root'])
    new_data = {}
    new_data['root'] = map_ret
    f = open(sys.argv[2], 'w')
    f.write(json.dumps(data))
    f.close()