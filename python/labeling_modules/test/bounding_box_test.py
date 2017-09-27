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

import sys
sys.path.append('../')
from bounding_box import *

def test1():
    print 'Test checks if the time intervals where there are transmissions are correctly computed'

    x1 = [0,0,1,1,0,0]
    x2 = [1,1,0,0,1,1]
    x3 = [0,0,0,0,0,0]
    x4 = [1,1,1,1,1,1]
    assert find_tx_intervals(x1)==[(2,4)]
    assert find_tx_intervals(x2)==[(0,2),(4,6)]
    assert find_tx_intervals(x3)==[]
    assert find_tx_intervals(x4)==[(0,6)]

# def test2():
#     N=1000
#     K=300
#     x=np.zeros(N)
#     x[0:K] = np.ones(K)
#     l = find_interv_freq_bounds(x)
#     l2 = find_interv_freq_bounds(x,find_tx_intervals(x))
#     print l,l2

def test3():
    b1 = BoundingBox((1,10),(-0.4,0.4))
    b2 = BoundingBox((2,3),(-0.1,0.01))
    b3 = BoundingBox((4,11),(0.2,0.45))
    b4 = BoundingBox((11,12),(-0.1,0.1))
    b5 = BoundingBox((2,5),(0.41,0.42))

    assert BoundingBox((2,3),(-0.1,0.01)).is_equal(b1.box_intersection(b2))
    assert BoundingBox((4,10),(0.2,0.4)).is_equal(b1.box_intersection(b3))
    assert b1.box_intersection(b4) is None
    assert b1.box_intersection(b5) is None

if __name__ == '__main__':
    test1()
    # test2()
    test3()

    print 'bounding_boxes_test.py: All tests have finished successfully'
    pass
