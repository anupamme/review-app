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

crawled_so_far = ['The Mansion Resort Hotel & Spa', 'Love F Hotel', 'The Bale', 'B Hotel Bali', 'Nandini Bali Resort & Spa Ubud', 'Nusa Dua Retreat and Spa', 'Ulu Segara Luxury Suites & Villas', 'Alila Villas Soori', 'Tarci Bungalow', 'Swiss-Belinn Legian', 'Patra Jasa Bali Resort & Villas', 'Anantara Bali Uluwatu Resort & Spa Bali', 'Puri Santrian', 'Saren Indah Hotel', 'Surya Shanti Villa', 'Bintang Kuta Hotel', 'Ibis Styles Bali Benoa', 'The Puri Nusa Dua', 'Spa Village Resort Tembok Bali', 'Park Regis Kuta Bali', 'The Trans Resort Bali', 'Grand Inna Kuta', 'The Purist Villas and Spa', 'Bambu Indah', 'Bali Mandira Beach Resort & Spa', 'The Haven Seminyak Hotel & Suites', 'Bunga Permai Hotel', '100 Sunset 2 Hotel', 'Bali Niksoma Boutique Beach Resort', 'The Breezes Bali Resort & Spa', 'Amaroossa Suite Bali', 'Artemis Villa and Hotel', 'Rama Candidasa Resort & Spa', 'Ramada Resort Camakila Bali', 'Kupu Kupu Barong Villas and Tree Spa', 'FuramaXclusive Ocean Beach', 'Padma Resort Legian', 'Mulia Villas', 'The Samaya Bali', 'Four Seasons Resort Bali at Jimbaran Bay', 'Courtyard by Marriott Bali Seminyak', 'Club Med Bali', 'Mulia Resort', 'HARRIS Hotel & Residences Riverview Kuta', 'Hotel Tugu Bali', 'Citadines Kuta Beach Bali', 'The Dipan Resort Petitenget', 'Puri Gangga Resort', 'Fontana Hotel Bali', 'Villa Sarna Ubud', 'Wapa di Ume Resort and Spa', 'Sun Island Hotel Kuta', 'Grand Istana Rama Hotel Bali', 'Sun Island Villas & Spa', 'Fairmont Sanur Beach Bali', 'All Seasons Legian Bali', 'Sheraton Bali Kuta Resort', 'Grand Mirage Resort', 'Villa Kub', 'Komaneka at Bisma', 'Tulamben Wreck Divers Resort', 'Novotel Bali Benoa', 'BEST WESTERN Kuta Villa', 'Sofitel Bali Nusa Dua Beach Resort', 'The Akmani Legian', 'Swiss-Belresort Watu Jimbar', 'H Sovereign Bali', 'The St. Regis Bali Resort', 'Liberty Dive Resort', 'The Gangsa Private Villa by Kayumanis', 'Lembongan Beach Club and Resort', 'Royal Candidasa: Royal Bali Beach Club', 'Hotel Vila Lumbung', 'The Segara Suites', 'Bali Shangrila Beach Club', 'Mega Boutique Hotel', 'Alila Manggis', 'Legian Paradiso Hotel', 'The Layar - Designer Villas and Spa', 'The Grand Bali Nusa Dua', 'Four Seasons Resort Bali at Sayan', 'The Radiant Hotel and Spa', 'Chapung SeBali Resort and Spa', 'Holiday Inn Express Bali Raya Kuta', 'H\'u Villas Bali', 'Kamandalu Ubud', 'Jamahal Private Resort & SPA', 'Fivelements Puri Ahimsa', 'PING Hotel Seminyak Bali', 'The Kana Kuta', 'Mercure Resort Sanur', 'Komaneka at Monkey Forest', 'Hotel Terrace At Kuta', 'Villa Kub', 'The Seminyak Suite Private Villa', 'Aston Kuta Hotel & Residence', 'Centra Taum Seminyak Bali', 'The Menjangan', 'Kayumanis Jimbaran Private Estate & Spa', u"H'u Villas Bali", 'Mercure Bali Legian', 'Agung Raka Resort & Villas', 'Ananta Legian Hotel', 'Holiday Inn Express Bali Kuta Square', 'Ramayana Resort & Spa', 'Alila Villas Uluwat', 'The Seminyak Beach Resort & Spa', 'Furama Villas & Spa Ubud', 'Aria Villas Ubud', 'The Kayon Resort', 'Ayung Resort Ubud', 'Villa Kub', 'Alila Villas Uluwat', 'Atanaya Hotel', 'The Club Villas', 'Hotel Tjampuhan & Spa', 'Ubud Bungalow', u"H'u Villas Bali", 'Biyukukung Suites and Spa', 'Kuta Puri Bungalows', 'Grand Hyatt Bali', 'The Stones Hotel - Legian Bali, Autograph Collection', 'Bulgari Resort Bali', 'Uma by COMO, Ubud', 'Royal Jimbaran: Royal Bali Beach Club', 'Santi Mandala', 'Abi Bali Resort & Villa', 'Bebek Tepi Sawah Villas & Spa', 'Puri Wirata Dive Resort and Spa Amed', 'Bali Ginger Suites', 'Pan Pacific Nirwana Bali Resort', 'Alila Villas Uluwat', 'Bounty Hotel', 'Nirwana Resort and Spa', 'Amandari', 'Risata Bali Resort & Spa', 'Villa Kub', 'The Ahimsa Estate', 'L Hotel Seminyak', 'Grandmas Seminyak Hotel', 'Mercure Bali Nusa Dua', 'Hotel Santika Siligita Nusa Dua', 'Hotel NEO + Kuta Legian', 'Puri Saron Seminyak', 'Puri Dajuma Cottages', 'Batu Karang Lembongan Resort & Day Spa', 'Le Grande Bali', 'Hard Rock Hotel Bali', 'Taman Harum Cottages', 'Swiss-Belhotel Segara Resort & Spa', u"H'u Villas Bali", 'Champlung Sari Hotel', 'HARRIS Hotel Bukit Jimbaran', 'Alindra Villa', 'Villa Kub', 'Griya Santrian', 'Alila Villas Uluwat', 'Kayumanis Ubud Private Villa & Spa', 'Peppers Seminyak', 'Puri Wulandari Boutique Resort', 'Matahari Tulamben Resort, Dive & SPA', u"H'u Villas Bali", 'The Sungu Resort & Spa', 'The Legian Bali \u2013 a GHM hotel', 'Svarga Loka Resort', 'Ramada Bintang Bali Resort', 'Amankila', 'Harris Hotel Seminyak', 'The Royal Eighteen Resort and Spa', 'The Elysian', 'The Magani Hotel and Spa', 'Alila Villas Uluwat', 'Junjungan Ubud Hotel and Spa', 'Vasanti Seminyak Resort', 'Conrad Bali', 'The Ritz-Carlton, Bali', 'Banyan Tree Ungasan, Bali', 'Puri Sebali Resort', 'Natura Resort and Spa', 'Villa Kub', 'Bliss Surfer Hotel', 'Mara River Safari Lodge', 'Le Jardin Villas', 'Alila Ubud', 'The Alea Hotel Seminyak', 'The Mulia', 'The Tusita Hotel', 'I-Villa', 'The Lovina', 'Ize Seminyak', 'The Payogan Villa Resort & Spa', 'Pradha Villas', 'The Bene Hotel', 'Villa Kayu Raja', 'Aqua Villa', 'Viceroy Bali', 'Pita Maha Resort and Spa', 'The Legian Bali \u2013 a GHM hotel', 'RIMBA Jimbaran Bali by AYANA', 'Ion Bali Benoa Hotel', 'Hotel Horison Seminyak', 'Keraton Jimbaran Resort & Spa', u"H'u Villas Bali", 'Legian Beach Hotel', 'The Ulin Villas & Spa', 'Pullman Bali Legian Nirwana', 'BEST WESTERN PREMIER Sunset Road Kuta', 'Sense Hotel Seminyak']

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