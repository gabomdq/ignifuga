#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


# Ignifuga Game Engine
# SDL2 based renderer
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.backends.sdl.SDL cimport *
from ignifuga.backends.sdl.Canvas cimport Canvas
from libc.stdlib cimport *
from libc.string cimport *
from libcpp.map cimport *
from libcpp.deque cimport *
from libcpp.pair cimport *

cdef struct _Sprite:
    # sx,sy  -> are the source coordinates in the sprite (0,0 as the sprite will always handle its own compositing)
    # sw,sh  -> are the dimensions of the source material/sprite
    # dx,dy  -> entity coordinates where to render
    # dw,dh  -> entity dimensions in scene coordinates
    SDL_Rect src, dst
    SDL_Texture *texture
    double angle
    SDL_Point center
    SDL_RendererFlip flip
    int z

ctypedef _Sprite* Sprite_p

cdef class Sprite:
    cdef Sprite_p sprite

cdef class Renderer:
    cdef Uint32 frameTimestamp, frameLapse
    cdef tuple nativeResolution
    # Scale factor = screen/scene
    cdef double _scale_x, _scale_y
    #cdef list dirtyRects
    # Native scene resolution
    cdef double _native_res_w, _native_res_h
    # Native scene size
    cdef double _native_size_w, _native_size_h
    cdef bint _keep_aspect
    # Scroll displacement in screen coordinates
    cdef int _scroll_x, _scroll_y

    # Sprites
    cdef map[int,deque[Sprite_p]] *zmap
    cdef deque[Sprite_p] *free_sprites
    cdef bint dirty

    cpdef update(self, Uint32 now)
    cpdef getTimestamp(self)
    cpdef checkRate(self, Uint32 lastTime, Uint32 rate)
    cpdef checkLapse(self, Uint32 lastTime, Uint32 lapse)
    #cpdef dirty(self, int x, int y, int w, int h)
    cpdef setNativeResolution(self, double w=*, double h=*, bint keep_aspect=*, bint autoscale=*)
    cpdef setSceneSize(self, int w, int h)
    cpdef _calculateScale(self, double scene_w, double scene_h, int screen_w, int screen_h, bint keep_aspect=*)
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

    cdef bint _allocSprites(self, int num=*)
    cdef bint _indexSprite(self, _Sprite *sprite)
    cdef bint _unindexSprite(self, _Sprite *sprite)


    cpdef Sprite addSprite(self, Canvas canvas, int z, int sx, int sy, int sw, int sh, int dx, int dy, int dw, int dh, double angle, int centerx, int centery, int flip)
    cpdef bint removeSprite(self, Sprite sprite_w)
    cpdef bint spriteZ(self, Sprite sprite_w, int z)
    cpdef bint spriteSrc(self, Sprite sprite_w, int x, int y, int w, int h)
    cpdef bint spriteDst(self, Sprite sprite_w, int x, int y, int w, int h, double angle, int centerx, int centery, int flip)
    cdef bint _spriteDst(self, _Sprite *sprite, int x, int y, int w, int h, double angle, int centerx, int centery, int flip)


    # Render target related stuff
    cdef int _width, _height
    cdef bint _fullscreen
    cdef str platform

    cdef SDL_Renderer * renderer
    cdef SDL_Window * window
    cdef bint _doublebuffered
    cdef SDL_RendererInfo render_info

    cpdef clear(self, x, y, w, h)
    cpdef clearRect(self, rect)
    cpdef flip(self)
    cpdef isVisible(self)
