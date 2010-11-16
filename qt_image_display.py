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

from PyQt4 import  QtCore, QtGui
import frame_recorder
import numpy
 
class ImageDisplay(QtGui.QWidget):
    """Display and update a QImage in a QLabel"""
    def __init__(self,i_cols_number = 1 , i_rows_number=1,  parent = None ):
        QtGui.QWidget.__init__(self, parent)
        h_layout = QtGui.QHBoxLayout()
        self.__labels = []
        self.__text_labels = []
        self.__cols = i_cols_number
        self.__rows = i_rows_number
        for i in range(0, i_cols_number):
            vbox_layout = QtGui.QVBoxLayout() 
            label_text = QtGui.QLabel()
            vbox_layout.addWidget(label_text)
            for  j in range(0, i_rows_number):
                label_img = QtGui.QLabel()#f=QtCore.Qt.WNoAutoErase)
                vbox_layout.addWidget(label_img)
                self.__labels.append(label_img) 
            
            self.__text_labels.append(label_text)
            h_layout.addLayout(vbox_layout)
        self.setLayout(h_layout)
        self.resize( 320, 240 )
         
    def getLabels(self):
        return self.__labels
    
    def clear(self):
        for i in range(0, len(self.__labels)):
            self.__labels[i].clear()
            self.__labels[i].resize(0,0)
            
        for i in range(0, len(self.__text_labels)):
            self.__text_labels[i].clear()
            self.__text_labels[i].resize(0,0)
    
    def setText(self, i_index=0, i_text=None):
        if not( i_text == None):
            self.__text_labels[i_index].setText(i_text)
            
    def setSize(self, i_width, i_height, i_index_col=0, i_index_row = 0):
        idx = i_index_col*self.__rows + i_index_row
        self.__labels[idx].resize(i_width, i_height)
        
    def setImage(self, i_image, i_index_col=0, i_index_row = 0,  i_text=None, i_scale=1.):
        """Update the display with a new image"""
        if not i_text is None:
            self.__text_labels[i_index_col].setText(i_text)
        idx = i_index_col*self.__rows + i_index_row
        w = i_image.width()*i_scale
        h = i_image.height()*i_scale
        self.setSize(w, h)
        self.__labels[idx].setPixmap(QtGui.QPixmap.fromImage(i_image).scaled(w,h))
        #self.repaint()
  
    def drawRectangleRaw( self, io_image, i_min_row, i_min_col, i_max_row, i_max_col, i_color=QtGui.QColor("red") , i_pen_width=2):
        """Overlay a red rectangle on the input image"""
        face_rect = QtCore.QRect(i_min_col, i_min_row, i_max_col-i_min_col, i_max_row-i_min_row)
        painter = QtGui.QPainter( io_image )
        pen = QtGui.QPen(i_color)
        pen.setWidth(i_pen_width)
        painter.setPen(pen)
        painter.drawRect( face_rect )  
        painter.end()
    
    def drawRectangle( self, io_image, i_rect, i_color=QtGui.QColor("red")  ):
        """Overlay a red rectangle on the input image"""
        painter = QtGui.QPainter( io_image )
        pen = QtGui.QPen(i_color)
        pen.setWidth(6)
        painter.setPen(pen)
        painter.drawRect( i_rect)  
        painter.end()
        
    def drawImage(self, io_image, i_image, i_x=0., i_y=0.):
        #Draw i_image on io_image at position x,y of io_image
        painter = QtGui.QPainter( io_image )
        point = QtCore.QPoint(i_x, i_y)
        painter.drawImage( point, i_image)
        painter.end()
    
    def drawLines(self, io_image,   start_xy_line, end_xy_line, color=QtGui.QColor("red") ):
        pen = QtGui.QPen(color)
        painter = QtGui.QPainter( io_image )
        pen.setWidth(0.25)
        painter.setPen(pen)
        lines = [QtCore.QLine ( start_xy_line[n,0], start_xy_line[n,1], end_xy_line[n,0],  end_xy_line[n,1] ) for n in range(0, len(start_xy_line)) ]
        painter.drawLines(lines )  
 
    def drawPoints(self, io_image,   i_points, color=QtGui.QColor("red") ):
        if len(i_points) > 0:
            pen = QtGui.QPen(color)
            painter = QtGui.QPainter( io_image )
            pen.setWidth(5)
            painter.setPen(pen)
            [painter.drawPoint(i_points[n,0],i_points[n,1]) for n in range(0, i_points.shape[0]) ]
        

    def drawArrows( self, io_image,  start_xy_line, end_xy_line, sze, color=QtGui.QColor("red") ):
    
    # pt, ppt, sze, color=QtGui.QColor("red") ):
        """A simple function to draw an arrow - for more intricate arrow designs
           one can use arrow=matplotlib.patches.FancyArrow(), and draw the polygon
           specified by the control points arrow.xy
        
           Input:
                    * start_xy_line: starting point of line 
                    * end_xy_line: end point of a line (where arrow will be inserted)
                    * sze: size of arrow
           """
        
        #doublePoint pd, pa, pb;
        #double tangent;
        pen = QtGui.QPen(color)
        painter = QtGui.QPainter( io_image )
        pen.setWidth(1)
        painter.setPen(pen)
        
        """in order to get the arrowhead the correct way round, 
         * we reverse the gradient. 
         * This is equivalent to reversing the geometry below...
        """
        delta = start_xy_line - end_xy_line  
        sum = numpy.absolute(delta[:,0]) + numpy.absolute(delta[:,1]).flatten()
        (idx, ) = numpy.nonzero( sum > 1E-4 )
        
        if len(idx) < 1: 
            return 
        
        delta = delta[ idx, :]  
        s_line = start_xy_line[idx]
        e_line = end_xy_line[idx]
        tangent = numpy.arctan2( delta[:,1], delta[:,0])
        arrow_angle1 = tangent + numpy.pi / 6.
        arrow_angle2 = tangent - numpy.pi / 6.
        arrow_x1 = sze * numpy.cos (arrow_angle1) + e_line[:,0]
        arrow_y1 = sze * numpy.sin (arrow_angle1) + e_line[:,1]
        arrow_x2 = sze * numpy.cos (arrow_angle2) + e_line[:,0]
        arrow_y2 = sze * numpy.sin (arrow_angle2) + e_line[:,1]
        
        for n in range(0, len(idx)):
            #Draw the line (input)
            line_start_point = QtCore.QPointF(s_line[n,0], s_line[n,1])
            line_end_point   = QtCore.QPointF(e_line[n,0], e_line[n,1])
            painter.drawLine(line_start_point , line_end_point )  
            #Draw the first arrow side
            arrow_start_point = line_end_point
            arrow_end_point = QtCore.QPointF( arrow_x1[n], arrow_y1[n])
            painter.drawLine(arrow_start_point , arrow_end_point )  
            #Draw the second arrow side
            arrow_end_point = QtCore.QPointF( arrow_x2[n], arrow_y2[n])
            painter.drawLine(arrow_start_point , arrow_end_point )  
                    
    def drawEllipse(self, io_image,  i_x, i_y, i_size, i_color=QtGui.QColor("red")):
        brush = QtGui.QBrush( i_color )
        #pen = QtGui.QPen(QtGui.QColor("white"))
        #pen.setWidth(penWidth)
        painter = QtGui.QPainter(io_image)
        painter.setBrush(brush)
        #painter.setPen(pen)
        ellipse = QtCore.QRectF( i_x, i_y,  i_size, i_size )
        painter.drawEllipse(ellipse)
        return io_image
                    
    def drawProbabilities(self, i_width, i_height, i_color, i_prob):
        """Draw a circle inside a white rectangle that scales according to a probability.
           If i_prob = 1.0 the circle will touch the sides of the rectangles"""
        o_image = QtGui.QImage(i_width,i_height, QtGui.QImage.Format_ARGB32)
        o_image.fill( i_color.rgba())
        height = i_height / 4
        width = i_width / 4
        dim = max(height,width)
        penWidth = 2        
        topx = penWidth
        topy = i_height - penWidth - dim
        rect =  QtCore.QRectF( topx + 4*penWidth + 2*dim, topy, dim, dim )    
        top = dim/2- i_prob*dim/2
        ellipse = QtCore.QRectF(rect.x() +top, rect.y() + top, i_prob*dim , i_prob*dim )
        brush = QtGui.QBrush( QtGui.QColor("white") )
        pen = QtGui.QPen(QtGui.QColor("white"))
        pen.setWidth(penWidth)
        painter = QtGui.QPainter(o_image)
        painter.setBrush(brush)
        painter.setPen(pen)
        painter.drawRect(rect)
        brush = QtGui.QBrush( i_color)
        painter.setBrush(brush)
        painter.drawEllipse(ellipse)
        return o_image
        
class ImageDisplayAndRecord( ImageDisplay ):
    """Same as image display, but with the ability to record while displaying"""
    def __init__(self, i_file_name="out.avi",i_cols_number = 1 , i_rows_number=1,  parent = None):
        ImageDisplay.__init__(self, i_cols_number, i_rows_number,  parent )
        self.__is_record = False
        self.__recorder = frame_recorder.FrameRecorder()
        self.__recorder.setParams( i_file_name, i_fps=20)
    def setRecorderParams( self, i_file_name, i_fps):
        self.__recorder.setParams( i_file_name, i_fps)
    def getRecorderParams(self):
        return self.__recorder.getParams()
    def isRecord(self):
        return self.__is_record
    def startRecord(self):
        self.__is_record = True
    def addFrame(self, i_image):
        if self.__is_record:
            self.__recorder.addFrame(i_image)
    def stopRecording(self):
        if self.__is_record:
            self.__recorder.stopRecording()
            self.__is_record = False
            
