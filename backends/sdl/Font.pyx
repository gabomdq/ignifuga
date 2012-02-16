#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


# Ignifuga Game Engine
# SDL Font wrapper
# Author: Gabriel Jacobo <gabriel@mdqinc.com>
from ignifuga.Log import *

cdef class Font(FontBase):
    def __init__(self, url, size):
        cdef bytes burl

        burl = bytes(url)
        self.ttf_font = TTF_OpenFont(burl, size)
        if self.ttf_font == NULL:
            error('Error loading font %s: %s' % (url, SDL_GetError()) )


    def __dealloc__(self):
        #debug('FONT DEALLOC')
        if self.ttf_font != NULL:
            #debug('Releasing TTF Font')
            TTF_CloseFont(self.ttf_font)
            self.ttf_font = NULL


    def __deepcopy__(self, memo):
        """ Don't allow deepcopying of the Font"""
        return self

    def __copy__(self):
        """ Don't allow copying of the Font"""
        return self