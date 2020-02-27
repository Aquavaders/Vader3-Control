#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 10 16:49:34 2020

@author: dd
"""
# IMPORTS
import cv2
import numpy as np
import timeit
from sklearn.cluster import KMeans
from skimage import img_as_ubyte

# END IMPORTS

# PARAMETERS
CROP = 0  # Crop the photo on the object before alignment
DEBUG = 1  # Turn on to see debug photos and outputs
GRAY = 1  # Normalize in grayscale
STD = 128  # Size for all photos after normalization and padding
NOISE_BLUR = 5  # Blur width for noise in difference image
FILTER_BLUR = 5  # Blur width for noise in filtering image
DOWN_SCALE = 20  # Downscale percent of original image
OFF = 32  # Padding to image (to fix cropping after warping)
BLACK_OFFSET = 60  # Offset of things we consider black (in grayscale 0 - 255)

# Filters to get the foreground (we allow noise but fine noise only)
FILTER_LOWER_BEFORE_RED = np.array([145, 74, 130])
FILTER_UPPER_BEFORE_RED = np.array([176, 188, 255])
FILTER_LOWER_BEFORE_WHITE = np.array([85, 0, 200])
FILTER_UPPER_BEFORE_WHITE = np.array([179, 57, 255])

FILTER_LOWER_AFTER_RED = np.array([140, 80, 0])
FILTER_UPPER_AFTER_RED = np.array([179, 255, 255])
FILTER_LOWER_AFTER_WHITE = np.array([0, 0, 255])
FILTER_UPPER_AFTER_WHITE = np.array([0, 0, 255])

# After clustering, if quantization is on, colors in the photo will be binned
# into their closest color from this array, to remove extra clusters and to allow
# for multiple filters
COLORS = (
    (0, 0, 0),  # BLACK
    (180, 105, 255),  # PINK
    (255, 255, 255)  # WHITE
)
BEFORE_PATH = 'before1.png'
AFTER_PATH = 'after3.png'
IS_AFTER_UNDERWATER = 1
# ECC params
n_iters = 1000
e_thresh = 1e-6
warp_mode = cv2.MOTION_HOMOGRAPHY


# END PARAMETERS

# FUNCTIONS
def scale(pic, scale_percent):
    width = int(pic.shape[1] * scale_percent / 100)
    height = int(pic.shape[0] * scale_percent / 100)
    pic = cv2.resize(pic, (width, height), interpolation=cv2.INTER_NEAREST)
    return pic


def filter_image(lower, upper, pic):
    hsv = cv2.cvtColor(pic, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower, upper)
    result = cv2.bitwise_and(pic, pic, mask=mask)
    return result


def cluster_image(pic, clusters, is_grey=0):
    pic_n = None
    if is_grey == 0:
        pic_n = pic.reshape(pic.shape[0] * pic.shape[1], pic.shape[2])
    else:
        pic_n = pic.reshape(pic.shape[0] * pic.shape[1], 1)
    clustering = KMeans(n_clusters=clusters, random_state=0).fit(pic_n)
    return clustering


def closest_color(rgb_values):
    ret = []
    for rgb in rgb_values:
        r, g, b = rgb
        color_diffs = []

        for color in COLORS:
            cr, cg, cb = color
            color_diff = ((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2)
            color_diffs.append((color_diff, color))

        ret.append(min(color_diffs)[1])
    return np.array(ret)


def get_clustered_pic(clustering, pic, is_grey=0, quantize=1):
    flat_pixels, cluster_pic = None, None
    if quantize == 1:
        flat_pixels = closest_color(clustering.cluster_centers_[clustering.labels_])
    else:
        flat_pixels = clustering.cluster_centers_[clustering.labels_]

    if is_grey == 0:
        cluster_pic = flat_pixels.reshape(pic.shape[0], pic.shape[1], pic.shape[2])
    else:
        cluster_pic = flat_pixels.reshape(pic.shape[0], pic.shape[1], 1)
    return cluster_pic


def crop(pic):
    thresh = cv2.threshold(pic, BLACK_OFFSET, 255, cv2.THRESH_BINARY)[1]
    inner_contours = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    inner_contours = inner_contours[0] if len(inner_contours) == 2 else inner_contours[1]
    c = max(inner_contours, key=cv2.contourArea)
    left = tuple(c[c[:, :, 0].argmin()][0])
    right = tuple(c[c[:, :, 0].argmax()][0])
    top = tuple(c[c[:, :, 1].argmin()][0])
    bottom = tuple(c[c[:, :, 1].argmax()][0])
    return left, right, top, bottom


def standard(pic):
    height_o = pic.shape[0]
    width_o = pic.shape[1]
    width_n, height_n = STD, STD
    pic = cv2.resize(pic, (width_n, height_n), interpolation=cv2.INTER_NEAREST)
    return pic, width_n / width_o, height_n / height_o


def normalize(pic, after_flag=0):
    #    pic = cv2.medianBlur(pic, 5)
    pic = scale(pic, DOWN_SCALE)
    # TODO: PREBLURRING
    #    pic = cv2.medianBlur(pic, 5)
    lower_r = FILTER_LOWER_BEFORE_RED
    upper_r = FILTER_UPPER_BEFORE_RED
    lower_w = FILTER_LOWER_BEFORE_WHITE
    upper_w = FILTER_UPPER_BEFORE_WHITE

    if after_flag == 1:
        lower_r = FILTER_LOWER_AFTER_RED
        upper_r = FILTER_UPPER_AFTER_RED
        lower_w = FILTER_LOWER_AFTER_WHITE
        upper_w = FILTER_UPPER_AFTER_WHITE
    #        cv2.imshow('Filtered', pic)

    pic_r = filter_image(lower_r, upper_r, pic)
    pic_r = cv2.medianBlur(pic_r, FILTER_BLUR)
    pic_w = filter_image(lower_w, upper_w, pic)
    pic_w = cv2.medianBlur(pic_w, FILTER_BLUR)
    pic = pic_w + pic_r

    # TODO: CLUSTERING VS QUANTIZATION VS CLUSTERING AND QUANTIZATION
    kmeans = cluster_image(pic, 6)
    pic = img_as_ubyte(get_clustered_pic(kmeans, pic, 0, 1) / 255.0)

    #    pic_n = pic.reshape(pic.shape[0]*pic.shape[1], pic.shape[2])
    #    pic_n = closest_color(pic_n)
    #    pic = pic_n.reshape(pic.shape[0], pic.shape[1], pic.shape[2])
    #    pic = pic.astype('uint8')
    if DEBUG == 1:
        cv2.imshow('FilteredClusteredQuantized', pic)

    l, r, t, b, ret = [0, 0], [0, 0], [0, 0], [0, 0], None

    # TODO:CROPPING
    if GRAY == 1:
        pic = cv2.cvtColor(pic, cv2.COLOR_BGR2GRAY)
        if CROP == 1:
            l, r, t, b = crop(pic)
    else:
        if CROP == 1:
            gray = cv2.cvtColor(pic, cv2.COLOR_BGR2GRAY)
            l, r, t, b = crop(gray)
    if CROP == 1:
        pic = pic[t[1]:b[1], l[0]:r[0]]

    pic, sc1x, sc1y = standard(pic)
    if GRAY == 1:
        ret = np.zeros((STD + 2 * OFF, STD + 2 * OFF), dtype=np.uint8)
    else:
        ret = np.zeros((STD + 2 * OFF, STD + 2 * OFF, 3), dtype=np.uint8)
    ret[OFF:OFF + STD, OFF:OFF + STD] = pic
    ret, sc2x, sc2y = standard(ret)

    # TODO: POSTBLURRING
    #    ret = cv2.medianBlur(ret, NOISE_BLUR)
    return ret, l, r, t, b, [sc1x, sc1y], [sc2x, sc2y]


def transform(pt, l2, t2, sc1_2, sc2_2):
    pt = [pt[0] / sc2_2[1] - OFF, pt[1] / sc2_2[0] - OFF]
    pt = [pt[0] / sc1_2[1] + t2[1], pt[1] / sc1_2[0] + l2[0]]
    pt = [pt[0] * 100 / DOWN_SCALE, pt[1] * 100 / DOWN_SCALE]
    return pt


def align(pic_align_on, pic_to_align, mode, w1, h1):
    init_warp = np.eye(2, 3, dtype=np.float32)
    if mode == cv2.MOTION_HOMOGRAPHY:
        init_warp = np.eye(3, 3, dtype=np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, n_iters, e_thresh)
    gray_align_on, gray_to_align, aligned_img = None, None, None
    if GRAY == 1:
        gray_align_on = pic_align_on
        gray_to_align = pic_to_align
    else:
        gray_align_on = cv2.cvtColor(pic_align_on, cv2.COLOR_BGR2GRAY)
        gray_to_align = cv2.cvtColor(pic_to_align, cv2.COLOR_BGR2GRAY)
    try:
        cc, transform_warp = cv2.findTransformECC(gray_align_on, gray_to_align, init_warp, mode, criteria, None, 1)
        if mode == cv2.MOTION_HOMOGRAPHY:
            aligned_img = cv2.warpPerspective(pic_to_align, transform_warp, (w1, h1), flags=cv2.WARP_INVERSE_MAP)
        else:
            aligned_img = cv2.warpAffine(pic_to_align, transform_warp, (w1, h1), flags=cv2.WARP_INVERSE_MAP)
        return True, aligned_img, transform_warp
    except:
        return False, pic_to_align, init_warp


def get_camera(args):
    if len(args) < 2:
        print("""
        You must give an argument to open a video stream.
        It can be a number as video device, e.g.: 0 would be /dev/video0
        It can be a url of a stream,        e.g.: rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov
        It can be a video file,             e.g.: myvideo.mkv
        """)
        exit(0)
    resource_name = ""
    resource = args[1]
    # If we are given just a number, interpret it as a video device
    if len(resource) < 3:
        resource_name = "/dev/video" + resource
        resource = int(resource)
    else:
        resource_name = resource
    print("Trying to open resource: " + resource_name)
    cap = cv2.VideoCapture(resource)
    if not cap.isOpened():
        print("Error opening resource: " + str(resource))
        print("Maybe opencv VideoCapture can't open it")
        exit(0)
    return cap


def display(name, pic):
    cv2.imshow(name, pic)
    while True:
        key = cv2.waitKey(1)
        if key == 27:
            break
    cv2.destroyAllWindows()


# END FUNCTIONS

# MAIN
if __name__ == '__main__':

    orig1 = cv2.imread(BEFORE_PATH)
    img1 = orig1.copy()
    img1, l1, r1, t1, b1, sc1_1, sc2_1 = normalize(img1, 0)
    h1, w1 = img1.shape[:2]

    cap = get_camera(["2", "1"])

    # orig2 = cv2.imread(AFTER_PATH)
    r_val, orig2 = cap.read()
    while r_val:
        full_scale_start_time = timeit.default_timer()
        r_val, orig2 = cap.read()
        cv2.imshow("pic2", orig2)
        img2 = orig2.copy()
        reading_time = timeit.default_timer() - full_scale_start_time

        img2, l2, r2, t2, b2, sc1_2, sc2_2 = normalize(img2, IS_AFTER_UNDERWATER)
        h2, w2 = img1.shape[:2]

        normalization_time = timeit.default_timer() - full_scale_start_time - reading_time

        alignment_success, img2_aligned, warp = align(img1, img2, warp_mode, w1, h1)
        alignment_time = timeit.default_timer() - full_scale_start_time - normalization_time - reading_time

        key = cv2.waitKey(20)
        if key == 27 or key == 1048603:
            break

        if not alignment_success:
            continue

        if DEBUG == 1:
            cv2.imwrite("1.png", img1)
            cv2.imwrite("2.png", img2_aligned)
            cv2.imwrite('2-before.png', img2)
            blended = cv2.addWeighted(img1, 0.5, img2_aligned, 0.5, 0)
            cv2.imwrite('Blended.png', blended)

        warp_diff = cv2.absdiff(img2_aligned, img1)
        warp_diff = cv2.medianBlur(warp_diff, NOISE_BLUR)
        warp_diff = cv2.medianBlur(warp_diff, NOISE_BLUR)

        if GRAY == 0:
            warp_diff = cv2.cvtColor(warp_diff, cv2.COLOR_BGR2GRAY)

        warp_diff = cv2.threshold(warp_diff, BLACK_OFFSET, 255, cv2.THRESH_BINARY)[1]
        contours, _ = cv2.findContours(warp_diff, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        boxes = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            pts = np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]], np.float32)
            pts = np.array([pts], np.float32)
            boxes.append(cv2.perspectiveTransform(pts, warp))
            cv2.rectangle(warp_diff, (x, y), (x + w, y + h), (255, 255, 255), 2)

        for box in boxes:
            tl = transform(box[0][0], l2, t2, sc1_2, sc2_2)
            tr = transform(box[0][1], l2, t2, sc1_2, sc2_2)
            br = transform(box[0][2], l2, t2, sc1_2, sc2_2)
            bl = transform(box[0][3], l2, t2, sc1_2, sc2_2)
            points = np.array([tl, tr, br, bl, tl])
            cv2.polylines(orig2, np.int32([points]), 1, (255, 255, 255), 3)

        postprocessing_time = timeit.default_timer() - full_scale_start_time - alignment_time - normalization_time - reading_time

        print('READING TIME(s):       ', reading_time)
        print('NORMALIZATION TIME(s): ', normalization_time)
        print('ALIGNMENT TIME(s):     ', alignment_time)
        print('POSTPROCESSING TIME(s):', postprocessing_time)
        print('TOTAL TIME(s):         ', timeit.default_timer() - full_scale_start_time)
        print('SUM TIME(s):           ', postprocessing_time + alignment_time + normalization_time + reading_time)
        print('Change Areas Found:    ', len(contours))
        print('_________________________')

        if DEBUG == 1:
            cv2.imshow('Out', orig2)
            cv2.imshow('Contours', warp_diff)

        cv2.imshow('DifferenceWithBoxes.png', warp_diff)
        display("Output.png", orig2)
# END MAIN
