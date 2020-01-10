#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 10 16:49:34 2020

@author: dd
"""
#IMPORTS
import cv2
import numpy as np
import timeit
from sklearn.cluster import KMeans
from skimage import img_as_ubyte
#END IMPORTS
#%%
#PARAMETERS
DEBUG=1
GRAY=1
STD = 128
NOISE_BLUR = 5
DOWN_SCALE = 15
OFF = 16
BLACK_OFFSET = 60
FILTER_LOWER_BEFORE =  np.array([94, 15, 149])
FILTER_UPPER_BEFORE = np.array([179, 255, 255])
FILTER_LOWER_AFTER =  np.array([94, 15, 149])
FILTER_UPPER_AFTER = np.array([179, 255, 255])
BEFORE_PATH = 'before1.png'
AFTER_PATH = 'after2.png'
# ECC params
n_iters = 1000
e_thresh = 1e-6
warp_mode = cv2.MOTION_HOMOGRAPHY
#END PARAMETERS
#%%
#FUNCTIONS
def scale(pic, scale_percent):
    width = int(pic.shape[1] * scale_percent / 100)
    height= int(pic.shape[0] * scale_percent / 100)
    pic =  cv2.resize(pic, (width, height) , interpolation = cv2.INTER_NEAREST) 
    return pic

def filterImage(lower, upper, pic):
    hsv = cv2.cvtColor(pic, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower, upper)
    result = cv2.bitwise_and(pic, pic, mask=mask)
    return result

def clusterImage(pic, clusters, isgrey=0):
    pic_n = pic
    if(isgrey==0):
        pic_n = pic.reshape(pic.shape[0]*pic.shape[1], pic.shape[2])
    else:
        pic_n =  pic.reshape(pic.shape[0]*pic.shape[1], 1)
    kmeans = KMeans(n_clusters=clusters, random_state=0).fit(pic_n)
    return kmeans

def getClusteredPic(kmeans, pic, isgrey=0):
    cluster_pic = pic
    print( kmeans.cluster_centers_)
    pic2show = kmeans.cluster_centers_[kmeans.labels_]  
    if(isgrey==0):
        cluster_pic = pic2show.reshape(pic.shape[0], pic.shape[1], pic.shape[2])
    else:
        cluster_pic = pic2show.reshape(pic.shape[0], pic.shape[1], 1) 
    return cluster_pic

def crop(pic):
    thresh = cv2.threshold(pic, BLACK_OFFSET, 255, cv2.THRESH_BINARY)[1]
    cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    c = max(cnts, key=cv2.contourArea)
    left = tuple(c[c[:, :, 0].argmin()][0])
    right = tuple(c[c[:, :, 0].argmax()][0])
    top = tuple(c[c[:, :, 1].argmin()][0])
    bottom = tuple(c[c[:, :, 1].argmax()][0])
    return left, right, top, bottom

def standard(pic):
    width_o = pic.shape[1]
    height_o = pic.shape[0]
    width_n = STD
    height_n = STD
    pic =  cv2.resize(pic,  (width_n, height_n) , interpolation = cv2.INTER_NEAREST) 
    return pic, width_n/width_o, height_n/height_o

def normalize(pic, after_flag = 0):
    pic = cv2.medianBlur(pic, 21)
    pic = scale(pic, DOWN_SCALE)
#TODO: PREBLURRING
#    pic = cv2.medianBlur(pic, 5)
    lower = FILTER_LOWER_BEFORE
    upper = FILTER_UPPER_BEFORE  
    if(after_flag==1):
        lower = FILTER_LOWER_AFTER
        upper = FILTER_UPPER_AFTER       
    pic = filterImage(lower, upper, pic)
    kmeans = clusterImage(pic, 3)
    pic = img_as_ubyte(getClusteredPic(kmeans, pic)/255.0)
    
    l,r,t,b,ret=[0,0],[0,0],[0,0],[0,0],None  
    if(GRAY==1):
        pic = cv2.cvtColor(pic, cv2.COLOR_BGR2GRAY)
#TODO:CROPPING
#        l,r,t,b = crop(pic)
#    else:
#        gray = cv2.cvtColor(pic, cv2.COLOR_BGR2GRAY)
#        l,r,t,b = crop(gray)    
#    pic = pic[t[1]:b[1], l[0]:r[0]]
        
    pic,sc1x,sc1y = standard(pic)  
    if(GRAY==1):
        ret = np.zeros((STD+2*OFF,STD+2*OFF),dtype=np.uint8)
    else:
        ret = np.zeros((STD+2*OFF,STD+2*OFF,3),dtype=np.uint8)   
    ret [OFF:OFF+STD, OFF:OFF+STD]=pic
    ret,sc2x,sc2y = standard(ret)
    
#TODO: POSTBLURRING
#    ret = cv2.medianBlur(ret, NOISE_BLUR)
    return ret, l, r, t, b, [sc1x, sc1y], [sc2x,sc2y]

def transform (pt, l2, t2, sc1_2, sc2_2):
    pt =[pt[0]/sc2_2[1]-OFF, pt[1]/sc2_2[0]-OFF]
    pt =[pt[0]/sc1_2[1] +t2[1], pt[1]/sc1_2[0] +l2[0]]
    pt =[pt[0]*100/DOWN_SCALE, pt[1]*100/DOWN_SCALE]
    return pt

def align(img1,img2,mode, w1, h1):
    init_warp =  np.eye(2, 3, dtype=np.float32)
    if mode == cv2.MOTION_HOMOGRAPHY :
        init_warp = np.eye(3, 3, dtype=np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, n_iters, e_thresh)
    gray1 = None
    gray2 = None
    if(GRAY==1):
        gray1 = img1
        gray2 = img2   
    else:
        gray1 = cv2.cvtColor(img1,cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2,cv2.COLOR_BGR2GRAY)
    cc, warp = cv2.findTransformECC(gray1, gray2, init_warp, mode, criteria,None,1)
    img2_aligned = gray2
    if mode == cv2.MOTION_HOMOGRAPHY :
        img2_aligned = cv2.warpPerspective(img2, warp, (w1, h1), flags=cv2.WARP_INVERSE_MAP)
    else:
        img2_aligned = cv2.warpAffine(img2, warp, (w1, h1), flags=cv2.WARP_INVERSE_MAP)
    return img2_aligned, warp
#END FUNCTIONS
#%%
#MAIN
if __name__ == '__main__':    
    full_scale_start_time = timeit.default_timer()
    
    orig1 = cv2.imread(BEFORE_PATH)
    img1= cv2.imread(BEFORE_PATH)
    orig2 = cv2.imread(AFTER_PATH)
    img2 = cv2.imread(AFTER_PATH)  
    reading_time = timeit.default_timer()-full_scale_start_time
    
    img1,l1,r1,t1,b1,sc1_1,sc2_1  = normalize(img1, 0)
    img2,l2,r2,t2,b2,sc1_2,sc2_2  = normalize(img2, 1)
    h1, w1 = img1.shape[:2]
    h2, w2 = img1.shape[:2]
    normalization_time = timeit.default_timer() - full_scale_start_time-reading_time
    
    img2_aligned, warp = align(img1, img2, warp_mode, w1, h1)      
    alignment_time = timeit.default_timer() - full_scale_start_time-normalization_time-reading_time   
    
    if DEBUG==1: 
        cv2.imwrite("1.png", img1)
        cv2.imwrite("2.png", img2_aligned)
        cv2.imwrite('2-before.png', img2)
        blended = cv2.addWeighted(img1, 0.5, img2_aligned, 0.5, 0)
        cv2.imwrite('Blended.png', blended)
    
    warp_diff = cv2.absdiff(img2_aligned, img1)
    warp_diff = cv2.medianBlur(warp_diff, NOISE_BLUR)
    warp_diff = cv2.medianBlur(warp_diff, NOISE_BLUR)
    
    if GRAY==0:
        warp_diff = cv2.cvtColor(warp_diff,cv2.COLOR_BGR2GRAY)
    
    warp_diff = cv2.threshold(warp_diff, BLACK_OFFSET, 255, cv2.THRESH_BINARY)[1]
    contours, hier = cv2.findContours(warp_diff, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        pts = np.array([[x,y],[x+w,y],[x+w,y+h],[x,y+h],[x,y]], np.float32)
        pts = np.array([pts], np.float32)
        boxes.append(cv2.perspectiveTransform(pts, warp))
        cv2.rectangle(warp_diff, (x, y), (x+w, y+h), (255, 255, 255), 2)
    
    for box in boxes: 
        tl = transform (box[0][0], l2, t2, sc1_2, sc2_2)
        tr = transform (box[0][1], l2, t2, sc1_2, sc2_2)
        br = transform (box[0][2], l2, t2, sc1_2, sc2_2)
        bl = transform (box[0][3], l2, t2, sc1_2, sc2_2)
        points = np.array([tl,tr,br,bl,tl])
        cv2.polylines(orig2, np.int32([points]), 1, (255,255,255),3)
    
    postprocessing_time = timeit.default_timer() - full_scale_start_time-alignment_time-normalization_time-reading_time
    
    print('READING TIME(s):       ', reading_time)
    print('NORMALIZATION TIME(s): ', normalization_time)
    print('ALIGNMENT TIME(s):     ', alignment_time)
    print('POSTPROCESSING TIME(s):', postprocessing_time)
    print('TOTAL TIME(s):         ', timeit.default_timer() - full_scale_start_time )
    print('SUM TIME(s):           ', postprocessing_time+alignment_time+normalization_time+reading_time)
    print('Change Areas Found:    ', len(contours))
    print('_________________________')
    
    if(DEBUG==1):
        cv2.imshow('Out', orig2)
        cv2.imshow('Contours', warp_diff)
        while True:
            key = cv2.waitKey(1)
            if key == 27:
                break
        cv2.destroyAllWindows()
    
    cv2.imwrite('DifferenceWithBoxes.png', warp_diff)
    cv2.imwrite("Output.png", orig2)
#END MAIN
