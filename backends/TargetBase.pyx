#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Ignifuga Game Engine
# SDL Render Target
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

cdef class TargetBase (object):
    def __init__ (self, width=1280, height=800, **kwargs):
        raise Exception('method not implemented')

    @property
    def width(self):
        return self._width
    
    @property
    def height(self):
        return self._height

    @property
    def isDoubleBuffered(self):
        return False

    cpdef clear(self, x, y, w, h):
        raise Exception('method not implemented')

    cpdef clearRect(self, rect):
        raise Exception('method not implemented')

    cpdef blitCanvas(self, CanvasBase canvas, int dx=0, int dy=0, int dw=-1, int dh=-1, int sx=0, int sy=0, int sw=-1, int sh=-1, double angle=0, bool offCenter=False, int centerx=0, int centery=0, int flip=0 ):
        raise Exception('method not implemented')

    cpdef flip(self):
        raise Exception('method not implemented')

    cpdef isVisible(self):
        raise Exception('method not implemented')

    property visible:
        def __get__(self):
            return self.isVisible()