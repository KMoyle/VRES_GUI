import numpy as np
import imageio
import subprocess
import sys
import wave 
import struct
import cv2
import matplotlib
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
		self.master.title("IDME Management Tool")
		self.master.protocol("WM_DELETE_WINDOW", self.OnClosing)

		# MENU
		self.menubar = Menu(self.master)
		self.filemenu = Menu(self.menubar, tearoff=0)
		self.filemenu.add_command(label="New", command=self.NewFile)
		self.filemenu.add_command(label="Open", command=self.OpenFile)
		self.filemenu.add_command(label="Save", command=self.SaveFile)
		self.filemenu.add_command(label="Save as...", command=self.SaveFileAs)
		self.filemenu.add_command(label="Close", command=self.CloseFile)
		self.filemenu.add_separator()
		self.filemenu.add_command(label="Exit", command=self.OnClosing)
		self.menubar.add_cascade(label="File", menu=self.filemenu)
		self.master["menu"] = self.menubar

		# DATASET INFORMATION FRAME		
		self.dataset_file_path_label = Label(self.master, text = "Dataset File:") 
		self.dataset_file_path_label.grid(row=0, column=0)

		self.dataset_file_path = Label(self.master, text = "", bg = '#bbb')
		self.dataset_file_path.grid(row=0, column=1, sticky=W+E)


		self.dataset_info_label = Label(self.master, text = "Dataset Information:") 
		self.dataset_info_label.grid(row=1, column=0, columnspan=2)

		self.dataset_name_label = Label(self.master, text = "Dataset Name:") 
		self.dataset_name_label.grid(row=2, column=0)
		self.dataset_name_entry = Entry(self.master)
		self.dataset_name_entry.grid(row=2, column=1, sticky=W+E)

		self.dataset_area_label = Label(self.master, text = "Dataset Area:") 
		self.dataset_area_label.grid(row=3, column=0)
		self.dataset_area_entry = Entry(self.master)
		self.dataset_area_entry.grid(row=3, column=1, sticky=W+E)

		self.dataset_datetime_label = Label(self.master, text = "Dataset Date Time:") 
		self.dataset_datetime_label.grid(row=4, column=0)
		self.dataset_datetime_entry = Entry(self.master)
		self.dataset_datetime_entry.grid(row=4, column=1, sticky=W+E)

		#video streams URL
		self.stream_1_url_label = Label(self.master, text = "Video One URL")
		self.stream_1_url_label.grid(row=6, column=0, columnspan=2,sticky=W)
		self.stream_1_url_entry = Entry(self.master)
		self.stream_1_url_text = self.stream_1_url_entry.get()
		self.stream_1_url_entry.grid(row=6, column=1, columnspan=2,sticky=W+E)

		self.stream_2_url_label = Label(self.master, text = "Video Two URL")
		self.stream_2_url_label.grid(row=7, column=0, columnspan=2,sticky=W)
		self.stream_2_url_entry = Entry(self.master)
		self.stream_2_url_text = self.stream_2_url_entry.get()
		self.stream_2_url_entry.grid(row=7, column=1, columnspan=2,sticky=W+E)

		#go to visualisation gui
		self.go_to_vis_gui_button = Button(self.master, text= "Go To Visualisation", state=DISABLED, command=self.GoToVisualisation)
		self.go_to_vis_gui_button.grid(row=8, column=0, columnspan=2)

		# VARIABLES
		self.dataset_file = None

	def GoToVisualisation(self):
		self.stream_1_url_text = self.stream_1_url_entry.get()
		self.stream_2_url_text = self.stream_2_url_entry.get()
		print self.stream_1_url_text
		print self.stream_2_url_text
		self.gui_window = Toplevel(self.master)
		v = CameraLocGUI(self.gui_window, self.stream_1_url_text, self.stream_2_url_text)

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

		
	def OpenFile(self):
		if self.CheckForUnsavedChanges() == False:
			return

		# get filename and attempt to read it
		filename = askopenfilename(filetypes = (("Dataset Files", ("*.yaml","*.xml")), ("All Files", '*.*')))

		if filename:
			try:
				self.dataset_file = IDME.DatasetFile(filename)
				self.UpdateControlsAndLabels()
			except Exception as e:
				showerror("Reading Dataset File", "Failed to read file \n'%s'"%filename)
				return False

		
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
			self.dataset_file_path['text'] = self.dataset_file.file_path
			self.dataset_name_entry.delete(0, END)
			self.dataset_name_entry.insert(0, self.dataset_file.name)
			self.dataset_area_entry.delete(0, END)
			self.dataset_area_entry.insert(0, self.dataset_file.area)
			self.dataset_datetime_entry.delete(0, END)
			self.dataset_datetime_entry.insert(0, self.dataset_file.datetime.strftime("%d/%m/%Y %H:%M"))
			self.go_to_vis_gui_button['state'] = 'normal'
		else:
			self.dataset_file_path['text'] = ""
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


	def AddImageSet(self):
		d = AddImageSetWindow(self.master, self.dataset_file)
		self.master.wait_window(d.add_image_set_window)


class AddImageSetWindow:
	def __init__(self, parent, dataset_file):
		self.add_image_set_window = Toplevel(parent)
		self.add_image_set_window.transient(parent)
		self.add_image_set_window.grab_set()

		self.metadata_files = GetMetadataFiles(dataset_file)
		self.dataset_file = dataset_file

		# create widgets
		self.folder_button = Button(self.add_image_set_window, text = "Select Image Folder", command=self.GetImageFolder) 
		self.folder_button.grid(row=0, column=0)
		self.folder_label = Label(self.add_image_set_window, bg = '#bbb')
		self.folder_label.grid(row=0, column=1, sticky=W+E)

		self.name_label = Label(self.add_image_set_window, text = "Name:") 
		self.name_label.grid(row=1, column=0)
		self.name_entry = Entry(self.add_image_set_window)
		self.name_entry.grid(row=1, column=1, sticky=W+E)
				
		if self.metadata_files != []:
			self.metadata_file_label = Label(self.add_image_set_window, text = "Select Existing Metadata File:") 
			self.metadata_file_label.grid(row=2, column=0)

			self.metadata_file_choice = StringVar(self.add_image_set_window)
			self.metadata_file_choice.set(self.metadata_files[0])

			self.metadata_file_options = OptionMenu(self.add_image_set_window, self.metadata_file_choice, *self.metadata_files)
			self.metadata_file_options.grid(row=2, column=1, sticky=W+E)
			self.metadata_file_options_set = True
		else:
			self.metadata_file_options_set = False

		self.load_metadata_file_button = Button(self.add_image_set_window, text="Load Metadata File", command=self.LoadMetadataFile)
		self.load_metadata_file_button.grid(row=3, column=0)

		self.create_metadata_file_button = Button(self.add_image_set_window, text="Create Metadata File", command=self.CreateMetadataFile)
		self.create_metadata_file_button.grid(row=3, column=1)

		self.done_button = Button(self.add_image_set_window, text = "Done", state=DISABLED, command=self.AddImageSet) 
		self.done_button.grid(row=4, column=0, sticky=E)

		self.cancel_button = Button(self.add_image_set_window, text = "Cancel", command=self.Cancel) 
		self.cancel_button.grid(row=4, column=1, sticky=W)
		

	def AddImageSet(self):
		# Get Image Folder
		image_set_folder = self.folder_label["text"]

		# Get metadata file
		if self.metadata_file_options_set == False:
			return
		else:
			metadata_file = self.metadata_file_choice.get()

		# Get Image Set Name, if empty fill it with selected folder name
		image_name = self.name_entry.get()
		if len(self.name_entry.get()) == 0 and len(image_set_folder) != 0:
			self.name_entry.insert(0, os.path.basename(image_set_folder))
			image_name = image_set_folder

		error = self.dataset_file.AddImageSet(image_name, image_set_folder, metadata_file)
		if error == IDME.IDME_OKAY:
			self.add_image_set_window.destroy()

	def Cancel(self):
		self.add_image_set_window.destroy()


	def GetImageFolder(self):
		# get folder
		image_folder = askdirectory()
		self.folder_label["text"] = image_folder

		if len(self.name_entry.get()) == 0:
			self.name_entry.insert(0, os.path.basename(image_folder))

		self.EnableDone()


	def LoadMetadataFile(self):
		# get filename and attempt to read it
		filename = askopenfilename(filetypes = (("Dataset Files", ("*.yaml","*.xml")), ("All Files", '*.*')))

		if len(filename) != 0:
			self.AddToExistingMetadataFileOptions(filename)
			self.EnableDone()


	def CreateMetadataFile(self):
		# get filename and attempt to save/create it
		filename = asksaveasfilename(initialdir = sys.path[0], title = "Save Dataset File As", filetypes =(("YAML", "*.yaml"), ("XML", ".xml")))

		if len(filename) != 0:
			self.AddToExistingMetadataFileOptions(filename)
			self.EnableDone()


	def AddToExistingMetadataFileOptions(self, filename_to_add):
		# add to options if doesn't already exist
		if filename_to_add not in self.metadata_files:
			self.metadata_files.append(filename_to_add)

		if self.metadata_files != []:
			self.metadata_file_label = Label(self.add_image_set_window, text = "Select Existing Metadata File:") 
			self.metadata_file_label.grid(row=2, column=0)

			self.metadata_file_choice = StringVar(self.add_image_set_window)
			self.metadata_file_choice.set(self.metadata_files[-1])	# choose the one recently added

			self.metadata_file_options = OptionMenu(self.add_image_set_window, self.metadata_file_choice, *self.metadata_files)
			self.metadata_file_options.grid(row=2, column=1, sticky=W+E)
			self.metadata_file_options_set = True


	def EnableDone(self):
		if len(self.folder_label["text"]) == 0:
			self.done_button['state'] = 'disabled'
			return

		if self.metadata_file_options_set == False:
			self.done_button['state'] = 'disabled'
			return

		image_name = self.name_entry.get()
		if len(self.name_entry.get()) == 0:
			self.name_entry.insert(0, os.path.basename(image_set_folder))

		self.done_button['state'] = 'normal'

	

def GetMetadataFiles(dataset_file):
	metadata_files = []
	for ii in range(0, dataset_file.NumberOfImageSets()):
		metadata_file = dataset_file.GetImageSet(ii).MetadataFilePath()
		unique = True

		for file in metadata_files:
			if file == metadata_file:
				unique = False

		if unique == True:
			metadata_files.append(metadata_file)

	return metadata_files

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
		self.cv2resized = cv2.resize(self.cv2image, (300, 225))

		self.im = Image.fromarray(self.cv2resized)
		self.frametk = ImageTk.PhotoImage(image=self.im)


		#load in video and change to .wav for processing
		if vid_url == '/home/kyle/Desktop/VRES/VRES_GUI/sync_sony.MTS':
		#	command_1 = "ffmpeg -i " + vid_url + " -acodec copy -vcodec copy sync_sony.avi"
		#	print(command_1)
		#	command_2 = "ffmpeg -i /home/kyle/Desktop/VRES/VRES_GUI/sync_sony.avi -ab 160k -ac 2 -ar 44100 -vn sync_sony.wav"
		#	subprocess.call(command_1, shell=True)
		#	subprocess.call(command_2, shell=True)

			spf = wave.open("/home/kyle/Desktop/VRES/VRES_GUI/sync_sony.wav",'r')

		elif vid_url == '/home/kyle/Desktop/VRES/VRES_GUI/sync_iphone.mov':
		#	command_1 = "ffmpeg -i " + vid_url + " -acodec copy -vcodec copy sync_iphone.avi"
		#	print(command_1)
		#	command_2 = "ffmpeg -i /home/kyle/Desktop/VRES/VRES_GUI/sync_iphone.avi -ab 160k -ac 2 -ar 44100 -vn sync_iphone.wav"
		#	subprocess.call(command_1, shell=True)
		#	subprocess.call(command_2, shell=True)

			spf = wave.open("/home/kyle/Desktop/VRES/VRES_GUI/sync_iphone.wav",'r')

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
		self.f = Figure(figsize=(5, 3), dpi=100)
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
		self.cv2resized = cv2.resize(self.cv2image, (300, 225))

		self.im = Image.fromarray(self.cv2resized)
		self.next_frame = ImageTk.PhotoImage(image=self.im)

	def GoToFrame(self, new_frame, vid_url):

		self.cap = cv2.VideoCapture()
		self.cap.open(vid_url)

		self.cap.set(1,new_frame)


		ret, self.frame = self.cap.read()			

		self.cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGBA)
		self.cv2resized = cv2.resize(self.cv2image, (300, 225))

		self.im = Image.fromarray(self.cv2resized)
		self.next_frame = ImageTk.PhotoImage(image=self.im)

	def SaveFrames(self, name, set_frame, vid_url):

		self.cap = cv2.VideoCapture()
		self.cap.open(vid_url)

		self.cap.set(1,set_frame)
		success, self.frame = self.cap.read()
		
		count = 0

		while success:
			success,frame = self.cap.read()
			if success:
				gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
				gray_resized = cv2.resize(gray, (300, 225))

			print('Reading frame number %d' % count)

			cv2.imwrite(name + "_frame_%d.jpg" % count, gray_resized)     # save frame as JPEG file
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
		self.imageframe_1.grid(row=1, column=1)

		self.imageframe_2 = Frame(parent)
		self.imageframe_2.grid(row=1, column=7)

		# setting image frames
		self.ONE_label = Label(self.imageframe_1, image=ONE.frametk)
		self.ONE_label.grid(row=1, column=0)
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

		Label(parent, text="Go to Video One frame",font=("Helvetica", 14), fg="red").grid(row=5, column=0, sticky=E)
		Label(parent, text="Go to Video Two frame",font=("Helvetica", 14), fg="red").grid(row=5, column=6, sticky=E)

		Button(parent, text='   GO   ', command=lambda: self.go_to_frame("Video_1_search",ONE, TWO)).grid(row=5, column=2, sticky=W+E,)
		Button(parent, text='   GO   ', command=lambda: self.go_to_frame("Video_2_search",ONE, TWO)).grid(row=5, column=8, sticky=W+E,columnspan=2)

		Button(parent, text="Set Initial Frame and Download", command=lambda: self.set_and_download(ONE, TWO)).grid(row=10, column=4, columnspan=2)
	
		# setting scale buttons
		self.ONE_scale_up_button = Button(parent, text="  Next Frame ", command=lambda: self.update("Video_1_scale_up", ONE, TWO) )
		self.ONE_scale_down_button = Button(parent, text="Previous Frame", command=lambda: self.update("Video_1_scale_down", ONE, TWO) )
		self.TWO_scale_up_button = Button(parent, text="  Next Frame ", command=lambda: self.update("Video_2_scale_up", ONE, TWO) )
		self.TWO_scale_down_button = Button(parent, text="Previous Frame", command=lambda: self.update("Video_2_scale_down", ONE, TWO) )

		self.ONE_scale_down_button.grid(row=4, column=0,columnspan=2, pady=15)
		self.ONE_scale_up_button.grid(row=4, column=2, columnspan=2,  pady=15)
		self.TWO_scale_down_button.grid(row=4, column=6, columnspan=2,  pady=15)
		self.TWO_scale_up_button.grid(row=4, column=8, columnspan=2,  pady=15)

		self.ONE_entry.grid(row=5, column=1, sticky=W)
		self.TWO_entry.grid(row=5, column=7, sticky=W)

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
		ONE_canvas.get_tk_widget().grid(row=6, column=0,columnspan=6, rowspan=2, padx=5, pady=5)

		toolbar = NavigationToolbar2TkAgg(ONE_canvas, toolbar_frame_1)
		toolbar.update()
		ONE_canvas._tkcanvas.grid()
		toolbar_frame_1.grid(row=9, column=1,columnspan=6, rowspan=1, sticky=W+S)


		TWO_canvas = FigureCanvasTkAgg(TWO.f, master=parent)
		TWO_canvas.show()
		TWO_canvas.get_tk_widget().grid(row=6, column=6, columnspan=6, rowspan=1,padx=5, pady=5)

		toolbar_1 = NavigationToolbar2TkAgg(TWO_canvas, toolbar_frame_2)
		toolbar_1.update()
		TWO_canvas._tkcanvas.grid()
		toolbar_frame_2.grid(row=9, column=7,columnspan=6, rowspan=1, sticky=W+S)


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
			self.ONE_label_index = int(self.ONE_entry.get())
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

		ONE.SaveFrames("Video_1", self.ONE_label_index, ONE.url)
		TWO.SaveFrames("Video_2", self.TWO_label_index, TWO.url)

		self.parent.destroy()



if __name__ == "__main__":

	#videos to be loaded
	#vid_stream_1_url = "/home/kyle/Desktop/VRES/VRES_GUI/sync_iphone.mov"
	#vid_stream_2_url = "/home/kyle/Desktop/VRES/VRES_GUI/sync_sony.MTS"

	root = Tk()

	loc_vis = Dataset_Initialisation_GUI(root)
	root.mainloop()







