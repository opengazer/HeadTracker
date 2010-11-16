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
import time

class FrameStore(object):
    """This class contains images of different formats, all derived from the basetype image.
       The basetype image is associated with a string ID, e.g., Ipl for opencv images, 
       and a function pointer to handle image conversions."""
    def __init__(self, i_id, i_converter ):
        self.__frames = {}
        self.__id = i_id
        self.__converter = i_converter
    def setFrame( self, i_image, i_formats=None ):
        """Update frame store.
           Inputs:  i_image: Image corresponding basetype image, 
                    i_formats: A list of string IDs associated with different formats.
                               When i_formats = None, only the basetype format will be stored, i.e., 
                               the i_image
           Output:  A dictionary of images"""
        self.__frames = {}
        if i_formats == None:
            self.__frames = {self.__id : i_image}
        else:
            self.__frames = self.__converter(i_image , i_formats)
            if not self.__frames.has_key(self.__id):
                self.__frames[self.__id]  = i_image
            else:
                if  self.__frames[self.__id] == None:
                    self.__frames[self.__id]  = i_image  
        return self.__frames
    def getFrame(self, i_format):
        """Return the frame in the specified format.
        If the requested format has already been computed, simply return the 
        stored image, otherwise convert on the fly and store."""
        if not self.__frames.has_key(self.__id):
            msg = "Frame store not initialised with an image associated with " + self.__id
            raise ValueError, msg
        else:
            if self.__frames.has_key(i_format):
                return self.__frames[i_format]
            else:
                image = self.__converter( self.__frames[self.__id],  [i_format])
                return image[i_format]
  
class IplFrameStore(FrameStore):
    def __init__(self):
        FrameStore.__init__(self, 'Ipl', image_utils.Ipl2Formats)

class NumpyFrameStore(FrameStore):
     def __init__(self):
        FrameStore.__init__(self, 'Numpy', image_utils.Numpy2Formats)
    
class FrameGrabber(object):
    """Grab images from a capturing device - at the moment capture from file and real-time 
   camera capture are supported. Available formats:
   Each FrameGrabber simply captures raw images and stores them in a variety of formats.
   The following formats are supported: 
    'Ipl', 'Numpy', 'QImage', 'PIL'
   All images are stored in a frame store which can be used as a separate module to e.g, 
   store a bunch of images derived from the same Ipl image when shared by many classes. 
   Sequential processing assumed at the moment (i.e., not thread safe!) """
    
 
    def __init__(self, i_capture_device, i_scale=1. , i_color=False):
        self.__current_frame = IplFrameStore()
        self.__capture_device = i_capture_device
        self.__scale = i_scale
        self.__time_start = time.time()
        self.__frame_cnt = 0
        self.__fps = 0
        self.__is_color = i_color
        
    def release(self):
        cv.highgui.cvReleaseCapture(self.__capture_device)
 
    def setScale(self, i_value):
        self.__scale = i_value

    def nextFrame(self):
        """Read the next frame from the capturing device.
           Note that the captured image is flipped horisontally."""
        current_frame = cv.highgui.cvQueryFrame(self.__capture_device )
        if not( current_frame == None ):
            cv.cvFlip(current_frame, None, 1);
          
            if self.__scale < 1.0:
                width = int(current_frame.width*self.__scale  + 0.5)
                height = int(current_frame.height*self.__scale + 0.5)
                current_frame = image_utils.IplResize(current_frame, width, height)
                
            if not self.__is_color: 
                current_frame = image_utils.IplRGBToGray(  current_frame)
        
            self.__current_frame.setFrame( current_frame )
            t = time.time()
            diff = t - self.__time_start
            if diff > 1:
                self.__fps =  self.__frame_cnt
                self.__frame_cnt = 0
                self.__time_start = t
            else:
                self.__frame_cnt += 1
            return self.currentFrame()
         
    def frameRate(self):
        return self.__fps
  
    def currentFrame(self, i_format='Ipl'):
        """Return the most recently captured frame in the format specified -
           if the requested format has already been computed, simply return the
           stored image, otherwise convert here.
           Supported formats include:
           Ipl: Opencv image
           QImage: Qt image
           PIL: PIL image
           Numpy: Numpy array"""
        return self.__current_frame.getFrame(i_format) 
    
class FrameGrabberWebCam(FrameGrabber):
    def __init__(self, i_scale=1., i_camera=0, i_color=False):
        FrameGrabber.__init__(self, cv.highgui.cvCreateCameraCapture(i_camera), i_scale, i_color)

    def setFrameRate(self, i_frame_rate):
        cv.highgui.cvSetCaptureProperty(  self._FrameGrabber__capture_device,  cv.highgui.CV_CAP_PROP_FPS, i_frame_rate)
        
    def setFrameSize(self, i_width, i_height):
        cv.highgui.cvSetCaptureProperty( self._FrameGrabber__capture_device,  cv.highgui.CV_CAP_PROP_FRAME_WIDTH, i_width)
        cv.highgui.cvSetCaptureProperty( self._FrameGrabber__capture_device,  cv.highgui.CV_CAP_PROP_FRAME_HEIGHT, i_height)        
        
class FrameGrabberFile(FrameGrabber):
    def __init__(self, i_file, i_loop_back = True, i_scale=1.,  i_color=False):
        FrameGrabber.__init__(self, cv.highgui.cvCreateFileCapture(i_file ), i_scale, i_color )
        self.loop_back = i_loop_back
    def restart(self, i_file, i_loop_back = True):
        FrameGrabber.__init__(self, cv.highgui.cvCreateFileCapture(i_file ) )
        self.loop_back = i_loop_back
    def setFramePos(self, i_pos):
        cv.highgui.cvSetCaptureProperty(  self._FrameGrabber__capture_device, cv.highgui.CV_CAP_PROP_POS_FRAMES, i_pos )
    def nextFrame(self):
        current_frame = FrameGrabber.nextFrame(self)
        if ( current_frame == None) and (self.loop_back):
            self.setFramePos(0)
            return  FrameGrabber.nextFrame(self)
        else: 
            return current_frame
        
if __name__ ==  "__main__":
    from PyQt4 import QtCore, QtGui
    from sys import stdin, exit, argv
    import qt_image_display
   
    timer = QtCore.QTimer()
    app = QtGui.QApplication(argv)
 
    #frame_grabber = FrameGrabberFile("out.avi", i_loop_back = True, i_scale=1.0)
    frame_grabber = FrameGrabberWebCam( i_scale=1.0, i_camera=0, i_color=False)
    display =  qt_image_display.ImageDisplay()

    def updateDisplay():
        current_frame = frame_grabber.nextFrame()  
        if current_frame == None:
            print "No image available"
            timer.stop()
        else:        
            qt_image =  frame_grabber.currentFrame('QImage')
            frame_rate = str(frame_grabber.frameRate())
            w = str(qt_image.width())
            h = str(qt_image.height())
            disp_str =  frame_rate + " fps, width = " +  w  + ", height = " + h
            display.setImage(qt_image, i_text=QtCore.QString(disp_str))
            display.show()
    QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), updateDisplay )
    timer.start( 50 )
    retVal = app.exec_()
    exit(retVal)
