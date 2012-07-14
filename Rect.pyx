#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


# xcython: profile=True

from cpython cimport bool


cdef class Rect(object):
#    def __init__(self, xywh):
#        """
#        xywh must be a 2 or 4 tuple or a Rect instance.
#        """
#        if isinstance(xywh, Rect):
#            self.left = xywh.left
#            self.top = xywh.top
#            self.width = xywh.width
#            self.height = xywh.height
#        else:
#            if len(xywh) == 4:
#                self.width = float(xywh[2])
#                self.height = float(xywh[3])
#                self.left = float(xywh[0])
#                self.top = float(xywh[1])
#            elif len(xywh) == 2:
#                self.width = float(xywh[0])
#                self.height = float(xywh[1])
#                self.left = 0.0
#                self.top = 0.0

    def __repr__(self):
        return "%s((%s,%s,%s,%s))" % (self.__class__.__name__, self.left, self.top, self.width, self.height)
        
    def __str__(self):
        return self.__repr__()

    #def __iter__(self):
    #    return (i for i in (self.left, self.top, self.width, self.height))
    #    pass

    property bottom:
        def __get__(self):
            return self.top + self.height - 1.0
        def __set__(self, float b):
            self.top = b - self.height + 1.0

    property right:
        def __get__(self):
            return self.left + self.width - 1.0
        def __set__(self, r):
            self.left = r - self.width + 1.0

    property center:
        def __get__(self):
            return self.left + (self.width*0.5), self.top + (self.height*0.5)
            
        def __set__(self, xy):
            self.left = xy[0] - (self.width*0.5)
            self.top = xy[1] + (self.height*0.5)
            
    property area:
        def __get__(self):
            return self.width * self.height
        
    cpdef move(self, double x, double y):
        """ Move the rectangle """
        self.left += x
        self.top += y
        
    cpdef tuple flatten (self):
        """ Flatten the rectangle, return (x,y,w,h) """
        return (self.left, self.top, self.width, self.height)
        
    cpdef Rect copy (self):
        """ Return a new copy of the rectangle """
        return rectFromRect(self)

    cdef bool intersects(self, other):
        """
        Test if a rect intersects with this rect.
        """
        if self.left > other.left+other.width: return False
        if self.top > other.top + other.height: return False
        if self.left + self.width < other.left: return False
        if self.top + self.width  < (other.top + other.height - 1.0): return False
        return True 

    cpdef Rect intersection(self, Rect other):
        """
        Return the intersection of this rect and other rect.
        Return None if no intersection.
        """
        cdef double left, top, right, bottom, oright, obottom
#        left = max((self.left, other.left))
#        top = max((self.top, other.top))
#        right = min((self.left + self.width, other.left + other.width)) - 1.0
#        bottom = min((self.top + self.height , other.top + other.height)) - 1.0

        left = self.left if self.left>other.left else other.left
        top = self.top if self.top > other.top else other.top
        right = self.left + self.width - 1.0
        oright = other.left + other.width - 1.0
        right = right if right < oright else oright
        bottom = self.top + self.height - 1.0
        obottom = other.top + other.height - 1.0
        bottom = bottom if bottom < obottom else obottom

        if left > right or top > bottom: return None
        return rectFromXYWH(left,top,right-left+1,bottom-top+1)

    cpdef bool contains(self, Rect other):
        """
        Return True if self contains other
        """
        if other.left >= self.left and other.left + other.width <= self.left + self.width:
            if other.top >= self.top and other.top + other.height <= self.top + self.height:
                return True
        return False

    cpdef bool fits(self, Rect other):
        return self.width >= other.width and self.height >= other.height

    cpdef scale(self, double scale_x=1.0, double scale_y=1.0):
        self.left *= scale_x
        self.width *= scale_x
        self.top *= scale_y
        self.height *= scale_y
        
    cpdef list cutout(self, Rect other):
        """ Intersect self with other, then provide 4 rectangles of the non overlapping parts
        
        big one is self
        small one is other
        
        |-----------------------------|
        |         r2                  |
        |     |-------|               |
        |  r1 |       |  r3           |
        |     |       |               |
        |     |-------|               |
        |         r4                  |
        |-----------------------------|
        """
        cdef rects = []
        cdef Rect r
        
        if other.contains(self):
            return []
            
        if self.intersects(other):
            # R1
            r = rectFromXYWH(self.left, self.top, other.left-self.left,self.bottom-self.top+1)
            if r.width > 0 and r.height > 0:
                rects.append(r)
                
            # R2
            r = rectFromXYWH(other.left, self.top, (other.left + other.width - 1.0)-other.left+1,other.top-self.top)
            if r.width > 0 and r.height > 0:
                rects.append(r)
            
            # R3
            r = rectFromXYWH(other.left + other.width , self.top, (self.left + self.width - 1.0)-(other.left + other.width - 1.0),(self.top + self.height - 1.0)-self.top+1)
            if r.width > 0 and r.height > 0:
                rects.append(r)
            
            # R4
            r = rectFromXYWH(other.left, other.top + other.height, (other.left + other.width - 1.0)-other.left+1,(self.top + self.height - 1.0)-(other.top + other.height - 1.0))
            if r.width > 0 and r.height > 0:
                rects.append(r)

            return rects
        else:
            return [rectFromRect(self)]



cpdef Rect rectFromRect(Rect r):
    newr = Rect()
    newr.left = r.left
    newr.top = r.top
    newr.width = r.width
    newr.height = r.height
    return newr

cpdef Rect rectFromXYWH(double x, double y, double w, double h):
    newr = Rect()
    newr.left = x
    newr.top = y
    newr.width = w
    newr.height = h
    return newr

cpdef Rect rectFromWH( double w, double h):
    newr = Rect()
    newr.left = 0
    newr.top = 0
    newr.width = w
    newr.height = h
    return newr
