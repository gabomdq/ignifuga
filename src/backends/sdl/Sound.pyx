#!/usr/bin/env python
#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Sound component - SDL_mixer based

from ignifuga.Log import debug, error
from ignifuga.Gilbert import Gilbert
from ignifuga.components.Component import Component
from ignifuga.Task import STOP

channelMap = {}

cdef public void ChannelFinishedCallback( int channel ) with gil:
    cdef PyObject *pycb
    cdef SDL_Event event
    if channel in channelMap:
        component = channelMap[channel]
        try:
            cb = component.channelStopped
            pycb = <PyObject*> cb
            Py_XINCREF(pycb)
            event.type = SDL_USEREVENT
            event.user.code = MIX_CHANNEL_STOPPED
            event.user.data1 = <void*>pycb
            event.user.data2 = <void*>channel
            SDL_PushEvent(&event)
        except:
            pass
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
        self.onStart = None
        self.onStop = None
        self.onLoop = None
        self._loop = 0
        self._loopMax = 1
        self._volume = MIX_MAX_VOLUME
        self.fadeIn = 0
        self.fadeOut = 0
        self.length = -1
        self.fadeInLoop = False

    cpdef init(self):
        self.chunk = Gilbert().dataManager.getChunk(self.file)

    cpdef free(self):
        self.chunk = None

    cpdef play(self, int fadein=0, int ticks=-1):
        global channelMap
        if self.channel == -1:
            if fadein == 0:
                self.channel = Mix_PlayChannelTimed(-1, self.chunk.chunk, 0, ticks)
            else:
                self.channel = Mix_FadeInChannelTimed(-1, self.chunk.chunk, 0, fadein, ticks)

            self.setVolume(self._volume)
            if self.channel != -1:
                channelMap[self.channel] = self
                if self._loop == 0 and self.onStart is not None:
                    self.run(self.onStart)
            else:
                error("Error playing %s" % self.file)

    cpdef stop(self, int fadeout=0):
        if self.channel != -1:
            # Prevent further looping
            self._loop = -2
            if fadeout == 0:
                Mix_HaltChannel(self.channel)
            else:
                Mix_FadeOutChannel(self.channel, fadeout)
            self.channel = -1

    cpdef pause(self):
        if self.channel != -1:
            Mix_Pause(self.channel)

    cpdef resume(self):
        if self.channel != -1:
            Mix_Resume(self.channel)

    cpdef channelStopped(self):
        self.channel = -1
        self._loop += 1
        if self._loop > 0 and (self._loopMax < 0 or self._loop < self._loopMax):
            if self.onLoop is not None:
                self.run(self.onLoop)
            if self.fadeInLoop:
                self.play(self.fadeIn, self.length)
            else:
                self.play(0, self.length)
        elif self.onStop is not None:
            self._loop = 0
            self.run(self.onStop)
            self.active = False

    cdef setVolume(self, int vol):
        if vol < 0:
            vol = 0
        elif vol > MIX_MAX_VOLUME:
            vol = MIX_MAX_VOLUME
        self._volume = vol
        if self.channel != -1:
            Mix_Volume(self.channel, self._volume)

    property loop:
        def __get__(self):
            return self._loopMax
        def __set__(self, value):
            if value is None:
                self._loopMax = -1
            else:
                self._loopMax = value

    property active:
        def __get__(self):
            return self.channel != -1
        def __set__(self, value):
            if value:
                if self.channel == -1:
                    self.play(self.fadeIn, self.length)
            else:
                if self.channel != -1:
                    self.stop(self.fadeOut)

    property volume:
        def __get__(self):
            return self._volume
        def __set__(self, value):
            self.setVolume(value)

    property isPaused:
        def __get__(self):
            if self.channel != -1:
                return Mix_Paused(self.channel) != 0
            return False

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
    def __init__(self, id=None, entity=None, active=False,  **data):
        # Default values
        self._loadDefaults({
            'file': None
        })

        # Don't change this initialization order!
        _SoundComponent.__init__(self)
        super(SoundComponent, self).__init__(id, entity, active, **data)


    def init(self, **data):
        """ Initialize the required external data """
        # Don't change this order!
        _SoundComponent.init(self)
        super(SoundComponent, self).init(**data)

    def free(self, **kwargs):
        # Don't change this order!
        _SoundComponent.free(self)
        super(SoundComponent, self).free(**kwargs)

    def update(self, now, **data):
        STOP()
        return

    @Component.active.getter
    def active(self):
        return _SoundComponent.active

    @Component.active.setter
    def active(self, value):
        _SoundComponent.active.__set__(self, value)
        Component.active.fset(self, value)

class MusicComponent(Component, _MusicComponent):
    """ A SDL Mixer based music component"""
    PROPERTIES = Component.PROPERTIES + []
    def __init__(self, id=None, entity=None, active=False, **data):
        # Default values
        self._loadDefaults({
            'file': None,
            })

        _MusicComponent.__init__(self)
        super(MusicComponent, self).__init__(id, entity, active, **data)


    def init(self, **data):
        """ Initialize the required external data """
        super(MusicComponent, self).init(**data)
        _SoundComponent.init(self)

    def free(self, **kwargs):
        super(MusicComponent, self).free(**kwargs)
        _SoundComponent.free(self)

    def update(self, now, **data):
        STOP()
        return
