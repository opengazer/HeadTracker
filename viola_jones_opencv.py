

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

# Extract path of this module
my_path = __file__
pos = __file__.rfind('/')
if pos != -1:
    my_path = my_path[:pos+1]
else:
    my_path = ''

from opencv.cv import *
from opencv.highgui import *
import numpy

"""Wrapper class for Viola Jones face detector (returns largest face rectangle, 
   no processing is done on the input image)"""

# Global Variables
g_cascade = None
g_storage = cvCreateMemStorage(0)
g_cascade_name = my_path + 'haarcascade_frontalface_alt.xml'
#g_cascade_name = my_path + 'haarcascade_profileface.xml'

"""parameters for haar detection
   From the API:
   The default parameters (scale_factor=1.1, min_neighbors=3, flags=0) are tuned 
   for accurate yet slow object detection. For a faster operation on real video 
   i_images the settings are: 
   scale_factor=1.2, min_neighbors=2, flags=CV_HAAR_DO_CANNY_PRUNING, 
   min_size=<minimum possible face size"""

g_parameters = {
    'robust': { # Settings for slow but robust detection--tuned for filtering web i_images
        'min_size': 0.03, #minimum size (w,w), where w = max(factor * i_image size
        'window_scale': 1.1,
        'min_neighbors': 3,
        'haar_flags': 0,
    },
    'webcam': { # Settings for faster detection--tuned for webcam input
        'min_size': 0.03,
        'window_scale':1.1,
        'min_neighbors': 3,
        'haar_flags': CV_HAAR_FIND_BIGGEST_OBJECT,
    },
}

def viola_jones_opencv(i_image, i_method='webcam', i_param=None):
    # i_image should be a cvMat
    # returns a rectangle in matrix coordinates (min_row, min_col, max_row, max_col)
    global g_cascade, g_parameters
    if i_param is None:
        i_param = g_parameters[i_method]
    search_width = int( float( i_image.width ) * i_param['min_size'] + 0.5 )
    search_height = int( float( i_image.height ) * i_param['min_size'] + 0.5 )
    max_length = max( search_width, search_height )
    min_size = cvSize( max_length, max_length ) 
    faces = cvHaarDetectObjects( i_image, g_cascade, g_storage, i_param['window_scale'],
                                i_param['min_neighbors'], i_param['haar_flags'],  min_size )
    if not(faces[0] == None):
        max_size = 0
        best_face = None
        for f in faces:
            s = numpy.sqrt( (float(f.height))**2 + (float(f.width))**2)
            if s >= max_size:
                max_size = s
                best_face = (f.y, f.x , f.y + f.height , f.x + f.width )
        return best_face
    return None

g_cascade = cvLoadHaarClassifierCascade(g_cascade_name, cvSize(1,1))
if not g_cascade:
    print "ERROR: Could not load classifier g_cascade"
    import sys
    sys.exit(-1)
    
if __name__ == "__main__":
    import image_utils
    import qt_image_display
    from PyQt4 import QtCore, QtGui
    from sys import stdin, exit, argv
 
    fileName =  "face_example.jpg"   
    print "Detecting faces in FILE: " , fileName
    image = cvLoadImage(fileName)
    face_rect =  viola_jones_opencv(image, i_method='webcam', i_param=None)
    
    if face_rect == None:
        print "No face detected!"
    else:
        (min_row, min_col, max_row, max_col) = face_rect
        image_gray = image_utils.IplRGBToGray(image)
        qt_image = image_utils.Ipl2QImage( image_gray)
        app = QtGui.QApplication(argv)
        display = qt_image_display.ImageDisplay()
        display.drawRectangleRaw(qt_image, min_row, min_col, max_row, max_col )     
        display.setImage( qt_image  )   
        display.show()
        retVal = app.exec_() 
        exit(retVal)
