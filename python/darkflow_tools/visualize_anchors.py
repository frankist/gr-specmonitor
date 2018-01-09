from __future__ import print_function
import cv2
import numpy as np
import sys
import argparse
from os import listdir
from os.path import isfile, join


def draw_anchors(anchors_list,model_width, model_height):
    H = model_height
    W = model_width
    stride = 32 # What is this?

    cv2.namedWindow('Image')
    cv2.moveWindow('Image',100,100)

    colors = [(255,0,0),(255,255,0),(0,255,0),(0,0,255),(0,255,255),(55,0,0),(255,55,0),(0,55,0),(0,0,25),(0,255,55)] # What is this?
    stride_h = 3#10
    stride_w = 3
    pt0 = (10,10)

    blank_image = np.zeros((H,W,3),np.uint8)
    for i,anchor in enumerate(anchors_list):
        w=int(anchor[0]*W/13.0)#stride)
        h=int(anchor[1]*H/13.0)#stride)
        print(w,h)

        pts = (pt0[0]+i*stride_w,pt0[0]+i*stride_h)
        pt1 = (max(0,pts[0]+min(0,(W-(pts[0]+w)))),
               max(0,pts[1]+min(0,(H-(pts[0]+h))))) # (10+i*stride_w,10+i*stride_h
        pt2 = (pt1[0]+w,pt1[1]+h)

        cv2.rectangle(blank_image,pt1,pt2,colors[i])
    cv2.imshow('Image',blank_image)

    # cv2.imwrite(filename,blank_image)
    cv2.waitKey(0)#10000)


# def main(argv):
#     parser = argparse.ArgumentParser()
#     parser.add_argument('-anchor_dir',
#                         default = 'generated_anchors/voc-anchors',
#                         help='path to anchors\n')

#     args = parser.parse_args()

#     print "anchors list you provided: {}".format(args.anchor_dir)

#     [H,W] = (416,416)
#     stride = 32

#     cv2.namedWindow('Image')
#     cv2.moveWindow('Image',100,100)

#     colors = [(255,0,0),(255,255,0),(0,255,0),(0,0,255),(0,255,255),(55,0,0),(255,55,0),(0,55,0),(0,0,25),(0,255,55)]

#     anchor_files = [f for f in listdir(args.anchor_dir) if (join(args.anchor_dir, f)).endswith('.txt')]
#     for anchor_file in anchor_files:
#         blank_image = np.zeros((H,W,3),np.uint8)

#         f = open(join(args.anchor_dir,anchor_file))
#         line = f.readline().rstrip('\n')

#         anchors = line.split(', ')

#         filename = join(args.anchor_dir,anchor_file).replace('.txt','.png')

#         print filename

#         stride_h = 10
#         stride_w = 3
#         if 'caltech' in filename:
#             stride_w = 25
#             stride_h = 10

#         for i in range(len(anchors)):
#             (w,h) = map(float,anchors[i].split(','))


#             w=int (w*stride)
#             h=int(h*stride)
#             print w,h
#             cv2.rectangle(blank_image,(10+i*stride_w,10+i*stride_h),(w,h),colors[i])

#             #cv2.imshow('Image',blank_image)

#             cv2.imwrite(filename,blank_image)
#             #cv2.waitKey(10000)

if __name__=="__main__":
    # main(sys.argv)
    anchors = [[0.875, 1.125], [0.875, 0.625], [6.625, 2.20833333], [0.125, 0.31617647], [0.875, 1.125], [0.875, 0.96875], [0.625, 13.]]

    # anchors = [[0.12,0.32], [0.62,13.00], [0.88,0.75], [0.88,1.09], [6.62,2.21]]
    # anchors = [[0.12,0.32], [0.86,1.84], [6.62,0.31], [6.62,1.62], [6.62,2.94]]
    # anchors = [[0.03,0.08], [0.16,3.25], [0.22,0.19], [0.22,0.27], [1.66,0.55]]
    draw_anchors(anchors,104,104)
