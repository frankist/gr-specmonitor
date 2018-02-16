#!/usr/bin/env python

import os
import numpy as np

def read_32fc_file(fname,sample_offset=0,num_samples=-1):
    with open(fname, "rb") as f:
        byte_idx = sample_offset*8
        f.seek(byte_idx, os.SEEK_SET)
        samples = np.fromfile(f, dtype=np.complex64, count=num_samples)
    return samples

def save_32fc_file(fname,array):
    a = np.array(array,np.complex64)
    with open(fname,'wb') as f:
        array.tofile(f)

if __name__=='__main__':
    fname = 'format_test_tmp.32fc'
    a = np.array(np.arange(10),np.complex64)
    save_32fc_file(fname,a)
    b = read_32fc_file(fname)
    assert np.array_equal(a,b)

    # print 'This is the binary data:'
    with open(fname,'r') as f:
        s = f.read()
        assert len(s)==len(a)*8
        # print s

    os.remove(fname)
