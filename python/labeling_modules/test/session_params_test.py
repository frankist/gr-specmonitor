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
sys.path.append('../../utils/')
from session_params import *
import numpy as np
import typesystem_utils as ts

def test1():
    tag = 'label1'
    values = range(10)
    p = LabeledParamValues(tag,values)

    it = p.get_iterable()
    l = list(values)
    for ii,v in enumerate(it):
        assert tag==v[0] and l[ii]==v[1]

def test2():
    l = [
        ('var1',range(20)),
        ('var2',['value1','value2'])
    ]
    p = StageParams(l)
    assert p.length() == len(range(20))*2
    it = p.get_iterable()
    l = list(it)
    assert l[0][0][1]==0 and l[0][1][1]=='value1'
    # print list(it)

def test3():
    stages = ['stage1','stage2']
    l = {
        'stage1': [
            ('var1',range(10)),
            ('var2',['value1','value2'])
        ],
        'stage2': [
            ('var3',range(3)),
            ('var4',np.linspace(0,1,4))
        ]
    }
    p = MultiStageParams(stages,l)
    assert p.length('stage1') == np.cumprod([len(t[1]) for t in l['stage1']])[-1]
    assert p.length('stage2') == np.cumprod([len(t[1]) for t in l['stage2']])[-1]
    assert p.length() == p.length('stage1')*p.length('stage2')
    assert p.length('stage1')==p.length(0) and p.length('stage2')==p.length(1)
    # print list(p.get_iterable('stage2'))

def test4():
    tags = ['sig','wifi']
    stages = ['waveform','Tx']
    l = { 'sig':
          {
              'waveform':
              [
                  ('source',['square','triangle']),
                  ('freq',np.linspace(0,10,5))
              ],
              'Tx':
              [
                  ('frequency_offset',np.linspace(-0.5,0.5,5))
              ]
          },
          'wifi':
          {
              'waveform':
              [
                 ('source','wlan'),
                 ('rate',np.linspace(0,1,6))
              ],
              'Tx':
              [
                 ('frequency_offset',np.linspace(-0.5,0.5,6))
              ]
         }
    }
    p = TaggedMultiStageParams(tags,stages,l)
    # print [[len(ts.convert2list(t[1])) for t in u['waveform']] for u in l.values()]
    assert p.length(stage='waveform') == sum([np.cumprod([len(ts.convert2list(t[1])) for t in u['waveform']])[-1] for u in l.values()])
    assert len(list(p.get_iterable(stage='waveform'))) == p.length(stage='waveform')
    assert len(list(p.get_iterable(stage='Tx'))) == p.length(stage='Tx')
    assert p.length(tag='wifi',stage='Tx')==6
    assert p.length(tag='sig')==(p.length('sig','waveform')*p.length('sig','Tx'))
    # assert p.length(stage='waveform')*p.length(stage='Tx')==p.length()

if __name__ == '__main__':
    test1()
    test2()
    test3()
    test4()
