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
from Tkinter import Tk, Label, Button, Frame, N, S, W, E 
from PIL import Image, ImageTk
from scipy.io import wavfile as wav
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

imageio.plugins.ffmpeg.download()
matplotlib.use('TkAgg')

class VideoProcessing:


	def __init__(self,name,vid_url):

		#load in video one and extract frames 
		vid = cv2.VideoCapture(vid_url)
		
		success,frame = vid.read()

		self.fps = int(vid.get(cv2.CAP_PROP_FPS))
		self.frame_total = (int(vid.get(cv2.CAP_PROP_FRAME_COUNT)))- 3 
		
		count = 0
		success = True
		while success:
			success,frame = vid.read()
			
			if success:
				gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
				gray_resized = cv2.resize(gray, (640, 480))

			print('Reading frame number %d' % count)

			cv2.imwrite(name + "_frame_%d.jpg" % count, gray_resized)     # save frame as JPEG file
			if cv2.waitKey(1) & 0xFF == ord('q'):
				break
			count += 1

		#load in video and change to .wav for processing
		command_1 = "ffmpeg -i /home/kylesm/Desktop/VRES/VRES_GUI/sync_iphone.mov -acodec copy -vcodec copy sync_iphone.avi"
		command_2 = "ffmpeg -i /home/kylesm/Desktop/VRES/VRES_GUI/sync_iphone.avi -ab 160k -ac 2 -ar 44100 -vn sync_iphone.wav"
		subprocess.call(command_1, shell=True)
		subprocess.call(command_2, shell=True)

		spf = wave.open("/home/kylesm/Desktop/VRES/VRES_GUI/sync_iphone.wav",'r')

		#Extract Raw Audio from Wav File
		self.wav_signal = spf.readframes(-1)
		self.wav_signal = np.fromstring(self.wav_signal, 'Int16')

		#creating a figure to house the audio signal plot
		self.f = Figure(figsize=(8, 5), dpi=100)
		self.a = self.f.add_subplot(111)

		#calculating the step size of the frames
		float(self.frame_total)
		self.length = self.frame_total/1757184.0

		#calculating time vector
		self.t = arange(0, self.frame_total, self.length) 

	def loadAudio(self,)


#localisation application class
class CameraLocGUI(object,VideoProcessing):


	def __init__(self,parent):

		self.parent = parent
		parent.title("Frame Comparison")

		REF = VideoProcessing("REF", REF_vid_url)

		QRY = VideoProcessing("QRY", QRY_vid_url)

		#setting the initial loaded frame
		REF_image = Image.open("/home/kylesm/Desktop/VRES/VRES_GUI/REF_frame_0.jpg")
		REF_photo = ImageTk.PhotoImage(REF_image)
		QRY_image = Image.open("/home/kylesm/Desktop/VRES/VRES_GUI/QRY_frame_0.jpg")
		QRY_photo = ImageTk.PhotoImage(QRY_image)
		
		#plotting REF & QRY signal 
		REF.a.plot(REF.t, REF.wav_signal)
		REF.a.set_title('REF Audio Signal')
		REF.a.set_xlabel('Frame')
		REF.a.set_ylabel('Amplitude')

		QRY.a.plot(QRY.t, QRY.wav_signal)
		QRY.a.set_title('QRY Audio Signal')
		QRY.a.set_xlabel('Frame')
		QRY.a.set_ylabel('Amplitude')

		# setting frames
		self.REF_label = Label(parent, image=REF_photo)
		self.REF_label.image = REF_photo
		self.REF_label_index = 0
	
		self.QRY_label = Label(parent, image=QRY_photo)
		self.QRY_label.image = QRY_photo
		self.QRY_label_index = 0

		# setting buttons
		self.REF_scale_up_button = Button(parent, text="  Next Frame ", command=lambda: self.update("REF_scale_up", REF, QRY) )
		self.REF_scale_down_button = Button(parent, text="Previous Frame", command=lambda: self.update("REF_scale_down", REF, QRY) )
		self.QRY_scale_up_button = Button(parent, text="  Next Frame ", command=lambda: self.update("QRY_scale_up", REF, QRY) )
		self.QRY_scale_down_button = Button(parent, text="Previous Frame", command=lambda: self.update("QRY_scale_down", REF, QRY) )

		# layout 
		self.REF_label.grid(row=1, column=0,columnspan=6,rowspan=2)
		self.QRY_label.grid(row=1, column=6, columnspan=6,rowspan=2)

		self.REF_scale_down_button.grid(row=4, column=0, columnspan=3,rowspan=1, padx=15, pady=15)
		self.REF_scale_up_button.grid(row=4, column=3, columnspan=3,rowspan=1, padx=15, pady=15)
		self.QRY_scale_down_button.grid(row=4, column=6, columnspan=3,rowspan=1, padx=15, pady=15)
		self.QRY_scale_up_button.grid(row=4, column=9, columnspan=3, rowspan=1, padx=15, pady=15)

		#setting frame titles
		REF_title = Label(parent, text='REF Frame', font=("Helvetica", 16), fg="red")
		REF_title.grid(row=0, column=0,columnspan=6)

		QRY_title = Label(parent, text='QRY Frame', font=("Helvetica", 16), fg="red")
		QRY_title.grid(row=0, column=6,columnspan=6)

		self.REF_number = Label(parent, font=("Helvetica", 12), fg="red")
		self.REF_number.grid(row=3, column=0,columnspan=6)
		self.REF_number.configure(text='Frame Number %d' % self.REF_label_index)

		self.QRY_number = Label(parent, font=("Helvetica", 12), fg="red")
		self.QRY_number.grid(row=3, column=6,columnspan=6)
		self.QRY_number.configure(text='Frame Number %d' % self.QRY_label_index)


		#Making frames for NAV bar
		toolbar_frame_1 = Frame(parent)
		toolbar_frame_2 = Frame(parent)
		
		# a tk.DrawingArea
		REF_canvas = FigureCanvasTkAgg(REF.f, master=parent)
		REF_canvas.show()
		REF_canvas.get_tk_widget().grid(row=5, column=0,columnspan=6, rowspan=2, padx=5, pady=5)

		toolbar = NavigationToolbar2TkAgg(REF_canvas, toolbar_frame_1)
		toolbar.update()
		REF_canvas._tkcanvas.grid()
		toolbar_frame_1.grid(row=9, column=1,columnspan=6, rowspan=1, sticky=W+S)


		QRY_canvas = FigureCanvasTkAgg(QRY.f, master=parent)
		QRY_canvas.show()
		QRY_canvas.get_tk_widget().grid(row=5, column=6, columnspan=6, rowspan=1,padx=5, pady=5)

		toolbar_1 = NavigationToolbar2TkAgg(QRY_canvas, toolbar_frame_2)
		toolbar_1.update()
		QRY_canvas._tkcanvas.grid()
		toolbar_frame_2.grid(row=9, column=7,columnspan=6, rowspan=1, sticky=W+S)


	#traverse through the frames	
	def update(self, method, REF, QRY):

		print(self.REF_label_index)
		print(self.QRY_label_index)

		if (method == "REF_scale_up") and (self.REF_label_index != REF.frame_total):
			self.REF_label_index += 1
			REF_image = Image.open("/home/kylesm/Desktop/VRES/VRES_GUI/REF_frame_%d.jpg" % self.REF_label_index)
			REF_photo = ImageTk.PhotoImage(REF_image)
			self.REF_label.configure(image=REF_photo)
			self.REF_label.image = REF_photo

		elif (method == "REF_scale_up") and (self.REF_label_index == REF.frame_total):
			self.REF_label_index = 0
			REF_image = Image.open("/home/kylesm/Desktop/VRES/VRES_GUI/REF_frame_%d.jpg" % self.REF_label_index)
			REF_photo = ImageTk.PhotoImage(REF_image)
			self.REF_label.configure(image=REF_photo)
			self.REF_label.image = REF_photo

		elif (method == "REF_scale_down") and (self.REF_label_index != 0):
			self.REF_label_index -= 1
			REF_image = Image.open("/home/kylesm/Desktop/VRES/VRES_GUI/REF_frame_%d.jpg" % self.REF_label_index)
			REF_photo = ImageTk.PhotoImage(REF_image)
			self.REF_label.configure(image=REF_photo)
			self.REF_label.image = REF_photo

		elif (method == "REF_scale_down") and (self.REF_label_index == 0):
			self.REF_label_index = REF.frame_total
			REF_image = Image.open("/home/kylesm/Desktop/VRES/VRES_GUI/REF_frame_%d.jpg" % self.REF_label_index)
			REF_photo = ImageTk.PhotoImage(REF_image)
			self.REF_label.configure(image=REF_photo)
			self.REF_label.image = REF_photo

		elif (method == "QRY_scale_up") and (self.QRY_label_index != QRY.frame_total):
			self.QRY_label_index += 1
			QRY_image = Image.open("/home/kylesm/Desktop/VRES/VRES_GUI/QRY_frame_%d.jpg" % self.QRY_label_index)
			QRY_photo = ImageTk.PhotoImage(QRY_image)
			self.QRY_label.configure(image=QRY_photo)
			self.QRY_label.image = QRY_photo

		elif (method == "QRY_scale_up") and (self.QRY_label_index == QRY.frame_total):
			self.QRY_label_index = 0
			QRY_image = Image.open("/home/kylesm/Desktop/VRES/VRES_GUI/QRY_frame_%d.jpg" % self.QRY_label_index)
			QRY_photo = ImageTk.PhotoImage(QRY_image)
			self.QRY_label.configure(image=QRY_photo)
			self.QRY_label.image = QRY_photo

		elif (method == "QRY_scale_down") and (self.QRY_label_index != 0):
			self.QRY_label_index -= 1
			QRY_image = Image.open("/home/kylesm/Desktop/VRES/VRES_GUI/QRY_frame_%d.jpg" % self.QRY_label_index)
			QRY_photo = ImageTk.PhotoImage(QRY_image)
			self.QRY_label.configure(image=QRY_photo)
			self.QRY_label.image = QRY_photo

		elif (method == "QRY_scale_down") and (self.QRY_label_index == 0):
			self.QRY_label_index = QRY.frame_total
			QRY_image = Image.open("/home/kylesm/Desktop/VRES/VRES_GUI/QRY_frame_%d.jpg" % self.QRY_label_index)
			QRY_photo = ImageTk.PhotoImage(QRY_image)
			self.QRY_label.configure(image=QRY_photo)
			self.QRY_label.image = QRY_photo

		# updating the frame numbers txt
		self.REF_number.configure(text='Frame Number %d' % self.REF_label_index)
		self.QRY_number.configure(text='Frame Number %d' % self.QRY_label_index)
		

if __name__ == "__main__":

	#videos to be loaded
	REF_vid_url = '/home/kylesm/Desktop/VRES/VRES_GUI/sync_iphone.mov'
	QRY_vid_url = '/home/kylesm/Desktop/VRES/VRES_GUI/sync_iphone.mov'

	root = Tk()
	
	loc_vis = CameraLocGUI(root)
	root.mainloop()







