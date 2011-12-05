#Copyright (c) 2010,2011, Gabriel Jacobo
#All rights reserved.

#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions are met:

    #* Redistributions of source code must retain the above copyright
      #notice, this list of conditions and the following disclaimer.
    #* Redistributions in binary form must reproduce the above copyright
      #notice, this list of conditions and the following disclaimer in the
      #documentation and/or other materials provided with the distribution.
    #* Altered source versions must be plainly marked as such, and must not be
      #misrepresented as being the original software.
    #* Neither the name of Gabriel Jacobo, MDQ Incorporeo, Ignifuga Game Engine
      #nor the names of its contributors may be used to endorse or promote
      #products derived from this software without specific prior written permission.
    #* You must NOT, under ANY CIRCUMSTANCES, remove, modify or alter in any way
      #the duration, code functionality and graphic or audio material related to
      #the "splash screen", which should always be the first screen shown by the
      #derived work and which should ALWAYS state the Ignifuga Game Engine name,
      #original author's URL and company logo.

#THIS LICENSE AGREEMENT WILL AUTOMATICALLY TERMINATE UPON A MATERIAL BREACH OF ITS
#TERMS AND CONDITIONS

#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL GABRIEL JACOBO NOR MDQ INCORPOREO NOR THE CONTRIBUTORS
#BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from cpython cimport bool

cdef class Rect(object):
    def __init__(self, xywh):
        """
        xywh must be a 2 or 4 tuple or a Rect instance.
        """
        if isinstance(xywh, Rect):
            self.left = xywh.left
            self.top = xywh.top
            self.width = xywh.width
            self.height = xywh.height
        else:
            if len(xywh) == 4:
                self.width = float(xywh[2])
                self.height = float(xywh[3])
                self.left = float(xywh[0])
                self.top = float(xywh[1])
            elif len(xywh) == 2:
                self.width = float(xywh[0])
                self.height = float(xywh[1])
                self.left = 0.0
                self.top = 0.0

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
        return Rect(self)
        
    cdef bool intersects(self, other):
        """
        Test if a rect intersects with this rect.
        """
        if self.left > other.left+other.width: return False
        if self.top > other.top + other.height: return False
        if self.left + self.width < other.left: return False
        if self.top + self.width  < other.bottom: return False
        return True 

    cpdef Rect intersection(self, Rect other):
        """
        Return the intersection of this rect and other rect.
        Return None if no intersection.
        """
        left = max((self.left, other.left))
        top = max((self.top, other.top))
        right = min((self.right, other.right))
        bottom = min((self.bottom, other.bottom))
        if left > right or top > bottom: return None
        return Rect((left,top,right-left+1,bottom-top+1))

    cpdef bool contains(self, Rect other):
        """
        Return True if self contains other
        """
        if other.left >= self.left and other.right <= self.right:
            if other.top >= self.top and other.bottom <= self.bottom:
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
            r = Rect((self.left, self.top, other.left-self.left,self.bottom-self.top+1))
            if r.width > 0 and r.height > 0:
                rects.append(r)
                
            # R2
            r = Rect((other.left, self.top, other.right-other.left+1,other.top-self.top))
            if r.width > 0 and r.height > 0:
                rects.append(r)
            
            # R3
            r = Rect((other.right+1, self.top, self.right-other.right,self.bottom-self.top+1))
            if r.width > 0 and r.height > 0:
                rects.append(r)
            
            # R4
            r = Rect((other.left, other.bottom+1, other.right-other.left+1,self.bottom-other.bottom))
            if r.width > 0 and r.height > 0:
                rects.append(r)

            return rects
        else:
            return [Rect(self),]