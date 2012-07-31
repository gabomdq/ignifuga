#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Ignifuga Game Engine
# Game Loop
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.backends.sdl.SDL cimport *
from ignifuga.Gilbert import Gilbert, Event
from ignifuga.backends.GameLoopBase cimport *
from ignifuga.backends.sdl.Renderer cimport Renderer, PointD
from ignifuga.FileWatcher.FileWatcher cimport FileWatcher, FileWatchListenerIgnifuga
from libcpp.string cimport *

cdef struct Touch:
    int x, y
    bint valid

cdef class GameLoop(GameLoopBase):
    cdef int _screen_w, _screen_h
    cdef Renderer renderer
    cdef FileWatcher *fw
    cdef FileWatchListenerIgnifuga *fwli
    cdef Touch touches[20], lastTouch
    cdef object touchCaptor
    cdef bint touchCaptured
    cdef int active_touches

    cpdef run(self)
    cdef handleSDLEvent(self, SDL_Event *sdlev)
    cdef normalizeFingerEvent(self, SDL_TouchFingerEvent *fev)

    cdef handleTouch(self, EventType action, int x, int y, int stream)
    cdef handleEthereal(self, EventType event)




