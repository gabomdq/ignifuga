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
# SDL 2D Canvas
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.Log import debug, info, error
from ignifuga.Gilbert import Gilbert, Event, Renderer as getRenderer
from ignifuga.Renderer cimport Renderer
from ignifuga.backends.sdl.Target cimport Target
from ignifuga.Log import *
from sys import exit
from SDL cimport *
import platform, os.path

cdef class Canvas (CanvasBase):
    BLENDMODE_BLEND = SDL_BLENDMODE_BLEND
    BLENDMODE_NONE = SDL_BLENDMODE_NONE
    BLENDMODE_ADD = SDL_BLENDMODE_ADD
    BLENDMODE_MOD = SDL_BLENDMODE_MOD
    def __init__ (self, width=None, height=None, hw=True, srcURL = None, isRenderTarget = False):
        """
        hw = True -> Hardware Canvas (Texture in SDL)
        hw = False -> Software Canvas (Surface in SDL)
        isRenderTarget -> if True, then other canvases with hw=True can be rendered on top of this canvas via hw rendering
        srclURL != None -> Load image into software canvas
        """
        cdef SDL_Surface *ss
        self._sdlRenderer = (<Target>getRenderer().target).renderer
        self._srcURL = srcURL
        self._isRenderTarget = isRenderTarget
        self._fontURL = None
        self._fontSize = 0
        self._font = None
        self._r = self._g = self_b = self._a = 1.0
        
        if srcURL != None:
            # Initialize a software surface with contents loaded from the image
            ss = IMG_Load(srcURL)
            
            # Create texture from image
            self._surfacehw = SDL_CreateTextureFromSurface(self._sdlRenderer, ss)
                
            self._hw = True
            self._width = ss.w
            self._height = ss.h
            SDL_FreeSurface(ss)
        else:
            self._hw = hw
            
            if width is None:
                width = Renderer().target.width
            if height is None:
                height = Renderer().target.height
                
            self._width = width
            self._height = height
                
            if self._hw:
                if isRenderTarget:
                    self._surfacehw = SDL_CreateTexture(self._sdlRenderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, self._width, self._height)
                else:
                    self._surfacehw = SDL_CreateTexture(self._sdlRenderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_STREAMING, self._width, self._height)
            else:
                self._surfacesw = SDL_CreateRGBSurface(0, self._width, self._height, 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
                
        
        if (self._hw and self._surfacehw == NULL) or ( not self._hw and self._surfacesw == NULL):
            # Error loading surface, we got a null pointer
            error("Could not initialize canvas (srcURL: %s, hw: %s)" % (srcURL, hw))
            exit(1)

        SDL_SetTextureBlendMode(self._surfacehw, SDL_BLENDMODE_BLEND)

    def __dealloc__(self):
        #debug( "CANVAS DEALLOC %s" % self)
        if self._hw:
            SDL_DestroyTexture(self._surfacehw)
        else:
            SDL_FreeSurface(self._surfacesw)

    cpdef blitCanvas(self, CanvasBase canvasbase, int dx=0, int dy=0, int dw=-1, int dh=-1, int sx=0, int sy=0, int sw=-1, int sh=-1, int blend=-1):
        cdef Canvas canvas

        canvas = <Canvas>canvasbase

        if sw == -1:
            sw = canvas._width
        if sh == -1:
            sh = canvas._height
        
        if dw == -1:
            dw = sw
        if dh == -1:
            dh = sh
            
        
        if self._isRenderTarget and self._hw and canvas._hw:
            # Both canvas are hardware based, and we can render on this canvas from another canvas
            return self.blitCanvasHW(canvas,dx,dy,dw,dh,sx,sy,sw,sh, blend)
        else:
            # At least one of the canvas is software based
            return self.blitCanvasSW(canvas,dx,dy,dw,dh,sx,sy,sw,sh, blend)
            
            
    cdef blitCanvasSW(self, Canvas canvas, int dx, int dy, int dw, int dh, int sx, int sy, int sw, int sh, int blend):
        """ Blit between canvas using an intermediary software surface """
        cdef SDL_BlendMode prevbmode
        cdef SDL_Rect srcRect, dstRect
        cdef SDL_Surface *src, *dst

        srcRect.x = sx
        srcRect.y = sy
        srcRect.w = sw
        srcRect.h = sh
        dstRect.x = dx
        dstRect.y = dy
        dstRect.w = dw
        dstRect.h = dh
        
        if blend != -1:
            SDL_GetTextureBlendMode(canvas._surfacehw, &prevbmode)
            SDL_SetTextureBlendMode(canvas._surfacehw, <SDL_BlendMode>blend)
        
        if self._hw:
            # Convert our surface to software surface
            dst = SDL_CreateRGBSurfaceFrom(NULL, dw, dh, 32, 0, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
            SDL_LockTexture(self._surfacehw, &dstRect, &dst.pixels, &dst.pitch)
        else:
            dst = self._surfacesw
            
        if canvas._hw:
            # Convert the other surface to software surface
            src = SDL_CreateRGBSurfaceFrom(NULL, sw, sh, 32, 0, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
            SDL_LockTexture(canvas._surfacehw, &srcRect, &src.pixels, &src.pitch)
        else:
            src = canvas._surfacesw
   
        SDL_UpperBlit(src, &srcRect, dst, &dstRect)
        
        if self._hw:
            SDL_FreeSurface(dst)
            SDL_UnlockTexture(self._surfacehw)
            
        if canvas._hw:
            SDL_FreeSurface(src)
            SDL_UnlockTexture(canvas._surfacehw)
            
        if blend != -1:
            SDL_SetTextureBlendMode(canvas._surfacehw, prevbmode)
            
    cdef blitCanvasHW(self, Canvas canvas, int dx, int dy, int dw, int dh, int sx, int sy, int sw, int sh, int blend):
        """ Blit between two hardware canvas"""
        cdef SDL_BlendMode prevbmode
        cdef SDL_Rect srcRect, dstRect

        srcRect.x = sx
        srcRect.y = sy
        srcRect.w = sw
        srcRect.h = sh
        dstRect.x = dx
        dstRect.y = dy
        dstRect.w = dw
        dstRect.h = dh
                
        if blend != -1:
            SDL_GetTextureBlendMode(canvas._surfacehw, &prevbmode)
            SDL_SetTextureBlendMode(canvas._surfacehw, <SDL_BlendMode>blend)
            
        SDL_SetTargetTexture(self._sdlRenderer, self._surfacehw)
        SDL_RenderCopy(self._sdlRenderer, canvas._surfacehw, &srcRect, &dstRect)
        SDL_SetTargetTexture(self._sdlRenderer, NULL)
        
        if blend != -1:
            SDL_SetTextureBlendMode(canvas._surfacehw, prevbmode)

    cpdef mod(self, float r, float g, float b, float a):
        """ Apply color modulation to the texture """
        self._r = r
        self._g = g
        self._b = b
        self._a = a
        
        # Due to current limitations in SDL Color modulation functionality, modulation is always in the range 0 <= r <= 1.0, ie you can not increase a color channel, only modulate it downwards (r can not be >=1.0)
        cdef Uint8 R,G,B,A

        if r < 0.0: r = 0.0
        if r > 1.0: r = 1.0
        if g < 0.0: g = 0.0
        if g > 1.0: g = 1.0
        if b < 0.0: b = 0.0
        if b > 1.0: b = 1.0
        if a < 0.0: a = 0.0
        if a > 1.0: a = 1.0

        R = <Uint8> (r * 255)
        G = <Uint8> (g * 255)
        B = <Uint8> (b * 255)
        A = <Uint8> (a * 255)

        if self._hw:
            SDL_SetTextureColorMod(self._surfacehw, R, G, B)
            SDL_SetTextureAlphaMod(self._surfacehw, A)

    cpdef text(self, text, color, fontURL, fontSize):
        """ Replaces the surface with a text created from TTF"""
        if self._font != None:
            if self._fontURL != fontURL or self._fontSize != fontSize:
                self._font = None
        if self._font == None:
            self._font = Gilbert().dataManager.getFont(fontURL, fontSize)
            if self._font == None:
                self._fontURL = None
                self._fontSize = 0
                return

        self._fontURL = fontURL
        self._fontSize = fontSize
        cdef SDL_Surface *ss
        cdef SDL_Color sdl_color
        cdef bytes btext = bytes(text)
        sdl_color.r, sdl_color.g, sdl_color.b = color
        ss = TTF_RenderUTF8_Solid(self._font.ttf_font, btext, sdl_color)
        if self._hw:
            SDL_DestroyTexture(self._surfacehw)
        else:
            SDL_FreeSurface(self._surfacesw)

        self._surfacehw = SDL_CreateTextureFromSurface(self._sdlRenderer, ss)
        self._hw = True
        self._width = ss.w
        self._height = ss.h
        SDL_FreeSurface(ss)
        self.mod(self._r, self._g, self._b, self._a)


    def __deepcopy__(self, memo):
        """ Don't allow deepcopying of the Canvas"""
        return self

    def __copy__(self):
        """ Don't allow copying of the Canvas"""
        return self