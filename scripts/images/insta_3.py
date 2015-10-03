import os
import sys
import json
import time
import clarifai

from clarifai.client import ClarifaiApi
import image_attribute_map as i_map

'''
read the insta images and query 1000 images and then sleep for 1 hour.
1. for any hotel, max images = 100
2. ignore hotel if images < 10
3. when 10000 images are done or all hotels are finished, exit.
'''

crawled_so_far = ['Riad Dar Zahia', 'Les Deux Tours', 'Riad Tzarra', 'Riad Dar Anika', 'RIad Al Loune', 'Riad Infinity Sea', 'La Mamounia Marrakech', 'Riad La Porte Rouge', 'Ryad Dyor', 'Riyad El Cadi', 'Riad Karmela', 'La Maison Arabe', 'Sahara Palace Marrakech', 'Selman Marrakech', 'Riad Houdo', 'Riad Alma', 'Pullman Marrakech Palmeraie Resort and Spa', 'Les Jardins de Touhina', 'Caravanserai', 'Riad 58 Bl', 'Dar Crystal', 'Riad Akka', 'Riad Sapphire and Spa', 'Riad Les Bougainvilliers', 'Hotel & Ryad Art Place Marrakech', 'La Villa des Orangers', 'AnaYela', 'Le Rihani', 'Lodge K', 'Riad el Noujoum', 'Al Fassia Aguedal', 'Beachcomber Royal Palm Marrakech', 'Ksar Char-Bagh', 'Hotel Framissima les Idrissides', 'Riad Camilia', 'Riad Hikaya', 'Palais Namaskar', 'Riad Tamarrakecht', 'Riad 72', 'La Sultana Marrakech', 'Riad Massiba', 'Riad Dar Najat', 'Riad Kheirredine', 'Royal Mansour Marrakech', 'Tigmiza - Suites & Pavillons', 'Riad Dar Massai', 'Zamzam Riad', 'Riad Africa', 'Dar Les Cigognes', 'Riad Tizwa', 'Dar Ayniwen Villa Hotel', u"P'tit Habibi", 'Riad Kniza', 'Riad Anjar', 'Riad Dar Thalge', 'Riad Tahili & Spa', 'Riad Dar Dialkoum', 'Riad Joya', 'Dar Charkia', 'Palais Sebban', 'Riad Ilayka', 'Riad Al Massarah', 'Dar Zemora', 'El Fenn', 'Four Seasons Resort Marrakech', 'Les Jardins de la Medina', 'Riad Nora', 'Eden Andalou Hotel Aquapark & Spa', 'Maison MK', 'Albakech House', 'Riad Mur Akush', 'Riad le Clos des Arts', 'Riad Dar Attajmil', 'Riad Farnatchi', 'Mosaic Palais Aziza & Spa', 'Riad Mirage', 'MonRiad', 'Riad Houdou', 'Riad Miski', 'Riad Al Badia', 'Riad 58 Blu']

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
        
        if total_count > 5000:
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