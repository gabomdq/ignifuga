#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


# Ignifuga Game Engine
# Canvas Base
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

cdef class CanvasBase (object):
    cdef int width, height
    cdef float _r,_g,_b,_a
    cpdef blitCanvas(self, CanvasBase canvas, int dx=*, int dy=*, int dw=*, int dh=*, int sx=*, int sy=*, int sw=*, int sh=*, int blend=*)
    cpdef mod(self, float r, float g, float b, float a)
    cpdef text(self, text, color, fontName, fontSize)