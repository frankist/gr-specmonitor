#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017 Francisco Paisana.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

import numpy as np

# CAUTION: This is a reference. If your array changes its position through np.append(.), you will have
# issues
class offset_array_view(object):
    def __init__(self,array,offset,size=None):
        self.array_ptr = array
        assert offset>=0
        self.offset = offset
        self.size = self.array_ptr.size-self.offset if size is None else size
        if self.size>self.array_ptr.size-self.offset:
            raise IndexError('The size that has been set {} goes \
            beyond the given array limits {}'.format(self.size,self.array_ptr.size))
        self.hist_len = self.offset # FIXME: Legacy

    def __add_idx_offset__(self,idx):
        if isinstance(idx,slice):
            start = idx.start+self.offset if idx.start is not None else self.offset
            stop = idx.stop+self.offset if idx.stop is not None else self.size+self.offset
            if stop>self.size+self.offset:
                raise IndexError('The index {} goes beyond \
                the array limits {}'.format(stop-self.offset,self.size))
            return slice(start,stop,idx.step)
        elif isinstance(idx,int):
            start = idx+self.offset
            if start<0 or start>=self.size+self.offset:
                raise IndexError('The index {} does not fit in the \
                array bounds [{},{}].'.format(start,0,self.size+self.offset))
            return start
        else:
            raise TypeError('The type {} is not supported while indexing array.'.format(type(idx)))

    def __getitem__(self,idx):
        idx_offset = self.__add_idx_offset__(idx)
        return self.array_ptr[idx_offset]

    def __setitem__(self,idx,value):
        idx_offset = self.__add_idx_offset__(idx)
        self.array_ptr[idx_offset] = value

    def __str__(self):
        return '[{} | {}]'.format(', '.join(str(i) for i in self.array_ptr[0:self.offset]),
                                ', '.join(str(i) for i in self.array_ptr[self.offset:self.size]))

def test1():
    a=np.arange(1000)
    offset=100
    a_view = offset_array_view(a,offset)
    a_view2 = offset_array_view(a,offset,300)
    assert a.size==a_view.size+offset
    assert np.array_equal(a[100:1000],a_view[0::])
    assert a_view2.size==300
    assert np.array_equal(a_view2[0::],a_view[0:a_view2.size])

def test_print():
    a=np.arange(15)
    offset=3
    a_view = offset_array_view(a,offset)
    print a_view

if __name__=='__main__':
    test1()
    test_print()
    print 'Finished the tests successfully'
