#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2017
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
import xml.etree.ElementTree as ET
from xml.dom import minidom
from PIL import Image
import cPickle as pickle
import cv2

from ..core import SignalDataFormat as ssa
from ..core.LuigiSimulatorHandler import StageLuigiTask
from ..utils.logging_utils import DynamicLogger
logger = DynamicLogger(__name__)

def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="\t")

def convert_annotations_to_VOC(img_filename,spec_metadata,img_size):
    # document
    root = ET.Element("annotation")

    # folder
    foldername = os.path.basename(os.path.dirname(os.path.dirname(img_filename)))
    ET.SubElement(root, "folder").text = foldername

    # filename
    ET.SubElement(root, "filename").text = os.path.basename(img_filename)

    # source
    xmlsource = ET.SubElement(root, "source")
    ET.SubElement(xmlsource, "database").text = "An RF signal database"
    ET.SubElement(xmlsource, "annotation").text = "PASCAL VOC2017"

    xmlowner = ET.SubElement(root, "owner")
    xmlownername = ET.SubElement(xmlowner, "name").text = "Faceless man"

    xmlsize = ET.SubElement(root, "size")
    ET.SubElement(xmlsize, "width").text = str(img_size[0])#spec_metadata[0].img_size[1])
    ET.SubElement(xmlsize, "height").text = str(img_size[1])#spec_metadata[0].img_size[0])
    ET.SubElement(xmlsize, "depth").text = str(spec_metadata[0].depth)

    ET.SubElement(root, "segmented").text = "0"

    for i in range(len(spec_metadata)):
        # get img bounding boxes
        imgboxes = spec_metadata[i].generate_img_bounding_boxes()

        for b in imgboxes:
            xmlobject = ET.SubElement(root, "object")
            assert b.params['label'] is not None
            ET.SubElement(xmlobject, "name").text = b.params['label']
            ET.SubElement(xmlobject, "pose").text = b.params.get('pose',"Unspecified")
            ET.SubElement(xmlobject, "truncated").text = "0"
            ET.SubElement(xmlobject, "difficult").text = "0"
            xmlbndbox = ET.SubElement(xmlobject, "bndbox")
            ET.SubElement(xmlbndbox, "xmin").text = str(b.colmin)
            ET.SubElement(xmlbndbox, "xmax").text = str(b.colmax)
            ET.SubElement(xmlbndbox, "ymin").text = str(b.rowmin)
            ET.SubElement(xmlbndbox, "ymax").text = str(b.rowmax)

    return prettify_xml(root)

def write_VOC_annotations(annotation_filename,img_filename,spec_metadata,img_size):
    xml_str = convert_annotations_to_VOC(img_filename,spec_metadata,img_size)
    with open(annotation_filename,'w') as f:
        f.write(xml_str)

def write_signal_to_img(img_filename,section,spec_metadata,img_size):
    ### get dependency file, and create a new stage_data object
    Sxxdims = []

    for i in range(len(spec_metadata)):
        Sxx = spec_metadata[i].image_data(section)
        Sxxdims.append(Sxx.shape)
        if Sxx.shape!=img_size:
            if Sxx.shape[0]>img_size[0] or Sxx.shape[1]>img_size[1]:
                logger.error('Your spectrogram has to fit in the provided image dimensions. values: {},{}'.format(Sxx.shape,img_size))
                raise AssertionError('Image size mismatch')
            Syy = np.zeros(img_size)
            Syy[0:Sxx.shape[0],0:Sxx.shape[1]] = Sxx
            Sxx = Syy

        # Save spectrogram as JPEG or PNG
        Sxx_bytes = np.uint8(Sxx*255)
        imgformat = os.path.splitext(img_filename)[1]
        if imgformat=='.jpeg' or imgformat=='.jpg':
            cv2.imwrite(img_filename, Sxx_bytes,
                        [int(cv2.IMWRITE_JPEG_QUALITY), 100])
        else:
            cv2.imwrite(img_filename, Sxx_bytes)
        # im = Image.fromarray(np.uint8(Sxx*255))
        # im.save(img_filename,'JPEG')

    return Sxxdims

def create_image_and_annotation(args):
    targetfilename = args['targetfilename']
    sourcefilename = args['sourcefilename']
    basefolder = os.path.dirname(targetfilename)
    fname = os.path.splitext(os.path.basename(targetfilename))[0]
    annotation_folder = basefolder+'/Annotations'
    img_folder = os.path.join(basefolder,'Images') #'/JPEGImages'
    if not os.path.exists(annotation_folder):
        os.mkdir(annotation_folder)
    if not os.path.exists(img_folder):
        os.mkdir(img_folder)
    annotation_filename = annotation_folder+'/'+fname+'.xml'
    img_filename = img_folder+'/'+fname+'.png' #'.jpg'

    # get parameters
    img_size = args['parameters']['img_size']

    ### get dependency file, and create a new stage_data object
    multi_stage_data = ssa.MultiStageSignalData.load_pkl(args)
    section = multi_stage_data.read_stage_samples()
    spec_metadata = multi_stage_data.get_stage_derived_params('spectrogram_img')
    assert len(spec_metadata)==1 # for now other options are not supported

    write_VOC_annotations(annotation_filename,img_filename,spec_metadata,img_size)
    Sxxdims = write_signal_to_img(img_filename,section,spec_metadata,img_size)

    # NOTE: spectrogram may be smaller than image just to fit in CNN input. In such case, it is a good idea
    # to keep the original spectrogram dimensions stored somewhere
    d = {'spectrogram_dims':Sxxdims,'image_dims':img_size}
    new_stage_data = ssa.StageSignalData(args,
                        {'voc_representation':d,'spectrogram_img':spec_metadata},
                        section)
    multi_stage_data.set_stage_data(new_stage_data)
    multi_stage_data.save_pkl()

class VOCFormatTask(StageLuigiTask):
    def run(self):
        this_run_params = self.get_run_parameters()
        create_image_and_annotation(this_run_params)
