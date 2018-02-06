#!/usr/bin/env python

from specmonitor import DynRandom
import numpy as np

class RandomGenerator(object):
    def __init__(self,dist_name,params):
        self.dist_name = dist_name
        self.params = params
        self.__gen__ = DynRandom(dist_name,params)

    def generate(self):
        return self.__gen__.generate()

    # These member is to make this object Pickable
    def __getstate__(self):
        d = self.__dict__
        del d['__gen__']
        return d

    def __setstate__(self,state):
        self.__init__(state['dist_name'],state['params'])

if __name__=='__main__':
    import pickle
    a=RandomGenerator('randint',[1,5])
    print 'result A:',a.generate()

    s = pickle.dumps(a)
    b = pickle.loads(s)

    print 'result B:',b.generate()
