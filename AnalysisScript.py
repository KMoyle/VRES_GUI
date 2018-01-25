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

def UpdateAnalysisFile(analysis_file, filename, x_map, y_map, theta_map, ref_forwad_filename, ref_surface_filename):

	#while array_index != image_index 

	# SET VO POSITION IN ANALYSIS FILE
	error1 = analysis_file.SetAnalysisValue(filename, "REF_forward_image", ref_forwad_filename)
	#if error1 != IDME.IDME_OKAY:
		#print "WARNING! Was unable to set the Forward REF Filename for image %s to %s. Error Code %d"%(filename,error1)

	error2 = analysis_file.SetAnalysisValue(filename, "REF_surface_image", ref_surface_filename)
	#if error2 != IDME.IDME_OKAY:
		#print "WARNING! Was unable to set the Surface REF Filename for image %s to %s. Error Code %d"%(filename,error2)

	error3 = analysis_file.SetAnalysisValue(filename, "position_in_reference_map", (x_map, y_map, theta_map))
	#if error3 != IDME.IDME_OKAY:
		#print "WARNING! Was unable to set the Position for image %s to (%d, %d, %d). Error Code %d"%(filename, x_map, y_map, theta_map, error3)

# # SEARCH TIMESTAMP FOR CORRESPONDING FRAME
# QRY_surface_index = GetMatchedIndex(QRY_dataset, QRY_forward_image_set, QRY_surface_image_set, QRY_forward_image_filenames, QRY_surface_image_filenames, "TimeStamp", image_index, step)
# REF_surface_index = GetMatchedIndex(REF_dataset, REF_forward_image_set, REF_surface_image_set, REF_forward_image_filenames, REF_surface_image_filenames, "TimeStamp", idx, step)


def GetMatchedIndex(dataset, current_imageset, search_imageset, current_filenames, search_filenames, metadata_value_name, index):
	metadata_index = 0
	END_FRAME = search_imageset.NumberOfImages() - 1

	if dataset == REF_dataset:
		forward_metadata_value = dataset.GetMetadataValue(current_imageset, current_filenames[index], metadata_value_name)
	elif dataset == QRY_dataset:
		forward_metadata_value = dataset.GetMetadataValue(current_imageset, current_filenames[index], metadata_value_name)

	if forward_metadata_value == None:
		print "The Metadata name %s could not be found within the parameter set %s."%(metadata_value_name, dataset.Name())
		exit()
	
	while metadata_index != END_FRAME:

		surface_metadata_value = dataset.GetMetadataValue(search_imageset, search_filenames[metadata_index], metadata_value_name)

		if surface_metadata_value == forward_metadata_value:
			break

		metadata_index += 1

	return metadata_index 

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


	template_region[0] = int(float(image_width)/2.0 - float(template_region[2])/2.0) + pixel_shift[0]
	template_region[1] = int(float(image_height)/2.0 - float(template_region[3])/2.0) + pixel_shift[1]

	template_region[0] = min(max(template_region[0], 0), image_width - template_region[2])
	template_region[1] = min(max(template_region[1], 0), image_height - template_region[3])

	return template_region


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
	REF_DATASET_PATH = '/home/kylesm/Desktop/VRES/VRES_GUI/REF/'
	REF_DATASET_FILE_NAME = 'REF_dataset.yaml'
	REF_SURFACE_IMAGE_SET = "REF_surface_images"
	REF_FORWARD_IMAGE_SET = "REF_forward_images"

	QRY_DATASET_PATH = '/home/kylesm/Desktop/VRES/VRES_GUI/QRY/'
	QRY_DATASET_FILE_NAME = 'QRY_dataset.yaml'
	QRY_SURFACE_IMAGE_SET = "QRY_surface_images"
	QRY_FORWARD_IMAGE_SET = "QRY_forward_images"

	# LOAD IN PARAMETER FILE
	PARAMETER_FILE = '/home/kylesm/Desktop/VRES/map_generation/ParameterFile.yaml'
	parameter_file = IDME.ParameterFile(PARAMETER_FILE)

	# LOAD IN PARMETERS
	SAVE_ANALYSIS = GetParameterValue(parameter_file, "Save_Analysis")
	TEMPLATE_SIZE = GetParameterValue(parameter_file["Template_Matching_Parameters"], "Template_Size")
	GEOMETRIC_PIXEL_SCALE = GetParameterValue(parameter_file["Visual_Odometry_Parameters"], "Geometric_Pixel_Scale")
	X_CAM = GetParameterValue(parameter_file["Visual_Odometry_Parameters"], "X_Cam")
	FILTER_SIZE = GetParameterValue(parameter_file["Visual_Odometry_Parameters"], "Filter_Size")

	# INITIALIZE DATASET FILE, GET IMAGE SET AND IMAGE FILENAMES
	REF_dataset = IDME.DatasetFile(REF_DATASET_PATH + REF_DATASET_FILE_NAME)
	REF_surface_image_set = REF_dataset.GetImageSet(REF_SURFACE_IMAGE_SET)
	REF_forward_image_set = REF_dataset.GetImageSet(REF_FORWARD_IMAGE_SET)

	if REF_surface_image_set == None:
		print "Failed to find the REF_surface_image_set within the dataset"
		exit()
	if REF_forward_image_set == None:
		print "Failed to find the REF_forward_image_set within the dataset"
		exit()

	print QRY_DATASET_PATH + QRY_DATASET_FILE_NAME

	QRY_dataset = IDME.DatasetFile(QRY_DATASET_PATH + QRY_DATASET_FILE_NAME)
	QRY_surface_image_set = QRY_dataset.GetImageSet(QRY_SURFACE_IMAGE_SET)
	QRY_forward_image_set = QRY_dataset.GetImageSet(QRY_FORWARD_IMAGE_SET)

	if QRY_surface_image_set == None:
		print "Failed to find the QRY_surface_image_set within the dataset"
		exit()
	if QRY_forward_image_set == None:
		print "Failed to find the QRY_forward_image_set within the dataset"
		exit()

	#if image_set == None:
	#	print "Failed to find the image set within the dataset"
	#	exit()
	print 

	REF_forward_image_filenames = REF_dataset.GetImageFilenames(REF_forward_image_set)
	REF_surface_image_filenames = REF_dataset.GetImageFilenames(REF_surface_image_set)

	QRY_forward_image_filenames = QRY_dataset.GetImageFilenames(QRY_forward_image_set)
	QRY_surface_image_filenames = QRY_dataset.GetImageFilenames(QRY_surface_image_set)

	# GET IMAGE SET ENDFRAME
	REF_surface_END_FRAME = REF_surface_image_set.NumberOfImages()
	REF_forward_END_FRAME = REF_forward_image_set.NumberOfImages()

	QRY_surface_END_FRAME = QRY_surface_image_set.NumberOfImages()
	QRY_forward_END_FRAME = QRY_forward_image_set.NumberOfImages()

	step = 30
	# PERFORM VISUAL ODOMETRY	
	START_FRAME = 0
	END_FRAME = 1198
	REF_image_index = 0
	QRY_image_index = 0

	REF_forward_START_FRAME = 0
	REF_array = 0
	QRY_array = 0

	# CREATE RESULTS SAVE DIRECTORY
	#REF_results_folder = REF_DATASET_PATH + "/Analyses"
	if SAVE_ANALYSIS:
		REF_results_folder =  REF_DATASET_PATH + "/Analyses/Mapping_Analysis_" + str(REF_dataset.NumberOfAnalyses("Mapping_Analysis"))

	if not os.path.exists(REF_results_folder):
		os.makedirs(REF_results_folder)

	# CREATE RESULTS SAVE DIRECTORY
	#QRY_results_folder = QRY_DATASET_PATH + "/Analyses"
	if SAVE_ANALYSIS:
		QRY_results_folder =  QRY_DATASET_PATH + "/Analyses/Mapping_Analysis_" + str(QRY_dataset.NumberOfAnalyses("Mapping_Analysis"))

	if not os.path.exists(QRY_results_folder):
		os.makedirs(QRY_results_folder)

	# INITIALIZE ANALYSIS FILE, COPY PARAMETERS AND METADATA AND ADD VISUAL ODOMETRY FIELD
	REF_analysis_file = IDME.GenericAnalysisFile("Mapping_Analysis", REF_dataset.GetDatasetFileInformation(),REF_SURFACE_IMAGE_SET, QRY_dataset.GetDatasetFileInformation(),QRY_SURFACE_IMAGE_SET, REF_results_folder + "/Mapping_Analysis.yaml" )
	REF_analysis_file.CopyParameterSetFromFile(parameter_file)
	REF_analysis_file.CopyImageSetMetadataFrom(QRY_surface_image_set, [])
	REF_analysis_file.AddAnalysisField("REF_forward_image", IDME.kValidTypes.STRING)
	REF_analysis_file.AddAnalysisField("REF_surface_image", IDME.kValidTypes.STRING)
	REF_analysis_file.AddAnalysisField("position_in_reference_map", IDME.kValidTypes.CV_POINT3d)

	# INITIALIZE ANALYSIS FILE, COPY PARAMETERS AND METADATA AND ADD VISUAL ODOMETRY FIELD
	QRY_analysis_file = IDME.GenericAnalysisFile("Mapping_Analysis", REF_dataset.GetDatasetFileInformation(),REF_SURFACE_IMAGE_SET, QRY_dataset.GetDatasetFileInformation(),QRY_SURFACE_IMAGE_SET, QRY_results_folder + "/Mapping_Analysis.yaml" )
	QRY_analysis_file.CopyParameterSetFromFile(parameter_file)
	QRY_analysis_file.CopyImageSetMetadataFrom(QRY_surface_image_set, [])
	QRY_analysis_file.AddAnalysisField("REF_forward_image", IDME.kValidTypes.STRING)
	QRY_analysis_file.AddAnalysisField("REF_surface_image", IDME.kValidTypes.STRING)
	QRY_analysis_file.AddAnalysisField("position_in_reference_map", IDME.kValidTypes.CV_POINT3d)

	# confusion_matrix = np.zeros(((QRY_forward_END_FRAME/step),(REF_forward_END_FRAME/step)))

	# for QRY_image_index in range(0, QRY_forward_END_FRAME - 1, step):

	# 	if QRY_image_index > QRY_forward_END_FRAME:
	# 		break

	# 	#print "qry index %d" % QRY_image_index
	# 	# GET FIRST REF IMAGE  
	#  	QRY_image_gray = cv2.imread(QRY_forward_image_set.Folder() + "/" + QRY_forward_image_filenames[QRY_image_index],cv2.IMREAD_GRAYSCALE)
	#  	#QRY_image_gray = cv2.cvtColor(QRY_image,cv2.COLOR_BGR2GRAY)
	#  	#cv2.imshow( "Display window", QRY_image_gray )
	#  	#QRY_image_gray_normalized = cv2.normalize(QRY_image_gray.astype('float'), None, 0.0, 1.0, cv2.NORM_MINMAX)
	#  	QRY_image_gray_resized = cv2.resize(QRY_image_gray, (100, 60))
	#  	#QRY_image_gray_normalized_resized_histeq = cv2.equalizeHist(QRY_image_gray_normalized_resized)
	#  	QRY_image_gray_resized_histeq = cv2.equalizeHist(QRY_image_gray_resized)
	#  	print "QRY_image_index %d" % QRY_image_index

	# 	#print ""
		
	# 	for REF_image_index in range(0, REF_forward_END_FRAME - 1, step):
	# 		#print "ref index %d" % REF_image_index

	# 	 	# GET FIRST REF IMAGE  
	# 		REF_image_gray = cv2.imread(REF_forward_image_set.Folder() + "/" + REF_forward_image_filenames[REF_image_index],cv2.IMREAD_GRAYSCALE)
	# 		#REF_image_gray = cv2.cvtColor(REF_image,cv2.COLOR_BGR2GRAY)
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

	# WRITE CONFUSION MATRIX
	#cv2.imwrite("confusion_matrix.png", confusion_matrix)

	confusion_matrix = cv2.imread("confusion_matrix.png")

	confusion_matrix_gray = cv2.cvtColor(confusion_matrix,cv2.COLOR_BGR2GRAY)

	confusion_length = QRY_forward_END_FRAME/step

	#print (len(confusion_matrix_gray)-1)

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
		bestmatch_array[idx] = best_match_index*step
		matched_frames = np.hstack((QRY_image_resized,REF_image_resized))

		# # PREVIEW IMAGES TO ENSURE MATCH
		# cv2.imshow( "Matched Frames", matched_frames )
		
		# k = cv2.waitKey(0)

		# if k == 27:         # wait for ESC key to exit
		# 	cv2.destroyAllWindows()

	# INIT VARIABLES
	pixel_shift = [0, 0]
	pixel_shift_history = []
	for ii in range(0, FILTER_SIZE):
		pixel_shift_history.append([None, None])
	position_estimates = np.zeros((END_FRAME-START_FRAME+1, 3), float)

	SURFACE_FRAME_COUNT = (QRY_surface_image_set.NumberOfImages())/step

	#print SURFACE_FRAME_COUNT
	array_index = 0
	# PERFORM SURFACE IMAGE POSE ESTIMATION
	for image_index in range(0, (len(bestmatch_array))):
		idx = bestmatch_array[image_index]


		QRY_index = image_index * step

		# SEARCH TIMESTAMP FOR CORRESPONDING FRAME
		QRY_surface_index = GetMatchedIndex(QRY_dataset, QRY_forward_image_set, QRY_surface_image_set, QRY_forward_image_filenames, QRY_surface_image_filenames, "TimeStamp", QRY_index)
		REF_surface_index = GetMatchedIndex(REF_dataset, REF_forward_image_set, REF_surface_image_set, REF_forward_image_filenames, REF_surface_image_filenames, "TimeStamp", idx)
		
		if (QRY_surface_index < (QRY_surface_image_set.NumberOfImages() - 2)) and (REF_surface_index < (REF_surface_image_set.NumberOfImages()- 2)):
			# LOAD IN SPECIFIC SURFACE IMAGES
			QRY_surface_image = cv2.imread(QRY_surface_image_set.Folder() + "/" + QRY_surface_image_filenames[QRY_surface_index], cv2.IMREAD_GRAYSCALE)
			REF_surface_image = cv2.imread(REF_surface_image_set.Folder() + "/" + REF_surface_image_filenames[REF_surface_index], cv2.IMREAD_GRAYSCALE)

			# GET TEMPLATE REGION AND IMAGE
			im_height, im_width = QRY_surface_image.shape[:2]
			template_region = GetTemplateRegion(TEMPLATE_SIZE, im_width, im_height)
			template = QRY_surface_image[template_region[1]:template_region[1]+template_region[3], template_region[0]:template_region[0]+template_region[2]]
			
			# GET PREDICTION REGION AND IMAGE
			prediction_region = [0, 0, im_height, im_width]
			prediction_region_image = REF_surface_image
			
			# PERFORM TEMPLATE MATCHING
			match_result = cv2.matchTemplate(prediction_region_image, template, cv2.TM_CCOEFF_NORMED)
			min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match_result)

			# GET MATCHED REGION RECTANGLE LOCATION
			rect_loc = [0,0]
			rect_loc[0] = max_loc[0]
			rect_loc[1] = max_loc[1]

			# VISUALIZATIONS
			#VisualOdometryVisualizations(REF_surface_image, QRY_surface_image, template_region)

			# END OF LOOP - UPDATE PREVIOUS IMAGE, UPDATE PIXEL SHIFTS, GET POSITION ESTIMATION, PERFORM POSITION SHIFT MOVING AVERAGING FILTER
			first_iteration = False
			pixel_shift[0] = template_region[0] - rect_loc[0]
			pixel_shift[1] = template_region[1] - rect_loc[1]

			pixel_shift_history = pixel_shift_history[-1:] + pixel_shift_history[:-1]
			pixel_shift_history[0][0] = pixel_shift[0]
			pixel_shift_history[0][1] = pixel_shift[1]

			# POSITION ESTIMATES USING PROCESS DEFINED IN NOURANI VISUAL ODOMETRY PAPERS
			delta_x = -pixel_shift[1] * GEOMETRIC_PIXEL_SCALE
			delta_theta = -float(pixel_shift[0])/float(X_CAM) * GEOMETRIC_PIXEL_SCALE

			position_estimates[array_index, 2] =  delta_theta
			position_estimates[array_index, 0] =  delta_x*np.cos(position_estimates[array_index-1, 2]) 
			position_estimates[array_index, 1] =  delta_x*np.sin(position_estimates[array_index-1, 2])

			REF_pose = REF_dataset.GetMetadataValue(REF_surface_image_set, REF_surface_image_filenames[REF_surface_index], "VO_Pos")

			x_position_in_reference_map = REF_pose[0] - position_estimates[array_index, 0]
			y_position_in_reference_map = REF_pose[1] - position_estimates[array_index, 1]
			theta_position_in_reference_map = REF_pose[2] - position_estimates[array_index, 2]

			print "x= %.3f" % x_position_in_reference_map
			print "y= %.3f" % y_position_in_reference_map 
			print "theta= %.3f" % theta_position_in_reference_map

			#def UpdateAnalysisFile(analysis_file, filename, x_map, y_map, theta_map)
			UpdateAnalysisFile(QRY_analysis_file, QRY_surface_image_filenames[QRY_surface_index], x_position_in_reference_map, y_position_in_reference_map, theta_position_in_reference_map, REF_forward_image_filenames[idx], REF_surface_image_filenames[REF_surface_index],QRY_surface_index,)
			UpdateAnalysisFile(REF_analysis_file, QRY_surface_image_filenames[QRY_surface_index], x_position_in_reference_map, y_position_in_reference_map, theta_position_in_reference_map, REF_forward_image_filenames[idx], REF_surface_image_filenames[REF_surface_index],QRY_surface_index)

		else:
			break
		#raw_input("press enter")
	
	QRY_analysis_file.WriteFile()
	REF_analysis_file.WriteFile()
	REF_dataset.AddAnalysis(REF_analysis_file)
	QRY_dataset.AddAnalysis(QRY_analysis_file)
	REF_dataset.WriteFiles()
	QRY_dataset.WriteFiles()



	

