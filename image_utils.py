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
import numpy
from PyQt4 import  QtCore, QtGui
import ImageQt

"""OpenCV (Ipl), Numpy, Qt and Pil image utility functions"""
g_color_table = [ ((QtGui.qRgb(i , i,  i) & 0xffffff) - 0x1000000) for  i in range(0,256) ]

def IplRGBToGray( i_image ): 
    """Convert RGB Ipl image to gray scale, returns copy of image if the format is already right."""
    o_image = cv.cvCreateImage( cv.cvSize( i_image.width, i_image.height ), 8 ,1)
    if (i_image.depth == 8) and (i_image.nChannels == 1) :
        cv.cvCopy( i_image,  o_image ) 
    else:
        #cv.cvCvtColor(i_image, o_image , cv.CV_BGR2GRAY )
        cv.highgui.cvConvertImage( i_image, o_image )  
    return o_image

def IplGrayToRGB( i_image ): 
    """Convert RGB Ipl image to gray scale, returns copy of image if the format is already right."""
    o_image = cv.cvCreateImage( cv.cvSize( i_image.width, i_image.height ), 8 ,3)
    if (i_image.depth == 8) and (i_image.nChannels == 3) :
        cv.cvCopy( i_image,  o_image ) 
    else:
        #cv.cvCvtColor(i_image, o_image , cv.CV_BGR2GRAY )
        cv.highgui.cvConvertImage( i_image, o_image )  
    return o_image


def Ipl2QImage(i_image):
    """ Converts Ipl to QImage that can be displayed in a QLabel
        Only supports displaying grayscale OpenCV and QImages. limited  type checking!"""
    rgb_im = ( cv.Ipl2PIL(i_image)).convert("RGB")
    return ImageQt.ImageQt(rgb_im)
 
def Ipl2Pil(i_image):    
    o_flipped_image = cv.cvCreateImage( cv.cvSize( i_image.width, i_image.height ) , i_image.depth, i_image.nChannels )
    cv.cvFlip( i_image, o_flipped_image )
    o_pil_image = cv.adaptors.Ipl2Pil( o_flipped_image )
    return o_pil_image 
    
def IplResize(i_image, i_width, i_height):
    """Convert RGB to Gray scale and resize to input width and height"""
    small_image = cv.cvCreateImage( cv.cvSize( i_width, i_height  ) , i_image.depth,  i_image.nChannels )
    cv.cvResize( i_image , small_image )
    return small_image
    
def Ipl2Formats(i_image, i_formats=['QImage', 'Numpy', 'Pil']):
    """Return a dictionary of converted images as speciefied by input formats (list of strings):
       at the moment conversions from Ipl to QImage, Numpy and Pil are supported"""
    o_images = {}
    for format in i_formats:
        o_images[format] =   Ipl2Format( i_image, format) 
    return o_images
 
def Ipl2Format( i_image, i_format):
    """Return the converted image as specified by i_format (string): possibilities include:"""
    conversions = { 'QImage' :  Ipl2QImage,  
                    'Numpy'  :  cv.Ipl2NumPy,
                    'Pil'    :  Ipl2Pil }
    if conversions.has_key(i_format):
        f = conversions[i_format]
        return f(i_image)
    else:
        if not(i_format == 'Ipl'):
            raise ValueError, i_format, " format is not supported" 
        return None
 
def Numpy2QImage(i_image):
    """ Converts Numpy to QImage that can be displayed in a QLabel
        Only supports displaying grayscale Numpy and QImages. limited  type checking!"""
    image = numpy.ubyte(i_image).tostring()
    o_image = QtGui.QImage( image, i_image.shape[1], i_image.shape[0], i_image.shape[1], 
                            QtGui.QImage.Format_Indexed8 ).copy()
    o_image.setColorTable( g_color_table )
    return QtGui.QImage.convertToFormat ( o_image.copy(), QtGui.QImage.Format_RGB32 )

def Numpy2Ipl(i_image):
    image = numpy.ubyte(i_image)
    return cv.NumPy2Ipl(image)

def Numpy2Formats(i_image, i_formats=['QImage', 'Ipl']):
    """Return a dictionary of converted images as speciefied by input formats (list of strings):
       at the moment conversions from a Numpy array to QImage and Ipl images are supported"""
    o_images = {}
    for format in i_formats:
        o_images[format] =   Numpy2Format( i_image, format) 
    return o_images
 
def Numpy2Format( i_image, i_format):
    """Return the converted image as specified by i_format (string): possibilities include:"""
    conversions = { 'QImage' :  Numpy2QImage,  
                    'Ipl'  :    Numpy2Ipl }
    if conversions.has_key(i_format):
        f = conversions[i_format]
        return f(i_image)
    else:
        if not(i_format == 'Numpy'):
            raise ValueError, i_format, " format is not supported" 
        return None

def Video2Numpy2D( i_file, i_scale=1.):
    from frame_grabber import FrameGrabberFile
    """Return a 3D numpy array from a video file"""
    frame_grabber = FrameGrabberFile(i_file, i_loop_back = False)
    o_data = None 
    nframes = 0
    w = 0
    h = 0
    while True:
        current_frame = frame_grabber.nextFrame() 
        if current_frame == None:
            break
        else:
            current_frame = frame_grabber.currentFrame()
            w = int( i_scale * float(current_frame.width) + 0.5 )
            h = int( i_scale * float(current_frame.height) + 0.5 )
            image = IplResizeAndConvert(current_frame,w,h)
            image = cv.Ipl2NumPy(image)
            if o_data == None:
                o_data = image.reshape(1, w*h)
            else:
                o_data = numpy.vstack([o_data, image.reshape(1, w*h)])
    return (o_data, w, h)

def Video2IplList(i_file, i_scale=1.0, i_reverse_list=False):
    from frame_grabber import FrameGrabberFile
    """Return a list of video frames in opencv format - first frame first in list if i_reverse_list=False, otherwise first frame is last"""
    frame_grabber = FrameGrabberFile(i_file, i_loop_back = False)
    o_data = [] 

    while True:
        current_frame = frame_grabber.nextFrame() 
        if current_frame == None:
            break
        else:
            current_frame = frame_grabber.currentFrame()
            w = int( i_scale * float(current_frame.width) + 0.5 )
            h = int( i_scale * float(current_frame.height) + 0.5 )
            o_data.append( IplResizeAndConvert(current_frame,w,h) )
    if i_reverse_list:
        o_data.reverse()
    return o_data
    

def Video2Numpy( i_file, i_scale=1. ):
    from frame_grabber import FrameGrabberFile
    """Return a 3D numpy array from a video file"""
    frame_grabber = FrameGrabberFile(i_file, i_loop_back = False)
    o_data = None 
    nframes = 0
    while True:
        current_frame = frame_grabber.nextFrame() 
        if current_frame == None:
            break
        else:
            current_frame = frame_grabber.currentFrame()
            w = int( i_scale * float(current_frame.width) + 0.5 )
            h = int( i_scale * float(current_frame.height) + 0.5 )
            image = IplResizeAndConvert(current_frame,w,h)
            image = cv.Ipl2NumPy(image)
            if o_data == None:
                o_data = image 
            else:
                o_data = numpy.dstack([o_data, image])
    return o_data

def IplList2Numpy(i_data, i_dstack=True):
    o_data = None 
    for current_frame in i_data:
        image = cv.Ipl2NumPy(current_frame)
        if o_data is None:
            if i_dstack:
                o_data = image
            else:
                o_data = image.flatten()
        else:
            #Either dstack or flatten and vstack
            if i_dstack:
                o_data = numpy.dstack([o_data, image])
            else:
                o_data = numpy.vstack([o_data, image.flatten()])
    return o_data

def Numpy2CvRect(i_min_row=None, i_min_col=None, i_max_row=None, i_max_col=None, i_face_roi=None):
    """Convert roi from matrix format (min_row, min_col, max_row, max_col) to opencv rect"""
    if i_face_roi is not None:
        (i_min_row, i_min_col, i_max_row, i_max_col) = i_face_roi
    y = i_min_row
    x = i_min_col
    height  = i_max_row - y
    width =i_max_col - x
    return cv.cvRect(x, y, width, height)     

def Cv2NumpyRect(i_roi):
    if i_roi is None:
        return
    min_row = i_roi.y
    min_col = i_roi.x
    max_row = min_row + i_roi.height
    max_col = min_col + i_roi.width
    return (min_row, min_col, max_row, max_col) 

def PlotRoi(i_ipl_image=None, i_ipl_roi=None, i_numpy_img=None):
    import pylab
    if i_numpy_img is not None:
        img = i_numpy_img
        pylab.imshow(img )
    else:
        img = cv.Ipl2NumPy(i_ipl_image)
        pylab.imshow(img,cmap = pylab.cm.gray)
 
    x = [i_ipl_roi.x, i_ipl_roi.x + i_ipl_roi.width, i_ipl_roi.x+i_ipl_roi.width, i_ipl_roi.x, i_ipl_roi.x]
    y = [i_ipl_roi.y, i_ipl_roi.y, i_ipl_roi.y+i_ipl_roi.height, i_ipl_roi.y+i_ipl_roi.height,i_ipl_roi.y]
    pylab.plot(x, y, 'r')
    disp_str = "Roi: x="+str(i_ipl_roi.x) + " y=" + str(i_ipl_roi.y) + " width="+str(i_ipl_roi.width) + " height="
    #disp_str += (str(i_ipl_roi.height) + "\n"+"Image: " + str(i_ipl_image.width) + " " + str(i_ipl_image.height))
    pylab.title(disp_str) 
    pylab.axis('image')
    
def CropImage(i_ipl_image, i_ipl_roi):
    src_region = cv.cvGetSubRect( i_ipl_image, i_ipl_roi)
    cropped_image = cv.cvCreateImage( cv.cvSize( i_ipl_roi.width,  i_ipl_roi.height) , 8 , 1)
    cv.cvCopy(src_region, cropped_image)
    return cropped_image
