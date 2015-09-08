from multiprocessing import Pool
import urllib2

def fetch(url):
    return {'name': url, 'data': urllib2.urlopen(url).read()}

if __name__ == '__main__':
    p = Pool(5)
#    arr = []
#    count = 0
#    while count < 20:
#        arr.append(count + 1)
#        count += 1
    print(p.map(fetch, ['http://google.com', 'http://apple.com', 'http://facebook.com']))