#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Ignifuga Game Engine
# Game Loop
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.backends.sdl.SDL cimport *
from ignifuga.backends.sdl.Target cimport Target
from ignifuga.Gilbert import Gilbert, Event
from ignifuga.backends.GameLoopBase cimport GameLoopBase

cdef class GameLoop(GameLoopBase):
    cdef int _screen_w, _screen_h
    cpdef run(self)
    cdef handleSDLEvent(self, SDL_Event *sdlev)
    cdef normalizeFingerEvent(self, SDL_TouchFingerEvent *fev)
