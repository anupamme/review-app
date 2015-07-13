import Queue
import threading
import urllib2

# called by each thread
def get_url(q, url):
    q.put(url * url)

theurls = [2, 1, 3, 4]

q = Queue.Queue()

for u in theurls:
    print 'calling for: ' + str(u)
    t = threading.Thread(target=get_url, args = (q,u))
    t.daemon = True
    t.start()

s = q.get()
print s