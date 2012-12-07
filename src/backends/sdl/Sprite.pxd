#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Ignifuga Game Engine
# SDL Sprite component
# Author: Gabriel Jacobo <gabriel@mdqinc.com>


from cpython cimport *
from libcpp.deque cimport *
from libcpp.map cimport *
from libcpp.pair cimport *
from libcpp.vector cimport *
from ignifuga.backends.sdl.SDL cimport *
from ignifuga.backends.sdl.Canvas cimport Canvas
from ignifuga.backends.sdl.Renderer cimport Renderer, _Sprite as _RendererSprite


ctypedef enum SPRITE_TYPE:
    SPRITE_TYPE_ATLAS = 0
    SPRITE_TYPE_DELTAP = 1
    SPRITE_TYPE_DELTAK = 2

ctypedef struct SPRITE_FRAME:
    int src_x, src_y
    int dst_x, dst_y
    int w,h

ctypedef struct SPRITE_OVERLAY:
    int x,y, op
    float r,g,b,a
    bint update
    PyObject *sprite

ctypedef char* char_p
ctypedef map[int,deque[SPRITE_FRAME]].iterator frame_iterator
ctypedef map[int,char_p].iterator hitmap_iterator
ctypedef map[int,SPRITE_OVERLAY].iterator overlay_iterator

cdef class _Sprite:
    """ Internal sprite implementation with animation"""
    cdef bint released
    cdef Canvas srcCanvas, canvas
    cdef int width, height, _frame, numFrames
    cdef SPRITE_TYPE type
    cdef deque[int] *keyframes
    cdef map[int,deque[SPRITE_FRAME]] *frames
    cdef map[int,char_p] *hitmap
    cdef char_p current_hitmap
    cdef object _hitmap

    cpdef free(self)
    cdef bint nextFrame(self)
    cdef bint prevFrame(self)
    cdef frame(self, int frame)
    cdef bint hits(self, int x, int y)


cdef class _SpriteComponent:
    cdef bint _started, _dirty
    cdef public bint forward, interactive, remainActiveOnStop, _static, _paused
    cdef public int loopMax, loop
    cdef Canvas _canvas, _atlas, _tmpcanvas
    cdef _Sprite sprite
    cdef Renderer renderer
    cdef public _SpriteComponent parent
    cdef object _spriteData
    cdef int _width_src, _height_src, _width_pre, _height_pre
    cdef public object onStart, onLoop, onStop
    cdef _RendererSprite *_rendererSprite
    cdef map[int,SPRITE_OVERLAY] *_overlays
    cdef int _lastBlurAmount, _blur
    cdef unsigned long lastUpdate

    cpdef init(self)
    cpdef free(self)
    cpdef _update(self, unsigned long now)
    cpdef updateRenderer(self)
    cdef _updateRenderer(self)
    cpdef updateRendererZ(self)
    cpdef reset(self)
    cpdef show(self)
    cpdef hide(self)
    cpdef reload(self, url)
    cdef _doCompositing(self)
    cpdef event(self, action, sx, sy)
    cdef _updateSize(self)
    cpdef hits(self, x, y)
    cpdef addOverlay(self, id, int x=?, int y=?, int z=?, float r=?, float g=?, float b=?, float a=?, int op=?, bint update=?)
    cpdef removeOverlay(self, int zindex, bint update=?)
    cpdef clearOverlays(self, update=?)
    cdef _doBluring(self, Canvas source, bint start_clean = ?)
    cpdef setFrame(self, int frame)
    cpdef setPaused(self, value)
    cpdef setOverlays(self, overlays)
