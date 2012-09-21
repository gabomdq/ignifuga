#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Ignifuga Game Engine
# Game Loop
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

# xcython: profile=True
# cython: boundscheck=False
# cython: wraparound=False

from ignifuga.Gilbert import Gilbert
from ignifuga.Log import debug, error
import time, sys

DEF NUM_STREAMS = 20

cdef class GameLoop(GameLoopBase):
    def __init__(self, fps = 30.0, remoteConsole = None, remoteScreen = False, ip='127.0.0.1', port=54322):
        super(GameLoop, self).__init__(fps, remoteConsole, remoteScreen, ip, port)
        self.renderer = <Renderer>Gilbert().renderer
        self._screen_w, self._screen_h = self.renderer.screenSize
        self.paused = False
        self.ticks_second = SDL_GetPerformanceFrequency()

#if DEBUG and (__LINUX__ or __OSX__ or __MINGW__)
        self.fw = new FileWatcher()
        self.fwli = new FileWatchListenerIgnifuga()
#endif

        self.active_touches = 0

        cdef int i
        for i in range(NUM_STREAMS):
            self.touches[i].valid = False

        self.touchCaptor = None
        self.touchCaptured = False
        self.lastTouch.x = 0
        self.lastTouch.y = 0

    cpdef run(self):
        cdef SDL_Event ev
        cdef Uint32 now
        cdef Sint64 remainingTime
        cdef Uint64 nowx, freqx = self.ticks_second / 1000
        cdef char *jpegBuf
        cdef unsigned long jpegBufSize
        cdef bytes screenCap

        overlord = Gilbert()
#        if overlord.platform in ['iphone',]:
#            # Special loop for single app mobile platforms that slows down when not active
#            # TODO: Is this really required for iPhone?
#            # Note: Android does not need this anymore, I've enabled a blocking option in Android_PumpEvents
#            while not self.quit:
#                now = SDL_GetTicks()
#                self.update(now)
#                if not self.paused:
#                    self.renderer.update(now)
#
#                while SDL_PollEvent(&ev):
#                    self.handleSDLEvent(&ev)
#
#                if self.paused and not overlord.loading:
#                    # Slow down the update rhythm to 1 frame every 2 seconds
#                    SDL_Delay( <Uint32> 2000 )
#                else:
#                    # Sleep for the remainder of the alloted frame time, if there's time left
#                    remainingTime = self._interval  - (SDL_GetTicks()-now)
#                    if remainingTime > 0:
#                        SDL_Delay( <Uint32>(remainingTime+0.5) )
#        else:
            # Regular loop, draws all the time independently of shown/hidden status

# TODO: When pausing/resuming, fix up the timing in the active actions so there's no abrupt jump

        while True:
            nowx = SDL_GetPerformanceCounter()
            now = nowx / freqx

            while SDL_PollEvent(&ev):
                self.handleSDLEvent(&ev)

            if not self.paused:
                self.update(now)
                if not self.freezeRenderer:
                    self.renderer.update(now)

            # Sleep for the remainder of the alloted frame time, if there's time left
            self.frame_time = SDL_GetPerformanceCounter()-nowx
            remainingTime = self._interval  - self.frame_time / self.ticks_second
            if remainingTime > 0:
#if DEBUG and (__LINUX__ or __OSX__ or __MINGW__)
                self.fw.update()
#endif
                if self.enableRemoteScreen:
                    if self.remoteScreenHandlers:
                        jpegBuf = NULL
                        jpegBufSize = 0
                        if self.renderer.captureScreenJPEG(<unsigned char**>&jpegBuf, &jpegBufSize):
                            screenCap = jpegBuf[:jpegBufSize]
                            self.renderer.releaseCapturedScreenBufferJPEG(<unsigned char*>jpegBuf)
                            jpegBuf = NULL

                            for handler in self.remoteScreenHandlers:
                                handler.screen = screenCap
                                handler.screenSize = jpegBufSize
                                handler.sem.release()
                    # If remote screen is enabled, the renderer won't flip automatically because its waiting for us to order the screenshot
                    self.renderer.flip()

                with nogil: # No gil in case there's other threads waiting for us (for example rconsole)
                    SDL_Delay( remainingTime)
            elif self.enableRemoteScreen:
                # If remote screen is enabled, the renderer won't flip automatically because its waiting for us to order the screenshot
                # in this case, there's not enough time
                self.renderer.flip()

            if self.quit:
                break

    cpdef cleanup(self):
        # Run the event loop one last time to purge any lingering messages
        cdef SDL_Event ev
        while SDL_PollEvent(&ev):
            self.handleSDLEvent(&ev)

    cdef handleSDLEvent(self, SDL_Event *sdlev):
        cdef SDL_MouseMotionEvent *mmev
        cdef SDL_MouseButtonEvent *mbev
        cdef SDL_MouseWheelEvent *mwev      
        cdef SDL_WindowEvent *winev
        cdef SDL_TouchFingerEvent *fev
        cdef SDL_UserEvent *uev
        cdef PyObject *pycb

        #if ROCKET
        self.renderer.rocket.PushSDLEvent(sdlev)
        #endif

        if sdlev.type == SDL_QUIT:
            Gilbert().endLoop()
#if __LINUX__ or __OSX_ or __MINGW__
        elif sdlev.type == SDL_MOUSEMOTION:
            mmev = <SDL_MouseMotionEvent*>sdlev
            if self.touches[0].valid:
                self.handleTouch(EVENT_TOUCH_MOTION, mmev.x, mmev.y, 0)
            elif self.touches[1].valid:
                self.handleTouch(EVENT_TOUCH_MOTION, mmev.x, mmev.y, 1)
            elif self.touches[2].valid:
                self.handleTouch(EVENT_TOUCH_MOTION, mmev.x, mmev.y, 2)
            else:
                self.handleTouch(EVENT_TOUCH_MOTION, mmev.x, mmev.y, 0)

        elif sdlev.type == SDL_MOUSEBUTTONDOWN:
            mbev = <SDL_MouseButtonEvent*>sdlev
            self.handleTouch(EVENT_TOUCH_DOWN, mbev.x, mbev.y, mbev.button-1)
        elif sdlev.type == SDL_MOUSEBUTTONUP:
            mbev = <SDL_MouseButtonEvent*>sdlev
            self.handleTouch(EVENT_TOUCH_UP, mbev.x, mbev.y, mbev.button-1)
#endif
        elif sdlev.type == SDL_FINGERMOTION:
            fev = <SDL_TouchFingerEvent*>sdlev
            self.normalizeFingerEvent(fev)
            self.handleTouch(EVENT_TOUCH_MOTION, fev.x, fev.y, fev.fingerId)
        elif sdlev.type == SDL_FINGERDOWN:
            fev = <SDL_TouchFingerEvent*>sdlev
            self.normalizeFingerEvent(fev)
            self.handleTouch(EVENT_TOUCH_DOWN, fev.x, fev.y, fev.fingerId)
        elif sdlev.type == SDL_FINGERUP:
            fev = <SDL_TouchFingerEvent*>sdlev
            self.normalizeFingerEvent(fev)
            self.handleTouch(EVENT_TOUCH_UP, fev.x, fev.y, fev.fingerId)
        elif sdlev.type == SDL_MOUSEWHEEL:
            mwev = <SDL_MouseWheelEvent*>sdlev
            if mwev.y > 0:
                self.handleEthereal(EVENT_ETHEREAL_ZOOM_IN)
            else:
                self.handleEthereal(EVENT_ETHEREAL_ZOOM_OUT)
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
                self.paused = False
                debug('Window restored')
            elif winev.event == SDL_WINDOWEVENT_MINIMIZED:
                self.paused = True
                debug('Window minimized')
            elif winev.event == SDL_WINDOWEVENT_FOCUS_GAINED:
                debug('Window focus gained')
                #self.paused = False
            elif winev.event == SDL_WINDOWEVENT_FOCUS_LOST:
                # Pause here is strictly required for fullscreen Direct3D backed apps...
                # but it doesn't hurt to pause in windowed apps or other platforms
                # TODO: Should we make pausing here optional? Command line option enabled?
                debug('Window focus lost')
                #self.paused = True
            elif winev.event == SDL_WINDOWEVENT_CLOSE:
                debug('Window closed')
                Gilbert().endLoop()
        elif sdlev.type == SDL_USEREVENT:
            # Used by the FileWatcher to report file changes
            uev = <SDL_UserEvent*>sdlev
            # TODO: Different actions depending on uev.code
            if uev.code == FILEWATCHER_ADD:
                Gilbert().dataManager.urlReloaded(bytes(<char*>uev.data1))
            elif uev.code == FILEWATCHER_DEL:
                Gilbert().dataManager.urlReloaded(bytes(<char*>uev.data1))
            elif uev.code == FILEWATCHER_MOD:
                Gilbert().dataManager.urlReloaded(bytes(<char*>uev.data1))
            elif uev.code == MIX_CHANNEL_STOPPED or uev.code == MIX_MUSIC_STOPPED:
                pycb = <PyObject*>uev.data1
                cb = <object>uev.data1
                Py_XDECREF(pycb)
                cb()

    cdef normalizeFingerEvent(self, SDL_TouchFingerEvent *fev):
        """ Normalize the finger event coordinates from 0->32768 to the screen resolution """
        fev.x = fev.x * self._screen_w / 32768
        fev.y = fev.y * self._screen_h / 32768

#if DEBUG and (__LINUX__ or __OSX__ or __MINGW__)
    cpdef addWatch(self, filename):
        self.fw.addWatch(string(<char*>filename), self.fwli, False)

    cpdef removeWatch(self, filename):
        self.fw.removeWatch(string(<char*>filename))
#endif

    cdef handleTouch(self, EventType action, int x, int y, int stream):
        if stream >=NUM_STREAMS or stream < 0:
            #NOTE: This code requires that SDL for iOS is compiled with #undef IPHONE_TOUCH_EFFICIENT_DANGEROUS
            error("RECEIVED AN INVALID STREAM NUMBER %d < %d < %d " % (0, stream, NUM_STREAMS ))
            return

        if action >= EVENT_TOUCH_LAST:
            return

        cdef bint continuePropagation = True, captureEvent = False
        cdef int deltax=0, deltay=0, zoomCenterX, zoomCenterY, sx, sy, currArea, prevArea
        cdef double cx, cy,
        cdef Touch* lastTouch, *prevTouch
        cdef PointD scenePoint


        self.lastTouch.x = x
        self.lastTouch.y = y

        if self.touches[stream].valid:
            lastTouch = &self.touches[stream]
            deltax = x - lastTouch.x
            deltay = y - lastTouch.y

        # Check which entities/components the event applies to
        if not self.touchCaptured:
            continuePropagation, captureEvent, captor = self.renderer.processEvent(action, x, y)
            self.touchCaptor = captor
            self.touchCaptured = True
        elif self.touchCaptor is not None:
            continuePropagation, captureEvent = self.touchCaptor.event(action, x, y)
            if not captureEvent:
                self.touchCaptor = None
                self.touchCaptured = False

        # Handle zoom/scrolling
        if continuePropagation and self.touchCaptor is None:
            if (deltax != 0 or deltay != 0) and action != EVENT_TOUCH_DOWN:
                if self.renderer._userCanScroll and stream == 0 and self.touches[stream].valid and self.active_touches==1:
                    # Handle scrolling
                    self.renderer.scrollBy(deltax, deltay)
                    self.touchCaptured = True
                    self.touchCaptor = None
                elif self.renderer._userCanZoom and self.active_touches == 2 and (stream == 0 or stream == 1) and self.touches[0].valid and self.touches[1].valid:
                    # Handle zooming
                    prevArea = (self.touches[0].x-self.touches[1].x)**2 + (self.touches[0].y-self.touches[1].y)**2
                    if stream == 0:
                        prevTouch = &self.touches[1]
                    else:
                        prevTouch = &self.touches[0]

                    currArea = (x-prevTouch.x)**2 +(y-prevTouch.y)**2
                    zoomCenterX = (x + prevTouch.x)/2
                    zoomCenterY = (y + prevTouch.y)/2
                    cx,cy = self.renderer.screenToScene(zoomCenterX, zoomCenterY)
                    self.renderer.scaleBy(currArea-prevArea)
                    sx,sy = self.renderer.sceneToScreen(cx,cy)
                    self.renderer.scrollBy(zoomCenterX-sx, zoomCenterY-sy)

                    self.touchCaptured = True
                    self.touchCaptor = None

        # Store / remove tracked touches
        if action == EVENT_TOUCH_UP:
            # Forget about this stream as the user lift the finger/mouse button
            if self.touches[stream].valid:
                self.touches[stream].valid = False
                self.active_touches -= 1
            self.touchCaptor = None
            self.touchCaptured = False
        elif action == EVENT_TOUCH_DOWN or self.touches[stream].valid:
            # Don't store touchmove events because in a pointer based platform this gives you scrolling with no mouse button pressed
            # Save the last touch event for the stream
            if not self.touches[stream].valid:
                self.touches[stream].valid = True
                self.active_touches +=1

        self.touches[stream].x = x
        self.touches[stream].y = y

    cdef handleEthereal(self, EventType action):
        if action <= EVENT_TOUCH_LAST:
            return

        cdef double cx, cy
        cdef int sx,sy

        #Send the event to all entities until something stops it
        self.renderer.processEvent(action, 0, 0)

        if self.renderer._userCanZoom:
            if action == EVENT_ETHEREAL_ZOOM_IN or action == EVENT_ETHEREAL_ZOOM_OUT:
                cx,cy = self.renderer.screenToScene(self.lastTouch.x, self.lastTouch.y)
                if action == EVENT_ETHEREAL_ZOOM_IN:
                    self.renderer.scaleByFactor(1.2)
                else:
                    self.renderer.scaleByFactor(0.8)
                sx,sy = self.renderer.sceneToScreen(cx,cy)
                self.renderer.scrollBy(self.lastTouch.x-sx, self.lastTouch.y-sy)
