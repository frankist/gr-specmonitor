from __future__ import division
from __future__ import print_function
from builtins import str
import xml.etree.ElementTree as ET
# import pickle
import os

# import parse_yolo_cfg as yolocfg

def write_tmp_imgpaths_file(outfile,images_path):
    '''
    creates a txt file that contains the names of the jpeg images of the dataset
    '''
    with open(outfile,'w') as fptr:
        for image_id in os.listdir(images_path):
            fname = os.path.abspath('{}/{}'.format(images_path,image_id))
            if not os.path.isfile(fname): # there can be directories
                continue
            # the respective annotation must exist
            fptr.write('{}\n'.format(fname))

def convert(size, box):
    dw = 1./size[0]
    dh = 1./size[1]
    x = (box[0] + box[1])/2.0
    y = (box[2] + box[3])/2.0
    w = box[1] - box[0]
    h = box[3] - box[2]
    x = x*dw
    w = w*dw
    y = y*dh
    h = h*dh
    return (x,y,w,h)

def convert_to_darknet_annotation(darknet_annotations_path,
                                  annotations_path,
                                  classes_list):
    '''
    Picks the bounding boxes of an image, and converts them to darknet format
    '''
    in_file = open(annotations_path)
    out_file = open(darknet_annotations_path, 'w')

    tree=ET.parse(in_file)
    root = tree.getroot()
    size = root.find('size')
    w = int(size.find('width').text)
    h = int(size.find('height').text)

    for obj in root.iter('object'):
        difficult = obj.find('difficult').text
        cls = obj.find('name').text
        if cls not in classes_list or int(difficult) == 1:
            continue
        cls_id = classes_list.index(cls)
        xmlbox = obj.find('bndbox')
        b = (float(xmlbox.find('xmin').text), float(xmlbox.find('xmax').text), float(xmlbox.find('ymin').text), float(xmlbox.find('ymax').text))
        bb = convert((w,h), b)
        out_file.write(str(cls_id) + " " + " ".join([str(a) for a in bb]) + '\n')

def generate_darknet_annotations(imgpaths_file,
                                 annotations_path,
                                 darknet_annotations_path,
                                 classes_list):
    '''
    picks all the annotations of the dataset and converts
    them to darknet annotations
    '''
    # opens file with image names, and creates a darknet annotation
    with open(imgpaths_file,'r') as fptr:
        for line in fptr:
            fname = line.rstrip('\n')
            id_ = os.path.splitext(os.path.basename(fname))[0]
            print(id_)
            annotations_filename = '{}/{}.xml'.format(annotations_path,id_)
            darknet_filename = '{}/{}.txt'.format(darknet_annotations_path,id_)
            convert_to_darknet_annotation(darknet_filename,
                                          annotations_filename,
                                          classes_list)

def write_labels_file(outfilename,classes_list):
    with open(outfilename, 'w') as fptr:
        for c in classes_list:
            fptr.write('{}\n'.format(c))

def setup_darknet_dataset(cfg_obj):
    # parse needed params
    img_path = cfg_obj.images_path()
    annotations_path = cfg_obj.annotations_path()
    darknet_annotations_path = cfg_obj.darknet_annotations_path()
    imgpaths_file = cfg_obj.tmp_imgpaths_filename()
    classes_list = cfg_obj.model_params()['classes']

    if not os.path.exists(darknet_annotations_path):
        os.makedirs(darknet_annotations_path)

    # generate a file with all the images names
    write_tmp_imgpaths_file(imgpaths_file,img_path)

    # generate darknet annotation files
    generate_darknet_annotations(imgpaths_file,
                                 annotations_path,
                                 darknet_annotations_path,
                                 classes_list)

