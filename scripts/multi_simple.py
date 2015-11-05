from multiprocessing import Pool

def f(x):
    print 'arg: ' + str(x)
    
if __name__ == "__main__":
    p = Pool(2)
    p.map(f, ['hello', 'I love', 'you'])