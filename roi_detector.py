
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

import opencv as cv
from viola_jones_opencv import viola_jones_opencv
import numpy
import image_utils as ImageUtils

class RoiDetector(object):
    """This class returns a region of interest from a sequence of images (stored in a 3-dim numpy array)"""
    def __init__(self):
        self.__min_row = 0  
        self.__max_row = 0  
        self.__min_col = 0
        self.__max_col = 0
        
    def setPrev(self, x,y, width, height):
        self.__prev_x = x
        self.__prev_y = y
        self.__prev_width = width
        self.__prev_height = height
       
    def compute( self, i_images ):
        return (self.__min_row, self.__min_col, self.__max_row, self.__max_col )

    def setRoi( self, i_roi ):
        self.__min_row = i_roi[0]
        self.__min_col = i_roi[1]
        self.__max_row =  i_roi[2]
        self.__max_col = i_roi[3]

    def getRoi( self ):
        return (self.__min_row, self.__min_col, self.__max_row, self.__max_col )
    
    def scaleRoi(self, i_roi, i_scale, i_max_width, i_max_height):
        """Scale the input roi with the scale factor provided, the roi is clipped
            if it falls out of the image boundaries"""
        (min_row, min_col, max_row, max_col) = i_roi
        ipl_roi = ImageUtils.Numpy2CvRect(min_row, min_col, max_row, max_col)
        height = ipl_roi.height*i_scale
        width = ipl_roi.width*i_scale
        delta_height = ipl_roi.height - height
        delta_width = ipl_roi.width - width
        ipl_roi.x += numpy.int(numpy.round( delta_width*0.5 ))
        ipl_roi.y += numpy.int(numpy.round( delta_height*0.5 ))
        ipl_roi.width =  numpy.int(numpy.round(width))
        ipl_roi.height = numpy.int(numpy.round(height))
        if ipl_roi.x < 0:
            ipl_roi.x  = 0
        if ipl_roi.y < 0:
            ipl_roi.y = 0
        if (ipl_roi.x + ipl_roi.width) > i_max_width:
            ipl_roi.width = i_max_width - ipl_roi.x
        if (ipl_roi.y + ipl_roi.height) > i_max_height:
            ipl_roi.height = i_max_height - ipl_roi.y
        (min_row, min_col, max_row, max_col) = ImageUtils.Cv2NumpyRect(ipl_roi)
        return (min_row, min_col, max_row, max_col)
         
    def trackRoi(self, i_ipl_image, i_adapt_window_size=True):
     
        face_roi = self.compute([i_ipl_image], i_ipl=True)
        if face_roi is None:
            return (0.0,  0.0, self.__prev_x, self.__prev_y, self.__prev_width, self.__prev_height)
        
        roi = ImageUtils.Numpy2CvRect( i_face_roi=face_roi )
        x = 0.9*self.__prev_x + 0.1*( roi.x + 0.5*roi.width)
        y = 0.9*self.__prev_y + 0.1*( roi.y + 0.5*roi.height)
        w = 0.9*self.__prev_width + 0.1*roi.width
        h = 0.9*self.__prev_height + 0.1*roi.height
    
        o_x = x - self.__prev_x
        o_y = y - self.__prev_y
      
        self.__prev_x = x
        self.__prev_y = y
        if i_adapt_window_size:
            self.__prev_width = w
            self.__prev_height = h
        return (o_x, o_y, self.__prev_x, self.__prev_y, self.__prev_width, self.__prev_height)
 
class ViolaJonesRoi( RoiDetector):
    """The first face in the sequence of numpy arrays is returned"""
    def __init__(self, i_scale=1.0):
        RoiDetector.__init__(self)
        self.__frame = -1
        self.__n_rows = 0
        self.__n_cols = 0
        self.__scale = i_scale
        
    def compute(self, i_data, i_ipl=False):
        frame = 0
        self.__frame = -1
        max_dist = 0
        
        if i_ipl:
            nframes = len(i_data)
        else:
            nframes = i_data.shape[2]
        list_of_roi = []
        list_of_frames = []
        list_of_sizes = []
        
        for frame in range(0, nframes):
            if i_ipl:
                ipl_image = i_data[frame]
            else:
                ipl_image = cv.NumPy2Ipl(i_data[:,:,frame])
                
            if self.__scale < 1.0:
                w = numpy.int(numpy.round( float( ipl_image.width ) * self.__scale ))
                h = numpy.int(numpy.round( float( ipl_image.height ) * self.__scale ))
                small_image = cv.cvCreateImage( cv.cvSize( w, h  ) , ipl_image.depth, ipl_image.nChannels )
                cv.cvResize( ipl_image , small_image )
                vj_box = viola_jones_opencv(small_image)
            else:
                vj_box = viola_jones_opencv(ipl_image)

            if vj_box is not None:
                (min_row, min_col, max_row, max_col) = vj_box
                w = max_col - min_col
                h = max_row - min_row
                dist = w*w + h*h       
                list_of_roi.append(vj_box)
                list_of_frames.append(frame)
                list_of_sizes.append(dist)
                self.__n_rows = ipl_image.height 
                self.__n_cols = ipl_image.width
        #Choose a percentile of the sorted list
        nboxes = len(list_of_sizes)
        if nboxes == 0:
            #print "Viola-Jones failed on all images"
            return
        list_of_sizes = numpy.array(list_of_sizes)
        idx = numpy.argsort(list_of_sizes)
        percentile = 0.8
        arg_idx = numpy.int(numpy.round(percentile * nboxes))
        if arg_idx >= nboxes:
            arg_idx = nboxes - 1
        if arg_idx < 0:
            arg_idx = 0
            
        #print "n boxes: ", nboxes, " chosen arg: ", arg_idx
        self.__frame = frame  = list_of_frames[idx[arg_idx]]
        best_roi =  list_of_roi[idx[arg_idx]]
        (min_row, min_col, max_row, max_col) = best_roi
        if self.__scale < 1.0:
            #print "best roi width = ", max_col - min_col, " best roi height = ", max_row-min_row
            max_col  =  numpy.int(numpy.round( float(max_col) / self.__scale ))
            max_row  =  numpy.int(numpy.round( float(max_row) / self.__scale ))
            min_col  =  numpy.int(numpy.round( float(min_col) / self.__scale ))
            min_row  =  numpy.int(numpy.round( float(min_row) / self.__scale ))
        vj_box = (min_row, min_col, max_row, max_col)  
        self.setRoi(vj_box)
        return self.getRoi()
        
    def getDetectedFrame(self):
        return self.__frame
    
    def convertFace2EyeRoi(self, i_roi):
        (min_row, min_col, max_row, max_col) = i_roi
        n_rows = max_row - min_row
        new_min_row = min_row + n_rows / 4
        new_max_row = new_min_row + n_rows/4
        
        n_cols = max_col - min_col
        new_min_col = min_col + n_cols / 9
        new_max_col = new_min_col + 7*n_cols/9
        return (new_min_row, new_min_col, new_max_row, new_max_col)
    
 
