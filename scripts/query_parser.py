import json
sys.path.insert(0, 'scripts/lib/')
import Levenshtein
import language_functions as text_p
import googlemaps
'''
algorithm:
    1. city: Parse nouns and do look up in list of cities. Do fuzzy match: closest in terms of spelling.
    2. is_location: look for phrases that indicate it is talking about specific place in the city. e.g. near to, on the shore of, etc.
    3. If is_location is true, then find which specific location it is talking about e.g. nusa dua beach, taj mahal, connought place.
    4. find the lat lng of the address (using google maps).
    5. do location search for this lat lng.
    6. if is_location is false, then find attribute of the sentence e.g. spa etc. 
    7. do attribute search.
'''

city_hotel_id_file = 'data/city_hotel_id.json'
attribute_file = 'data/tree-data/percolate_8.json'
delim_address = ', '
gmaps = googlemaps.Client(key='AIzaSyAXQ2pGkeUBhRZG4QNqy2t1AbzA6O3ToUU') 

default_city = 'Bali'
location_phrases = ['next', 'near', 'far', 'close', 'distance', 'walking', 'drive', 'on']

city_country_map = {
    'bali': 'indonesia',
    'marrakech': 'morocco'
}

def find_city(noun_arr, city_list):
    max_ratio = -1
    max_city = None
    for noun in noun_arr:
        for city in city_list:
            ratio = Levenshtein.ratio(city, noun) 
            if ratio > max_ratio:
                max_ratio = ratio
                max_city = city
    if max_ratio > 0.5:
        return max_city
    return None

def is_location(tokens):
    for tok in tokens:
        if tok in location_phrases:
            return True
    return False

def find_lat_lng(noun_phrases, city_name, country, result_lat_long):
    for np in noun_phrases:
        street_address = np + delim_address + city_name + delim_address + country
        geocode_result = gmaps.geocode(street_address)
        if geocode_result == None or len(geocode_result) == 0:
            print 'geo code not found for street address: ' + str(street_address)
        else:
            location = {}
            location['lat'] = geocode_result[0]['geometry']['location']['lat']
            location['lon'] = geocode_result[0]['geometry']['location']['lng']


if __name__ == "__main__":
    city_hotel_id_map = json.loads(open(city_hotel_id_file, 'r').read())
    city_list = []
    for key in city_hotel_id_map:
        city_list.append(key)
    attribute_seed = json.loads(open(attribute_file, 'r').read())
    user_input = raw_input("Some input please: ")
    while user_input != 'stop':
        result = text_p.find_attribute_2(attribute_seed, user_input)
        noun_arr = result['nouns']
        # step 1
        city_name = find_city(noun_arr, city_list)
        if city_name == None:
            print 'defaulting to: ' + default_city
            city_name = default_city
        tokens = result['tokens']
        is_location = is_location(tokens)
        if is_location:
            noun_phrases = result['NP']
            result_lat_long = []
            # check to see google maps if there is lat lng for any of the noun phrases.
            find_lat_lng(noun_phrases, city_name, city_country_map[city_name], result_lat_long)
            if result_lat_long == []:
                result_loc = text_p.find_attribute_2(attribute_seed['root']['next']['location'], user_input)
                attr_loc = result_loc['path']
                print 'attr_location: ' + str(attr_loc)
            else:
                print 'location_search: ' + str(lat_lng)
        else:
            attr_path = result['path']
            print 'attr_general: ' + str(attr_path)