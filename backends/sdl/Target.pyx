#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


# Ignifuga Game Engine
# SDL Render Target
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.Log import debug, info, error
from ignifuga.Gilbert import Gilbert, Event
import sys, platform

SDL_WINDOWPOS_CENTERED_MASK = 0x2FFF0000
SDL_WINDOWPOS_UNDEFINED_MASK = 0x1FFF0000

cdef class Target (TargetBase):
    def __init__ (self, width=1280, height=800, fullscreen = True, **kwargs):
        # Create target window and renderer
        self._fullscreen = fullscreen
        cdef SDL_DisplayMode dm
        cdef int display = 0
        if 'display' in kwargs:
            display = kwargs[display]
            
        SDL_GetDesktopDisplayMode(display, &dm)

        debug("Desktop mode is %dx%d" % (dm.w, dm.h))
        self.platform = Gilbert().platform
        
        if self.platform in ['win32',]:
            if fullscreen:
                self.window = SDL_CreateWindow("Ignifuga",
                            SDL_WINDOWPOS_UNDEFINED_MASK | display, SDL_WINDOWPOS_UNDEFINED_MASK | display,
                            dm.w, dm.h, SDL_WINDOW_FULLSCREEN)
            else:
                self.window = SDL_CreateWindow("Ignifuga",
                            SDL_WINDOWPOS_CENTERED_MASK, SDL_WINDOWPOS_CENTERED_MASK, #
                            width, height, SDL_WINDOW_RESIZABLE)
        elif self.platform in ['linux',]:
            if fullscreen:
#                self.window = SDL_CreateWindow("Ignifuga",
#                            SDL_WINDOWPOS_UNDEFINED_MASK | display, SDL_WINDOWPOS_UNDEFINED_MASK | display,
#                            dm.w, dm.h, SDL_WINDOW_FULLSCREEN)
                self.window = SDL_CreateWindow("Ignifuga",
                    SDL_WINDOWPOS_CENTERED_MASK, SDL_WINDOWPOS_CENTERED_MASK,
                    width, height, SDL_WINDOW_FULLSCREEN)
            else:
                self.window = SDL_CreateWindow("Ignifuga",
                            SDL_WINDOWPOS_CENTERED_MASK, SDL_WINDOWPOS_CENTERED_MASK,
                            width, height, SDL_WINDOW_RESIZABLE)
        else:
            # Android doesn't care what we tell it to do, it creates a full screen window anyway
            self.window = SDL_CreateWindow("Ignifuga",
                            SDL_WINDOWPOS_CENTERED_MASK, SDL_WINDOWPOS_CENTERED_MASK,
                            width, height, SDL_WINDOW_FULLSCREEN)

        if self.window == NULL:
            error("COULD NOT CREATE SDL WINDOW")
            error(SDL_GetError())
            sys.exit(1)
            return

        #self.renderer = SDL_CreateRenderer(self.window, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC)
        self.renderer = SDL_CreateRenderer(self.window, -1, 0)
        self.updateSize()
        
        #renderer = cast(self.renderer, POINTER(SDL_Renderer))
        #self._width = renderer.contents.viewport.w
        #self._height = renderer.contents.viewport.h
        #print "Window size: ", self._width, self._height

        SDL_GetRendererInfo(self.renderer, &self.render_info)

        #if bytes(self.render_info.name) in ['opengles', 'opengles2', 'direct3d']:
            # This renderers have 2 or more separate render surfaces, we have to render the whole screen all the time
            #self._doublebuffered = True
        #else:
            # OPENGL, etc
            # Not double buffered, we can render only the required parts of the screen
            #self._doublebuffered = False
            
        # Test: Render it all as if doublebuffered
        self._doublebuffered = True
        debug('SDL backend is %s' % bytes(self.render_info.name))

        # Start with a black window
        SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 255);
        SDL_RenderClear(self.renderer);
        SDL_RenderPresent(self.renderer);

    def __dealloc__(self):
        debug('Releasing SDL main render target')
        if self.renderer != NULL:
            SDL_DestroyRenderer(self.renderer)
        if self.window != NULL:
            SDL_DestroyWindow(self.window)

    property width:
        def __get__(self):
            return self._width

    property height:
        def __get__(self):
            return self._height

    property isDoubleBuffered:
        def __get__(self):
            return self._doublebuffered

    cpdef updateSize(self):
        SDL_GetWindowSize(self.window, &self._width, &self._height)
        SDL_RenderSetViewport(self.renderer, NULL)
        debug('updateSize: new window size is %d x %d' % (self._width, self._height))

    cpdef clear(self, x, y, w, h):
        self.ctx.clearRect(x,y,w,h);

    cpdef clearRect(self, rect):
        return self.clear(rect[0], rect[1], rect[2], rect[3])
    
    cpdef blitCanvas(self, CanvasBase canvasbase, int dx=0, int dy=0, int dw=-1, int dh=-1, int sx=0, int sy=0, int sw=-1, int sh=-1, double angle=0, bool offCenter=False, int centerx=0, int centery=0, int flip=0 ):
        cdef SDL_Rect srcRect, dstRect
        cdef SDL_Point center
        cdef Canvas canvas

        canvas = <Canvas>canvasbase

        center.x = centerx
        center.y = centery
        
        if sw == -1:
            sw = canvas.width
        if sh == -1:
            sh = canvas.height
        
        if dw == -1:
            dw = sw
        if dh == -1:
            dh = sh
            
        
        srcRect.x = sx
        srcRect.y = sy
        srcRect.w = sw
        srcRect.h = sh
        dstRect.x = dx
        dstRect.y = dy
        dstRect.w = dw
        dstRect.h = dh

        #print "Rendering from %d,%d,%d,%d to %d,%d,%d,%d" % (sx,sy,sw,sh,dx,dy,dw,dh)
        #sys.stdout.flush()

        if canvas.hw:
            if offCenter:
                SDL_RenderCopyEx(self.renderer, canvas._surfacehw, &srcRect, &dstRect, angle, &center, <SDL_RendererFlip> flip)
            else:
                SDL_RenderCopyEx(self.renderer, canvas._surfacehw, &srcRect, &dstRect, angle, NULL, <SDL_RendererFlip> flip)
        else:
            pass

    cpdef flip(self):
        """ Show the contents of the target in a coordinated manner"""
        SDL_RenderPresent(self.renderer)
        if self._doublebuffered:
            SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 255);
            SDL_RenderClear(self.renderer);


    cpdef isVisible(self):
        if self.window != NULL:
            return SDL_GetWindowFlags(self.window) & SDL_WINDOW_SHOWN != 0

        return False
