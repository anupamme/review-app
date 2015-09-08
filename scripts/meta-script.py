import json
import sys

'''
input: london, united kingdom
tripadvisor url: http://

steps:
1. run scrapy crawler for input city.
2. Take the output and extract hotel names and run instagram user searcher and image finder
3. take the output of 1 and run attribute_adjective finder for all the reviews.
4. take the output of 2 and run image identification with clarifai.
5. take the output of 4 and run attribute finder.
6. run elastic search indexer on the output of 3 and 5.
'''
if __name__ == "__main__":
    # step 1: scrapy crawl tripadvisor-hotel -a uri="Hotels-g187147-Paris_Ile_de_France-Hotels.html" -o output/result_paris.json
    uri_for_step_1 = sys.argv[1]
    