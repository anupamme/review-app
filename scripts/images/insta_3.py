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

crawled_so_far = 77

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
    count = 0
    for hotel_id in hotel_data:
        hotel_meta = hotel_data[hotel_id]
        if count < crawled_so_far:
            count += 1
            continue
        hotel_name = hotel_meta['name'].encode('utf-8')
        print 'crawling hotel name: ' + hotel_name
        image_arr = hotel_meta['results']
        if image_arr == None:
            print 'error 00: images are none: ' + hotel_name
            count += 1
            continue
        if len(image_arr) < 10:
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
    
    f = open(sys.argv[2], 'w')
    f.write(json.dumps(final_result))
    f.close()