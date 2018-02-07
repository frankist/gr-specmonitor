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
import numpy as np
from scipy import signal
from scipy import misc
from PIL import Image
import cv2
from pylab import cm
import matplotlib.pyplot as plt

from ..sig_format import pkl_sig_format as psf
from ..labeling_tools import bounding_box
from ..sig_format import sig_data_access as fdh
from ..sig_format import stage_signal_data as ssa
from ..core.LuigiSimulatorHandler import StageLuigiTask
from ..utils import logging_utils
logger = logging_utils.DynamicLogger(__name__)

def get_pixel_coordinates(imgbox):
    ud_l = [(e,imgbox.colmin) for e in range(imgbox.rowmin,imgbox.rowmax)]
    ud_r = [(e,imgbox.colmax-1) for e in range(imgbox.rowmin,imgbox.rowmax)]
    lr_u = [(imgbox.rowmin,e) for e in range(imgbox.colmin,imgbox.colmax)]
    lr_d = [(imgbox.rowmax-1,e) for e in range(imgbox.colmin,imgbox.colmax)]
    pixels = set(ud_l) | set(ud_r) | set(lr_u) | set(lr_d)

    # need to transpose
    pixels = [(p[1],p[0]) for p in pixels]
    return pixels

def paint_box(im,bbox):
    if bbox.rowmin < 0:
        return False # bounding box was too close to the border. Not gonna draw it
    thick = int(min(im.shape[0],im.shape[1]) // 150)
    color = (255,130,255,255)#colors[max_indx]
    cv2.rectangle(im,(bbox.colmin,bbox.rowmin),
                  (bbox.colmax,bbox.rowmax),
                  color, thick)
    # pixel_list = get_pixel_coordinates(bbox)
    # paint_box_pixels(im,pixel_list)
    return True

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


def generate_spectrogram_imgs(this_run_params, insync, mark_boxes):
    multi_stage_data = ssa.MultiStageSignalData.load_pkl(this_run_params)
    x = multi_stage_data.read_stage_samples()
    targetfile = this_run_params['targetfilename']
    sourcefile = this_run_params['sourcefilename']
    # freader = psf.WaveformPklReader(sourcefile)
    spec_metadata = multi_stage_data.get_stage_derived_params('spectrogram_img')
    num_sections = len(spec_metadata)
    is_framed = True if 'frame_params' in multi_stage_data.session_data else False
    # sig_data = multi_stage_data.get_stage_data()
    # is_framed = sig_data.is_framed()
    # sig_data = freader.data()
    # x = freader.read_section()
    # is_framed = fdh.is_framed(sig_data)
    if insync is False or is_framed is False:
        logger.error('I have to implement this functionality')
        print sig_data
        raise NotImplementedError('data has to be framed and in sync to be stored as an img with bounding boxes')

    # spec_metadata = fdh.get_stage_derived_parameter(sig_data,'section_spectrogram_img_metadata')
    # num_sections = len(spec_metadata)
    assert num_sections==1 # TODO: Implement this for several subsections
    # section_size = fdh.get_stage_derived_parameter(sig_data,'section_size')
    section_size = multi_stage_data.session_data['frame_params']['section_size']

    for i in range(num_sections):
        # get the image bounding boxes
        imgboxes = spec_metadata[i].generate_img_bounding_boxes() if mark_boxes==True else []
        Sxx = spec_metadata[i].image_data(x)#,nan_val=np.nan)

        # desired dims
        orig_dims = Sxx.shape
        img_width = 300
        final_dims = (img_width,img_width*2)#(min(Sxx.shape)*4,min(Sxx.shape)*4)

        # convert image data to img format
        # im = Image.fromarray(np.uint8(cm.gist_earth(Sxx)*255))
        # im_no_boxes = im.copy()
        imnp = np.uint8(cm.gist_earth(Sxx)*255)
        im_no_boxes = Image.fromarray(cv2.resize(imnp,final_dims)).copy()
        imnp = cv2.resize(imnp,final_dims)

        # paint the bounding boxes in the image
        for b in imgboxes:
            bnew = b.resized_box((final_dims[1],final_dims[0]))
            paint_box(imnp,bnew)

        # put images side by side
        im = Image.fromarray(cv2.resize(imnp,final_dims))
        im = concatenate_images([im_no_boxes,im])#[im_no_boxes,im])
        im.save(targetfile,'PNG')

class ImgSpectrogramBoundingBoxTask(StageLuigiTask):
    def __init__(self,*args,**kwargs):
        kwargs['output_fmt'] = '.png'
        # new_args = args + ('.png',)
        super(ImgSpectrogramBoundingBoxTask,self).__init__(*args,**kwargs)

    def run(self):
        this_run_params = self.get_run_parameters()
        is_signal_insync = True
        mark_box = True
        generate_spectrogram_imgs(this_run_params,is_signal_insync, mark_box)
