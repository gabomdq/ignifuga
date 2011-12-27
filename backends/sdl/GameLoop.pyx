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
# Game Loop
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.Gilbert import Gilbert, Event
from ignifuga.Log import debug
import time, sys

cdef class GameLoop(GameLoopBase):
    def __init__(self, fps = 30.0):
        super(GameLoop, self).__init__(fps)
        self._screen_w, self._screen_h = Gilbert().renderer.screenSize

    cpdef run(self):
        cdef SDL_Event ev
        cdef Uint32 now

        overlord = Gilbert()
        target = overlord.renderer.target
        #self._interval=1000
        while not self.quit:
            now = SDL_GetTicks()
            overlord.update(now/1000.0)
            if target.visible:
                overlord.renderScene()

            while SDL_PollEvent(&ev):
                self.handleSDLEvent(&ev)

            # Sleep for the remainder of the alloted frame time, if there's time left
            remainingTime = self._interval  - (SDL_GetTicks()-now)
            if remainingTime > 0:
                SDL_Delay( <Uint32>(remainingTime+0.5) )

    cdef handleSDLEvent(self, SDL_Event *sdlev):
        cdef SDL_MouseMotionEvent *mmev
        cdef SDL_MouseButtonEvent *mbev
        cdef SDL_MouseWheelEvent *mwev      
        cdef SDL_WindowEvent *winev
        cdef SDL_TouchFingerEvent *fev
        
        if sdlev.type == SDL_QUIT:
            Gilbert().endLoop()
        elif sdlev.type == SDL_MOUSEMOTION:
            mmev = <SDL_MouseMotionEvent*>sdlev
            gev = Event(Event.TYPE._mousemove, mmev.x, mmev.y)
            Gilbert().reportEvent(gev)
            sys.stdout.flush()
        elif sdlev.type == SDL_MOUSEBUTTONDOWN:
            mbev = <SDL_MouseButtonEvent*>sdlev
            gev = Event(Event.TYPE._mousedown, mbev.x, mbev.y, mbev.button)
            Gilbert().reportEvent(gev)
        elif sdlev.type == SDL_MOUSEBUTTONUP:
            mbev = <SDL_MouseButtonEvent*>sdlev
            gev = Event(Event.TYPE._mouseup, mbev.x, mbev.y, mbev.button)
            Gilbert().reportEvent(gev)
        elif sdlev.type == SDL_MOUSEWHEEL:
            mwev = <SDL_MouseWheelEvent*>sdlev
            if mwev.y > 0:
                gev = Event(Event.TYPE.zoomin)
            else:
                gev = Event(Event.TYPE.zoomout)
            Gilbert().reportEvent(gev)
        elif sdlev.type == SDL_FINGERMOTION:
            fev = <SDL_TouchFingerEvent*>sdlev
            self.normalizeFingerEvent(fev)
            gev = Event(Event.TYPE.touchmove, fev.x, fev.y, stream=fev.fingerId)
            Gilbert().reportEvent(gev)
        elif sdlev.type == SDL_FINGERDOWN:
            fev = <SDL_TouchFingerEvent*>sdlev
            self.normalizeFingerEvent(fev)
            gev = Event(Event.TYPE.touchdown, fev.x, fev.y, stream=fev.fingerId)
            Gilbert().reportEvent(gev)
        elif sdlev.type == SDL_FINGERUP:
            fev = <SDL_TouchFingerEvent*>sdlev
            self.normalizeFingerEvent(fev)
            gev = Event(Event.TYPE.touchup, fev.x, fev.y, stream=fev.fingerId)
            Gilbert().reportEvent(gev)
        elif sdlev.type == SDL_WINDOWEVENT:
            winev = <SDL_WindowEvent*>sdlev
            if winev.event == SDL_WINDOWEVENT_SIZE_CHANGED or winev.event==SDL_WINDOWEVENT_RESIZED:
                Gilbert().renderer.windowResized()
                self._screen_w, self._screen_h = Gilbert().renderer.screenSize
            elif winev.event == SDL_WINDOWEVENT_MOVED:
                debug('Window moved to %s, %s' % (winev.data1, winev.data2))
            
    cdef normalizeFingerEvent(self, SDL_TouchFingerEvent *fev):
        """ Normalize the finger event coordinates from 0->32768 to the screen resolution """
        fev.x = fev.x * self._screen_w / 32768
        fev.y = fev.y * self._screen_h / 32768

        
