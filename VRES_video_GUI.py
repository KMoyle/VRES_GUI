import numpy as np
import matplotlib.pyplot as plt
import cv2

#load in video one and get 
vid_1 = cv2.VideoCapture('sync_sony.MTS')
vid_1.set(6, 100)
fps_1 = int(vid_1.get(cv2.CAP_PROP_FPS))
frames_1 = int(vid_1.get(cv2.CAP_PROP_FRAME_COUNT))

print ("fps = %d" % frames_1)

#load in video two
vid_2 = cv2.VideoCapture('sync_iphone.mov')
vid_2.set(cv2.CAP_PROP_FPS, 60)

#setting up figure for multiple images
fig = plt.figure()
plt.ion()

while(vid_1.isOpened()):
    ret, frame_1 = vid_1.read()
    ret, frame_2 = vid_2.read()

    gray_1 = cv2.cvtColor(frame_1, cv2.COLOR_BGR2GRAY)
    gray_2 = cv2.cvtColor(frame_2, cv2.COLOR_BGR2GRAY)

    gray_resized_1 = cv2.resize(gray_1, (640, 480))
    gray_resized_2 = cv2.resize(gray_2, (640, 480))

    a = fig.add_subplot(1,2,1)
    imgplot = plt.imshow(gray_resized_1)
    a = fig.add_subplot(1,2,2)
    imgplot = plt.imshow(gray_resized_2)

    
    #cv2.imshow('frame',gray_resized_1, gray_resized_2)
    

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    plt.show()
vid_1.release()
vid_2.release()
cv2.destroyAllWindows()