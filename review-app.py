import cgi
import webapp2
import nltk
import gensim
from gensim.models import word2vec

class Model():
    
    attributeCloud = {}
    subAttributeCloud = {}
    model = None
    
    def buildWordCloud(self):
        a = 1
    
    def findMostProbableAttributes(self, text):
        a = 1
    
    def init(self):
        # inits the model.
        a = 1
        print("initing...")
        # read model
        modelFile = "vectors-phrase.bin"
        self.model = word2vec.Word2Vec.load_word2vec_format(modelFile, binary=True)
        # build word cloud.
        attributeCloud, subAttributeCloud = self.buildWordCloud()
        
        
    def findAttribute(self, text):
        # extracts attributes from the text.
        a = 1
        print("finding attributes...")
        sortedAttributesOnProbability = self.findMostProbableAttributes(text)

mod = Model()

class Demo(webapp2.RequestHandler):

    def get(self):
        form = cgi.FieldStorage()
        disp = form["textVal"].value
        print('disp: ' + disp)
        nltk.tokenize.api.TokenizerI.tokenize()
        html = open('demo.html', 'r').read()
        self.response.headers['Content-Type'] = 'text/html'
        attr = mod.findAttribute('Food was tasty!')
    	self.response.write(html)
        
class MainPage(webapp2.RequestHandler):

    def get(self):
        mod.init()
        html = open('index.html', 'r').read()
        self.response.headers['Content-Type'] = 'text/html'
    	self.response.write(html)
        

application = webapp2.WSGIApplication([
    ('/', MainPage), ('/demo', Demo)], debug=True)


