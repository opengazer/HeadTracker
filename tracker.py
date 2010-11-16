
#!/usr/bin/env python

############################################################################
#    Copyright 2010 Emli-Mari Nel
#    This file is part of Opengazer-headtracker
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#    See <http://www.gnu.org/licenses/>
############################################################################
 
from roi_detector import ViolaJonesRoi
from image_normaliser import IplImageNormaliser
import image_utils
import numpy
import opencv as cv
import os
from PyQt4 import QtCore, QtGui
import time
from sys import stdin, exit, argv
import qt_image_display
from frame_grabber import FrameGrabberWebCam
from frame_grabber import FrameGrabberFile
 
class  HeadTracker(object): 
    def __init__(self, i_viola_scale=0.5, i_img_resize_scale=1.0):
         
        self.__params = {
            'filter_size' : 0,  
            'viola_scale': i_viola_scale
        }
        self.__normaliser =  IplImageNormaliser()
        self.__normaliser.setParams( i_resize_scale=i_img_resize_scale, i_filter_size=self.__params['filter_size'],
                        i_eq=False, i_roi=None)
        self.__roi_detector = ViolaJonesRoi( i_scale= self.__params['viola_scale'])
        
    def getParams(self):
        return self.__params 
    
    def setGain(self, i_gain):
        self.__xy_gain = float(i_gain)
    
    def detectRoi(self, i_data, i_roi_scale_factor=1.2, i_track=True):
        ipl_roi = self.__normaliser.getRoi() 
        if (ipl_roi is not None) and not(i_track):
            x = numpy.float(ipl_roi.x) + 0.5*ipl_roi.width
            y = numpy.float(ipl_roi.y) + 0.5*ipl_roi.height
            self.__roi_detector.setPrev(x, y, ipl_roi.width, ipl_roi.height)
            return (0., 0., x,y, ipl_roi.width, ipl_roi.height)
        if ipl_roi is None:
            face_roi = self.__roi_detector.compute([i_data], i_ipl=True)
            if face_roi is None:
                return (0.0, 0.0, 0.0, 0.0,0.0, 0.0)
            face_roi = self.__roi_detector.scaleRoi(face_roi, i_roi_scale_factor, i_data.width-1, i_data.height-1)
            ipl_roi = image_utils.Numpy2CvRect( i_face_roi = face_roi)
            self.__normaliser.setRoi(ipl_roi)

            x = numpy.float(ipl_roi.x) + 0.5*ipl_roi.width
            y = numpy.float(ipl_roi.y) + 0.5*ipl_roi.height
            self.__roi_detector.setPrev(x, y, ipl_roi.width, ipl_roi.height)
        
            return (0.0, 0.0, x, y, ipl_roi.width, ipl_roi.height)
        #At this point i_track=True, ipl_roi is not None
        return self.__roi_detector.trackRoi(i_data )
 
    def update(self, i_ipl_image, i_track=False):
        (delta_x, delta_y, x,y,w,h) = self.detectRoi(i_ipl_image,i_track=i_track)
        return (delta_x, delta_y, x, y,w,h)
    
    def setRoi(self, i_roi):
        self.__normaliser.setRoi(i_roi)
        self.__roi_detector.setRoi(image_utils.Cv2NumpyRect)
        
    def getRoi(self, i_ipl=False):
        if i_ipl:
            return self.__normaliser.getRoi()
        return image_utils.Cv2NumpyRect(self.__normaliser.getRoi())
    
    def clearRoi(self):
        self.__normaliser.clearRoi()
        

class HeadTrackerDisplay(QtGui.QWidget):
 
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.__active_box.setChecked(False)
    
    def __init__(self, i_head_tracker, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.__display =  qt_image_display.ImageDisplayAndRecord()
        #Recording button 
        self.__record_button = QtGui.QPushButton(self)
        self.__record_button.setCheckable(True)
        self.__record_button.setObjectName("recordButton")
        self.__record_button.setText("Record")
        self.connect( self.__record_button, QtCore.SIGNAL("clicked(bool)"),  self.recordSlot )
        
        #File playback button 
        self.__file_button = QtGui.QPushButton(self)
        self.__file_button.setCheckable(True)
        self.__file_button.setObjectName("fileButton")
        self.__file_button.setText("Display .avi")
        self.connect( self.__file_button, QtCore.SIGNAL("clicked(bool)"),  self.fileSlot )  
    
        #Run Viola Jones on each frame and get the largest face
        self.__face_button = QtGui.QPushButton(self)
        self.__face_button.setCheckable(True)
        self.__face_button.setObjectName("detectButton")
        self.__face_button.setText("Detect faces")
        #Tracking checkBox
        self.__tracking_box = QtGui.QCheckBox()
        self.__tracking_box.setChecked(True)
        self.__tracking_box.setObjectName("trackingBox")
        self.__tracking_box.setText("Enable tracking")
        #Enable xy coordinate out put
        self.__active_box = QtGui.QCheckBox()
        self.__active_box.setChecked(False)
        self.__active_box.setObjectName("activeBox")
        self.__active_box.setText("Activate Cursor Control (ESC to exit)")
        #The scroll bar
        self.__scrollbar_gain_x = QtGui.QScrollBar()
        self.__scrollbar_gain_x.setGeometry(QtCore.QRect(0, 190, 291, 20))
        self.__scrollbar_gain_x.setMinimum(1)
        self.__scrollbar_gain_y = QtGui.QScrollBar()
        self.__scrollbar_gain_y.setGeometry(QtCore.QRect(0, 190, 291, 20))
        self.__scrollbar_gain_y.setMinimum(1)
        slider_max = 100
        self.__scrollbar_gain_x.setMaximum(slider_max)
        self.__scrollbar_gain_x.setProperty("value", QtCore.QVariant(slider_max/2))
        self.__scrollbar_gain_x.setSliderPosition(slider_max/2)
        self.__scrollbar_gain_x.setOrientation(QtCore.Qt.Horizontal)
        self.__scrollbar_gain_x.setObjectName("scrollbar_gain")
        self.__scrollbar_gain_y.setMaximum(slider_max)
        self.__scrollbar_gain_y.setProperty("value", QtCore.QVariant(slider_max/2))
        self.__scrollbar_gain_y.setSliderPosition(slider_max/2)
        self.__scrollbar_gain_y.setOrientation(QtCore.Qt.Horizontal)
        self.__scrollbar_gain_y.setObjectName("scrollbar_gain")
        self.__label_gain_x = QtGui.QLabel()
        self.__label_gain_x.setText(QtCore.QString("X gain"))
        self.__label_gain_y = QtGui.QLabel()
        self.__label_gain_y.setText(QtCore.QString("Y gain"))
        
        #Camera capture settings
        self.__scale_select = QtGui.QDoubleSpinBox()
        self.__scale_select.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.__scale_select.setMaximum(1.0)
        self.__scale_select.setMinimum(0.1)
        self.__scale_select.setSingleStep(0.25)
        self.__scale_select.setProperty("value", QtCore.QVariant(1.0))
        self.__scale_label = QtGui.QLabel()
        self.__scale_label.setText(QtCore.QString("Image scale"))     
        
        
        self.__device = QtGui.QComboBox(self)
        self.__device.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.__device.setObjectName("device")
        for n in range(0, 6):
            self.__device.addItem(QtCore.QString(str(n)), QtCore.QVariant(n))  
        
        self.__device.setCurrentIndex(0)
        self.__device_label = QtGui.QLabel()
        self.__device_label.setText(QtCore.QString("Device number"))    
        
        #Set the layout
        g_layout = QtGui.QGridLayout()  
        g_layout.addWidget(self.__face_button, 0, 0)
        g_layout.addWidget(self.__record_button,1,0)
        g_layout.addWidget(self.__file_button, 2, 0)
        g_layout.addWidget(self.__tracking_box,3,0)
        g_layout.addWidget(self.__active_box,4, 0)
        g_layout.addWidget(self.__label_gain_x,5,0)
        g_layout.addWidget(self.__scrollbar_gain_x),6,0
        g_layout.addWidget(self.__label_gain_y,7,0)
        g_layout.addWidget(self.__scrollbar_gain_y,8,0)
        g_layout.addWidget(self.__scale_label,9,0)
        g_layout.addWidget(self.__scale_select,10,0)
        g_layout.addWidget(self.__device_label,11,0)
        g_layout.addWidget(self.__device,12,0)
        v_layout = QtGui.QVBoxLayout()  
        v_layout.addWidget(self.__display)
        spacer = QtGui.QSpacerItem(10, 100, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        v_layout.addItem(spacer)
        
        g_layout.addLayout(v_layout, 0, 1,12,1)
      
        self.setLayout(g_layout)
        #Screen size
        desktop = QtGui.QDesktopWidget()
        screen_size = QtCore.QRectF(desktop.screenGeometry(desktop.primaryScreen()))
        x = screen_size.x() + screen_size.width()
        y = screen_size.y() + screen_size.height()
        self.__current_pos = [x/2., y/2.] 
         
        #Init the core algorithms
        self.__frame_grabber_file=  FrameGrabberFile("out.avi")
        (cam, is_data) = self.__device.itemData(self.__device.currentIndex()).toInt()
        self.__frame_grabber_cam = FrameGrabberWebCam(i_scale=self.__scale_select.value(),i_camera=cam)
        self.__frame_grabber = self.__frame_grabber_cam
        self.__head_tracker = i_head_tracker

        #Connect signals
        QtCore.QObject.connect(self.__scale_select, QtCore.SIGNAL("valueChanged(double)"), self.updateImageScale )
        QtCore.QObject.connect(self.__device, QtCore.SIGNAL("currentIndexChanged(int)"), self.updateDevice )
       
        #Main functions
        self.__timer = QtCore.QTimer()
        QtCore.QObject.connect(self.__timer, QtCore.SIGNAL("timeout()"), self.update )
        self.__timer.start( 20 )
    
    def updateDevice(self,i_index):
        self.__timer.stop()
        (cam, is_data) = self.__device.itemData(i_index).toInt()
        #FIXME: We shouldn't have to release the memory in Python?
        self.__frame_grabber_cam.release()
        self.__frame_grabber_cam = FrameGrabberWebCam(i_scale=self.__scale_select.value(),i_camera=cam)
        self.__head_tracker.clearRoi()
        self.__timer.start()
    
    def updateImageScale(self,i_value):
        self.__frame_grabber.setScale(i_value)
        self.__head_tracker.clearRoi()
        
    def update(self):
        current_frame = self.__frame_grabber.nextFrame()  
        if current_frame == None:
            print "No image available from selected device"
        else:       
            if self.__face_button.isChecked():
                self.__head_tracker.clearRoi() 
            (delta_x, delta_y, x, y, w, h) = self.__head_tracker.update(current_frame, i_track=self.__tracking_box.isChecked())    
            gain_x = float(self.__scrollbar_gain_x.value())
            gain_y = float(self.__scrollbar_gain_y.value())
            self.__current_pos[0] += (delta_x * gain_x)
            self.__current_pos[1] += (delta_y * gain_y)
            
            desktop = QtGui.QDesktopWidget()
            screen_size = QtCore.QRectF(desktop.screenGeometry(desktop.primaryScreen()))
            if self.__current_pos[0] < screen_size.x():
                self.__current_pos[0] = screen_size.x()
            if self.__current_pos[0] > ( screen_size.x() +  screen_size.width()):
                self.__current_pos[0] = screen_size.x() +  screen_size.width()
            if self.__current_pos[1] < screen_size.y():
                self.__current_pos[1] = screen_size.y()
            if self.__current_pos[1] > ( screen_size.y() +  screen_size.height()):
                self.__current_pos[1] = screen_size.y() +  screen_size.height()
            
            qt_image = image_utils.Ipl2QImage( image_utils.IplGrayToRGB(self.__frame_grabber.currentFrame()))
            roi = self.__head_tracker.getRoi()
            if roi is not None:
                point  = numpy.atleast_2d(numpy.array([x, y]))
                self.__display.drawPoints( qt_image, point)
                self.__display.drawRectangleRaw(qt_image,y-0.5*h,x-0.5*w,y+0.5*h,x+0.5*h, i_color=QtGui.QColor("red") , i_pen_width=2)
            
            
            if self.__display.isRecord():
                ipl_image = self.__frame_grabber.currentFrame( 'Ipl')
                self.__display.addFrame( image_utils.IplRGBToGray(ipl_image) )
           
            fps = "Capture rate: " + str(self.__frame_grabber.frameRate()) + " fps"
            im_size = "Image size: " + str(qt_image.width()) + " x " + str(qt_image.height()) + "\n"
            disp_str = im_size + fps
            self.__display.setImage(qt_image, i_text=QtCore.QString(disp_str))
    
            if self.__active_box.isChecked():
                QtGui.QCursor.setPos(self.__current_pos[0], self.__current_pos[1] )
   
    ###########################################################################
    #Recording
    ###########################################################################
    def recordSlot(self, checked):
        if checked:
            self.__timer.stop()
            filename = QtGui.QFileDialog.getSaveFileName( self, "Select output file",os.getcwd(), "Avi Files (*.avi)")
            if len(filename) > 0:
                self.__record_button.setText("Stop recording")
                self.__display.setRecorderParams( str(filename), i_fps =20)
                self.__display.startRecord()
            self.__timer.start()
        else:
            self.__display.stopRecording()
            self.__record_button.setText("Record") 
            
    ###########################################################################
    #Change capturing device to be from file not from webcam
    ###########################################################################
    def fileSlot(self, checked):
        if checked:
            self.__timer.stop()
            filename = QtGui.QFileDialog.getOpenFileName( self, "Select output file",os.getcwd(), "Avi Files (*.avi)")
            if len(filename) > 0:
                self.__frame_grabber_file.restart( i_file=str(filename), i_loop_back = True)
                self.__frame_grabber = self.__frame_grabber_file
                self.__file_button.setText("Stop display from .avi")
            self.__timer.start()
        else:
            self.__frame_grabber = self.__frame_grabber_cam
            self.__file_button.setText("Display .avi")
        
if __name__ == "__main__":     
    app = QtGui.QApplication(argv)
    head_tracker = HeadTracker()
    disp = HeadTrackerDisplay(i_head_tracker=head_tracker)
    disp.show()
    retVal = app.exec_()
    exit(retVal)
