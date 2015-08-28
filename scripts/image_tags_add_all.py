'''
input: hotel_name -> attribute -> [image_url]
output: [{
    "id": count,
    "hotel_id": hotel_id,
    "attributes": [
        "value": "amenity",
        "value": "gym"
    ],
    "url": "my_url"
}]
'''

import sys
import json

if __name__ == "__main__":

    