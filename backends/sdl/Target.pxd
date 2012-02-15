#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Ignifuga Game Engine
# SDL Render Target
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.backends.TargetBase cimport TargetBase
from ignifuga.backends.sdl.Canvas cimport Canvas
from ignifuga.backends.CanvasBase cimport CanvasBase
from SDL cimport *
from cpython cimport bool

cdef class Target (TargetBase):
    cdef SDL_Renderer * renderer
    cdef SDL_Window * window
    cdef bool _doublebuffered
    cdef SDL_RendererInfo render_info

    cpdef blitCanvas(self, CanvasBase canvas, int dx=*, int dy=*, int dw=*, int dh=*, int sx=*, int sy=*, int sw=*, int sh=*, double angle=*, bool offCenter=*, int centerx=*, int centery=*, int flip=*)
    cpdef updateSize(self)
