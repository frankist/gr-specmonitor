import numpy as np
import struct
import os

def binfile_batch_read_32fc(fname):
    with open(fname,'rb') as f:
        x = np.fromfile(f,dtype=np.dtype('complex64'))
    return x
