#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


# Ignifuga Game Engine
# SDL 2D Canvas
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.backends.CanvasBase cimport CanvasBase
from ignifuga.backends.sdl.Font cimport Font
from SDL cimport *

cdef class Canvas (CanvasBase):
    cdef object __weakref__
    cdef SDL_Renderer * _sdlRenderer
    cdef SDL_Texture * _surfacehw
    cdef SDL_Surface * _surfacesw
    cdef bytes _srcURL, _fontURL
    cdef readonly bint _isRenderTarget, _hw
    cdef readonly int _width, _height, _fontSize, _req_width, _req_height
    cdef bytes embedded_data
    cdef Font _font
    cdef readonly object spriteData
    
    cpdef blitCanvas(self, CanvasBase canvas, int dx=*, int dy=*, int dw=*, int dh=*, int sx=*, int sy=*, int sw=*, int sh=*, int blend=*)
    cdef blitCanvasHW(self, Canvas canvas, int dx, int dy, int dw, int dh, int sx, int sy, int sw, int sh, int blend)
    cdef blitCanvasSW(self, Canvas canvas, int dx, int dy, int dw, int dh, int sx, int sy, int sw, int sh, int blend)
    cpdef mod(self, float r, float g, float b, float a)
    cpdef text(self, text, color, fontURL, fontSize)