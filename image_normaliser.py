
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
import image_utils  
import numpy

class IplImageNormaliser(object):
    """Do a set of standard preprocessing (normalisation) operations on an Ipl image"""
    def __init__(self):
        self.__resize_scale  = 1     #Floating point value: Resize cropped image with this scale factor, 
                                     #newsize = roud( resize_scale_fac*old_size )
        self.__filter_size = 0       #Filtering input image - if set to 0 no filtering will be performed
        self.clearRoi()             #Cv Rect specifying region of interest=None for no cropping
        self.__equalise_hist = False #Apply histogram equalisation or not
        self.__rot_mat = None       #Scaling and rotation affine matrix, set to None if no affine warping is required
        self.__cropped_image = None
      
    def clearRoi(self):
        self.__roi = None  
    
    def croppedImage(self):
        return self.__cropped_image
    
    def getRoi(self):
        if self.__roi is None:
            return None
        return cv.cvRect(self.__roi.x, self.__roi.y, self.__roi.width, self.__roi.height)  
    
    def setRoi(self, i_roi):
        self.__roi = cv.cvRect( i_roi.x, i_roi.y, i_roi.width, i_roi.height )
        
    def setParams(self, i_resize_scale=1, i_filter_size=0, i_eq=False, i_roi=None):
        self.__resize_scale = i_resize_scale
        self.__filter_size =  i_filter_size
        if not i_roi == None:
            self.__roi = cv.cvRect( i_roi.x, i_roi.y, i_roi.width, i_roi.height )
        else:
            self.__roi = None
        self.__equalise_hist  = i_eq
        
    def clearAffine(self):
        self.__rot_mat = None
    
    def setAffineTransform(self, i_center, i_scale, i_rot_angle):
        """See open cv documentation of cvWarpAffine"""
        if  (abs(i_scale - 1.0) < 1E-6) and ( abs(i_rot_angle) < 1E-6 ):
            self.__rot_mat = None
        else:
            self.__rot_mat = cv.cvCreateMat(2,3, 5) #Affine matrix
            cv.cv2DRotationMatrix( i_center, i_rot_angle, i_scale, self.__rot_mat )
    
    def similarityTransform(self, i_image, i_transform, i_crop=True ):
        """Apply affine transform around center of region of interest, then translate roi"""
        tx = numpy.int32(numpy.round(i_transform[0]))
        ty = numpy.int32(numpy.round(i_transform[1]))
        scale = i_transform[2]
        angle = i_transform[3]
        center = cv.cvPoint2D32f( self.__roi.x + self.__roi.width/2,self.__roi.y + self.__roi.height/2 )
        self.setAffineTransform( center, scale, angle)
        original_roi = cv.cvRect( self.__roi.x,  self.__roi.y,  self.__roi.width,  self.__roi.height)
        
        if not i_crop:
            self.__roi = None
        else:
            self.__roi.x = self.__roi.x + int(tx)
            self.__roi.y = self.__roi.y + int(ty)
        filter_size = self.__filter_size
        self.__filter_size = 0
        o_image =  self.normalise(i_image)
        self.__filter_size = filter_size
        self.__roi = cv.cvRect(original_roi.x, original_roi.y, original_roi.width,  original_roi.height)
        return  cv.Ipl2NumPy(o_image)
    
    def correctImage(self, i_image, i_transform):
        roi = self.getRoi()
        tx = numpy.int( numpy.round( i_transform[0] ) )
        ty = numpy.int( numpy.round( i_transform[1] ) )
        roi.x += tx
        roi.y += ty
        self.setRoi(roi)
        scale = i_transform[2]
        angle = i_transform[3]
        center = cv.cvPoint2D32f( self.__roi.x + self.__roi.width/2,self.__roi.y + self.__roi.height/2 )
        self.setAffineTransform( center, scale, angle)
        o_image =  self.normalise(i_image)
        return  cv.Ipl2NumPy(o_image)
    
    def crop(self, i_image):
        src_region = cv.cvGetSubRect(i_image, self.__roi)
        self.__cropped_image = cv.cvCreateImage( cv.cvSize(self.__roi.width, self.__roi.height) , 8 , 1)
        cv.cvCopy(src_region, self.__cropped_image)
        return self.__cropped_image
        
    def normalise(self, i_ipl_image):
        #Do the affine transform
        if self.__rot_mat == None:
            warped_image = i_ipl_image
        else:
            warped_image = cv.cvCreateImage(cv.cvSize(i_ipl_image.width,i_ipl_image.height), 8, 1)
            cv.cvWarpAffine(i_ipl_image , warped_image,  self.__rot_mat );
        #Crop
        if self.__roi == None:
            self.__cropped_image = warped_image
        else:
            self.crop(warped_image)
        #Scale
        if  self.__resize_scale == 1:
            scaled_image = self.__cropped_image
        else: 
            w = int(round( self.__cropped_image.width * self.__resize_scale))
            h = int(round( self.__cropped_image.height * self.__resize_scale))
            scaled_image = cv.cvCreateImage(cv.cvSize(w, h), 8, 1)
            cv.cvResize( self.__cropped_image, scaled_image ,cv.CV_INTER_LINEAR)
        #Histogram equalisation
        if self.__equalise_hist: 
            cv.cvEqualizeHist(scaled_image,scaled_image)
        #Blur
        if self.__filter_size == 0: 
            smoothed_image = scaled_image
        else: 
            smoothed_image = cv.cvCreateImage(cv.cvSize(scaled_image.width, scaled_image.height), 8, 1)
            cv.cvSmooth(scaled_image, smoothed_image, cv.CV_GAUSSIAN, self.__filter_size)
        return smoothed_image
        
    def normalise_batch(self, i_frame_list):
        o_data = [self.normalise(i_frame_list[n]) for n in range(0, len(i_frame_list))]
        return o_data

    def jitter( self, i_image , i_n_examples ):
        """1) Apply various random affine transform to i_image (scale, rotation), 
              where i_n_examples is the number of transformations. The affine transforms happen 
              around the center of the original region of interest. 
           2) Translate roi with various values - crop the image from this region.
           3) The same normalisation is then applied to all the cropped images, specified by setParams"""
        
        #Store transforms applied in format tx ty scale angle
        o_transforms = numpy.array([0., 0.,  1.,  0.]) 
        
        if self.__roi == None:
            print "No region of interest - returning input image!"
            return None
        #Always return the normalised verion of the input image
        image = cv.Ipl2NumPy(self.normalise(i_image))
        o_data = numpy.tile( None, (image.shape[0], image.shape[1], 1))
        o_data[:,:,0] =  image
        if i_n_examples == 0:
            return ( o_data, o_transforms)
        #Rotation point should be around original roi center
        center = cv.cvPoint2D32f( self.__roi.x + self.__roi.width/2,self.__roi.y + self.__roi.height/2 )
        angles = numpy.random.uniform(-30.,30.,i_n_examples)
        scales = numpy.random.uniform(0.9,1.1, i_n_examples)
        tx = numpy.int32( numpy.round( numpy.random.uniform(-20,20,i_n_examples)))
        ty = numpy.int32( numpy.round( numpy.random.uniform(-20,20,i_n_examples)))
        x = self.__roi.x + tx
        y = self.__roi.y + ty
        #FIXME: Extend valid indices to outliers due to affine transform!!!
        min_x = 0; min_y = 0;
        max_x = i_image.width - self.__roi.width - 1
        max_y = i_image.height - self.__roi.height - 1  
        valid_x = numpy.hstack([numpy.nonzero( x >= min_x )[0], numpy.nonzero( x < max_x)[0]])
        valid_y = numpy.hstack([numpy.nonzero( y >= min_y )[0], numpy.nonzero( y < max_y)[0]])
        valid_idx = numpy.unique(numpy.hstack([valid_x, valid_y]))
        original_roi = cv.cvRect( self.__roi.x,  self.__roi.y,  self.__roi.width,  self.__roi.height)
        if self.__rot_mat == None:
            original_rot_matrix = None
        else:
            original_rot_matrix = cv.cvCloneImage(self.__rot_mat)
        for index in valid_idx:
            params = numpy.array([tx[index], ty[index], scales[index], angles[index] ]) 
            self.setAffineTransform( center, scales[index], angles[index])
            self.__roi.x = int( x[index] )
            self.__roi.y = int( y[index] )     
            image = cv.Ipl2NumPy(self.normalise( i_image ))
            o_data = numpy.dstack( [o_data, image])
            o_transforms = numpy.vstack( [o_transforms, params])  
        #Restore the original region of interest
        self.__roi.x = original_roi.x
        self.__roi.y = original_roi.y
        if original_rot_matrix == None:
            self.__rot_mat= None
        else:
            self.__rot_mat = cv.cvCloneImage(original_rot_matrix)
        return (o_data, o_transforms)
    
    def jitter_video(self, i_data, i_n_jitter):
        """Batch processing - jitter a whole video according to region of interest"""    
        x = None
        y = None
        n_jittered = None
        
        for i in range(0, i_data.shape[2]):
            (jittered_images, transforms) = self.jitter(  image_utils.Numpy2Ipl( i_data[:,:,i] ),  i_n_jitter)
            start_index = 0
            if  x == None:
                start_index = 1
                x = jittered_images[:,:,0].ravel()
                if i_n_jitter > 0:
                    y = transforms[0,:]
                    n_jittered = numpy.array([jittered_images.shape[2]])
            else:
                if i_n_jitter > 0:
                    n_jittered = numpy.vstack([n_jittered, jittered_images.shape[2]])
                
            for j in range(start_index, jittered_images.shape[2]):
                x = numpy.vstack([x, jittered_images[:,:,j].ravel()])
                if i_n_jitter > 0:
                    y = numpy.vstack([y, transforms[j]])
        o_images = x
        o_transforms = y
        o_n_jittered = n_jittered
        return (o_images, o_transforms, o_n_jittered)

if __name__ ==  "__main__":
    from PyQt4 import QtCore, QtGui
    from sys import stdin, exit, argv
    from qt_image_display import ImageDisplay 
    from roi_detector import ViolaJonesRoi

   
    data = image_utils.Video2Numpy("recordings/calibration.avi", 1) 
    detector = ViolaJonesRoi()
    #Compute a region of interest automatically
    face_roi= detector.compute(data)
    eye_roi = detector.convertFace2EyeRoi(face_roi)
    detector.setRoi(eye_roi)
    (min_row, min_col, max_row, max_col)  = eye_roi
        
    roi = image_utils.Numpy2CvRect(min_row, min_col, max_row, max_col)
    #Setup normaliser
    normaliser = IplImageNormaliser()
    normaliser.setParams(i_resize_scale=1., i_filter_size=0, i_eq=False, i_roi=roi)
    center = cv.cvPoint2D32f( roi.x + roi.width/2, roi.y + roi.height/2 )
    normaliser.setAffineTransform(center, i_scale=1., i_rot_angle=0)
    nframe = 0
    app = QtGui.QApplication(argv)
    timer = QtCore.QTimer()
    n_jitter_examples = 5
    display = ImageDisplay(n_jitter_examples + 2)
    (jittered_images, transforms, n_jittered) = normaliser.jitter_video(data, n_jitter_examples)
    nframe = 0

    def updateDisplay():
        global nframe
        rows = max_row - min_row
        cols = max_col - min_col
                
        if nframe >= data.shape[2]:
            nframe = 0
        else:
            qt_image = image_utils.Numpy2QImage(data[:,:,nframe])
            display.setImage(qt_image)
            for i in range(nframe, nframe + n_jittered[nframe]):
                t = transforms[i,:]
                str = QtCore.QString("Frame=%d\n tx=%d\n ty=%d\n scale=%.2f\n angle=%.2f\n " %(nframe + i,t[0],t[1],t[2],t[3]) ) 
                img = jittered_images[i,:].reshape(rows,cols)
                qt_image = image_utils.Numpy2QImage(numpy.int32( img ) )
                display.setImage(qt_image, i+1 - nframe, 0,  str) 
        nframe += 1
        display.show()
    QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), updateDisplay )
    timer.start( 500 )
    ret_val = app.exec_()
    exit(ret_val)
 
