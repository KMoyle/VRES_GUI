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

class Dataset_Initialisation_GUI:
	def __init__(self, master):
	
		# TKINTER WIDGES
		self.master = master
		self.master.title("Localisation and Mapping Tool")
		self.master.protocol("WM_DELETE_WINDOW", self.OnClosing)

		# Variables
		self.pose_est = BooleanVar()

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

		#video streams URL
		self.video_1_open_button = Button(self.master, text = "Select Video One",command=lambda: self.SelectVideoFile("video_1_file"))
		self.video_1_open_button.grid(row=5, column=0,sticky=W+E)

		self.video_1_file_label = Label(self.master, text='<Please Select a video File>', bg='#bbb')
		self.video_1_file_label.grid(row=5, column=1, sticky=W+E)

		self.video_2_open_button = Button(self.master, text = "Select Video Two",command=lambda: self.SelectVideoFile("video_2_file"))
		self.video_2_open_button.grid(row=6, column=0, sticky=W+E)

		self.video_2_file_label = Label(self.master, text='<Please Select a video File>', bg='#bbb')
		self.video_2_file_label.grid(row=6, column=1, sticky=W+E)

		self.perform_pose_est_checkbox = Checkbutton(self.master, text="Perform Pose Estimation.", variable=self.pose_est, onvalue=True, offvalue=False)
		self.perform_pose_est_checkbox.grid(row=8, column=0, columnspan=2, sticky=W+E)

		#go to visualisation gui
		self.go_to_vis_gui_button = Button(self.master, text= "Go To Visualisation", state=DISABLED, command=self.GoToVisualisation)
		self.go_to_vis_gui_button.grid(row=7, column=0, columnspan=2)

		self.save_and_update_button = Button(self.master, text= "Save Dataset and Update Metadata", command=self.SaveAndUpdate)
		self.save_and_update_button.grid(row=9, column=0, columnspan=2)

		# VARIABLES
		self.dataset_file = None
		self.video_1_initial = 1
		self.video_2_initial = 678


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


	def GenerateDataset(self):

		START_TIME = datetime.now()
		CAMERA_1_FPS = 30
		CAMERA_2_FPS = 60

		self.dataset_file.AddImageSet('Video_1', '/home/kylesm/Desktop/VRES/VRES_GUI/Video_1', '/home/kylesm/Desktop/VRES/VRES_GUI/Vid_1_meta.yaml')
		self.dataset_file.AddImageSet('Video_2', '/home/kylesm/Desktop/VRES/VRES_GUI/Video_2','/home/kylesm/Desktop/VRES/VRES_GUI/Vid_2_meta.yaml')

		self.meta_1 = IDME.MetadataFile('/home/kylesm/Desktop/VRES/VRES_GUI/Vid_1_meta.yaml')
		self.meta_2 = IDME.MetadataFile('/home/kylesm/Desktop/VRES/VRES_GUI/Vid_2_meta.yaml')

		self.SetTimeStamps(self.dataset_file, 'Video_1', START_TIME, CAMERA_1_FPS, self.video_1_initial)
		self.SetTimeStamps(self.dataset_file, 'Video_2', START_TIME, CAMERA_2_FPS, self.video_2_initial)

		self.dataset_file.WriteFiles()



	def SaveAndUpdate(self):

		self.SaveFileAs()

		self.GenerateDataset()

		self.master.destroy()
		self.master.quit()

		print self.pose_est.get()



	def SelectVideoFile(self, vid_name):
		# get filename and attempt to read it
		map_gen_folder = "/home/kylesm/Desktop/VRES/VRES_GUI/"
		filename = askopenfilename(initialdir = map_gen_folder, title='Select Video File', filetypes = (("Video Files", ("*.MTS","*.mov","*.avi")), ("All Files", '*.*')))

		print filename
		if vid_name == "video_1_file":
			if filename:
				try:
					self.video_1_file_label['text'] = filename
					self.video_1_file_path = filename
				except Exception as e:
					self.video_1_file_label['text'] = '<Please Select a Dataset File>'
					self.video_1_file_path = ''
					showerror("Opening Dataset File", "Failed to open the selected file as a dataset file.\n'%s'"%filename)
					return

		elif vid_name == "video_2_file":
			if filename:
				try:
					self.video_2_file_label['text'] = filename
					self.video_2_file_path = filename
				except Exception as e:
					self.video_2_file_label['text'] = '<Please Select a Dataset File>'
					self.video_2_file_path = ''
					showerror("Opening Dataset File", "Failed to open the selected file as a dataset file.\n'%s'"%filename)
					return

	def GoToVisualisation(self):
		self.UpdateDatasetInformation()

		#self.dataset_file.WriteFiles()
		self.gui_window = Toplevel(self.master)

		print self.pose_est

		v = CameraLocGUI(self.gui_window, self.video_1_file_path, self.video_2_file_path)

		self.video_1_initial = v.video_1_initial_frame
		self.video_2_initial = v.video_2_initial_frame

		self.perform_pose_est_checkbox['state'] = 'normal'
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

			if self.dataset_file.area != self.dataset_area_entry.get():
				self.dataset_file.area = self.dataset_area_entry.get()

			if self.dataset_file.datetime.strftime("%d/%m/%Y %H:%M") != self.dataset_datetime_entry.get():
				date_time_str = self.dataset_datetime_entry.get()
				try:
					val = datetime.strptime(date_time_str, '%d/%m/%Y %H:%M')
					self.dataset_file.datetime = val
				except Exception as e:
					showerror("Dataset Information", "The date time entered is not valid.\nThe format is dd/mm/yyyy HH:MM in 24 hour time (i.e. 15/01/2001 17:30)")



class VideoProcessing:


	def __init__(self,name,vid_url):

		self.url = vid_url
		print vid_url
		#load in video one and extract frames 
		self.vid = cv2.VideoCapture(self.url)
		
		#success,frame = vid.read()

		self.fps = int(self.vid.get(cv2.CAP_PROP_FPS))
		self.frame_total = (int(self.vid.get(cv2.CAP_PROP_FRAME_COUNT))) - 3

		print self.fps
		print self.frame_total
		self.length_secs = float(self.frame_total/self.fps)
		self.frame_num = 0

		self.vid.set(1,self.frame_num)
		_, self.frame = self.vid.read()

		self.cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGBA)
		self.cv2resized = cv2.resize(self.cv2image, (640,480))

		self.im = Image.fromarray(self.cv2resized)
		self.frametk = ImageTk.PhotoImage(image=self.im)


		#load in video and change to .wav for processing
		if vid_url == '/home/kylesm/Desktop/VRES/VRES_GUI/sync_sony.MTS':
			command_1 = "ffmpeg -i " + vid_url + " -acodec copy -vcodec copy sync_sony.avi"
			print(command_1)
			command_2 = "ffmpeg -i /home/kylesm/Desktop/VRES/VRES_GUI/sync_sony.avi -ab 160k -ac 2 -ar 44100 -vn sync_sony.wav"
			subprocess.call(command_1, shell=True)
			subprocess.call(command_2, shell=True)

			spf = wave.open("/home/kylesm/Desktop/VRES/VRES_GUI/sync_sony.wav",'r')

		elif vid_url == '/home/kylesm/Desktop/VRES/VRES_GUI/sync_iphone.MTS':
			command_1 = "ffmpeg -i " + vid_url + " -acodec copy -vcodec copy sync_iphone.avi"
			print(command_1)
			command_2 = "ffmpeg -i /home/kylesm/Desktop/VRES/VRES_GUI/sync_iphone.avi -ab 160k -ac 2 -ar 44100 -vn sync_iphone.wav"
			subprocess.call(command_1, shell=True)
			subprocess.call(command_2, shell=True)

			spf = wave.open("/home/kylesm/Desktop/VRES/VRES_GUI/sync_iphone.wav",'r')

		#Extract Raw Audio from Wav File
		self.wav_signal = spf.readframes(-1)
		self.wav_signal = np.fromstring(self.wav_signal, 'Int16')
		sig_length = len(self.wav_signal)

		print "sig_length %d" % sig_length
		m = np.argmax(self.wav_signal)

		lower_audio = m - ((len(self.wav_signal)/self.frame_total)*5)
		upper_audio = m + ((len(self.wav_signal)/self.frame_total)*5)

		self.new_signal = self.wav_signal[lower_audio : upper_audio]

		lower_percent = float(lower_audio)/float(sig_length)
		upper_percent = float(upper_audio)/float(sig_length)

		lower_frame = float(lower_percent)*int(self.frame_total)
		upper_frame = float(upper_percent)*int(self.frame_total)

		#creating a figure to house the audio signal plot
		self.f = Figure(figsize=(6,3),dpi=100)
		self.a = self.f.add_subplot(111)
		self.plot_length = len(self.new_signal)


		#calculating the step size of the frames
		self.length = (upper_frame-lower_frame)/(len(self.new_signal))

		#calculating time vector
		self.t = arange(int(lower_frame), int(upper_frame), self.length)

		self.t = self.t[0:len(self.new_signal)]

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

	def GoToFrame(self, new_frame, vid_url):

		self.cap = cv2.VideoCapture()
		self.cap.open(vid_url)

		self.cap.set(1,new_frame)


		ret, self.frame = self.cap.read()			

		self.cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGBA)
		self.cv2resized = cv2.resize(self.cv2image, (640,480))

		self.im = Image.fromarray(self.cv2resized)
		self.next_frame = ImageTk.PhotoImage(image=self.im)

	def SaveFrames(self, name, path, vid_url):

		self.cap = cv2.VideoCapture()
		self.cap.open(vid_url)

		success, self.frame = self.cap.read()
		
		count = 0

		while success:
			success,frame = self.cap.read()
			if success:
				RGB_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
				#gray_resized = cv2.resize(gray, (300, 225))

			print('Reading frame number %d' % count)

			cv2.imwrite(os.path.join((path+name), name + "_frame_%05d.jpg" % count), RGB_frame)     # save frame as JPG file
			if cv2.waitKey(1) & 0xFF == ord('q'):
				break
			count += 1


#localisation application class
class CameraLocGUI:

	def __init__(self,parent, vid_1_url, vid_2_url):

		self.parent = parent

		parent.title("Frame Comparison")

		print vid_1_url
		print vid_2_url

		ONE = VideoProcessing("Video_1", vid_1_url)
		TWO = VideoProcessing("Video_2", vid_2_url)


		#setting the initial loaded frame
		self.imageframe_1 = Frame(parent)
		self.imageframe_1.grid(row=1, column=1, columnspan=3)

		self.imageframe_2 = Frame(parent)
		self.imageframe_2.grid(row=1, column=7, columnspan=3)

		# setting image frames
		self.ONE_label = Label(self.imageframe_1, image=ONE.frametk)
		self.ONE_label.grid(row=1, column=1)
		self.ONE_label.image = ONE.frametk
		self.ONE_label_index = 0

		self.TWO_label = Label(self.imageframe_2, image=TWO.frametk)
		self.TWO_label.grid(row=1, column=6)
		self.TWO_label.image = TWO.frametk
		self.TWO_label_index = 0
		
		#plotting REF & QRY signal 
		ONE.a.plot(ONE.t, ONE.new_signal)
		ONE.a.set_title('REF Audio Signal')
		ONE.a.set_xlabel('Frame')
		ONE.a.set_ylabel('Amplitude')

		TWO.a.plot(TWO.t, TWO.new_signal)
		TWO.a.set_title('QRY Audio Signal')
		TWO.a.set_xlabel('Frame')
		TWO.a.set_ylabel('Amplitude')

		# setting frame search entry
		self.ONE_entry = Entry(parent)
		self.TWO_entry = Entry(parent)

		self.ONE_entry.grid(row=5, column=1, sticky=W+E)
		self.TWO_entry.grid(row=5, column=7, sticky=W+E)

		# setting t=0 frame entry
		self.initial_frame_ONE_entry = Entry(parent)
		self.initial_frame_TWO_entry = Entry(parent)

		self.initial_frame_ONE_entry.grid(row=6, column=1, sticky=W+E)
		self.initial_frame_TWO_entry.grid(row=6, column=7, sticky=W+E)

		# setting search buttons
		Label(parent, text="Go to Frame Number",font=("Helvetica", 14), fg="red").grid(row=5, column=0, sticky=E)
		Label(parent, text="Go to Frame Number",font=("Helvetica", 14), fg="red").grid(row=5, column=6, sticky=E)

		Button(parent, text='   GO   ', command=lambda: self.go_to_frame("Video_1_search",ONE, TWO)).grid(row=5, column=2, sticky=W+E)
		Button(parent, text='   GO   ', command=lambda: self.go_to_frame("Video_2_search",ONE, TWO)).grid(row=5, column=8, sticky=W+E)

		Label(parent, text="Set t=0 Frame",font=("Helvetica", 14), fg="red").grid(row=6, column=0, sticky=E)
		Label(parent, text="Set t=0 Frame",font=("Helvetica", 14), fg="red").grid(row=6, column=6, sticky=E)

		Button(parent, text='   SET   ', command=lambda: self.set_initial_frame("Video_1",ONE, TWO)).grid(row=6, column=2, sticky=W+E)
		Button(parent, text='   SET   ', command=lambda: self.set_initial_frame("Video_2",ONE, TWO)).grid(row=6, column=8, sticky=W+E)

		self.save_frames_button = Button(parent, text="Save Frames", command=lambda: self.set_and_download(ONE, TWO)).grid(row=10, column=4, columnspan=2)
	
		# setting scale buttons
		self.ONE_scale_up_button = Button(parent, text="  Next Frame ", command=lambda: self.update("Video_1_scale_up", ONE, TWO) )
		self.ONE_scale_down_button = Button(parent, text="Previous Frame", command=lambda: self.update("Video_1_scale_down", ONE, TWO) )
		self.TWO_scale_up_button = Button(parent, text="  Next Frame ", command=lambda: self.update("Video_2_scale_up", ONE, TWO) )
		self.TWO_scale_down_button = Button(parent, text="Previous Frame", command=lambda: self.update("Video_2_scale_down", ONE, TWO) )

		self.ONE_scale_down_button.grid(row=4, column=0,columnspan=2)
		self.ONE_scale_up_button.grid(row=4, column=2, columnspan=2)
		self.TWO_scale_down_button.grid(row=4, column=6, columnspan=2)
		self.TWO_scale_up_button.grid(row=4, column=8, columnspan=2)


		#setting frame titles and corresponding number
		ONE_title = Label(parent, text='Video One Frame\nfps = %d  frames = %d' % (ONE.fps, ONE.frame_total), font=("Helvetica", 14), fg="red")
		ONE_title.grid(row=0, column=0,columnspan=6)

		TWO_title = Label(parent, text='Video Two Frame\nfps = %d  frames = %d' % (TWO.fps, TWO.frame_total), font=("Helvetica", 14), fg="red")
		TWO_title.grid(row=0, column=6,columnspan=6)

		self.ONE_number = Label(parent, font=("Helvetica", 10), fg="red")
		self.ONE_number.grid(row=3, column=0,columnspan=6)
		self.ONE_number.configure(text='Frame Number %d' % self.ONE_label_index)

		self.TWO_number = Label(parent, font=("Helvetica", 10), fg="red")
		self.TWO_number.grid(row=3, column=6,columnspan=6)
		self.TWO_number.configure(text='Frame Number %d' % self.TWO_label_index)

		# frame object for NAV bar
		toolbar_frame_1 = Frame(parent)
		toolbar_frame_2 = Frame(parent)
		
		# a tk.DrawingArea
		ONE_canvas = FigureCanvasTkAgg(ONE.f, master=parent)
		ONE_canvas.show()
		ONE_canvas.get_tk_widget().grid(row=7, column=0,columnspan=6, rowspan=1)

		toolbar = NavigationToolbar2TkAgg(ONE_canvas, toolbar_frame_1)
		toolbar.update()
		ONE_canvas._tkcanvas.grid()
		toolbar_frame_1.grid(row=9, column=1,columnspan=6, rowspan=1, sticky=W+S)


		TWO_canvas = FigureCanvasTkAgg(TWO.f, master=parent)
		TWO_canvas.show()
		TWO_canvas.get_tk_widget().grid(row=7, column=6, columnspan=6, rowspan=1)

		toolbar_1 = NavigationToolbar2TkAgg(TWO_canvas, toolbar_frame_2)
		toolbar_1.update()
		TWO_canvas._tkcanvas.grid()
		toolbar_frame_2.grid(row=9, column=7,columnspan=6, rowspan=1, sticky=W+S)

		#start mainloop
		self.parent.mainloop()

	def set_initial_frame(self, name, ONE, TWO):

		if name == "Video_1":
			self.video_1_initial_frame = self.initial_frame_ONE_entry.get()
			print self.video_1_initial_frame
			
		
		elif name == "Video_2":
			self.video_2_initial_frame = self.initial_frame_TWO_entry.get()
			print self.video_2_initial_frame
			


	#traverse through the frames	
	def update(self, method, ONE, TWO):


		if (method == "Video_1_scale_up") and (self.ONE_label_index != ONE.frame_total):
			self.ONE_label_index += 1
			ONE.NextFrame(self.ONE_label_index, ONE.url)
			self.ONE_label.configure(image=ONE.next_frame)
			self.ONE_label.image = ONE.next_frame

		elif (method == "Video_1_scale_up") and (self.ONE_label_index == ONE.frame_total):
			self.ONE_label_index = 0
			ONE.NextFrame(self.ONE_label_index, ONE.url)
			self.ONE_label.configure(image=ONE.next_frame)
			self.ONE_label.image = ONE.next_frame

		elif (method == "Video_1_scale_down") and (self.ONE_label_index != 0):
			self.ONE_label_index -= 1
			ONE.NextFrame(self.ONE_label_index, ONE.url)
			self.ONE_label.configure(image=ONE.next_frame)
			self.ONE_label.image = ONE.next_frame

		elif (method == "Video_1_scale_down") and (self.ONE_label_index == 0):
			self.ONE_label_index = ONE.frame_total
			ONE.NextFrame(self.ONE_label_index, ONE.url)
			self.ONE_label.configure(image=ONE.next_frame)
			self.ONE_label.image = ONE.next_frame

		elif (method == "Video_2_scale_up") and (self.TWO_label_index != TWO.frame_total):
			self.TWO_label_index += 1
			TWO.NextFrame(self.TWO_label_index, TWO.url)
			self.TWO_label.configure(image=TWO.next_frame)
			self.TWO_label.image = TWO.next_frame

		elif (method == "Video_2_scale_up") and (self.TWO_label_index == TWO.frame_total):
			self.TWO_label_index = 0
			TWO.NextFrame(self.TWO_label_index, TWO.url)
			self.TWO_label.configure(image=TWO.next_frame)
			self.TWO_label.image = TWO.next_frame

		elif (method == "Video_2_scale_down") and (self.TWO_label_index != 0):
			self.TWO_label_index -= 1
			TWO.NextFrame(self.TWO_label_index, TWO.url)
			self.TWO_label.configure(image=TWO.next_frame)
			self.TWO_label.image = TWO.next_frame

		elif (method == "Video_2_scale_down") and (self.TWO_label_index == 0):
			self.TWO_label_index = TWO.frame_total
			TWO.NextFrame(self.TWO_label_index, TWO.url)
			self.TWO_label.configure(image=TWO.next_frame)
			self.TWO_label.image = TWO.next_frame

		# updating the frame numbers txt
		self.ONE_number.configure(text='Frame Number %d' % self.ONE_label_index)
		self.TWO_number.configure(text='Frame Number %d' % self.TWO_label_index)

	def go_to_frame(self, search, ONE, TWO):

		if search == "Video_1_search":
			self.ONE_label_index = self.ONE_entry.get()
			ONE.GoToFrame(self.ONE_label_index, ONE.url)
			self.ONE_label.configure(image=ONE.next_frame)
			self.ONE_label.image = ONE.next_frame

		elif search == "Video_2_search":
			self.TWO_label_index = int(self.TWO_entry.get())
			TWO.GoToFrame(self.TWO_label_index, TWO.url)
			self.TWO_label.configure(image=TWO.next_frame)
			self.TWO_label.image = TWO.next_frame

		# updating the frame numbers txt
		self.ONE_number.configure(text='Frame Number %d' % self.ONE_label_index)
		self.TWO_number.configure(text='Frame Number %d' % self.TWO_label_index)

	def set_and_download(self, ONE, TWO):

		name_1 = "Video_1"
		name_2 = "Video_2"

		path = "/home/kylesm/Desktop/VRES/VRES_GUI/"

		os.makedirs(path+name_1)
		os.makedirs(path+name_2)

		ONE.SaveFrames(name_1, path, ONE.url)
		TWO.SaveFrames(name_2, path, TWO.url)


		self.parent.destroy()
		self.parent.quit()

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

	DATASET_PATH = '/home/kylesm/Desktop/VRES/VRES_GUI'
	DATASET_FILE_NAME = '/dataset.yaml'
	IMAGE_SET_TO_USE = "Video_1"
	PARAMETER_FILE = '/home/kylesm/Desktop/VRES/map_generation/ParameterFile.yaml'

	root = Tk()

	loc_vis = Dataset_Initialisation_GUI(root)
	root.mainloop()


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
	END_FRAME = 1199#GetParameterValue(parameter_file, "End_Frame")
	if START_FRAME < 0:
		START_FRAME = 0
	if END_FRAME < 0:
		END_FRAME = image_set.NumberOfImages()

	PREDICTION_ON = GetParameterValue(parameter_file["Visual_Odometry_Parameters"], "Prediction_On")
	PREDICTION_PADDING = GetParameterValue(parameter_file["Visual_Odometry_Parameters"], "Prediction_Padding")
	FILTER_SIZE = GetParameterValue(parameter_file["Visual_Odometry_Parameters"], "Filter_Size")

	CROP_ON = GetParameterValue(parameter_file["PreProcessing_Parameters"], "Crop_On")
	CROP_REGION = GetParameterValue(parameter_file["PreProcessing_Parameters"], "Crop_Region")

	TEMPLATE_SIZE = GetParameterValue(parameter_file["Template_Matching_Parameters"], "Template_Size")

	GEOMETRIC_PIXEL_SCALE = GetParameterValue(parameter_file["Visual_Odometry_Parameters"], "Geometric_Pixel_Scale")
	X_CAM = GetParameterValue(parameter_file["Visual_Odometry_Parameters"], "X_Cam")

	dataset.AddMetadataField(image_set, 'VO_Pos', IDME.kValidTypes.CV_POINT3d)
	
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

	# GET IMAGE FILENAMES
	

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
		if error != IDME.IDME_OKAY:
			print "WARNING! Was unable to set the VO Position for image %s to (%d, %d, %d). Error Code %d"%(filename, position_estimates[array_index, 0], position_estimates[array_index, 1], position_estimates[array_index, 2], error)

	cv2.destroyAllWindows()


	# WRITE OUT ANALYSIS FILE AND ADD TO DATASET FILE
	if SAVE_ANALYSIS == True: 
		#analysis_file.WriteFile()
		#dataset.AddAnalysis(analysis_file)
		dataset.WriteFiles()


	# POSITION PLOT
	fig = plt.figure()
	plt.suptitle('Visual Odometry Position')
	plt.xlabel('X Position (m)')
	plt.ylabel('Y Position (m)')
	plt.plot(position_estimates[:,0], position_estimates[:,1], marker='x', color='b')
	plt.axis('equal')
	plt.show()



