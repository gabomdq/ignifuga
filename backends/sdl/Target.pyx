#Copyright (c) 2010,2011, Gabriel Jacobo
#All rights reserved.

#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions are met:

    #* Redistributions of source code must retain the above copyright
      #notice, this list of conditions and the following disclaimer.
    #* Redistributions in binary form must reproduce the above copyright
      #notice, this list of conditions and the following disclaimer in the
      #documentation and/or other materials provided with the distribution.
    #* Altered source versions must be plainly marked as such, and must not be
      #misrepresented as being the original software.
    #* Neither the name of Gabriel Jacobo, MDQ Incorporeo, Ignifuga Game Engine
      #nor the names of its contributors may be used to endorse or promote
      #products derived from this software without specific prior written permission.
    #* You must NOT, under ANY CIRCUMSTANCES, remove, modify or alter in any way
      #the duration, code functionality and graphic or audio material related to
      #the "splash screen", which should always be the first screen shown by the
      #derived work and which should ALWAYS state the Ignifuga Game Engine name,
      #original author's URL and company logo.

#THIS LICENSE AGREEMENT WILL AUTOMATICALLY TERMINATE UPON A MATERIAL BREACH OF ITS
#TERMS AND CONDITIONS

#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL GABRIEL JACOBO NOR MDQ INCORPOREO NOR THE CONTRIBUTORS
#BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Ignifuga Game Engine
# SDL Render Target
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.Log import debug, info, error
from ignifuga.Gilbert import Gilbert, Event
import sys

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

        print "Desktop mode is %dx%d" % (dm.w, dm.h)
        
        if sys.platform in ['win32',]:
            if fullscreen:
                self.window = SDL_CreateWindow("Ignifuga",
                            SDL_WINDOWPOS_UNDEFINED_MASK | display, SDL_WINDOWPOS_UNDEFINED_MASK | display, #
                            dm.w, dm.h, SDL_WINDOW_FULLSCREEN)
            else:
                self.window = SDL_CreateWindow("Ignifuga",
                            SDL_WINDOWPOS_CENTERED_MASK, SDL_WINDOWPOS_CENTERED_MASK, #
                            width, height, SDL_WINDOW_RESIZABLE)
        elif sys.platform in ['linux',]:
            # Dance around Xinerama et al
            if fullscreen:
                self.window = SDL_CreateWindow("Ignifuga",
                            SDL_WINDOWPOS_UNDEFINED_MASK | display, SDL_WINDOWPOS_UNDEFINED_MASK | display, #
                            dm.w, dm.h, SDL_WINDOW_FULLSCREEN)
            else:
                self.window = SDL_CreateWindow("Ignifuga",
                            SDL_WINDOWPOS_CENTERED_MASK, SDL_WINDOWPOS_CENTERED_MASK, #
                            width, height, SDL_WINDOW_RESIZABLE)
        else:
            # Android doesn't care what we tell it to do, it creates a full screen window anyway
            self.window = SDL_CreateWindow("Ignifuga",
                            SDL_WINDOWPOS_CENTERED_MASK, SDL_WINDOWPOS_CENTERED_MASK, #
                            width, height, SDL_WINDOW_FULLSCREEN)
            
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
    
    @property
    def width(self):
        # Update size as it can change!
        return self._width
    
    @property
    def height(self):
        # Update size as it can change!  
        return self._height

    @property
    def isDoubleBuffered(self):
        return self._doublebuffered

    cpdef updateSize(self):
        SDL_GetWindowSize(self.window, &self._width, &self._height)
        SDL_RenderSetViewport(self.renderer, NULL)
        debug('Window size is %d x %d' % (self._width, self._height))

    def clear(self, x, y, w, h):
        self.ctx.clearRect(x,y,w,h);

    def clearRect(self, rect):
        return self.clear(rect[0], rect[1], rect[2], rect[3])
    
    cpdef blitCanvas(self, Canvas canvas, int dx=0, int dy=0, int dw=-1, int dh=-1, int sx=0, int sy=0, int sw=-1, int sh=-1, double angle=0, bool offCenter=False, int centerx=0, int centery=0, int flip=0 ):
        cdef SDL_Rect srcRect, dstRect
        cdef SDL_Point center
        
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

    def flip(self):
        """ Show the contents of the target in a coordinated manner"""
        SDL_RenderPresent(self.renderer)
        if self._doublebuffered:
            SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 255);
            SDL_RenderClear(self.renderer);