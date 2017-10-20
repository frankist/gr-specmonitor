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
import pkl_sig_format as psf
from scipy import signal
from scipy import misc
import numpy as np
import matplotlib.pyplot as plt
import bounding_box
import filedata_handling as fdh
from PIL import Image
from pylab import cm

def generate_img(S):
    Srange = (np.min(np.min(S)),np.max(np.max(S)))
    Snorm = (S-Srange[0])/(Srange[1]-Srange[0])
    im = Image.fromarray(np.uint8(cm.gist_earth(Snorm)*255))
    return im

def box_pixels(rowlims,collims,dims):
    assert rowlims[0]>=0 and collims[0]>=0
    assert rowlims[0]<rowlims[1] and collims[0]<collims[1]
    assert rowlims[1]<=dims[0] and collims[1]<=dims[1]
    # print 'dims:',dims,'rowlims:',rowlims,'collims:',collims
    # uplims = (min(rowlims[1]+1,dims[0]),min(collims[1]+1,dims[1]))
    # l1 = [(e,collims[0]) for e in range(rowlims[0],uplims[0])]
    # l2 = [(e,uplims[1]-1) for e in range(rowlims[0],uplims[0])]
    # l3 = [(rowlims[0],e) for e in range(collims[0],uplims[1])]
    # l4 = [(uplims[0]-1,e) for e in range(collims[0],uplims[1])]
    # return set(l1) | set(l2) | set(l3) | set(l4)
    ud_l = [(e,collims[0]) for e in range(rowlims[0],rowlims[1])]
    ud_r = [(e,collims[1]-1) for e in range(rowlims[0],rowlims[1])]
    lr_u = [(rowlims[0],e) for e in range(collims[0],collims[1])]
    lr_d = [(rowlims[1]-1,e) for e in range(collims[0],collims[1])]
    return set(ud_l) | set(ud_r) | set(lr_u) | set(lr_d)

def pixel_transpose(pixel_list):
    return [(p[1],p[0]) for p in pixel_list]

def paint_box_pixels(im,pixel_list):
    def get_val(im,pix):
        shade = 255#np.max(np.max(pix))
        if im.mode == '1':
            value = int(shade >= 127) # Black-and-white (1-bit)
        elif im.mode == 'L':
            value = shade # Grayscale (Luminosity)
        elif im.mode == 'RGB':
            value = (shade, shade, 0)
        elif im.mode == 'RGBA':
            value = (shade, shade, 0, 255)
        elif im.mode == 'P':
            raise NotImplementedError("TODO: Look up nearest color in palette")
        else:
            raise ValueError("Unexpected mode for PNG image: %s" % im.mode)
        return value
    pix = im.load()
    value = get_val(im,pix)
    for p in pixel_list:
        # print 'pixel:',p,',value:',value,'size:',im.size
        assert im.size[0]>p[0] and im.size[1]>p[1]
        im.putpixel(p,value)
        # pix[p[0],p[1]] = value
    # plt.imshow(im)
    # plt.show()
    return im

def save_spectrograms(sourcefname,insync,mark_boxes):
    dirname = os.path.dirname(sourcefname)
    fbase = os.path.splitext(os.path.basename(sourcefname))[0]
    targetfilename_format_no_ext = dirname + '/img/' + fbase + '_{}'
    freader = psf.WaveformPklReader(sourcefname)
    sig_data = freader.data()
    is_framed = fdh.is_framed(sig_data)

    if insync is False or is_framed is False:
        print 'ERROR: I have to implement this functionality'
        print sig_data
        exit(-1)

    section_bounds = fdh.get_stage_derived_parameter(sig_data,'section_bounds')
    box_list = fdh.get_stage_derived_parameter(sig_data,'section_bounding_boxes')
    num_sections = len(section_bounds)
    x = freader.read_section()

    for i in range(num_sections):
        # print 'section:',section_bounds[i]
        section = x[section_bounds[i][0]:section_bounds[i][1]]
        f,t,Sxx = signal.spectrogram(section,1.0,nperseg=64,nfft=64,return_onesided=False)
        Sxx = np.fft.fftshift(np.transpose(Sxx), axes=(1,))
        # plt.plot(np.real(section))
        # plt.show()
        im = generate_img(Sxx)
        pixels = im.load()
        print 'Going to write image',targetfilename_format_no_ext.format(i)
        if mark_boxes is True and len(box_list[i])>0:
            for b in box_list[i]:
                # print 'box:',b
                section_size = section_bounds[i][1]-section_bounds[i][0]
                xmin,xmax,ymin,ymax = bounding_box.get_box_limits_in_image(b,section_size,Sxx.shape)
                pixel_list = pixel_transpose(box_pixels((xmin,xmax),(ymin,ymax),Sxx.shape))
                # pixel_list = box_pixels((ymin,ymax),(xmin,xmax),im.size)
                # print 'square:',xmin,xmax,ymin,ymax,'dims:',im.size
                im = paint_box_pixels(im,pixel_list)
            # plt.show()
        im.save(targetfilename_format_no_ext.format(i),'PNG')
        # misc.imsave(targetfilename_format.format(i),Sxx)
