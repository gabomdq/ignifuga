#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Ignifuga Game Engine
# SDL Render Target
# Author: Gabriel Jacobo <gabriel@mdqinc.com>
from cpython cimport bool
from ignifuga.backends.CanvasBase cimport CanvasBase

cdef class TargetBase (object):    
    cdef int _width, _height
    cdef bool _fullscreen
    cdef str platform

    cpdef clear(self, x, y, w, h)
    cpdef clearRect(self, rect)
    cpdef blitCanvas(self, CanvasBase canvas, int dx=*, int dy=*, int dw=*, int dh=*, int sx=*, int sy=*, int sw=*, int sh=*, double angle=*, bool offCenter=*, int centerx=*, int centery=*, int flip=*)
    cpdef flip(self)
    cpdef isVisible(self)
