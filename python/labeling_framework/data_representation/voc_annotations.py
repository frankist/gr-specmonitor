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

import numpy as np
import xml.etree.ElementTree as ET
from xml.dom import minidom

from ..labeling_tools import bounding_box as bbox

def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def convert_annotations_to_VOC(args):
    params = args['parameters']
    sourcefilename = args['sourcefilename']
    targetfilename = args['targetfilename']

    ### get dependency file, and create a new stage_data object
    freader = pkl_sig_format.WaveformPklReader(sourcefilename)
    stage_data = freader.data()
    bbox_list = get_stage_derived_parameter(stage_data,'bounding_boxes')

    imgbbox_list = [bbox.ImageBoundingBox.convert_from_BoundingBox(b,img_shape,section_size) for b in bbox_list]

    # document
    root = ET.Element("annotation")

    # folder
    ET.SubElement(root, "folder").text = os.path.dirname(os.path.dirname(targetfilename))

    # filename
    ET.SubElement(root, "filename").text = os.path.basename(targetfilename)

    # source
    xmlsource = ET.SubElement(root, "source")
    ET.SubElement(xmlsource, "database").text = "An RF signal database"
    ET.SubElement(xmlsource, "annotation").text = "PASCAL VOC2017"

    xmlowner = ET.SubElement(root, "owner").text = "Faceless man"

    xmlsize = ET.SubElement(root, "size")
    ET.SubElement(xmlsize, "width").text = img_shape[1]
    ET.SubElement(xmlsize, "height").text = img_shape[0]
    ET.SubElement(xmlsize, "depth").text = img_depth

    ET.SubElement(root, "segmented").text = 0

    for b in imgbbox_list:
        xmlobject = ET.SubElement(root, "object")
        ET.SubElement(xmlobject, "name").text = b.label
        ET.SubElement(xmlobject, "pose").text = "Unspecified"
        ET.SubElement(xmlobject, "truncated").text = 0
        ET.SubElement(xmlobject, "difficult").text = 0
        xmlbndbox = ET.SubElement(xmlobject, "bndbox")
        ET.SubElement(xmlbndbox, "xmin").text = b.row_bounds[0]
        ET.SubElement(xmlbndbox, "xmax").text = b.row_bounds[1]
        ET.SubElement(xmlbndbox, "ymin").text = b.col_bounds[0]
        ET.SubElement(xmlbndbox, "ymax").text = b.col_bounds[1]

    return prettify_xml(root)

def write_VOC_annotations(args):
    targetfilename = args['targetfilename']
    basefolder = os.path.dirname(targetfilename)
    fname = os.path.splitext(os.path.basename(targetfilename))[0]
    annotation_filename = basefolder+'/Annotations/'+fname+'.xml'

    xml_str = convert_annotations_to_VOC(args)
    with open(annotation_filename,'w') as f:
        f.write(xml_str)

def create_image_and_annotation(args):
    write_VOC_annotations(args)
    write_signal_as_img(args)

