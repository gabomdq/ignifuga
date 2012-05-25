#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


# Ignifuga Game Engine
# Main Renderer
# Backends available: SDL
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.backends.TargetBase cimport TargetBase
from ignifuga.backends.CanvasBase cimport CanvasBase
from cpython cimport bool

cdef class Renderer:
    cdef double frameTimestamp
    cdef double frameLapse
    cdef tuple nativeResolution
    # Scale factor = screen/scene
    cdef double _scale_x, _scale_y
    cdef TargetBase _target
    #cdef list dirtyRects
    # Native scene resolution
    cdef double _native_res_w, _native_res_h
    # Native scene size
    cdef double _native_size_w, _native_size_h
    cdef bool _keep_aspect
    # Scroll displacement in screen coordinates
    cdef int _scroll_x, _scroll_y

    cpdef update(self)
    #cpdef dirty(self, int x, int y, int w, int h)
    cpdef setNativeResolution(self, double w=*, double h=*, bool keep_aspect=*, bool autoscale=*)
    cpdef setSceneSize(self, int w, int h)
    cpdef _calculateScale(self, double scene_w, double scene_h, int screen_w, int screen_h, bool keep_aspect=*)
    cpdef windowResized(self)
    cpdef scrollBy(self, int deltax, int deltay)
    cpdef scrollTo(self, int x, int y)
    cpdef scaleBy(self, int delta)
    cpdef scaleByFactor(self, double factor)
    cpdef centerScene(self)
    cpdef centerOnScenePoint(self, double sx, double sy)
    cpdef centerOnScreenPoint(self, int sx, int sy)
    cpdef tuple screenToScene(self, int sx, int sy)
    cpdef tuple sceneToScreen(self, double sx, double sy)
