#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


# Ignifuga Game Engine
# SDL Font wrapper
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

# xcython: profile=True

from ignifuga.Log import *
from libc.stdlib cimport *

cdef class Font(FontBase):
    def __init__(self, url, size):
        cdef bytes burl

        burl = bytes(url)
        #self.ttf_font = TTF_OpenFont(burl, size) -> Fails under Android (deadlocks!)
        cdef unsigned int chunk = 65536, read
        self.buffersize = 0
        self.buffer = <char*>malloc(chunk * sizeof(char))
        if self.buffer == NULL:
            error("Could not allocate tmp buffer to load font!")
            return

        cdef SDL_RWops *file = SDL_RWFromFile(burl, "rb")
        if file != NULL:
            while True:
                read = file.read(file, self.buffer+self.buffersize, sizeof(char), chunk)
                self.buffersize += read * sizeof(char)
                if read >= chunk:
                    self.buffer = <char*>realloc(self.buffer, self.buffersize)
                else:
                    break

            file.close(file)
            file = SDL_RWFromMem(self.buffer, self.buffersize)
            self.ttf_font = TTF_OpenFontRW(file, 1, size)

        if self.ttf_font == NULL:
            error('Error loading font %s: %s' % (url, SDL_GetError()) )


    def __dealloc__(self):
        #debug('FONT DEALLOC')
        if self.ttf_font != NULL:
            #debug('Releasing TTF Font')
            TTF_CloseFont(self.ttf_font)
            self.ttf_font = NULL
            free(self.buffer)
            self.buffer = NULL
            self.buffersize = 0


    def __deepcopy__(self, memo):
        """ Don't allow deepcopying of the Font"""
        return self

    def __copy__(self):
        """ Don't allow copying of the Font"""
        return self