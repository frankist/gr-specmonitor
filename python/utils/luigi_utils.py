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

def check_complete_with_date(luigitask):
    # assuming 1 output
    assert isinstance(luigitask.output().path,str)

    # if output does not exist return false
    if not os.path.exists(luigitask.output().path):
        return False
    self_mtime = mtime(luigitask.output().path)

    for el in force_iterable_not_str(luigitask.requires()):
        # if one of the dependencies does not exist
        if not el.complete():
            return False
        # if one of the dependencies is newer
        for out in force_iterable_not_str(el.output()):
            if mtime(out.path) > self_mtime:
                return False 
    return True
