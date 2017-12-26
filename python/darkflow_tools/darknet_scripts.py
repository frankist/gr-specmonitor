from os import listdir
from os.path import isfile
import argparse
import cv2
import numpy as np
import sys
import os
import shutil
import random
import math
import matplotlib.pyplot as plt

def anchors_fmt_str(centroids,model_width,model_height,separator='\n'):
    anchors = centroids.copy()

    for i in range(anchors.shape[0]):
        anchors[i][0]*=13#model_width/32.
        anchors[i][1]*=13#model_height/32.

    widths = anchors[:,0]
    sorted_indices = np.argsort(widths)
    anchors_sorted = anchors[sorted_indices]

    anchor_str = ''
    for r in range(anchors_sorted.shape[0]):
        w = anchors_sorted[r,0]
        h = anchors_sorted[r,1]
        anchor_str += '%0.2f,%0.2f'%(w,h) + separator
    return anchor_str

def write_anchors_to_file(centroids,dist,anchor_file,model_width,model_height):
    with open(anchor_file,'w') as f:
        fmt_str = anchors_fmt_str(centroids,model_width,model_height,'  ')
        #write anchors separated by \n
        f.write(fmt_str)
        f.write('%f\n'%(dist))

def print_anchors(centroids,dist,model_width,model_height):
    fmt_str = anchors_fmt_str(centroids,model_width,model_height,'  ')
    print fmt_str
    print '%f'.format(dist)

def IOU(x,centroids):
    similarities = []
    k = len(centroids)
    for centroid in centroids:
        c_w,c_h = centroid
        w,h = x
        if c_w>=w and c_h>=h:
            similarity = w*h/(c_w*c_h)
        elif c_w>=w and c_h<=h:
            similarity = w*c_h/(w*h + (c_w-w)*c_h)
        elif c_w<=w and c_h>=h:
            similarity = c_w*h/(w*h + c_w*(c_h-h))
        else: #means both w,h are bigger than c_w and c_h respectively
            similarity = (c_w*c_h)/(w*h)
        similarities.append(similarity) # will become (k,) shape
    return np.array(similarities) 

def avg_IOU(X,centroids):
    n,d = X.shape
    sum = 0.
    for i in range(X.shape[0]):
        #note IOU() will return array which contains IoU for each centroid and X[i] // slightly ineffective, but I am too lazy
        sum+= max(IOU(X[i],centroids)) 
    return sum/n

def kmeans(X,centroids,eps):
    N = X.shape[0]
    iterations = 0
    k,dim = centroids.shape
    prev_assignments = np.ones(N)*(-1)
    iter = 0
    old_D = np.zeros((N,k))

    while True:
        D = []
        iter+=1
        for i in range(N):
            d = 1 - IOU(X[i],centroids)
            D.append(d)
        D = np.array(D) # D.shape = (N,k)

        print "iter {}: dists = {}".format(iter,np.sum(np.abs(old_D-D)))

        #assign samples to centroids
        assignments = np.argmin(D,axis=1)

        if (assignments == prev_assignments).all():
            return centroids

        #calculate new centroids
        centroid_sums=np.zeros((k,dim),np.float)
        for i in range(N):
            centroid_sums[assignments[i]]+=X[i]
        for j in range(k):
            count_assignments = np.sum(assignments==j)
            if count_assignments==0:
                print('WARNING: There were centroids without assignments')
                continue
            centroids[j] = centroid_sums[j]/count_assignments

        prev_assignments = assignments.copy()
        old_D = D.copy()

def compute_kmeans_centroids(annotation_dims,num_anchors,num_attempts=10):
    possible_dims = np.unique(annotation_dims,axis=0)
    assert possible_dims.shape[0]>=num_anchors
    best_dist = np.inf
    best_centroids = []
    eps = 0.005
    for trial in range(num_attempts):
        # create the initial cluster centroids. Make them unique
        indices = range(possible_dims.shape[0])
        random.shuffle(indices)
        indices = indices[0:num_anchors]
        centroids = annotation_dims[indices]

        new_centroids = kmeans(annotation_dims,centroids,eps)

        dist = avg_IOU(annotation_dims,new_centroids)
        if dist < best_dist:
            best_centroids = new_centroids
            best_dist = dist

        # plt.plot(centroids[:,0],centroids[:,1],'o')
        # plt.plot(new_centroids[:,0],new_centroids[:,1],'xr')
        # plt.show()
    return best_centroids,best_dist

def read_annotation_dims(imglist_file,darknet_annotation_path):
    annotation_dims = []
    with open(imglist_file) as f:
        for line in f.readlines():
            img_file = line.rstrip('\n')
            img_id = os.path.splitext(os.path.basename(img_file))[0]
            darknet_annotation_file = darknet_annotation_path + '/'+ img_id + '.txt'
            # print darknet_annotation_file

            with open(darknet_annotation_file) as f2:
                for line in f2.readlines():
                    line = line.rstrip('\n')
                    w,h = line.split(' ')[3:]
                    #print w,h
                    annotation_dims.append(map(float,(w,h)))
    annotation_dims = np.array(annotation_dims)
    return annotation_dims

def generate_anchors(imglist_file,darknet_annotations_path,num_anchors):
    if isinstance(num_anchors,int):
        num_anchors = [num_anchors] # make it iterable

    # get all possible box dimensions
    annotation_dims = read_annotation_dims(imglist_file,darknet_annotations_path)

    centroids_list = []
    for a in num_anchors:
        centroids,dist = compute_kmeans_centroids(annotation_dims,a)
        centroids_list.append((centroids,dist))
        print "Normalized Centroids:\n",centroids
        print "Darknet Centroids (13x13):"
        l = ['{},{}'.format(centroids[i,0]*13,centroids[i,1]*13) for i in range(len(centroids))]
        print ',  '.join(l)
        print "Copy these anchors to your darknet .cfg file"
    return centroids_list

def write_anchors_from_yml_params(cfg_obj):
    '''
    This function generates the best fit for the darknet model
    based on my dataset
    '''
    imglist_filename = cfg_obj.tmp_imgpaths_filename()
    num_anchors = cfg_obj.model_params()['num_anchors']
    output_dir = cfg_obj.tmp_path()
    annotation_dir = cfg_obj.darknet_annotations_path()
    model_height = cfg_obj.model_params()['height']
    model_width = cfg_obj.model_params()['width']

    centroids_list = generate_anchors(imglist_filename,annotation_dir,num_anchors)

    for centroids,dist in centroids_list:
        # write file in tmp folder
        anchor_file = os.path.join(output_dir,'anchors%d.txt'%(len(centroids)))
        write_anchors_to_file(centroids,dist,anchor_file,model_width,model_height)

def print_anchors_cmdline(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-filelist',
                        default = '\\path\\to\\voc\\filelist\\train.txt',
                        help='path to filelist\n' )
    # parser.add_argument('-output_dir',
    #                     default = 'generated_anchors/anchors', type = str,
    #                     help='Output anchor directory\n' )
    parser.add_argument('-annotation_dir', type = str,
                        help='Path to annotations in darknet format\n' )
    parser.add_argument('-num_anchors', default = 5, type = int,
                        help='number of anchors\n' )

    args = parser.parse_args()
    # output_dir = args.output_dir
    annotation_dir = args.annotation_dir
    num_anchors = args.num_anchors
    imglist_filename = args.filelist
    model_height = cfg_obj.model_params()['height']
    model_width = cfg_obj.model_params()['width']

    centroids_list = generate_anchors(imglist_filename,annotation_dir,num_anchors)

    for centroids,dist in centroids_list:
        print_anchors(centroids,dist,model_width,model_height)

if __name__=="__main__":
    print_anchors_cmdline(sys.argv)
