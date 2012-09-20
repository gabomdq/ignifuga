#!/usr/bin/env python
#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Sound components - SDL_mixer based

from ignifuga.backends.sdl.SDL cimport *
from cpython cimport *
from libcpp.map cimport *

cdef initializeSound()
cdef public void ChannelFinishedCallback( int channel ) with gil

cdef class Chunk:
    cdef bytes _srcURL, embedded_data
    cdef Mix_Chunk *chunk

    cpdef load(self)
    cpdef reload(self, url)
    cdef free(self)

cdef class Music:
    cdef bytes _srcURL, embedded_data
    cdef Mix_Music *music

    cpdef load(self)
    cpdef reload(self, url)
    cdef free(self)

cdef class _SoundComponent:
    cdef Chunk chunk
    cdef int channel
    cpdef init(self)
    cpdef free(self)
    cpdef play(self, int loops=?)
    cpdef channelStopped(self)

cdef class _MusicComponent:
    cdef Music music
    cpdef init(self)
    cpdef free(self)
