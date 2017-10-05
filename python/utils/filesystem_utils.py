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

def check_dependency_met(dep_filename,this_filename=None):
    if os.path.isfile(dep_filename): # if dep file already exists
        if this_filename is not None and os.path.isfile(this_filename):
            dep_date = time.ctime(os.path.getmtime(dep_filename))
            this_date = time.ctime(os.path.getmtime(this_filename))
            if dep_date<this_date: # If dep file is older than this file
                return True
            else:
                return False
        else:
            return True
    return False

