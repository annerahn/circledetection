# Importing the necessary python libraries
import cv2
from pathlib import Path
import json 
import numpy as np
from flask import Flask, request, Response
app = Flask(__name__)

@app.route('/', methods=['POST'])
def detection():
    npimg = np.fromfile(request.files['image'], np.uint8)
    # convert numpy array to image
    img_orig = img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    #cv2.imshow("img", img_orig)
    #cv2.waitKey(0) # waits indefinitely untill a key (any key) is pressed inside the display window
    img = cv2.cvtColor(img_orig, cv2.COLOR_BGR2GRAY) # converting image to grayscale
    img = cv2.GaussianBlur(img, (13, 13), 0)  # blurring to remove some noise 
    img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 99, 4) # adpative local thresholding to convert to binary image

    # finding and filtering contours
    ( cnts, cnts_hs ) = cv2.findContours(img.copy(), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE) # finding contours based on cv2.RETR_CCOMP setting
    cnts = [cnt for i,cnt in enumerate(cnts) if cnts_hs[0,i,3] != -1] # retaining only child contours 
    cnts_area  = [cv2.contourArea(cnt) for cnt in cnts] # finding area for the contours
    max_cnt_area = max(cnts_area)
    thresh_cnt_area = 0.15
    cnts = [cnt for i,cnt in enumerate(cnts) if cnts_area[i] > thresh_cnt_area*max_cnt_area] # retaining only contours with area greater than thresh_cnt_area*max_cnt_area
     
    # Retaining only contours with a near circular/ellipse shape. Detected by comparing area of contour with area of circle enclosing it 
    cnts_enclosing_circles      = [cv2.minEnclosingCircle(cnt) for cnt in cnts] # finding minimum enclosing circles for the contours
    cnts_enclosing_circles_area = [ np.pi*radius*radius for (x,y),radius in cnts_enclosing_circles ] # finding area of the enclosing circles
    thresh_cnt_shape = 0.5
    cnts = [cnt for i,cnt in enumerate(cnts) if cv2.contourArea(cnt) > thresh_cnt_shape*cnts_enclosing_circles_area[i]] 
    flag_shape_distortion = True if len(cnts) < len(cnts_enclosing_circles) else False

    # determining contour row locations 
    min_enclosing_circles = [cv2.minEnclosingCircle(cnt) for cnt in cnts] # finding enclosing circles 
    ycenters = sorted([y for (x,y),radius in min_enclosing_circles]) # finding centers of enclosing circles
    mean_radius = np.mean([radius for (x,y),radius in min_enclosing_circles])  # finding mean radius across all enclosing circles
    thresh_csep = 1 # circles with distance between centers < thresh_csep*mean_radius threshold are considered to belong to the same row
    num_cnts = len(min_enclosing_circles) # total number of contours/enclosing circles
    counter = 0 
    circle_counts_per_row = [] # list for storing number of circles per row
    yval_curr_row = ycenters[0] 
    for yval in ycenters:
        if (yval-yval_curr_row < thresh_csep*mean_radius) :
            counter = counter + 1
        else :
            circle_counts_per_row.append(counter)
            counter = 1 # reinitializing the counter
            yval_curr_row = yval    
    circle_counts_per_row.append(counter) # adding count for the last row

    # detecting if number of rows > 10 or number of circles per row > 10 
    max_rows = 10
    max_circles_per_row = 10
    num_rows = len(circle_counts_per_row)
    bool_extra_circles = [ count > max_circles_per_row for count in circle_counts_per_row ]
    bool_extra_circles = True in bool_extra_circles
    flag_extra_counts = True if ( ( num_rows > max_rows) or ( bool_extra_circles ) ) else False
    
    # setting output codes based on flag_shape_distortion and flag_extra_counts
    if (flag_shape_distortion and flag_extra_counts) :
        output_code = 4
    elif flag_shape_distortion :
        output_code = 2
    elif flag_extra_counts :
        output_code = 3
    else :
        output_code = 1            

    output_dict = dict()
    output_dict["output_code"] = output_code
    output_dict["counts"] = circle_counts_per_row

    # (Debug purpose) Visualizing detected contours and saving to disk
    #cv2.drawContours(img_orig, cnts, -1, (0, 255, 0), 2)
    #cv2.putText(img_orig, "Total count: {}".format(len(cnts)), (50,50) , cv2.FONT_HERSHEY_SIMPLEX, 0.8 , (0,255,0), 2)
    #cv2.putText(img_orig, "Rowwise Count: {}".format(circle_counts_per_row), (50,80) , cv2.FONT_HERSHEY_SIMPLEX, 0.8 , (0,255,0), 2)
    ##outfilepath = output_folder_path / input_filepath.name
    ##cv2.imwrite(str(outfilepath), img_orig)
    #cv2.imshow("img", img_orig)
    #cv2.waitKey(0) # waits indefinitely untill a key (any key) is pressed inside the display window

    return Response(json.dumps(output_dict, indent=4), mimetype='application/json')
