#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

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
        self.paused = False

    cpdef run(self):
        cdef SDL_Event ev
        cdef Uint32 now

        overlord = Gilbert()
        target = overlord.renderer.target
        if overlord.platform in ['android', 'iphone']:
            # Special loop for single app mobile platforms that slows down when not active
            while not self.quit:
                now = SDL_GetTicks()
                overlord.update(now/1000.0)
                if not self.paused:
                    overlord.renderScene()

                while SDL_PollEvent(&ev):
                    self.handleSDLEvent(&ev)

                if self.paused and not overlord.loading:
                    # Slow down the update rhythm to 1 frame every 2 seconds
                    SDL_Delay( <Uint32> 2000 )
                else:
                    # Sleep for the remainder of the alloted frame time, if there's time left
                    remainingTime = self._interval  - (SDL_GetTicks()-now)
                    if remainingTime > 0:
                        SDL_Delay( <Uint32>(remainingTime+0.5) )
        else:
            # Regular loop, draws all the time independently of shown/hidden status
            while not self.quit:
                now = SDL_GetTicks()
                overlord.update(now/1000.0)
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
        cdef Target target
        
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
                debug('New Window Size stored: %dx%d' % (self._screen_w, self._screen_h))
            elif winev.event == SDL_WINDOWEVENT_MOVED:
                debug('Window moved to %s, %s' % (winev.data1, winev.data2))
            elif winev.event == SDL_WINDOWEVENT_SHOWN:
                debug('Window shown')
                self.paused = False
            elif winev.event == SDL_WINDOWEVENT_HIDDEN:
                debug('Window hidden')
                self.paused = True
            elif winev.event == SDL_WINDOWEVENT_RESTORED:
                debug('Window is being restored')
                t = Gilbert().renderer.target
                target = <Target> t
                result = SDL_GL_CreateContext(target.window)
                self.paused = False
                debug('Window restored')
                
            elif winev.event == SDL_WINDOWEVENT_MINIMIZED:
                self.paused = True
                debug('Window minimized')

            
    cdef normalizeFingerEvent(self, SDL_TouchFingerEvent *fev):
        """ Normalize the finger event coordinates from 0->32768 to the screen resolution """
        fev.x = fev.x * self._screen_w / 32768
        fev.y = fev.y * self._screen_h / 32768

        
