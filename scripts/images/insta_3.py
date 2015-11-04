import os
import sys
import json
import time
import clarifai
import socket

from clarifai.client import ClarifaiApi
import image_attribute_map as i_map

'''
read the insta images and query 1000 images and then sleep for 1 hour.
1. for any hotel, max images = 100
2. ignore hotel if images < 10
3. when 10000 images are done or all hotels are finished, exit.
'''

max_count = 5000

crawled_so_far = ["Mike's Place", "Ramada Caravela Beach Resort", "Martin's Comfort", "The Zuri White Sands Goa Resort & Casino", "Taj Exotica Goa", "10 Calangute", "Majestic Inn", "Bogmallo Beach Resort", "Lotus Beach Resort", "Mykonos Bl", "Riva Beach Resort", "Resort Lagoa Azul", "Old Goa Residency", "The Banyan Soul", "Little Palm Grove", "Sur La Mer", "Renzo's Inn", "Marigold", "Sea Mist Resort", "Branco Guest House", "Maharaja Hotels", "Hotel Nova Goa", "The Tubki Resort", "Angelina Beach Resort", "The Acacia Hotel & Spa Goa", "The Fern Gardenia Resort, Canacona", "WelcomHeritage Panjim Inn", "Hill Top Hotel", "Santo Antonio Hotel", "Vivanta by Taj - Holiday Village, Goa", "Hotel Supreme", "Prainha", "Spazio Leisure Resort", "Panaji Residency", "La Calypso Goa", "Casa Paradiso", "Mobor Beach Resort", "Majorda Beach Resort", "Sunset Beach Hotel", "La Sunila Clarks Inn Suites", "Sun Kissed Resort", "Keys Resort Ronil", "Hotel Blessings", "Rio Residency", "The HQ", "Lucky Star Hotel", "La Vaiencia Beach Resort", "Alor Holiday Resort", "Hotel Calangute Towers", "Seabreeze Resort", "Royal Benaulim", "Cleopatra Resort", "Casa De Goa Boutique Resort", "Hotel Germany", "Alagoa Resort", "Dreamcatcher Resort", "Horizon", "Mandrem Beach Resort", "Vivanta by Taj - Fort Aguada, Goa", "Chances Resort and Casino", "Royal Resort", "El Paso Hotel", "The Sea Horse Resort", "Neelams The Grand", "Hotel Bonanza", "Sol de Goa", "Abalone Resort", "Citrus Goa", "Meraden La Oasis", "Afonso Guest House", "La Grace Resort", "Dunhill Beach Resort", "Coconut Grove", "Sea Breeze Beach Hotel", "Jasminn by Mango Hotels", "Leoney Resort", "Stonewater Eco Resort", "Alcon Holiday Village", "Lui Beach Resort", "North 16 Goa", "Angels Resort", "Nazri Resort Hotel", "Silver Sands Beach Resort"]

def crawl(api, image_arr):
    func = lambda x: x['images']['standard_resolution']['url']
    filtered_arr = map(func, image_arr)
    print 'size of request: ' + str(len(filtered_arr))
    try:
        resp = api.tag_image_urls(filtered_arr)
        return resp
    except clarifai.client.client.ApiError:
        print 'error while querying: ' + str(filtered_arr)
        return None
    except clarifai.client.client.ApiThrottledError:
        print 'throttle error while trying: ' + str(filtered_arr)
        return None
    except socket.error,v:
        print 'socket error: ' + str(v)
        return None
    except urllib2.URLError:
        print 'url lib error for: ' + str(filtered_arr)
        return None

if __name__ == "__main__":
    hotel_data = json.loads(open(sys.argv[1], 'r').read())
    hourly_count = 0
    total_count = 0
    final_result = {}
    api = ClarifaiApi()
    hotels_covered = len(crawled_so_far)
    for hotel_id in hotel_data:
        hotel_meta = hotel_data[hotel_id]
        hotel_name = hotel_meta['name'].encode('utf-8')
        if hotel_name in crawled_so_far:
            continue
        print 'crawling hotel name: ' + hotel_name
        hotels_covered += 1
        image_arr = hotel_meta['results']
        if image_arr == None:
            print 'error 00: images are none: ' + hotel_name
            continue
        if len(image_arr) < 10:
            print 'less images so not crawling.'
            continue
        capped_images_arr = image_arr[:(100)]
        image_len = len(capped_images_arr)
        #print 'image array: ' + str(image_len)
        hourly_count += image_len
        total_count += image_len
        
        if total_count > max_count:
            break
        
        print 'hourly_count: ' + str(hourly_count)
        
        if hourly_count > 950:
            # sleep for 60 mins. and set hourly count to 0
            print 'sleeping...'
            time.sleep(3600)
            print 'waking...'
            hourly_count = image_len
        
        result = crawl(api, capped_images_arr)
        time.sleep(10)
        if result == None:
            print 'Api error for hotel: ' + hotel_name
            break
        else:
            final_result[hotel_name] = result
    
    print 'hotels covered: ' + str(hotels_covered)
    f = open(sys.argv[2], 'w')
    f.write(json.dumps(final_result))
    f.close()