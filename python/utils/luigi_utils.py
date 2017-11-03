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

import os
import time
import collections
from basic_utils import *

def mtime(path):
    return time.ctime(os.path.getmtime(path))

def time_cmp(f1,f2): # If f1 is newer, returns positive
    return os.path.getmtime(f1)-os.path.getmtime(f2)

def check_complete_with_date(luigitask):
    # assuming 1 output
    outputfile = luigitask.output().path
    assert len(force_iterable_not_str(outputfile))==1

    # if output does not exist return false
    if not os.path.exists(outputfile):
        return False
    self_mtime = mtime(outputfile)

    for el in force_iterable_not_str(luigitask.requires()):
        # if one of the dependencies does not exist
        if not el.complete():
            return False
        # if one of the dependencies is newer
        for out in force_iterable_not_str(el.output()):
            if time_cmp(out.path,outputfile)>0:
                return False 
    return True
