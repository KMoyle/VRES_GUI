## BSD 2-Clause License
# 
# Copyright (c) 2018, Kyle Moyle All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
# 
# Redistributions of source code must retain the above copyright notice, this
#  list of conditions and the following disclaimer.
# 
# Redistributions in binary form must reproduce the above copyright notice, this
#  list of conditions and the following disclaimer in the documentation and/or
#  other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. 
##

import numpy as np
import imageio
import subprocess
import sys
import wave 
import struct
import cv2
import matplotlib
import matplotlib.pyplot as plt
import Tkinter as Tk
import PIL
from PIL import ImageTk, Image
from datetime import datetime, timedelta
import soundfile as sf 

from numpy import arange
import IDME    
import os.path 
import sys
from tkFileDialog import *
from tkMessageBox import *
from datetime import datetime

#################################
####### GENERIC FUNCTIONS #######
#################################

def GetParameterValue(parameter_set, parameter_name):
	parameter_value = parameter_set.GetParameterValue(parameter_name)
	if parameter_value == None:
		print "The Parameter %s could not be found within the parameter set %s."%(parameter_name, parameter_set.Name())
		exit()
	return parameter_value

def PrepareImage(imageset,filename):
	pil_image = Image.open(imageset.Folder() + "/" + filename)
	width_org, height_org = pil_image.size
	# set the resizing factor so the aspect ratio is retained
	factor = 0.20
	width = int(width_org * factor)
	height = int(height_org * factor)
	pil_image2 = pil_image.resize((width, height), Image.ANTIALIAS)
	frametk2 = ImageTk.PhotoImage(pil_image2)
	return frametk2

def GetImageSetNames(dataset):
	image_set_names = []
	for ii in range(0, dataset.NumberOfImageSets()):
		image_set_names.append(dataset.GetImageSet(ii).Name())
	return image_set_names
# RETURN THE INDEX OF THE MINIMUM VALUE IN CONFUSION MATRIX
def FindBestMatch(confusion_matrix, index):
	min_index = np.argmin(confusion_matrix[index, : ])
	return min_index

# UPDATES ANALYSIS FILE AFTER EVERY ITERATION
def UpdateAnalysisFile(analysis_file, filenames, x_map, y_map, theta_map, ref_forwad_filename, ref_surface_filename):

	# SET MATCHING REF FORWARD IMAGE IN ANALYSIS FILE
	error1 = analysis_file.SetAnalysisValue(filenames, "REF_forward_image", ref_forwad_filename)
	if error1 != IDME.IDME_OKAY:
		print "WARNING! Was unable to set the Forward REF Filename for image %s to %s. Error Code %d"%(filename, ref_forwad_filename, error1)

	# SET MATCHING REF DOWNFACING IMAGE IN ANALYSIS FILE
	error2 = analysis_file.SetAnalysisValue(filenames, "REF_surface_image", ref_surface_filename)
	if error2 != IDME.IDME_OKAY:
		print "WARNING! Was unable to set the Surface REF Filename for image %s to %s. Error Code %d"%(filename, ref_surface_filename, error2)

	# SET POSITION IN REFERENCE MAP IN ANALYSIS FILE
	error3 = analysis_file.SetAnalysisValue(filenames, "position_in_reference_map", (x_map, y_map))
	if error3 != IDME.IDME_OKAY:
		print "WARNING! Was unable to set the Position for image %s to (%d, %d). Error Code %d"%(filename, x_map, y_map, error3)


# UTILISES TIMESTAMP DATA TO RETRIEVE CORRESPONDING IMAGE INDEX
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

# RETURNS SPECIFIC PARAMETER VALUE 
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


# MAIN GUI THAT ALLOWS THE USER TO SELECT A DATASET AND ACCOMPANING IMAGE SETS
class ProgramOptionSelectionGUI():
	def __init__(self):

		# TK ROOT GUI
		self.root_gui = Tk.Tk()
		self.root_gui.wm_title('Program Option Selection')
		self.root_gui.protocol('WM_DELETE_WINDOW', self.CloseGUI)

		# VARIABLES
		self.dataset_file_path = ''
		self.parameter_file_path = ''
		self.image_set_to_use = ''
		self.program_options_valid = False
		self.map_preprocessing = Tk.BooleanVar()		

		# INIT GUI WIDGETS
		self.select_dataset_button = Tk.Button(self.root_gui, text='Select Dataset File', command=self.SelectDatasetFile)
		self.select_dataset_button.grid(row=0, column=0, sticky=Tk.W+Tk.E)

		self.dataset_file_label = Tk.Label(self.root_gui, text='<Please Select a Dataset File>', bg='#bbb')
		self.dataset_file_label.grid(row=0, column=1, sticky=Tk.W+Tk.E)

		self.select_parameter_button = Tk.Button(self.root_gui, text='Select Parameter File', command=self.SelectParameterFile)
		self.select_parameter_button.grid(row=1, column=0, sticky=Tk.W+Tk.E)

		self.parameter_file_label = Tk.Label(self.root_gui, text='<Please Select a Parameter File>', bg='#bbb')
		self.parameter_file_label.grid(row=1, column=1, sticky=Tk.W+Tk.E)

		self.forward_image_set_label_1 = Tk.Label(self.root_gui, text='Select Forward Facing Image Set: ')
		self.forward_image_set_label_1.grid(row=2, column=0, columnspan=2, sticky=Tk.W+Tk.E)

		self.forward_image_set_listbox_1 = Tk.Listbox(self.root_gui, exportselection=0, selectmode=Tk.SINGLE, state=Tk.NORMAL, bg='#bbb')
		self.forward_image_set_listbox_1.grid(row=3, column=0, columnspan=2, sticky=Tk.W+Tk.E)

		self.surface_image_set_label_2 = Tk.Label(self.root_gui, text='Select Surface Facing Image Set:')
		self.surface_image_set_label_2.grid(row=4, column=0, columnspan=2, sticky=Tk.W+Tk.E)

		self.surface_image_set_listbox_2 = Tk.Listbox(self.root_gui, exportselection=0, selectmode=Tk.SINGLE, state=Tk.NORMAL, bg='#bbb')
		self.surface_image_set_listbox_2.grid(row=5, column=0, columnspan=2, sticky=Tk.W+Tk.E)
		
		self.finish_button = Tk.Button(self.root_gui, text='        GO       ', command=self.FinishButton)
		self.finish_button.grid(row=6, column=0, columnspan=2, sticky=Tk.W+Tk.E)

		# START MAINLOOP
		self.root_gui.mainloop()


	def CloseGUI(self):		
		self.root_gui.destroy()
		self.root_gui.quit()


	def SelectDatasetFile(self):
		# get filename and attempt to read it
		filename = askopenfilename(initialdir = '/home/kyle/Desktop/VRES', title='Select Dataset File', filetypes = (("Dataset Files", ("*.yaml","*.xml")), ("All Files", '*.*')))
		self.file_name = os.path.basename(filename)

		if filename:
			try:
				dataset_file = IDME.DatasetFile(filename)
				self.dataset_file_label['text'] = filename
				self.dataset_file_path = filename
			except Exception as e:
				self.dataset_file_label['text'] = '<Please Select a Dataset File>'
				self.dataset_file_path = ''
				showerror("Opening Dataset File", "Failed to open the selected file as a dataset file.\n'%s'"%filename)
				return

		# update image set list boxt
		image_set_names = GetImageSetNames(dataset_file)
		self.UpdateForwardImageSetNames(image_set_names)
		self.UpdateSurfaceImageSetNames(image_set_names)

	def SelectParameterFile(self):
		# get filename and attempt to read it
		map_gen_folder = os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))
		filename = askopenfilename(initialdir = map_gen_folder, title='Select Parameter File', filetypes = (("Parameter Files", ("*.yaml","*.xml")), ("All Files", '*.*')))

		if filename:
			try:
				dataset_file = IDME.ParameterFile(filename)
				self.parameter_file_label['text'] = filename
				self.parameter_file_path = filename
			except Exception as e:
				self.parameter_file_label['text'] = '<Please Select a Parameter File>'
				self.parameter_file_path = ''
				showerror("Opening Parameter File", "Failed to open the selected file as a parameter file.\n'%s'"%filename)


	def UpdateForwardImageSetNames(self, image_set_names):
		if len(image_set_names) != 0:
			self.forward_image_set_listbox_1['state'] = Tk.NORMAL
			self.forward_image_set_listbox_1['bg'] = '#fff'

		self.forward_image_set_listbox_1.delete(0, Tk.END)
		for image_set in image_set_names:
			self.forward_image_set_listbox_1.insert(Tk.END, image_set)
	
	def UpdateSurfaceImageSetNames(self, image_set_names):
		if len(image_set_names) != 0:
			self.surface_image_set_listbox_2['state'] = Tk.NORMAL
			self.surface_image_set_listbox_2['bg'] = '#fff'

		self.surface_image_set_listbox_2.delete(0, Tk.END)
		for image_set in image_set_names:
			self.surface_image_set_listbox_2.insert(Tk.END, image_set)


	def FinishButton(self):
		if len(self.dataset_file_path) == 0:
			showerror("Dataset File", "Please select a dataset.\n")
			return
		if len(self.parameter_file_path) == 0:
			showerror("Parameter File", "Please select a parameter file to use.\n")
			return

		if self.forward_image_set_listbox_1.curselection() != ():
			self.image_set_to_use_1 = self.forward_image_set_listbox_1.get(self.forward_image_set_listbox_1.curselection())

		if self.surface_image_set_listbox_2.curselection() != ():
			self.image_set_to_use_2 = self.surface_image_set_listbox_2.get(self.surface_image_set_listbox_2.curselection())

		if len(self.image_set_to_use_1) == 0:
			showerror("Dataset File", "Please select an image set to use.\n")
			return

		elif len(self.image_set_to_use_2) == 0:
			showerror("Dataset File", "Please select an image set to use.\n")
			return
		
		self.program_options_valid = True

		self.CloseGUI()

# MATCHED IMAGE GUI LOADS THE MATCHED IMAGES INTO A DISPLAY WINDOW ALLOWING THE USER TO VISUALLY CHECK THEY MATCH
class MatchedImagesGUI:
	def __init__(self,imageset1, filename1, imageset2, filename2):

		self.root = Tk.Tk()

		self.master = self.root
		self.master.wm_title('Matched Image Comparison')


		frametk1 = PrepareImage(imageset1, filename1)
		frametk2 = PrepareImage(imageset2, filename2)

		# INIT GUI WIDGETS
		self.YES_button = Tk.Button(self.master, text='YES', command=self.YES)
		self.YES_button.grid(row=1, column=2, columnspan=2, sticky=Tk.W+Tk.E)

		self.NO_button = Tk.Button(self.master, text='NO', command=self.NO)
		self.NO_button.grid(row=2, column=2, columnspan=2, sticky=Tk.W+Tk.E)

		#setting the initial loaded frame
		self.imageframe_1 = Tk.Frame(self.master)
		self.imageframe_1.grid(row=0, column=0, columnspan=6)


		self.label1 = Tk.Label(self.imageframe_1,image=frametk1)
		self.label1.grid(row=0, column=0,columnspan=3)
		self.label1.image = frametk1 # keep a reference!

		self.label2 = Tk.Label(self.imageframe_1,image=frametk2)
		self.label2.grid(row=0, column=3,columnspan=3)
		self.label2.image = frametk2 # keep a reference!

		# START MAINLOOP
		self.master.mainloop()

	def YES(self):
		self.MATCH = True
		self.CloseGUI()

	def NO(self):
		self.MATCH = False
		self.CloseGUI()

	def CloseGUI(self):		
		self.master.destroy()
		self.master.quit()

# STEP SIZE GUI RETRIVES STEP SIZE SELECTION FROM USER
class StepSizeGUI:
	def __init__(self):

		self.root = Tk.Tk()

		self.step_size_label = Tk.Label(self.root, text='Enter Step Size')
		self.step_size_label.grid(row=0, column=0, sticky=Tk.W+Tk.E)

		self.step_size_entry = Tk.Entry(self.root)
		self.step_size_entry.grid(row=1, column=0, sticky=Tk.W+Tk.E)
		
		self.step_size_set_button= Tk.Button(self.root, text='SET', command=self.set_step_size)
		self.step_size_set_button.grid(row=2, column=0, sticky=Tk.W+Tk.E)

		self.root.mainloop()

	def set_step_size(self):
		self.step_size = self.step_size_entry.get()
		self.CloseGUI()

	def CloseGUI(self):
		self.root.destroy()
		self.root.quit()

if __name__ == "__main__":

	# GET PROGRAM OPTIONS USING GUI
	REF = ProgramOptionSelectionGUI()
	REF_Parameter_File = REF.parameter_file_path
	REF_DATASET_PATH = REF.dataset_file_path
	REF_DATASET_FILE_NAME = REF.file_name
	REF_FORWARD_IMAGE_SET = REF.image_set_to_use_1
	REF_SURFACE_IMAGE_SET = REF.image_set_to_use_2

	# GET PROGRAM OPTIONS USING GUI
	QRY = ProgramOptionSelectionGUI()
	QRY_Parameter_File = QRY.parameter_file_path
	QRY_DATASET_PATH = QRY.dataset_file_path
	QRY_DATASET_FILE_NAME = QRY.file_name
	QRY_FORWARD_IMAGE_SET = QRY.image_set_to_use_1
	QRY_SURFACE_IMAGE_SET = QRY.image_set_to_use_2

	# STEP SIZE GUI
	step = StepSizeGUI()
	step = int(step.step_size)

	# LOAD IN PARAMETER FILE
	parameter_file = IDME.ParameterFile(QRY_Parameter_File)

	# LOAD IN PARMETERS
	SAVE_ANALYSIS = GetParameterValue(parameter_file, "Save_Analysis")
	TEMPLATE_SIZE = GetParameterValue(parameter_file["Template_Matching_Parameters"], "Template_Size")
	GEOMETRIC_PIXEL_SCALE = GetParameterValue(parameter_file["Visual_Odometry_Parameters"], "Geometric_Pixel_Scale")
	X_CAM = GetParameterValue(parameter_file["Visual_Odometry_Parameters"], "X_Cam")
	FILTER_SIZE = GetParameterValue(parameter_file["Visual_Odometry_Parameters"], "Filter_Size")

	# INITIALIZE DATASET FILE, GET IMAGE SET AND IMAGE FILENAMES
	REF_dataset = IDME.DatasetFile(REF_DATASET_PATH)
	REF_surface_image_set = REF_dataset.GetImageSet(REF_SURFACE_IMAGE_SET)
	REF_forward_image_set = REF_dataset.GetImageSet(REF_FORWARD_IMAGE_SET)

	if REF_surface_image_set == None:
		print "Failed to find the REF_surface_image_set within the dataset"
		exit()
	if REF_forward_image_set == None:
		print "Failed to find the REF_forward_image_set within the dataset"
		exit()

	QRY_dataset = IDME.DatasetFile(QRY_DATASET_PATH)
	QRY_surface_image_set = QRY_dataset.GetImageSet(QRY_SURFACE_IMAGE_SET)
	QRY_forward_image_set = QRY_dataset.GetImageSet(QRY_FORWARD_IMAGE_SET)

	if QRY_surface_image_set == None:
		print "Failed to find the QRY_surface_image_set within the dataset"
		exit()
	if QRY_forward_image_set == None:
		print "Failed to find the QRY_forward_image_set within the dataset"
		exit()

	# GET IMAGE SET FILENAMES
	REF_forward_image_filenames = REF_dataset.GetImageFilenames(REF_forward_image_set)
	REF_surface_image_filenames = REF_dataset.GetImageFilenames(REF_surface_image_set)
	QRY_forward_image_filenames = QRY_dataset.GetImageFilenames(QRY_forward_image_set)
	QRY_surface_image_filenames = QRY_dataset.GetImageFilenames(QRY_surface_image_set)

	# GET IMAGE SET ENDFRAME
	REF_surface_END_FRAME = REF_surface_image_set.NumberOfImages()
	REF_forward_END_FRAME = REF_forward_image_set.NumberOfImages()
	QRY_surface_END_FRAME = QRY_surface_image_set.NumberOfImages()
	QRY_forward_END_FRAME = QRY_forward_image_set.NumberOfImages()

	# CREATE RESULTS SAVE DIRECTORY
	REF_PATH = os.path.split(REF_DATASET_PATH)
	QRY_PATH = os.path.split(QRY_DATASET_PATH)

	if SAVE_ANALYSIS:
		REF_results_folder =  REF_PATH[0] + "/Analyses/Mapping_Analysis_" + (str(REF_dataset.NumberOfAnalyses("Mapping_Analysis")))

	if not os.path.exists(REF_results_folder):
		os.makedirs(REF_results_folder)

	# CREATE RESULTS SAVE DIRECTORY
	if SAVE_ANALYSIS:
		QRY_results_folder =  QRY_PATH[0] + "/Analyses/Mapping_Analysis_" + (str(QRY_dataset.NumberOfAnalyses("Mapping_Analysis")))

	if not os.path.exists(QRY_results_folder):
		os.makedirs(QRY_results_folder)

	# INITIALIZE ANALYSIS FILE, COPY PARAMETERS AND METADATA AND ADD VISUAL ODOMETRY FIELD
	REF_analysis_file = IDME.GenericAnalysisFile("Mapping_Analysis", REF_dataset.GetDatasetFileInformation(),REF_SURFACE_IMAGE_SET, QRY_dataset.GetDatasetFileInformation(),QRY_SURFACE_IMAGE_SET, REF_results_folder + "/Mapping_Analysis.yaml" )
	REF_analysis_file.CopyParameterSetFromFile(parameter_file)
	REF_analysis_file.CopyImageSetMetadataFrom(QRY_surface_image_set, [])
	REF_analysis_file.AddAnalysisField("REF_forward_image", IDME.kValidTypes.STRING)
	REF_analysis_file.AddAnalysisField("REF_surface_image", IDME.kValidTypes.STRING)
	REF_analysis_file.AddAnalysisField("position_in_reference_map", IDME.kValidTypes.CV_POINT2d)

	# INITIALIZE ANALYSIS FILE, COPY PARAMETERS AND METADATA AND ADD VISUAL ODOMETRY FIELD
	QRY_analysis_file = IDME.GenericAnalysisFile("Mapping_Analysis", REF_dataset.GetDatasetFileInformation(),REF_SURFACE_IMAGE_SET, QRY_dataset.GetDatasetFileInformation(),QRY_SURFACE_IMAGE_SET, QRY_results_folder + "/Mapping_Analysis.yaml" )
	QRY_analysis_file.CopyParameterSetFromFile(parameter_file)
	QRY_analysis_file.CopyImageSetMetadataFrom(QRY_surface_image_set, [])
	QRY_analysis_file.AddAnalysisField("REF_forward_image", IDME.kValidTypes.STRING)
	QRY_analysis_file.AddAnalysisField("REF_surface_image", IDME.kValidTypes.STRING)
	QRY_analysis_file.AddAnalysisField("position_in_reference_map", IDME.kValidTypes.CV_POINT2d)

	# INITILISE CONFUSION MATRIX PER STEP CHOICE AND INDEX VARIABLES
	confusion_matrix = np.zeros(((QRY_forward_END_FRAME/step),(REF_forward_END_FRAME/step)))
	REF_image_index = 0
	QRY_image_index = 0
	REF_array = 0
	QRY_array = 0

	# MEAN ABSOLUTE DIFFERENCE
	for QRY_image_index in range(0, QRY_forward_END_FRAME - 1, step):
		if QRY_image_index > QRY_forward_END_FRAME:
			break

	 	# GET FIRST REF IMAGE  
	  	QRY_image_gray = cv2.imread(QRY_forward_image_set.Folder() + "/" + QRY_forward_image_filenames[QRY_image_index],cv2.IMREAD_GRAYSCALE)
	  	QRY_image_gray_resized = cv2.resize(QRY_image_gray, (100, 60))
	  	QRY_image_gray_resized_histeq = cv2.equalizeHist(QRY_image_gray_resized)
	  	print "QRY_image_index %d" % QRY_image_index
		
	 	for REF_image_index in range(0, REF_forward_END_FRAME - 1, step):
			if REF_image_index > REF_forward_END_FRAME - 1:
				break

	 	 	# GET FIRST REF IMAGE  
			REF_image_gray = cv2.imread(REF_forward_image_set.Folder() + "/" + REF_forward_image_filenames[REF_image_index],cv2.IMREAD_GRAYSCALE)
	 		REF_image_gray_resized = cv2.resize(REF_image_gray, (100, 60))
	 		REF_image_gray_resized_histeq = cv2.equalizeHist(REF_image_gray_resized)

	  		# CALCULATE THE MEAN ABS DIFFERENCE OF REF&QRY
			difference_img = cv2.absdiff(QRY_image_gray_resized_histeq, REF_image_gray_resized_histeq)
	  		confusion_matrix[QRY_array, REF_array] = int(difference_img.sum()/(100*60))

	  		REF_image_index = REF_image_index+step
	  		REF_array = REF_array + 1

	  	REF_array = 0
	  	QRY_array = QRY_array + 1
	  	QRY_image_index = QRY_image_index+step

	# WRITE CONFUSION MATRIX
	cv2.imwrite("confusion_matrix.png", confusion_matrix)
	confusion_matrix = cv2.imread("confusion_matrix.png")
	confusion_matrix_gray = cv2.cvtColor(confusion_matrix,cv2.COLOR_BGR2GRAY)
	
	# RESIZING LENGTH PER STEP CHOICE & INITIALISE ARRAY FOR BEST MATCHED IMAGES
	confusion_length = QRY_forward_END_FRAME/step
	bestmatch_array = np.zeros((confusion_length,), dtype=np.int)

	# PERFORM BEST MATCH ANALYSIS
	for idx in range(0, (len(confusion_matrix_gray))):

		# LOCATE INDEX OF MIN VALUE
		best_match_index = FindBestMatch(confusion_matrix_gray, idx)

		# LOAD IN SPECIFIC FORWARD FACING IMAGES
		matched_comparaison = MatchedImagesGUI(QRY_forward_image_set,QRY_forward_image_filenames[idx*step],REF_forward_image_set,REF_forward_image_filenames[best_match_index*step]) 	

		# FILL BEST MATCH ARRAY
		if matched_comparaison.MATCH:		 
			bestmatch_array[idx] = best_match_index*step
		else:
			bestmatch_array[idx] = -1


	# INIT VARIABLES
	array_index = 1
	START_FRAME= 0
	END_FRAME= QRY_surface_image_set.NumberOfImages() - 1
	pixel_shift = [0, 0]
	pixel_shift_history = []

	position_estimates = np.zeros((END_FRAME-START_FRAME+1, 3), float)

	for ii in range(0, FILTER_SIZE):
		pixel_shift_history.append([None, None])
	
	# PERFORM SURFACE IMAGE POSE ESTIMATION
	for image_index in range(0, (len(bestmatch_array))):
		idx = bestmatch_array[image_index]
		print "idx= %d" % idx

		if idx >= 0:
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

				# END OF LOOP - UPDATE PREVIOUS IMAGE, UPDATE PIXEL SHIFTS, GET POSITION ESTIMATION, PERFORM POSITION SHIFT MOVING AVERAGING FILTER
				first_iteration = False
				pixel_shift[0] = template_region[0] - rect_loc[0]
				pixel_shift[1] = template_region[1] - rect_loc[1]

				# POSITION ESTIMATES USING PROCESS DEFINED IN NOURANI VISUAL ODOMETRY PAPERS
				delta_x = -pixel_shift[1] * GEOMETRIC_PIXEL_SCALE
				delta_theta = -float(pixel_shift[0])/float(X_CAM) * GEOMETRIC_PIXEL_SCALE

				# REF POSE FROM SELECTED IMAGE
				REF_pose = REF_dataset.GetMetadataValue(REF_surface_image_set, REF_surface_image_filenames[REF_surface_index], "VO_Pos")

				# POSITION IN REFERENCE MAP VARIABLES
				x_position_in_reference_map = REF_pose[0] - delta_x*np.cos(position_estimates[array_index-1, 2])
				y_position_in_reference_map = REF_pose[1] - delta_x*np.sin(position_estimates[array_index-1, 2])
				theta_position_in_reference_map = REF_pose[2] -  delta_theta

				# FILLING ESTIMATE ARRAY
				position_estimates[array_index, 0] =  x_position_in_reference_map 
				position_estimates[array_index, 1] =  y_position_in_reference_map
				position_estimates[array_index, 2] =  theta_position_in_reference_map

				print "x= %.3f" % x_position_in_reference_map
				print "y= %.3f" % y_position_in_reference_map 
				print "theta= %.3f" % theta_position_in_reference_map

				print "QRY_surface_index= %d" % QRY_surface_index
				print "REF_surface_index= %d" % REF_surface_index

				# UPDATING ANALYSIS FILE WITH REF FORWARD/SURFACE FILENAMES AND POSITION IN REFERENCE MAP
				UpdateAnalysisFile(QRY_analysis_file, QRY_surface_image_filenames[QRY_surface_index], x_position_in_reference_map, y_position_in_reference_map, theta_position_in_reference_map, REF_forward_image_filenames[idx], REF_surface_image_filenames[REF_surface_index])
				UpdateAnalysisFile(REF_analysis_file, QRY_surface_image_filenames[QRY_surface_index], x_position_in_reference_map, y_position_in_reference_map, theta_position_in_reference_map, REF_forward_image_filenames[idx], REF_surface_image_filenames[REF_surface_index])
				array_index = array_index + 1
			else:
				break
		else:
			pass

	# WRITING FILES
	QRY_analysis_file.WriteFile()
	REF_analysis_file.WriteFile()
	REF_dataset.AddAnalysis(REF_analysis_file)
	QRY_dataset.AddAnalysis(QRY_analysis_file)
	REF_dataset.WriteFiles()
	QRY_dataset.WriteFiles()

# POSTION PLOTS
fig = plt.figure()
plt.suptitle('Estimated Position')
plt.xlabel('X Position (m)')
plt.ylabel('Y Position (m)')
plt.plot(position_estimates[:-1,0], position_estimates[:-1,1], 'rx')
plt.axis('equal')
plt.show()


	

