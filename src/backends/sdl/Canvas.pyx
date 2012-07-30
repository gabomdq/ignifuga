#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


# Ignifuga Game Engine
# SDL 2D Canvas
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

# xcython: profile=True

from ignifuga.Log import debug, info, error
from ignifuga.Gilbert import Gilbert, Event, getRenderer
from ignifuga.backends.sdl.Renderer cimport Renderer
from ignifuga.Log import *
from sys import exit
from SDL cimport *
import platform, os.path, json

cdef class Canvas (CanvasBase):
    BLENDMODE_BLEND = SDL_BLENDMODE_BLEND
    BLENDMODE_NONE = SDL_BLENDMODE_NONE
    BLENDMODE_ADD = SDL_BLENDMODE_ADD
    BLENDMODE_MOD = SDL_BLENDMODE_MOD
    def __init__ (self, width=None, height=None, hw=True, srcURL = None, embedded=None, isRenderTarget = False):
        """
        hw = True -> Hardware Canvas (Texture in SDL)
        hw = False -> Software Canvas (Surface in SDL)
        isRenderTarget -> if True, then other canvases with hw=True can be rendered on top of this canvas via hw rendering
        srclURL != None -> Load image into software canvas
        """
        cdef SDL_Surface *ss = NULL
        cdef char *bindata
        cdef bytes embedded_data
        renderer = getRenderer()
        self._sdlRenderer = (<Renderer>renderer).renderer
        self._srcURL = srcURL
        self._isRenderTarget = isRenderTarget
        self._fontURL = None
        self._fontSize = 0
        self._font = None
        self._r = self._g = self_b = self._a = 1.0
        self.spriteData = None
        
        if srcURL != None or embedded != None:
            # Initialize a software surface with contents loaded from the image
            if srcURL != None:
                ss = IMG_Load(srcURL)
            elif embedded != None:
                src_len = len(embedded)
                embedded_data = bytes(embedded)
                bindata = embedded_data
                rwops = SDL_RWFromConstMem(<void*>bindata, src_len )
                if rwops != NULL:
                    ss = IMG_Load_RW(rwops, 1)

            if ss != NULL:
                # Create texture from image
                self._surfacehw = SDL_CreateTextureFromSurface(self._sdlRenderer, ss)

                if ss.userdata != NULL:
                    self.spriteData = json.loads(<char*>ss.userdata)
                    
                self._hw = True
                self._width = ss.w
                self._height = ss.h
                SDL_FreeSurface(ss)
        else:
            self._hw = hw
            
            if width is None:
                width = Renderer()._width
            if height is None:
                height = Renderer()._height
                
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
        debug( ">>>CANVAS DEALLOC %s (URL: %s) <<<" % (self, self._srcURL))
        if self._hw:
            SDL_DestroyTexture(self._surfacehw)
            self._surfacehw = NULL
        else:
            SDL_FreeSurface(self._surfacesw)
            self._surfacesw = NULL

    cpdef blitCanvas(self, CanvasBase canvasbase, int dx=0, int dy=0, int dw=-1, int dh=-1, int sx=0, int sy=0, int sw=-1, int sh=-1, int blend=-1):
        #cdef Canvas canvas

        #canvas = <Canvas>canvasbase

        if sw == -1:
            sw = canvasbase._width
        if sh == -1:
            sh = canvasbase._height
        
        if dw == -1:
            dw = sw
        if dh == -1:
            dh = sh
            
        
        if self._isRenderTarget and self._hw and canvasbase._hw:
            # Both canvas are hardware based, and we can render on this canvas from another canvas
            return self.blitCanvasHW(<Canvas>canvasbase,dx,dy,dw,dh,sx,sy,sw,sh, blend)
        else:
            # At least one of the canvas is software based
            return self.blitCanvasSW(<Canvas>canvasbase,dx,dy,dw,dh,sx,sy,sw,sh, blend)
            
            
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
            
        SDL_SetRenderTarget(self._sdlRenderer, self._surfacehw)
        SDL_RenderCopy(self._sdlRenderer, canvas._surfacehw, &srcRect, &dstRect)
        SDL_SetRenderTarget(self._sdlRenderer, NULL)
        
        if blend != -1:
            SDL_SetTextureBlendMode(canvas._surfacehw, prevbmode)

    cpdef mod(self, float r, float g, float b, float a):
        """ Apply color modulation to the texture """
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

        self._r = r
        self._g = g
        self._b = b
        self._a = a

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
        if ss != NULL:
            if self._hw and self._surfacehw != NULL:
                SDL_DestroyTexture(self._surfacehw)
            elif self._surfacesw != NULL:
                SDL_FreeSurface(self._surfacesw)

            self._surfacehw = SDL_CreateTextureFromSurface(self._sdlRenderer, ss)
            if self._surfacehw == NULL:
                error(">>> Problem creating Text HW Surface!! <<<")
                exit(1)

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