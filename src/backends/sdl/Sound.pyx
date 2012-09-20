#!/usr/bin/env python
#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Sound component - SDL_mixer based

from ignifuga.Log import debug, error
from ignifuga.Gilbert import Gilbert
from ignifuga.components.Component import Component

channelMap = {}

cdef public void ChannelFinishedCallback( int channel ) with gil:
    if channel in channelMap:
        channelMap[channel].channelStopped()
        channelMap[channel] = None

cdef initializeSound():
    #cdef channel_finished_ptr ptr = ChannelFinishedCallback
    Mix_ChannelFinished(ChannelFinishedCallback)


cdef class Chunk:
    def __init__ (self, srcURL = None, embedded=None):

        if srcURL is not None:
            self._srcURL = bytes(srcURL)
        else:
            self._srcURL = None

        if embedded is not None:
            self.embedded_data = bytes(embedded)
        else:
            self.embedded_data = None
        self.load()

    cpdef load(self):
        cdef char *bindata
        cdef int src_len
        self.free()
        if self._srcURL is not None or self.embedded_data is not None:
            if self._srcURL is not None:
                self.chunk = Mix_LoadWAV(self._srcURL)
            elif self.embedded_data is not None:
                src_len = len(self.embedded_data)
                bindata = self.embedded_data
                rwops = SDL_RWFromConstMem(<void*>bindata, src_len )
                if rwops != NULL:
                    self.chunk = Mix_LoadWAV_RW(rwops, 1)

        if self.chunk == NULL:
            error("Error loading audio chunk (%s - %s)" % (self._srcURL, self.embedded_data))

    cpdef reload(self, url):
        cdef Mix_Chunk * oldchunk = self.chunk
        self.free()
        self._srcURL = bytes(url)
        self.load()
        if oldchunk != NULL and self.chunk != NULL and self.chunk != oldchunk:
            # Update anyone that needs an update
            pass

    cdef free(self):
        if self.chunk != NULL:
            Mix_FreeChunk(self.chunk)
            self.chunk = NULL

    def __dealloc__(self):
        self.free()

cdef class Music:
    def __init__ (self, srcURL = None, embedded=None):

        if srcURL is not None:
            self._srcURL = bytes(srcURL)
        else:
            self._srcURL = None

        if embedded is not None:
            self.embedded_data = bytes(embedded)
        else:
            self.embedded_data = None

        self.load()

    cpdef load(self):
        cdef char *bindata
        cdef int src_len
        self.free()
        if self._srcURL is not None or self.embedded_data is not None:
            if self._srcURL is not None:
                self.music = Mix_LoadMUS(self._srcURL)
            elif self.embedded_data is not None:
                src_len = len(self.embedded_data)
                bindata = self.embedded_data
                rwops = SDL_RWFromConstMem(<void*>bindata, src_len )
                if rwops != NULL:
                    self.music = Mix_LoadMUSType_RW(rwops,MUS_NONE, 1)

    cpdef reload(self, url):
        cdef Mix_Music * oldmusic = self.music
        self.free()
        self._srcURL = bytes(url)
        self.load()
        if oldmusic != NULL and self.music != NULL and self.music != oldmusic:
            # Update anyone that needs an update
            pass

    cdef free(self):
        if self.music != NULL:
            Mix_FreeMusic(self.music)
            self.music = NULL

    def __dealloc__(self):
        self.free()


cdef class _SoundComponent:
    """ A SDL Mixer based sound component"""
    def __init__(self):
        self.chunk = None
        self.channel = -1

    cpdef init(self):
        self.chunk = Gilbert().dataManager.getChunk(self.file)

    cpdef free(self):
        self.chunk = None

    cpdef play(self, int loops=0):
        global channelMap
        if self.channel == -1:
            self.channel = Mix_PlayChannel(-1, self.chunk.chunk, loops)
            if self.channel != -1:
                channelMap[self.channel] = self
            else:
                error("Error playing %s" % self.file)

    cpdef channelStopped(self):
        self.channel = -1

cdef class _MusicComponent:
    """ A SDL Mixer based music component"""
    def __init__(self):
        self.music = None

    cpdef init(self):
        self.music = Gilbert().dataManager.getMusic(self.file)

    cpdef free(self):
        self.music = None


class SoundComponent(Component, _SoundComponent):
    """ A SDL Mixer based sound component"""
    PROPERTIES = Component.PROPERTIES + []
    def __init__(self, id=None, entity=None, active=True, frequency=15.0,  **data):
        # Default values
        self._loadDefaults({
            'file': None,
        })

        super(SoundComponent, self).__init__(id, entity, active, frequency, **data)
        _SoundComponent.__init__(self)

    def init(self, **data):
        """ Initialize the required external data """
        super(SoundComponent, self).init(**data)
        _SoundComponent.init(self)

    def free(self, **kwargs):
        super(SoundComponent, self).free(**kwargs)
        _SoundComponent.free(self)

    def update(self, now, **data):
        #STOP()
        return

class MusicComponent(Component, _MusicComponent):
    """ A SDL Mixer based music component"""
    PROPERTIES = Component.PROPERTIES + []
    def __init__(self, id=None, entity=None, active=True, frequency=15.0,  **data):
        # Default values
        self._loadDefaults({
            'file': None,
            })

        super(MusicComponent, self).__init__(id, entity, active, frequency, **data)
        _MusicComponent.__init__(self)

    def init(self, **data):
        """ Initialize the required external data """
        super(MusicComponent, self).init(**data)
        _SoundComponent.init(self)

    def free(self, **kwargs):
        super(MusicComponent, self).free(**kwargs)
        _SoundComponent.free(self)

    def update(self, now, **data):
        #STOP()
        return
