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
from PIL import Image, ImageTk
from scipy.io import wavfile as wav
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

imageio.plugins.ffmpeg.download()
matplotlib.use('TkAgg')

# INITIAL INTERFACE, CREATES DATASET AND IMPORTS TWO VIDEO FILES FOR ANALYSES
class Dataset_Initialisation_GUI:
	def __init__(self, master):
	
		# TKINTER WIDGES
		self.master = master
		self.master.title("Dataset Creation")
		self.master.protocol("WM_DELETE_WINDOW", self.OnClosing)

		# MENU
		self.menubar = Menu(self.master)
		self.filemenu = Menu(self.menubar, tearoff=0)
		self.filemenu.add_command(label="New", command=self.NewFile)
		self.filemenu.add_command(label="Save", command=self.SaveFile)
		self.filemenu.add_command(label="Save as...", command=self.SaveFileAs)
		self.filemenu.add_command(label="Close", command=self.CloseFile)
		self.filemenu.add_separator()
		self.filemenu.add_command(label="Exit", command=self.OnClosing)
		self.menubar.add_cascade(label="File", menu=self.filemenu)
		self.master["menu"] = self.menubar

		# INIT GUI
		self.dataset_info_label = Label(self.master, text = "Dataset Information:") 
		self.dataset_info_label.grid(row=0, column=0, columnspan=2)

		self.dataset_name_label = Label(self.master, text = "Dataset Name:") 
		self.dataset_name_label.grid(row=1, column=0)
		self.dataset_name_entry = Entry(self.master)
		self.dataset_name_entry.grid(row=1, column=1, sticky=W+E)

		self.dataset_area_label = Label(self.master, text = "Dataset Area:") 
		self.dataset_area_label.grid(row=2, column=0)
		self.dataset_area_entry = Entry(self.master)
		self.dataset_area_entry.grid(row=2, column=1, sticky=W+E)

		self.dataset_datetime_label = Label(self.master, text = "Dataset Date Time:") 
		self.dataset_datetime_label.grid(row=3, column=0)
		self.dataset_datetime_entry = Entry(self.master)
		self.dataset_datetime_entry.grid(row=3, column=1, sticky=W+E)

		self.video_1_open_button = Button(self.master, text = "Select Forward Facing Video",command=lambda: self.SelectVideoFile("forward_facing_video_file"))
		self.video_1_open_button.grid(row=5, column=0,sticky=W+E)

		self.video_1_file_label = Label(self.master, text='<Please Select a video File>', bg='#bbb')
		self.video_1_file_label.grid(row=5, column=1, sticky=W+E)

		self.video_2_open_button = Button(self.master, text = "Select Surface Facing Video",command=lambda: self.SelectVideoFile("surface_facing_video_file"))
		self.video_2_open_button.grid(row=6, column=0, sticky=W+E)

		self.video_2_file_label = Label(self.master, text='<Please Select a video File>', bg='#bbb')
		self.video_2_file_label.grid(row=6, column=1, sticky=W+E)

		#go to visualisation gui
		self.go_to_vis_gui_button = Button(self.master, text= "Go To Visualisation", state=DISABLED, command=self.GoToVisualisation)
		self.go_to_vis_gui_button.grid(row=7, column=0, columnspan=2)

		self.save_and_update_button = Button(self.master, text= "Save Dataset and Update Metadata",state=DISABLED, command=self.SaveAndUpdate)
		self.save_and_update_button.grid(row=9, column=0, columnspan=2)

		# VARIABLES
		self.dataset_file = None

	# SETS TIMESTAMPS OF NEW VIDEO FILE
	def SetTimeStamps(self, dataset, image_set, start_time, fps, t_zero_frame):

		# Get image set and add timestamp metadata field
		image_set = self.dataset_file.GetImageSet(image_set)
		NUM_FRAMES = image_set.NumberOfImages() 

		if image_set == None:
			print "Failed to get %s image set"%image_set
			exit()
		self.dataset_file.AddMetadataField(image_set, 'TimeStamp', IDME.kValidTypes.DATE_TIME)

		# set values based on start time and fps
		image_names = self.dataset_file.GetImageFilenames(image_set)
		for ii, filename in enumerate(image_names):
			additional_seconds = ((ii-int(t_zero_frame))/float(fps))
			current_time = start_time + timedelta(seconds=additional_seconds)
			if self.dataset_file.SetMetadataValue(image_set, filename, "TimeStamp", current_time) != IDME.IDME_OKAY:
				print "Error could not set <filename> timestamp to <value>"

	# ADDS IMAGE SETS AND ACCOMPANYING METADATA TO NEWLY CREATED DATASET
	def GenerateDataset(self):

		START_TIME = datetime.now()

		self.dataset_file.AddImageSet(self.dataset_file.name + '_forward_images', '/home/kyle/Desktop/VRES/REF/'+ self.dataset_file.name + '_forward_facing_images', '/home/kyle/Desktop/VRES/REF/'+ self.dataset_file.name + '_forward_images_meta.yaml')
		self.dataset_file.AddImageSet(self.dataset_file.name + '_surface_images', '/home/kyle/Desktop/VRES/REF/'+ self.dataset_file.name + '_surface_facing_images','/home/kyle/Desktop/VRES/REF/'+ self.dataset_file.name + '_surface_images_meta.yaml')

		self.meta_1 = IDME.MetadataFile('/home/kyle/Desktop/VRES/REF/'+ self.dataset_file.name + '_forward_images_meta.yaml')
		self.meta_2 = IDME.MetadataFile('/home/kyle/Desktop/VRES/REF/'+ self.dataset_file.name + '_surface_images_meta.yaml')

		self.SetTimeStamps(self.dataset_file, self.dataset_file.name + '_forward_images', START_TIME, self.CAMERA_1_FPS, self.forward_facing_initial)
		self.SetTimeStamps(self.dataset_file, self.dataset_file.name + '_surface_images', START_TIME, self.CAMERA_2_FPS, self.surface_facing_initial)

		self.dataset_file.WriteFiles()

	# INITILISES NEW DATASET INFORMATION
	def SaveAndUpdate(self):

		self.SaveFileAs()
		self.GenerateDataset()

		self.master.destroy()
		self.master.quit()

	# LOADS IN SELECTED FORWARD AND DOWNWARD VIDEO FILES
	def SelectVideoFile(self, vid_name):
		# get filename and attempt to read it
		map_gen_folder = "/home/kyle/Desktop/VRES/"
		filename = askopenfilename(initialdir = map_gen_folder, title='Select Video File', filetypes = (("Video Files", ("*.MTS","*.mov","*.avi")), ("All Files", '*.*')))

		print filename
		if vid_name == "forward_facing_video_file":
			if filename:
				try:
					self.video_1_file_label['text'] = filename
					self.forward_facing_file_path = filename
				except Exception as e:
					self.video_1_file_label['text'] = '<Please Select a Dataset File>'
					self.video_1_file_path = ''
					showerror("Opening Dataset File", "Failed to open the selected file as a dataset file.\n'%s'"%filename)
					return

		elif vid_name == "surface_facing_video_file":
			if filename:
				try:
					self.video_2_file_label['text'] = filename
					self.surface_facing_file_path = filename
				except Exception as e:
					self.video_2_file_label['text'] = '<Please Select a Dataset File>'
					self.video_2_file_path = ''
					showerror("Opening Dataset File", "Failed to open the selected file as a dataset file.\n'%s'"%filename)
					return

	# OPENS VISUALISATION GUI AND INITIALISES CAMERA DATA
	def GoToVisualisation(self):
		self.UpdateDatasetInformation()
		self.gui_window = Toplevel(self.master)

		# VISUALISATION GUI
		v = CameraLocGUI(self.gui_window, self.dataset_file.name, self.forward_facing_file_path, self.surface_facing_file_path)

		self.forward_facing_initial = int(v.forward_facing_initial_frame)
		self.surface_facing_initial = int(v.surface_facing_initial_frame)
		self.CAMERA_1_FPS = v.ONE_fps
		self.CAMERA_2_FPS = v.TWO_fps
		self.Do_Pose = v.pose 

		self.save_and_update_button['state'] = 'normal'

	def CheckForUnsavedChanges(self):
		self.UpdateDatasetInformation()
		if self.dataset_file != None and self.dataset_file.ChangesSavedToDisk() == False:
			if askquestion("Save Changes", "Would you like to save changes to the currently opened dataset file?", icon='warning') == 'yes':
				if len(self.dataset_file.file_path) == 0:
					return self.SaveFileAs()
				else:
					return self.SaveFile()

		return True

	def NewFile(self):
		if self.CheckForUnsavedChanges() == False:
			return

		self.dataset_file = IDME.DatasetFile()		
		self.UpdateControlsAndLabels()

	def SaveFile(self):
		self.UpdateDatasetInformation()
		if len(self.dataset_file.file_path) == 0:
			return self.SaveFileAs()

		error = self.dataset_file.WriteFiles()
		if self.dataset_file.WriteFiles() != IDME.IDME_OKAY:
			showerror("Save Dataset File", "Failed to save dataset file \n'%s'\nError Code (%d)"%(self.dataset_file.file_path, error))
			return False
		else:
			self.UpdateControlsAndLabels()
			return True

	
	def SaveFileAs(self):
		# get filename and attempt to save/create it
		filename = asksaveasfilename(initialdir = sys.path[0], title = "Save Dataset File As", filetypes =(("YAML", "*.yaml"), ("XML", ".xml")))

		print filename

		if len(filename) != 0 and filename != self.dataset_file.file_path:
			self.dataset_file.file_path = filename
			return self.SaveFile()
			
	def CloseFile(self):
		if self.CheckForUnsavedChanges() == False:
			return

		# Reset everything
		self.dataset_file = None
		self.UpdateControlsAndLabels()


	def OnClosing(self):
		if self.CheckForUnsavedChanges() == True:
			self.master.destroy()

	# UPDATES GUI AFTER USER INTERACTION
	def UpdateControlsAndLabels(self):
		if self.dataset_file != None:
		
			self.dataset_name_entry.delete(0, END)
			self.dataset_name_entry.insert(0, self.dataset_file.name)
			self.dataset_area_entry.delete(0, END)
			self.dataset_area_entry.insert(0, self.dataset_file.area)
			self.dataset_datetime_entry.delete(0, END)
			self.dataset_datetime_entry.insert(0, self.dataset_file.datetime.strftime("%d/%m/%Y %H:%M"))
			self.go_to_vis_gui_button['state'] = 'normal'		
		else:

			self.go_to_vis_gui_button['state'] = 'disabled'
			self.dataset_name_entry.delete(0, END)
			self.dataset_area_entry.delete(0, END)


	def UpdateDatasetInformation(self):
		if self.dataset_file != None:
			if self.dataset_file.name != self.dataset_name_entry.get():
				self.dataset_file.name = self.dataset_name_entry.get()
				self.name = self.dataset_file.name
				print self.name

			if self.dataset_file.area != self.dataset_area_entry.get():
				self.dataset_file.area = self.dataset_area_entry.get()

			if self.dataset_file.datetime.strftime("%d/%m/%Y %H:%M") != self.dataset_datetime_entry.get():
				date_time_str = self.dataset_datetime_entry.get()
				try:
					val = datetime.strptime(date_time_str, '%d/%m/%Y %H:%M')
					self.dataset_file.datetime = val
				except Exception as e:
					showerror("Dataset Information", "The date time entered is not valid.\nThe format is dd/mm/yyyy HH:MM in 24 hour time (i.e. 15/01/2001 17:30)")


# INITIALISES CAMERA METADATA AND RETRIVES/PROCESS AUDIO FROM VIDEO FILE FOR DISPLAY
class VideoProcessing:
	def __init__(self,name,vid_url):
		# SET VARIABLES AND INITIALISE FRAME INFORMATION
		self.frame_num = 0
		self.url = vid_url
		self.vid = cv2.VideoCapture(self.url)

		self.fps = round(float(self.vid.get(cv2.CAP_PROP_FPS)))
		self.frame_total = (int(self.vid.get(cv2.CAP_PROP_FRAME_COUNT))) - 3
		self.length_secs = float(self.frame_total/round(self.fps))

		self.vid.set(1,self.frame_num)
		_, self.frame = self.vid.read()

		self.cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGBA)
		self.cv2resized = cv2.resize(self.cv2image, (320,240))

		self.im = Image.fromarray(self.cv2resized)
		self.frametk = ImageTk.PhotoImage(image=self.im)

		# AUDIO PROCESSING
		if vid_url == '/home/kyle/Desktop/VRES/REF/forward_facing_video.MTS':
			command_1 = "ffmpeg -i " + vid_url + " -acodec copy -vcodec copy forward_facing_video.avi"
			command_2 = "ffmpeg -i /home/kyle/Desktop/VRES/VRES_GUI/forward_facing_video.avi -ab 160k -ac 2 -ar 44100 -vn forward_facing_video.wav"
			subprocess.call(command_1, shell=True)
			subprocess.call(command_2, shell=True)

			spf = wave.open("/home/kyle/Desktop/VRES/VRES_GUI/forward_facing_video.wav",'r')

		elif vid_url == '/home/kyle/Desktop/VRES/REF/surface_facing_video.MTS':
			command_1 = "ffmpeg -i " + vid_url + " -acodec copy -vcodec copy surface_facing_video.avi"
			command_2 = "ffmpeg -i /home/kyle/Desktop/VRES/VRES_GUI/surface_facing_video.avi -ab 160k -ac 2 -ar 44100 -vn surface_facing_video.wav"
			subprocess.call(command_1, shell=True)
			subprocess.call(command_2, shell=True)

			spf = wave.open("/home/kyle/Desktop/VRES/VRES_GUI/surface_facing_video.wav",'r')

		# EXTRACT RAW AUDIO DATA AND FIND CLAP (ARGMAX)
		self.wav_signal = spf.readframes(-1)
		self.wav_signal = np.fromstring(self.wav_signal, 'Int16')
		sig_length = len(self.wav_signal)
		m = np.argmax(self.wav_signal)

		# SETTING UPPER AND LOWER VALUES FOR AUDIO DISPLAY
		lower_audio = m - ((len(self.wav_signal)/self.frame_total)*5)
		upper_audio = m + ((len(self.wav_signal)/self.frame_total)*5)
		self.new_signal = self.wav_signal[lower_audio : upper_audio]

		lower_percent = float(lower_audio)/float(sig_length)
		upper_percent = float(upper_audio)/float(sig_length)
		lower_frame = float(lower_percent)*int(self.frame_total)
		upper_frame = float(upper_percent)*int(self.frame_total)

		# CREATING FIGURE TO HOUSE AUDIO SIGNAL
		self.f = Figure(figsize=(4,2),dpi=100)
		self.a = self.f.add_subplot(111)
		self.plot_length = len(self.new_signal)

		# CALCULATING STEP SIZE BETWEEN FRAMES
		self.length = (upper_frame-lower_frame)/(len(self.new_signal))

		# CALCULATING TIME VECTOR
		self.t = arange(int(lower_frame), int(upper_frame), self.length)
		self.t = self.t[0:len(self.new_signal)]

	# PREPARES DISPLAYED FRAMES
	def NextFrame(self, next_frame, vid_url):

		self.cap = cv2.VideoCapture()
		self.cap.open(vid_url)

		self.frame_num = (next_frame/ (self.length_secs*self.fps))
		self.cap.set(1,next_frame)
		ret, self.frame = self.cap.read()			

		self.cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGBA)
		self.cv2resized = cv2.resize(self.cv2image, (640,480))

		self.im = Image.fromarray(self.cv2resized)
		self.next_frame = ImageTk.PhotoImage(image=self.im)

	# PREPARES USER SELECTED FRAME 
	def GoToFrame(self, new_frame, vid_url):
		self.cap = cv2.VideoCapture()
		self.cap.open(vid_url)

		self.cap.set(1,new_frame)
		ret, self.frame = self.cap.read()			

		self.cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGBA)
		self.cv2resized = cv2.resize(self.cv2image, (640,480))

		self.im = Image.fromarray(self.cv2resized)
		self.next_frame = ImageTk.PhotoImage(image=self.im)

	# WRITES FRAMES TO FOLDER
	def SaveFrames(self, name, path, vid_url):
		self.cap = cv2.VideoCapture()
		self.cap.open(vid_url)
		success, self.frame = self.cap.read()
		count = 0

		while success:
			success,raw_frame = self.cap.read()

		 	print('Reading frame number %d' % count)

		 	cv2.imwrite(os.path.join((path+name), name + "_%05d.jpg" % count), raw_frame)     # save frame as JPG file
		 	if cv2.waitKey(1) & 0xFF == ord('q'):
		 		break
		 	count += 1

# MAIN VISUALISATION GUI, DISPLAYING VIDEO FRAMES AND AUDIO
class CameraLocGUI:
	def __init__(self, parent, dataset_name, vid_1_url, vid_2_url):
		self.parent = parent
		parent.title("Frame Comparison")
		
		# INITIALISE VARIABLES
		self.pose_est = BooleanVar()
		self.dataset_name = dataset_name
		self.ONE_label_index = 0
		self.TWO_label_index = 0

		# PROCESSES SELECTED VIDEO FILES
		ONE = VideoProcessing("forward_facing_video", vid_1_url)
		TWO = VideoProcessing("surface_facing_video", vid_2_url)
		self.ONE_fps = ONE.fps
		self.TWO_fps = TWO.fps

		# INIT GUI
		ONE_title = Label(parent, text='Forward Facing\nfps = %d  frames = %d' % (ONE.fps, ONE.frame_total), font=("Helvetica", 9), fg="red")
		ONE_title.grid(row=0, column=0,columnspan=2)
		TWO_title = Label(parent, text='Surface Facing\nfps = %d  frames = %d' % (TWO.fps, TWO.frame_total), font=("Helvetica", 9), fg="red")
		TWO_title.grid(row=0, column=2,columnspan=2)

		self.ONE_number = Label(parent, font=("Helvetica", 7), fg="red")
		self.ONE_number.grid(row=2, column=0,columnspan=3)
		self.ONE_number.configure(text='Frame Number %d' % self.ONE_label_index)

		self.TWO_number = Label(parent, font=("Helvetica", 7), fg="red")
		self.TWO_number.grid(row=2, column=2,columnspan=3)
		self.TWO_number.configure(text='Frame Number %d' % self.TWO_label_index)

		self.imageframe_1 = Frame(parent)
		self.imageframe_1.grid(row=1, column=0, columnspan=2)

		self.imageframe_2 = Frame(parent)
		self.imageframe_2.grid(row=1, column=2, columnspan=2)

		self.ONE_label = Label(self.imageframe_1, image=ONE.frametk)
		self.ONE_label.grid(row=0, column=0)
		self.ONE_label.image = ONE.frametk

		self.TWO_label = Label(self.imageframe_2, image=TWO.frametk)
		self.TWO_label.grid(row=0, column=0)
		self.TWO_label.image = TWO.frametk
		
		self.ONE_scale_up_button = Button(parent, text="  Next Frame  ", command=lambda: self.update("forward_facing_scale_up", ONE, TWO) )
		self.ONE_scale_down_button = Button(parent, text="Previous Frame", command=lambda: self.update("forward_facing_scale_down", ONE, TWO) )
		self.TWO_scale_up_button = Button(parent, text="  Next Frame  ", command=lambda: self.update("surface_facing_scale_up", ONE, TWO) )
		self.TWO_scale_down_button = Button(parent, text="Previous Frame", command=lambda: self.update("surface_facing_scale_down", ONE, TWO) )

		self.ONE_scale_down_button.grid(row=3, column=0)
		self.ONE_scale_up_button.grid(row=3, column=1)
		self.TWO_scale_down_button.grid(row=3, column=2)
		self.TWO_scale_up_button.grid(row=3, column=3)

		self.ONE_entry = Entry(parent)
		self.TWO_entry = Entry(parent)
		self.ONE_entry.grid(row=4, column=0, sticky=E)
		self.TWO_entry.grid(row=4, column=2, sticky=E)

		# SETTING SEARCH BUTTONS
		Label(parent, text="Go to Frame Number",font=("Helvetica", 8), fg="red").grid(row=4, column=0, sticky=W)
		Label(parent, text="Go to Frame Number",font=("Helvetica", 8), fg="red").grid(row=4, column=2, sticky=W)

		Button(parent, text='GO', command=lambda: self.go_to_frame("forward_facing_search",ONE, TWO)).grid(row=4, column=1, sticky=W+E)
		Button(parent, text='GO', command=lambda: self.go_to_frame("surface_facing_search",ONE, TWO)).grid(row=4, column=3, sticky=W+E)

		Label(parent, text="t=0 Frame",font=("Helvetica", 8), fg="red").grid(row=5, column=0, sticky=W)
		Label(parent, text="t=0 Frame",font=("Helvetica", 8), fg="red").grid(row=5, column=2, sticky=W)

		self.initial_frame_ONE_entry = Entry(parent)
		self.initial_frame_TWO_entry = Entry(parent)
		self.initial_frame_ONE_entry.grid(row=5, column=0, sticky=E)
		self.initial_frame_TWO_entry.grid(row=5, column=2, sticky=E)

		Button(parent, text='SET', command=lambda: self.set_initial_frame("forward_facing",ONE, TWO)).grid(row=5, column=1, sticky=W+E)
		Button(parent, text='SET', command=lambda: self.set_initial_frame("surface_facing",ONE, TWO)).grid(row=5, column=3, sticky=W+E)

		# PLOTTING VIDEO FILE AUDIO
		ONE.a.plot(ONE.t, ONE.new_signal)
		ONE.a.set_title('Forward Facing Audio Signal')
		ONE.a.set_xlabel('Frame')
		ONE.a.set_ylabel('Amplitude')

		TWO.a.plot(TWO.t, TWO.new_signal)
		TWO.a.set_title('Surface Facing Audio Signal')
		TWO.a.set_xlabel('Frame')
		TWO.a.set_ylabel('Amplitude')

		# PERFORM POSE EST AND SAVE FRAMES UI
		self.perform_pose_est_checkbox = Checkbutton(parent, text="Perform Pose Estimation.", variable=self.pose_est, onvalue=True, offvalue=False)
		self.perform_pose_est_checkbox.grid(row=7, column=0)
		self.save_frames_button = Button(parent, text="SAVE FRAMES", command=lambda: self.set_and_download(ONE, TWO)).grid(row=8, column=0)
	
		ONE_canvas = FigureCanvasTkAgg(ONE.f, master=parent)
		ONE_canvas.show()
		ONE_canvas.get_tk_widget().grid(row=6, column=0,columnspan=2)

		TWO_canvas = FigureCanvasTkAgg(TWO.f, master=parent)
		TWO_canvas.show()
		TWO_canvas.get_tk_widget().grid(row=6, column=2, columnspan=2)

		self.parent.mainloop()

	# SETS INTIAL FRAME, DEFAULT= 0
	def set_initial_frame(self, name, ONE, TWO):
		if name == "forward_facing":
			self.forward_facing_initial_frame = self.initial_frame_ONE_entry.get()			
		
		elif name == "surface_facing":
			self.surface_facing_initial_frame = self.initial_frame_TWO_entry.get()


	# TRAVERSE THROUGH FRAMES	
	def update(self, method, ONE, TWO):
		if (method == "forward_facing_scale_up") and (self.ONE_label_index != ONE.frame_total):
			self.ONE_label_index += 1
			ONE.NextFrame(self.ONE_label_index, ONE.url)
			self.ONE_label.configure(image=ONE.next_frame)
			self.ONE_label.image = ONE.next_frame

		elif (method == "forward_facing_scale_up") and (self.ONE_label_index == ONE.frame_total):
			self.ONE_label_index = 0
			ONE.NextFrame(self.ONE_label_index, ONE.url)
			self.ONE_label.configure(image=ONE.next_frame)
			self.ONE_label.image = ONE.next_frame

		elif (method == "forward_facing_scale_down") and (self.ONE_label_index != 0):
			self.ONE_label_index -= 1
			ONE.NextFrame(self.ONE_label_index, ONE.url)
			self.ONE_label.configure(image=ONE.next_frame)
			self.ONE_label.image = ONE.next_frame

		elif (method == "forward_facing_scale_down") and (self.ONE_label_index == 0):
			self.ONE_label_index = ONE.frame_total
			ONE.NextFrame(self.ONE_label_index, ONE.url)
			self.ONE_label.configure(image=ONE.next_frame)
			self.ONE_label.image = ONE.next_frame

		elif (method == "surface_facing_scale_up") and (self.TWO_label_index != TWO.frame_total):
			self.TWO_label_index += 1
			TWO.NextFrame(self.TWO_label_index, TWO.url)
			self.TWO_label.configure(image=TWO.next_frame)
			self.TWO_label.image = TWO.next_frame

		elif (method == "surface_facing_scale_up") and (self.TWO_label_index == TWO.frame_total):
			self.TWO_label_index = 0
			TWO.NextFrame(self.TWO_label_index, TWO.url)
			self.TWO_label.configure(image=TWO.next_frame)
			self.TWO_label.image = TWO.next_frame

		elif (method == "surface_facing_scale_down") and (self.TWO_label_index != 0):
			self.TWO_label_index -= 1
			TWO.NextFrame(self.TWO_label_index, TWO.url)
			self.TWO_label.configure(image=TWO.next_frame)
			self.TWO_label.image = TWO.next_frame

		elif (method == "surface_facing_scale_down") and (self.TWO_label_index == 0):
			self.TWO_label_index = TWO.frame_total
			TWO.NextFrame(self.TWO_label_index, TWO.url)
			self.TWO_label.configure(image=TWO.next_frame)
			self.TWO_label.image = TWO.next_frame

		# UPDATING FRAME NUMBERS
		self.ONE_number.configure(text='Frame Number %d' % self.ONE_label_index)
		self.TWO_number.configure(text='Frame Number %d' % self.TWO_label_index)

	# GO TO SPECIFIC FRAME
	def go_to_frame(self, search, ONE, TWO):
		if search == "forward_facing_search":
			self.ONE_label_index = self.ONE_entry.get()
			ONE.GoToFrame(self.ONE_label_index, ONE.url)
			self.ONE_label.configure(image=ONE.next_frame)
			self.ONE_label.image = ONE.next_frame

		elif search == "surface_facing_search":
			self.TWO_label_index = int(self.TWO_entry.get())
			TWO.GoToFrame(self.TWO_label_index, TWO.url)
			self.TWO_label.configure(image=TWO.next_frame)
			self.TWO_label.image = TWO.next_frame

		# UPDATING FRAME NUMBERS
		self.ONE_number.configure(text='Frame Number %d' % self.ONE_label_index)
		self.TWO_number.configure(text='Frame Number %d' % self.TWO_label_index)

	# SETS FOLDERS COMMENCES VIDEO FILE DOWNLOAD
	def set_and_download(self, ONE, TWO):
		self.pose = self.pose_est.get()
		name_1 = self.dataset_name +"_forward_facing_images"
		name_2 = self.dataset_name +"_surface_facing_images"

		path = "/home/kyle/Desktop/VRES/" + self.dataset_name + "/"

		os.makedirs(path+name_1)
		os.makedirs(path+name_2)

		ONE.SaveFrames(name_1, path, ONE.url)
		TWO.SaveFrames(name_2, path, TWO.url)

		self.parent.destroy()
		self.parent.quit()

# REUTRNS SPECIFIC PARAMETER VALUE
def GetParameterValue(parameter_set, parameter_name):
	parameter_value = parameter_set.GetParameterValue(parameter_name)
	if parameter_value == None:
		print "The Parameter %s could not be found within the parameter set %s."%(parameter_name, parameter_set.Name())
		exit()
	return parameter_value

#########################################
####### VISUAL ODOMETRY FUNCTIONS #######
#########################################
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

	DATASET_PATH = '/home/kyle/Desktop/VRES/REF'
	DATASET_FILE_NAME = '/REF_dataset.yaml'
	IMAGE_SET_TO_USE = "REF_surface_images"
	PARAMETER_FILE = '/home/kyle/Desktop/VRES/map_generation/ParameterFile.yaml'

	root = Tk()

	# RUNS DATASET CREATION AND VISUALISATION UI 
	loc_vis = Dataset_Initialisation_GUI(root)
	root.mainloop()

	# TRUE IS USER SELECTS POSE ESTIMATION
	if loc_vis.Do_Pose:
		# INITIALIZE DATASET FILE, GET IMAGE SET AND IMAGE FILENAMES
		dataset = IDME.DatasetFile(DATASET_PATH + DATASET_FILE_NAME)
		image_set = dataset.GetImageSet(IMAGE_SET_TO_USE)
		if image_set == None:
			print "Failed to find the image set within the dataset"
			exit()
		image_filenames = dataset.GetImageFilenames(image_set)
		

		# INITIALIZE PARAMETER FILE AND GET PARAMETERS
		parameter_file = IDME.ParameterFile(PARAMETER_FILE)
		SAVE_ANALYSIS = True #GetParameterValue(parameter_file, "Save_Analysis")
		START_FRAME = 0#GetParameterValue(parameter_file, "Start_Frame")
		END_FRAME = image_set.NumberOfImages() - 2
		
		# INTIALISING PARAMETERS FOR VISUAL ODOM
		PREDICTION_ON = GetParameterValue(parameter_file["Visual_Odometry_Parameters"], "Prediction_On")
		PREDICTION_PADDING = GetParameterValue(parameter_file["Visual_Odometry_Parameters"], "Prediction_Padding")
		FILTER_SIZE = GetParameterValue(parameter_file["Visual_Odometry_Parameters"], "Filter_Size")
		CROP_ON = GetParameterValue(parameter_file["PreProcessing_Parameters"], "Crop_On")
		CROP_REGION = GetParameterValue(parameter_file["PreProcessing_Parameters"], "Crop_Region")
		TEMPLATE_SIZE = GetParameterValue(parameter_file["Template_Matching_Parameters"], "Template_Size")
		GEOMETRIC_PIXEL_SCALE = GetParameterValue(parameter_file["Visual_Odometry_Parameters"], "Geometric_Pixel_Scale")
		X_CAM = GetParameterValue(parameter_file["Visual_Odometry_Parameters"], "X_Cam")

		# ADD POSE EST AND du,dv
		dataset.AddMetadataField(image_set, 'VO_Pos', IDME.kValidTypes.CV_POINT3d)
		dataset.AddMetadataField(image_set, 'Pixel_du_dv', IDME.kValidTypes.CV_POINT2i)
		
		# INIT VARIABLES
		pixel_shift = [0, 0]
		ave_pixel_shift = [None, None]
		pixel_shift_history = []
		for ii in range(0, FILTER_SIZE):
			pixel_shift_history.append([None, None])
		position_estimates = np.zeros((END_FRAME-START_FRAME+1, 3), float)

		# INIT DISPLAY WINDOWS
		cv2.namedWindow("Previous Frame", cv2.WINDOW_NORMAL)
		cv2.namedWindow("Current Frame", cv2.WINDOW_NORMAL)		

		# GET FIRST IMAGE SET TO PREVIOUS IMAGE (CROP IF REQUIRED)
		previous_image = cv2.imread(image_set.Folder() + "/" + image_filenames[START_FRAME], cv2.IMREAD_GRAYSCALE)
		if CROP_ON == True:
			previous_image = previous_image[CROP_REGION[1]:CROP_REGION[1]+CROP_REGION[3], CROP_REGION[0]:CROP_REGION[0]+CROP_REGION[2]]

		# PERFORM VISUAL ODOMETRY
		image_index = START_FRAME
		array_index = 0
		while image_index != END_FRAME:
			image_index = image_index+1
			array_index = array_index + 1
			filename = image_filenames[image_index]

			# GET TEMPLATE REGION AND IMAGE
			im_height, im_width = previous_image.shape[:2]
			template_region = GetTemplateRegion(TEMPLATE_SIZE, im_width, im_height)
			template = previous_image[template_region[1]:template_region[1]+template_region[3], template_region[0]:template_region[0]+template_region[2]]

			# GET CURRENT IMAGE (CROP IMAGE IF REQUIRED)
			current_image = cv2.imread(image_set.Folder() + "/" + filename, cv2.IMREAD_GRAYSCALE)
			if CROP_ON == True:
				current_image = current_image[CROP_REGION[1]:CROP_REGION[1]+CROP_REGION[3], CROP_REGION[0]:CROP_REGION[0]+CROP_REGION[2]]

			# GET PREDICTION REGION AND IMAGE
			im_height, im_width = current_image.shape[:2]
			if image_index != START_FRAME+1 and PREDICTION_ON == True:
				prediction_region = GetPredictionRegion(ave_pixel_shift, template_region, im_width, im_height, PREDICTION_PADDING)
				prediction_region_image = current_image[prediction_region[1]:prediction_region[1]+prediction_region[3], prediction_region[0]:prediction_region[0]+prediction_region[2]]
			else:
				prediction_region = [0, 0, im_height, im_width]
				prediction_region_image = current_image


			# PERFORM TEMPLATE MATCHING
			match_result = cv2.matchTemplate(prediction_region_image, template, cv2.TM_CCOEFF_NORMED)
			min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match_result)

			# GET MATCHED REGION RECTANGLE LOCATION
			rect_loc = [0,0]
			if PREDICTION_ON == True:
				rect_loc[0] = prediction_region[0] + max_loc[0]
				rect_loc[1] = prediction_region[1] + max_loc[1]
			else:
				rect_loc[0] = max_loc[0]
				rect_loc[1] = max_loc[1]

			# VISUALIZATIONS
			if PREDICTION_ON:
				VisualOdometryVisualizations(current_image, previous_image, template_region, prediction_region)
			else:
				VisualOdometryVisualizations(current_image, previous_image, template_region)

			# END OF LOOP - UPDATE PREVIOUS IMAGE, UPDATE PIXEL SHIFTS, GET POSITION ESTIMATION, PERFORM POSITION SHIFT MOVING AVERAGING FILTER
			first_iteration = False
			previous_image = current_image
			pixel_shift[0] = template_region[0] - rect_loc[0]
			pixel_shift[1] = template_region[1] - rect_loc[1]

			pixel_shift_history = pixel_shift_history[-1:] + pixel_shift_history[:-1]
			pixel_shift_history[0][0] = pixel_shift[0]
			pixel_shift_history[0][1] = pixel_shift[1]
			ave_pixel_shift[0] = 0
			ave_pixel_shift[1] = 0
			count = 0
			for shift in pixel_shift_history:
				if shift[0] != None:
					count = count + 1
					ave_pixel_shift[0] = ave_pixel_shift[0] + shift[0]
					ave_pixel_shift[1] = ave_pixel_shift[1] + shift[1]
			ave_pixel_shift[0] = ave_pixel_shift[0]/count
			ave_pixel_shift[1] = ave_pixel_shift[1]/count

			# POSITION ESTIMATES USING PROCESS DEFINED IN NOURANI VISUAL ODOMETRY PAPERS
			delta_x = -pixel_shift[1] * GEOMETRIC_PIXEL_SCALE
			delta_theta = -float(pixel_shift[0])/float(X_CAM) * GEOMETRIC_PIXEL_SCALE

			position_estimates[array_index, 2] = position_estimates[array_index-1, 2] + delta_theta
			position_estimates[array_index, 0] = position_estimates[array_index-1, 0] + delta_x*np.cos(position_estimates[array_index-1, 2]) 
			position_estimates[array_index, 1] = position_estimates[array_index-1, 1] + delta_x*np.sin(position_estimates[array_index-1, 2]) 

			# SET VO POSITION IN ANALYSIS FILE
			error = dataset.SetMetadataValue(image_set, filename, "VO_Pos", (position_estimates[array_index, 0], position_estimates[array_index, 1], position_estimates[array_index, 2]))
			error1 = dataset.SetMetadataValue(image_set, filename, "Pixel_du_dv", (pixel_shift[0], pixel_shift[1]))
			if error1 != IDME.IDME_OKAY:
				print "WARNING! Was unable to set the VO Position for image %s to (%d, %d, %d). Error Code %d"%(filename, position_estimates[array_index, 0], position_estimates[array_index, 1], position_estimates[array_index, 2], error)

		cv2.destroyAllWindows()


		# WRITE OUT ANALYSIS FILE AND ADD TO DATASET FILE
		if SAVE_ANALYSIS == True: 

			dataset.WriteFiles()


		# POSITION PLOT
		fig = plt.figure()
		plt.suptitle('Visual Odometry Position')
		plt.xlabel('X Position (m)')
		plt.ylabel('Y Position (m)')
		plt.plot(position_estimates[:,0], position_estimates[:,1], marker='x', color='b')
		plt.axis('equal')
		plt.show()

	else:
		pass



