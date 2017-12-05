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
import pickle

from ..sig_format import sig_data_access as sda
from ..sig_format import pkl_sig_format
import image_representation as imrep
import timefreq_box as tfbox
from ..labeling_tools import bounding_box as bbox

def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def convert_annotations_to_VOC(img_filename,sourcefilename):
    ### get dependency file, and create a new stage_data object
    freader = pkl_sig_format.WaveformPklReader(sourcefilename)
    stage_data = freader.data()
    spec_metadata = sda.get_stage_derived_parameter(stage_data,'section_spectrogram_img_metadata')
    x = freader.read_section()

    # document
    root = ET.Element("annotation")

    # folder
    ET.SubElement(root, "folder").text = os.path.dirname(os.path.dirname(img_filename))

    # filename
    ET.SubElement(root, "filename").text = os.path.basename(img_filename)

    # source
    xmlsource = ET.SubElement(root, "source")
    ET.SubElement(xmlsource, "database").text = "An RF signal database"
    ET.SubElement(xmlsource, "annotation").text = "PASCAL VOC2017"

    xmlowner = ET.SubElement(root, "owner")
    xmlownername = ET.SubElement(xmlowner, "name").text = "Faceless man"

    xmlsize = ET.SubElement(root, "size")
    ET.SubElement(xmlsize, "width").text = str(spec_metadata[0].img_size[1])
    ET.SubElement(xmlsize, "height").text = str(spec_metadata[0].img_size[0])
    ET.SubElement(xmlsize, "depth").text = str(spec_metadata[0].depth)

    ET.SubElement(root, "segmented").text = "0"

    assert len(spec_metadata)==1 # FIXME: Implement it for more
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

def write_VOC_annotations(annotation_filename,img_filename,sourcefilename):
    xml_str = convert_annotations_to_VOC(img_filename,sourcefilename)
    with open(annotation_filename,'w') as f:
        f.write(xml_str)

def write_signal_to_jpeg(img_filename,sourcefilename):
    ### get dependency file, and create a new stage_data object
    freader = pkl_sig_format.WaveformPklReader(sourcefilename)
    stage_data = freader.data()
    section = freader.read_section()

    spec_metadata = sda.get_stage_derived_parameter(stage_data,'section_spectrogram_img_metadata')

    assert len(spec_metadata)==1
    for i in range(len(spec_metadata)):
        Sxx = spec_metadata[i].image_data(section)
        im = Image.fromarray(np.uint8(Sxx*255))
        im.save(img_filename,'JPEG')

def create_image_and_annotation(args):
    targetfilename = args['targetfilename']
    sourcefilename = args['sourcefilename']
    basefolder = os.path.dirname(targetfilename)
    fname = os.path.splitext(os.path.basename(targetfilename))[0]
    annotation_folder = basefolder+'/Annotations'
    img_folder = basefolder+'/JPEGImages'
    if not os.path.exists(annotation_folder):
        os.mkdir(annotation_folder)
    if not os.path.exists(img_folder):
        os.mkdir(img_folder)
    annotation_filename = annotation_folder+'/'+fname+'.xml'
    img_filename = img_folder+'/'+fname+'.jpg'

    write_VOC_annotations(annotation_filename,img_filename,sourcefilename)
    write_signal_to_jpeg(img_filename,sourcefilename)
    with open(targetfilename,'w') as f:
        pickle.dump({'status':'done'},f)

