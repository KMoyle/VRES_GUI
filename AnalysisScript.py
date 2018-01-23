import numpy as np
import imageio
import subprocess
import sys
import wave 
import struct
import cv2
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import soundfile as sf 

from numpy import arange
import IDME
import os.path
import sys
from Tkinter import *
from tkFileDialog import *
from tkMessageBox import *
from datetime import datetime


def ConvertCV2ImageToTkImage(cv2_image, resize=None):
	if resize != None:
		cv2_image = cv2.resize(cv2_image, resize)

	b,g,r = cv2.split(cv2_image)
	image = cv2.merge((r,g,b))
	image = Image.fromarray(cv2_image)

	return ImageTk.PhotoImage(image=image)

def FindBestMatch(confusion_matrix, index):
	
	min_index = np.argmin(confusion_matrix[index, : ])

	return min_index

def GetParameterValue(parameter_set, parameter_name):
	parameter_value = parameter_set.GetParameterValue(parameter_name)
	if parameter_value == None:
		print "The Parameter %s could not be found within the parameter set %s."%(parameter_name, parameter_set.Name())
		exit()
	return parameter_value

def GetTemplateRegion(template_size, image_width, image_height):
	template_region = [0, 0, 0, 0]
	template_region[2] = int(template_size * float(image_width))
	template_region[3] = int(template_size * float(image_height))

	if image_index == 1:
		template_region[0] = int(float(image_width)/2.0 - float(template_region[2])/2.0)
		template_region[1] = 0
	else:
		template_region[0] = int(float(image_width)/2.0 - float(template_region[2])/2.0) + pixel_shift[0]
		template_region[1] = int(float(image_height)/2.0 - float(template_region[3])/2.0) + pixel_shift[1]

	template_region[0] = min(max(template_region[0], 0), image_width - template_region[2])
	template_region[1] = min(max(template_region[1], 0), image_height - template_region[3])

	return template_region

def GetPredictionRegion(ave_pixel_shifts, template_region, image_width, image_height, region_padding = 0):
	prediction_region = [0, 0, image_width, image_height]
	prediction_region[0] = template_region[0] - ave_pixel_shift[0] - region_padding
	prediction_region[1] = template_region[1] - ave_pixel_shift[1] - region_padding
	prediction_region[2] = template_region[2] + 2*region_padding
	prediction_region[3] = template_region[3] + 2*region_padding

	prediction_region[0] = min(max(prediction_region[0], 0), image_width - prediction_region[2])
	prediction_region[1] = min(max(prediction_region[1], 0), image_height - prediction_region[3])

	return prediction_region

def VisualOdometryVisualizations(current_image, previous_image, template_region, prediction_region = None):
	# DRAW RECTANGLES ON IMAGES
	current_image_copy = current_image.copy()
	cv2.rectangle(current_image_copy, (rect_loc[0], rect_loc[1]), (rect_loc[0]+template_region[2], rect_loc[1]+template_region[3]), (0,0,255), 6)
	cv2.rectangle(previous_image, (template_region[0], template_region[1]), (template_region[0]+template_region[2], template_region[1]+template_region[3]), (0,0,255), 6)

	if prediction_region != None:
		cv2.rectangle(current_image_copy, (prediction_region[0], prediction_region[1]), (prediction_region[0]+prediction_region[2], prediction_region[1]+prediction_region[3]), (0,0,255), 6)

	# DISPLAY IMAGES
	cv2.imshow("Previous Frame", previous_image)
	cv2.imshow("Current Frame", current_image_copy)
	cv2.waitKey(1)


if __name__ == "__main__":

	# LOAD IN REF AND QRY DATA SETS 
	REF_DATASET_PATH = '/home/kylesm/Desktop/VRES/VRES_GUI'
	REF_DATASET_FILE_NAME = '/dataset.yaml'
	REF_SURFACE_IMAGE_SET = "REF_surface_images"
	REF_FORWARD_IMAGE_SET = "REF_forward_images"

	QRY_DATASET_PATH = '/home/kylesm/Desktop/VRES/VRES_GUI'
	QRY_DATASET_FILE_NAME = '/dataset.yaml'
	QRY_SURFACE_IMAGE_SET = "REF_surface_images"
	QRY_FORWARD_IMAGE_SET = "REF_forward_images"

	PARAMETER_FILE = '/home/kylesm/Desktop/VRES/map_generation/ParameterFile.yaml'

	# INITIALIZE DATASET FILE, GET IMAGE SET AND IMAGE FILENAMES
	REF_dataset = IDME.DatasetFile(REF_DATASET_PATH + REF_DATASET_FILE_NAME)
	REF_surface_image_set = REF_dataset.GetImageSet(REF_SURFACE_IMAGE_SET)
	REF_forward_image_set = REF_dataset.GetImageSet(REF_FORWARD_IMAGE_SET)

	QRY_dataset = IDME.DatasetFile(QRY_DATASET_PATH + QRY_DATASET_FILE_NAME)
	QRY_surface_image_set = QRY_dataset.GetImageSet(QRY_SURFACE_IMAGE_SET)
	QRY_forward_image_set = QRY_dataset.GetImageSet(QRY_FORWARD_IMAGE_SET)

	#if image_set == None:
	#	print "Failed to find the image set within the dataset"
	#	exit()

	REF_forward_image_filenames = REF_dataset.GetImageFilenames(REF_forward_image_set)
	REF_surface_image_filenames = REF_dataset.GetImageFilenames(REF_surface_image_set)

	QRY_forward_image_filenames = QRY_dataset.GetImageFilenames(QRY_forward_image_set)
	QRY_surface_image_filenames = QRY_dataset.GetImageFilenames(QRY_surface_image_set)

	# GET IMAGE SET ENDFRAME
	REF_surface_END_FRAME = REF_surface_image_set.NumberOfImages()
	REF_forward_END_FRAME = REF_forward_image_set.NumberOfImages()

	QRY_surface_END_FRAME = QRY_surface_image_set.NumberOfImages()
	QRY_forward_END_FRAME = QRY_forward_image_set.NumberOfImages()

	print "ref total %d" % int(REF_forward_END_FRAME)
	print "qry total %d" % int(QRY_forward_END_FRAME)

	step = 30
	# PERFORM VISUAL ODOMETRY
	REF_image_index = 0
	QRY_image_index = 0

	REF_forward_START_FRAME = 0
	REF_array = 0
	QRY_array = 0

	#REF_image = cv2.imread(REF_forward_image_set.Folder() + "/" + REF_forward_image_filenames[REF_image_index])
	#cv2.imshow( "Display window", REF_image )

	#cv2.waitKey(0)

	#confusion_matrix = np.zeros(((QRY_forward_END_FRAME/step),(REF_forward_END_FRAME/step)))

	# for QRY_image_index in range(0, QRY_forward_END_FRAME, step):

	# 	#print "qry index %d" % QRY_image_index
	# 	# GET FIRST REF IMAGE  
	#  	QRY_image = cv2.imread(QRY_forward_image_set.Folder() + "/" + QRY_forward_image_filenames[QRY_image_index])
	#  	QRY_image_gray = cv2.cvtColor(QRY_image,cv2.COLOR_BGR2GRAY)
	#  	#cv2.imshow( "Display window", QRY_image_gray )
	#  	#QRY_image_gray_normalized = cv2.normalize(QRY_image_gray.astype('float'), None, 0.0, 1.0, cv2.NORM_MINMAX)
	#  	QRY_image_gray_resized = cv2.resize(QRY_image_gray, (100, 60))
	#  	#QRY_image_gray_normalized_resized_histeq = cv2.equalizeHist(QRY_image_gray_normalized_resized)
	#  	QRY_image_gray_resized_histeq = cv2.equalizeHist(QRY_image_gray_resized)
	#  	print "QRY array %d" % QRY_array

	# 	#print ""
		
	# 	for REF_image_index in range(0, REF_forward_END_FRAME, step):
	# 		#print "ref index %d" % REF_image_index

	# 	 	# GET FIRST REF IMAGE  
	# 		REF_image = cv2.imread(REF_forward_image_set.Folder() + "/" + REF_forward_image_filenames[REF_image_index])
	# 		REF_image_gray = cv2.cvtColor(REF_image,cv2.COLOR_BGR2GRAY)
	# 		#cv2.imshow( "Display window", REF_image_gray )
	# 		#REF_image_gray_normalized = cv2.normalize(REF_image_gray.astype('float'), None, 0.0, 1.0, cv2.NORM_MINMAX)
	# 		REF_image_gray_resized = cv2.resize(REF_image_gray, (100, 60))

	# 		#REF_image_gray_normalized_resized_histeq = cv2.equalizeHist(REF_image_gray_normalized_resized)
	# 		REF_image_gray_resized_histeq = cv2.equalizeHist(REF_image_gray_resized)

	#  		# CALCULATE THE MEAN ABS DIFFERENCE OF REF&QRY

	#  		difference_img = cv2.absdiff(QRY_image_gray_resized_histeq, REF_image_gray_resized_histeq)
	#  		#print "REF array %d" % REF_array
	#  		confusion_matrix[QRY_array, REF_array] = int(difference_img.sum()/(100*60))
	#  		#print "dif sum %d" % int(difference_img.sum()/(100*60))

	#  		REF_image_index = REF_image_index+step
	#  		REF_array = REF_array+1

	#  	REF_array = 0
	#  	QRY_image_index = QRY_image_index+step
	#  	QRY_array = QRY_array+1

	# # WRITE CONFUSION MATRIX
	# cv2.imwrite("confusion_matrix.png", confusion_matrix)

	confusion_matrix = cv2.imread("confusion_matrix.png")

	confusion_matrix_gray = cv2.cvtColor(confusion_matrix,cv2.COLOR_BGR2GRAY)

	confusion_length = QRY_forward_END_FRAME/step
	print (len(confusion_matrix_gray)-1)

	bestmatch_array = np.zeros((confusion_length,), dtype=np.int)

	# PERFORM BEST MATCH ANALYSIS
	for idx in range(0, (len(confusion_matrix_gray))):

		# LOCATE INDEX OF MIN VALUE
		best_match_index = FindBestMatch(confusion_matrix_gray, idx)

		# LOAD IN SPECIFIC FORWARD FACING IMAGES
		QRY_image = cv2.imread(QRY_forward_image_set.Folder() + "/" + QRY_forward_image_filenames[idx*step])
		QRY_image_resized = cv2.resize(QRY_image, (600,480))

		REF_image = cv2.imread(REF_forward_image_set.Folder() + "/" + REF_forward_image_filenames[best_match_index*step])
		REF_image_resized = cv2.resize(REF_image, (600, 480))

		# FILL BEST MATCH ARRAY 
		bestmatch_array[idx] = best_match_index
		print idx

		matched_frames = np.hstack((QRY_image_resized,REF_image_resized))

		# # PREVIEW IMAGES TO ENSURE MATCH
		# cv2.imshow( "Matched Frames", matched_frames )
		
		# k = cv2.waitKey(0)

		# if k == 27:         # wait for ESC key to exit
		# 	cv2.destroyAllWindows()

	# PERFORM SURFACE IMAGE POSE ESTIMATION
	for image_index in range(0, (len(bestmatch_array))):

		# LOAD IN SPECIFIC SURFACE IMAGES
		QRY_surface_image = cv2.imread(QRY_surface_image_set.Folder() + "/" + QRY_surface_image_filenames[idx*step])
		QRY_surface_image_resized = cv2.resize(QRY_surface_image, (600,480))

		REF_surface_image = cv2.imread(REF_surface_image_set.Folder() + "/" + REF_surface_image_filenames[best_match_index*step])
		REF_surface_image_resized = cv2.resize(REF_surface_image, (600, 480))

		# GET TEMPLATE REGION AND IMAGE
		im_height, im_width = QRY_surface_image_resized.shape[:2]
		template_region = GetTemplateRegion(TEMPLATE_SIZE, im_width, im_height)
		template = previous_image[template_region[1]:template_region[1]+template_region[3], template_region[0]:template_region[0]+template_region[2]]

		# GET PREDICTION REGION AND IMAGE
		prediction_region = [0, 0, im_height, im_width]
		prediction_region_image = REF_surface_image_resized

		# GET MATCHED REGION RECTANGLE LOCATION
		rect_loc = [0,0]
		rect_loc[0] = max_loc[0]
		rect_loc[1] = max_loc[1]

		# VISUALIZATIONS
		VisualOdometryVisualizations(current_image, previous_image, template_region)

	

