#!/usr/bin/env python

from specmonitor import DynRandom
import numpy as np

class random_generator(object):
    table_map = {'uniform':'randint','randint':'randint','constant':'constant'}
    def __init__(self,dist_name,params):
        self.dist_name = random_generator.table_map[dist_name]
        self.params = params

    def generate(self):
        gen = self.dynrandom()
        return gen.generate()

    def dynrandom(self):
        return DynRandom(self.dist_name,self.params)

    # # These member is to make this object Pickable
    # def __getstate__(self):
    #     d = self.__dict__
    #     del d['__gen__']
    #     return d

    # def __setstate__(self,state):
    #     self.__init__(state['dist_name'],state['params'])

    @classmethod
    def load_param(cls,param_value):
        if isinstance(param_value,random_generator):
            return param_value
        elif isinstance(param_value,tuple):
            return cls(param_value[0],param_value[1])
        return cls('constant',[param_value])

    @classmethod
    def load_generator(cls,param_value):
        return cls.load_param(param_value)

    @classmethod
    def load_value(cls,param_value):
        gen = cls.load_generator(param_value)
        return gen.generate()

if __name__=='__main__':
    # simple test
    import cPickle as cpickle
    import pickle
    a=random_generator('randint',[1,5])
    print 'result A:',a.generate()

    s = pickle.dumps(a)
    b = cpickle.loads(s)

    print 'result B:',b.generate()
