#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Ignifuga Game Engine
# Canvas Base
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

# xcython: profile=True

cdef class CanvasBase (object):
    def __init__ (self, width=None, height=None, hw=True, srcURL = None, isRenderTarget = False):
        raise Exception('method not implemented')

    property width:
        def __get__(self):
            return self._width
    
    property height:
        def __get__(self):
            return self._height
    
    property hw:
        def __get__(self):
            return self._hw

    property r:
        def __get__(self):
            return self._r

    property g:
        def __get__(self):
            return self._g

    property b:
        def __get__(self):
            return self._b

    property a:
        def __get__(self):
            return self._a

    cpdef blitCanvas(self, CanvasBase canvas, int dx=0, int dy=0, int dw=-1, int dh=-1, int sx=0, int sy=0, int sw=-1, int sh=-1, int blend=-1):
        raise Exception('method not implemented')

    cpdef mod(self, float r, float g, float b, float a):
        raise Exception('method not implemented')

    cpdef text(self, text, color, fontName, fontSize):
        raise Exception('method not implemented')

