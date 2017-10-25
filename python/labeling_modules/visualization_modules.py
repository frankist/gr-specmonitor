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

class SpectrogramImageUtils:
    @staticmethod
    def generate_img(Sxx):
        Srange = (np.min(Sxx),np.max(Sxx))
        Snorm = (Sxx-Srange[0])/(Srange[1]-Srange[0])
        assert np.max(Snorm)<=1.0 and np.min(Snorm)>=0
        im = Image.fromarray(np.uint8(cm.gist_earth(Snorm)*255))
        return im

    # based on the box limits, computes the pixel coordinates
    @staticmethod
    def box_pixel_coordinates(row_lims,col_lims):
        assert row_lims[0]>=0 and col_lims[0]>=0
        assert row_lims[0]<row_lims[1] and col_lims[0]<col_lims[1]
        ud_l = [(e,col_lims[0]) for e in range(row_lims[0],row_lims[1])]
        ud_r = [(e,col_lims[1]-1) for e in range(row_lims[0],row_lims[1])]
        lr_u = [(row_lims[0],e) for e in range(col_lims[0],col_lims[1])]
        lr_d = [(row_lims[1]-1,e) for e in range(col_lims[0],col_lims[1])]
        return set(ud_l) | set(ud_r) | set(lr_u) | set(lr_d)

    @staticmethod
    def transpose_pixel_coordinates(pixel_list):
        return [(p[1],p[0]) for p in pixel_list]

# convert a spectrogram matrix to a normalized image
def generate_img(S):
    Srange = (np.min(S),np.max(S))
    Snorm = (S-Srange[0])/(Srange[1]-Srange[0])
    assert np.max(Snorm)<=1.0 and np.min(Snorm)>=0
    im = Image.fromarray(np.uint8(cm.gist_earth(Snorm)*255))
    return im

def concatenate_images(img_list):
    div = 4
    widths, heights = zip(*(i.size for i in img_list))
    total_width = sum(widths)
    max_height = max(heights)

    new_im = Image.new('RGBA', (total_width+div*(len(img_list)-1), max_height))

    x_offset = 0
    for im in img_list:
        new_im.paste(im, (x_offset,0))
        x_offset += im.size[0]+div

    return new_im

# returns the pixels of a box
def box_pixels(rowlims,collims,dims):
    assert rowlims[0]>=0 and collims[0]>=0
    assert rowlims[0]<rowlims[1] and collims[0]<collims[1]
    assert rowlims[1]<=dims[0] and collims[1]<=dims[1]
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

def debug_plot_data(section,section_boxes,Sxx,im1):
    print 'boxes:',[b.__str__() for b in section_boxes]
    fig, (ax0, ax1, ax2, ax3) = plt.subplots(nrows=4)
    ax0.plot(np.abs(section))
    im0 = generate_img(Sxx)
    im0 = im0.transpose(Image.ROTATE_90)
    ax1.imshow(im0)
    ax2.imshow(im1.transpose(Image.ROTATE_90))
    section_fft = np.fft.fftshift(np.abs(np.fft.fft(section))**2)
    section_fft = 10*np.log10([max(s,1.0e-7) for s in section_fft])
    ax3.plot(section_fft)
    for b in section_boxes:
        b_range = range(b.time_bounds[0],b.time_bounds[1])
        ax0.plot(b_range,np.abs(section[b_range]),'ro:')
        b_range = range(int(np.round((b.freq_bounds[0]+0.5)*section.size)),int(np.round((b.freq_bounds[1]+0.5)*section.size)))
        ax3.plot(b_range,section_fft[b_range],'ro:')
    plt.show()

def paint_box(im,Spec,box):
    rowmin,rowmax,colmin,colmax = Spec.convert_box_to_coordinates(box)
    if rowmin < 0:
        return False # bounding box was too close to the border. Not gonna draw it
    pixel_list = SpectrogramImageUtils.box_pixel_coordinates((rowmin,rowmax),(colmin,colmax))
    pixel_list = SpectrogramImageUtils.transpose_pixel_coordinates(pixel_list) # to be consistent with the image
    paint_box_pixels(im,pixel_list)
    return True

def save_spectrograms(sourcefname,insync,mark_boxes):
    dirname = os.path.dirname(sourcefname)
    fbase = os.path.splitext(os.path.basename(sourcefname))[0]
    targetfilename_format = dirname + '/img/' + fbase + '_{}.png'
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
        # print 'section:',section.size,section_bounds[i][1]-section_bounds[i][0]
        assert section.size == section_bounds[i][1]-section_bounds[i][0]
        Spec = bounding_box.Spectrogram.make_spectrogram(section)
        im = SpectrogramImageUtils.generate_img(Spec.matrix())
        im_no_boxes = im.copy()

        # print 'Going to write image',targetfilename_format.format(i)
        if mark_boxes is True:
            for box in box_list[i]:
                # print 'box:',box.__str__(),Spec.Sxx.shape
                paint_box(im,Spec,box)
        # debug_plot_data(section,box_list[i],Sxx,im)
        im = concatenate_images([im_no_boxes,im])
        im.save(targetfilename_format.format(i),'PNG')
        # misc.imsave(targetfilename_format.format(i),Sxx)
