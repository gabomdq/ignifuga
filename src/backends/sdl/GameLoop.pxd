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
from libcpp.string cimport *

#if DEBUG and (__LINUX__ or __OSX__ or __MINGW__)
from ignifuga.FileWatcher.FileWatcher cimport FileWatcher, FileWatchListenerIgnifuga
#endif

cdef struct Touch:
    int x, y
    bint valid

cdef class GameLoop(GameLoopBase):
    cdef int _screen_w, _screen_h
    cdef Renderer renderer
#if DEBUG and (__LINUX__ or __OSX__ or __MINGW__)
    cdef FileWatcher *fw
    cdef FileWatchListenerIgnifuga *fwli
#endif
    cdef Touch touches[20], lastTouch
    cdef object touchCaptor
    cdef bint touchCaptured
    cdef int active_touches

    cdef handleSDLEvent(self, SDL_Event *sdlev)
    cdef normalizeFingerEvent(self, SDL_TouchFingerEvent *fev)

    cdef handleTouch(self, EventType action, int x, int y, int stream)
    cdef handleEthereal(self, EventType event)




