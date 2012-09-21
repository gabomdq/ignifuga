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
cdef public void MusicFinishedCallback( ) with gil

cdef class MixChunk:
    cdef bytes _srcURL, embedded_data
    cdef Mix_Chunk *chunk

    cpdef load(self)
    cpdef reload(self, url)
    cdef free(self)

cdef class MixMusic:
    cdef bytes _srcURL, embedded_data
    cdef Mix_Music *music

    cpdef load(self)
    cpdef reload(self, url)
    cdef free(self)

cdef class _SoundComponent:
    cdef MixChunk chunk
    cdef int channel, _loop, _loopMax, _volume
    cdef public int fadeIn, fadeOut
    cdef public bint fadeInLoop
    cdef public object onStart, onLoop, onStop

    cpdef init(self)
    cpdef free(self)
    cpdef play(self, int fadein=?, int ticks=?)
    cpdef stop(self, int fadeout=?)
    cpdef pause(self)
    cpdef resume(self)
    cdef setVolume(self, int vol)
    cpdef channelStopped(self)

cdef class _MusicComponent:
    cdef MixMusic music
    cdef int _loop, _loopMax, _volume
    cdef public int fadeIn, fadeOut, length
    cdef public bint fadeInLoop, stopOnDeactivation
    cdef public object onStart, onLoop, onStop
    cdef bint _released
    cdef object stopCallback

    cpdef init(self)
    cpdef free(self)
    cpdef play(self, int fadein=?)
    cpdef stop(self, cb=?, int fadeout=?)
    cpdef pause(self)
    cpdef resume(self)
    cdef setVolume(self, int vol)
    cpdef musicStopped(self)

