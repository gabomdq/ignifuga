#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


from cpython cimport bool

cdef class Rect(object):
    cdef public double left, top, width, height
    cpdef move(self, double x, double y)
    cpdef tuple flatten (self)
    cpdef Rect copy (self)
    cdef bool intersects(self, other)
    cpdef Rect intersection(self, Rect other)
    cpdef bool contains(self, Rect other)
    cpdef bool fits(self, Rect other)
    cpdef scale(self, double scale_x=*, double scale_y=*)
    cpdef list cutout(self, Rect other)
