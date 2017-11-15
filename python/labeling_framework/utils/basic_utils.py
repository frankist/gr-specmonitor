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
import collections

def is_sorted(l,ascending=True):
    if ascending:
        return all(b >= a for a, b in zip(l, l[1:]))
    return all(b <= a for a, b in zip(l, l[1:]))

def first_where(l,expr,ifnotfound=None,offset=0):
    if isinstance(l,np.ndarray):
        v = np.where(expr(l))[0]
    else:
        #v = [i for i in range(len(l)) if expr(l[i])==True]
        v = np.where([expr(i) for i in l])[0]
    return v[0]+offset if len(v)>0 else ifnotfound

def first_where_sorted(l,val,ifnotfound=None):
    i = np.searchsorted(l,val)
    if l[i]!=val:
        return ifnotfound
    return i

def force_iterable(v):
    return v if isinstance(v,collections.Iterable) else [v]

def force_iterable_not_str(v):
    test = isinstance(v,collections.Iterable) and not isinstance(v,basestring)
    return v if test else [v]
    # NOTE: in Python2 check if it is string by comparing with basetring

if __name__ == '__main__':
    pass
