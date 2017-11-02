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

# This object stores all the info and methods require to understand
# stage_dependency_tree
class StageDependencyTree:
    def __init__(self,d):
        self.dep_tree = d
        self.stage_names = self.__compute_stage_names__()
        self.root,self.stage_dep_path = self.__compute_derived_params__()
        self.stage_lvl = {k:len(p)-1 for k,p in self.stage_dep_path.items()}

        # sort stage names by their lvl
        lvls = [self.stage_lvl[s] for s in self.stage_names]
        idx = np.argsort(lvls)
        self.stage_names = [self.stage_names[i] for i in idx]

    def get_stage_dependency(self,stage_name):
        assert stage_name in self.stage_names
        if stage_name in self.dep_tree:
            return self.dep_tree[stage_name]
        else:
            return None

    def __compute_stage_names__(self):
        unique_names = set(self.dep_tree.keys()) | set(self.dep_tree.values())
        return list(unique_names)

    def __compute_derived_params__(self):
        root = None
        stage_dependency_path = {}
        for s in self.stage_names:
            p = self.__get_root_path__(s)
            stage_dependency_path[s] = p
            if root is None:
                root = p[-1]
            elif root==p[-1]:
                continue
            else:
                logging.error('The dependency tree has more than one root')
                exit(-1)
        assert root is not None
        return (root,stage_dependency_path)

    # I assume each stage only depends on another single one
    def __get_root_path__(self,stage_name):
        leaf = stage_name
        path = []
        while leaf in self.dep_tree.keys():
            path.append(leaf)
            leaf = self.dep_tree[leaf]
            assert isinstance(leaf,str) # asserts single root
            if leaf in path:
                logging.error('Dependency tree is not a DAG')
                exit(-1)
        path.append(leaf)
        return path

# make some tests
if __name__=='__main__':
    dep_tree = {'Tx':'waveform','RF':'Tx','TxImg':'Tx'}
    sdt = StageDependencyTree(dep_tree)
    assert sdt.get_stage_dependency('RF')=='Tx'
    assert sdt.get_stage_dependency('Tx')=='waveform'
    assert sdt.get_stage_dependency('waveform')==None
    assert sdt.get_stage_dependency('TxImg')=='Tx'
    assert sdt.stage_lvl['RF']==2
    assert sdt.stage_lvl['Tx']==1
    assert sdt.stage_lvl['waveform']==0
    assert sdt.stage_lvl['TxImg']==2
    assert sdt.root == 'waveform'
    assert sdt.stage_dep_path['RF']==['Tx','waveform']
    print 'Successfully finished the tests'
