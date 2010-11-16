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

import opencv as cv
import opencv.highgui  
import image_utils
import qt_image_display
 

class FrameRecorder(object):
    def __init__(self, i_file_name="out.avi", i_fps=20, i_is_color=1 ):
        self.__videoWriter = None
        self.setParams( i_file_name, i_fps, i_is_color)
    
    def setParams( self, i_file_name, i_fps=20, i_is_color=1):
        self.stopRecording()
        self.__file_name = i_file_name
        self.__fps = i_fps
        self.__is_color = i_is_color
        
    def getParams( self ):
        return (self.__file_name, self.__fps, self.__is_color )
        
    def stopRecording(self):
        if not (self.__videoWriter == None):
            self.__videoWriter = None

    def __initVideoWriter(self, i_frame_size): 
        self.__videoWriter = cv.highgui.cvCreateVideoWriter(
                                    self.__file_name, 
                                    cv.highgui.CV_FOURCC('M','J','P','G'),
                                    self.__fps, 
                                    i_frame_size,
                                    self.__is_color ) 
        
    def addFrame(self, i_image ):
        if self.__videoWriter == None:
            frame_size = cv.cvSize(i_image.width , i_image.height )
            self.__initVideoWriter( frame_size )
            
        if i_image.nChannels == 3:
            cv.highgui.cvWriteFrame( self.__videoWriter, i_image ) 
        else:
            img = image_utils.IplGrayToRGB(i_image)
            cv.highgui.cvWriteFrame( self.__videoWriter, img ) 
  

if __name__ ==  "__main__":
    from PyQt4 import QtCore, QtGui
    from sys import stdin, exit, argv
    import qt_image_display
    from frame_grabber import  FrameGrabberWebCam
   
    timer = QtCore.QTimer()
    app = QtGui.QApplication(argv)
  
    #frame_grabber = FrameGrabberFile("out.avi", i_loop_back = True, i_scale=1.0)
    frame_grabber = FrameGrabberWebCam( i_scale=1., i_camera=0)
    frame_recorder =  FrameRecorder( i_file_name="out.avi", i_fps=20, i_is_color=1 )
    display =  qt_image_display.ImageDisplay()

    def updateDisplay():
        current_frame = frame_grabber.nextFrame()  
        if current_frame == None:
            print "No image available"
            timer.stop()
        else:        
            frame_recorder.addFrame(current_frame)
            qt_image =  frame_grabber.currentFrame('QImage')
            frame_rate = str(frame_grabber.frameRate())
            w = str(qt_image.width())
            h = str(qt_image.height())
            disp_str =  frame_rate + " fps, width = " +  w  + ", height = " + h
            display.setImage(qt_image, i_text=QtCore.QString(disp_str))
            display.show()
    QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), updateDisplay )
    timer.start( 20 )
    retVal = app.exec_()
    frame_recorder.stopRecording()
    exit(retVal)
