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
from StageParamData import *
import StageDependencyTree
import numpy as np
import typesystem_utils as ts

# check if labeledparamvalues is efficiently stored and iterable over
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
    stage_dep_tree = {'stage2':'stage1'}
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
    tr = StageDependencyTree.StageDependencyTree(stage_dep_tree)
    p = MultiStageParams(tr,l)
    assert p.length('stage1') == np.cumprod([len(t[1]) for t in l['stage1']])[-1]
    assert p.length('stage2') == np.cumprod([len(t[1]) for t in l['stage2']])[-1]
    assert p.length() == p.length('stage1')*p.length('stage2')
    # print list(p.get_iterable('stage2'))

def generate_multi_stage_multi_tag_data():
    tags = ['sig','wifi']
    stages = ['waveform','Tx','Img'] # Img does not have parameters
    stage_dep_tree = {'Tx':'waveform','Img':'Tx'}
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
                 ('frequency_offset',[0]),#np.linspace(-0.5,0.5,6))
              ]
         }
    }
    return tags,stages,stage_dep_tree,l

def test4():
    """
    This test checks if the session data class computes correctly the number of runs per stage/tag
    """
    tags,stages,stage_dep_tree,l = generate_multi_stage_multi_tag_data()
    t = StageDependencyTree.StageDependencyTree(stage_dep_tree)
    p = TaggedMultiStageParams(tags,t,l)

    assert p.length(stages='waveform') == sum([np.cumprod([len(ts.convert2list(t[1])) for t in u['waveform']])[-1] for u in l.values()])
    assert len(list(p.get_iterable(stages='waveform'))) == p.length(stages='waveform')
    assert len(list(p.get_iterable(stages='Tx'))) == p.length(stages='Tx')
    assert p.length(tags='wifi',stages='Tx')==1
    assert p.length(tags='sig')==(p.length(tags='sig',stages='waveform')*p.length(tags='sig',stages='Tx'))
    assert p.length(tags='wifi')==(p.length(tags='wifi',stages='waveform')*p.length(tags='wifi',stages='Tx'))
    assert p.slice_stage_lengths().shape == (len(p.tag_names),len(p.stage_names()))
    assert p.slice_stage_lengths(tags='wifi').shape == (1,len(p.stage_names()))
    assert p.slice_stage_lengths(stages='waveform').shape == (len(p.tag_names),1)

def test5():
    tags,stages,stage_dep_tree,l = generate_multi_stage_multi_tag_data()
    t = StageDependencyTree.StageDependencyTree(stage_dep_tree)
    p = TaggedMultiStageParams(tags,t,l)

    for ti,t in enumerate(p.tag_names):
        assert np.cumprod(p.__length_matrix__[ti,:])[-1]==p.length(tags=t)
    for si,s in enumerate(p.stage_names()):
        assert np.sum(p.__length_matrix__[:,si])==p.length(stages=s)
    
    wifi_wf_files = p.length(tags='wifi',stages='waveform')
    sig_wf_files = p.length(tags='sig',stages='waveform')
    tag_list_wv_stage = ['sig']*sig_wf_files + ['wifi']*wifi_wf_files
    for i in range(p.length(stages='waveform')):
        wf_idx = i if tag_list_wv_stage[i]=='sig' else i-sig_wf_files
        tuple_idx = (tag_list_wv_stage[i],wf_idx)
        assert tag_list_wv_stage[i]==get_run_parameters(p,tuple_idx,'waveform')['session_tag']
    
    l = list(generate_session_run_idxs(p,final_stage='Tx'))
    assert len(l)==p.length()
    for i in l:
        assert get_run_parameters(p,i,'waveform')==get_run_parameters(p,i[0:-1],'waveform')
        assert i[0]==get_run_parameters(p,i,'waveform')['session_tag']
        assert i[0]==get_run_parameters(p,i,'Tx')['session_tag']
    l2 = list(generate_session_run_idxs(p,final_stage='waveform'))
    assert len(l2)==p.length(stages='waveform')
    for i in l:
        assert get_run_parameters(p,i,'waveform')==get_run_parameters(p,i[0:-1],'waveform')

if __name__ == '__main__':
    test1()
    test2()
    test3()
    test4()
    test5()
    print "Finished all the tests successfully"
