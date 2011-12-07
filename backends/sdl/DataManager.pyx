#Copyright (c) 2010,2011, Gabriel Jacobo
#All rights reserved.

#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions are met:

    #* Redistributions of source code must retain the above copyright
      #notice, this list of conditions and the following disclaimer.
    #* Redistributions in binary form must reproduce the above copyright
      #notice, this list of conditions and the following disclaimer in the
      #documentation and/or other materials provided with the distribution.
    #* Altered source versions must be plainly marked as such, and must not be
      #misrepresented as being the original software.
    #* Neither the name of Gabriel Jacobo, MDQ Incorporeo, Ignifuga Game Engine
      #nor the names of its contributors may be used to endorse or promote
      #products derived from this software without specific prior written permission.
    #* You must NOT, under ANY CIRCUMSTANCES, remove, modify or alter in any way
      #the duration, code functionality and graphic or audio material related to
      #the "splash screen", which should always be the first screen shown by the
      #derived work and which should ALWAYS state the Ignifuga Game Engine name,
      #original author's URL and company logo.

#THIS LICENSE AGREEMENT WILL AUTOMATICALLY TERMINATE UPON A MATERIAL BREACH OF ITS
#TERMS AND CONDITIONS

#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL GABRIEL JACOBO NOR MDQ INCORPOREO NOR THE CONTRIBUTORS
#BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Ignifuga Game Engine
# Data Manager
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import json
from ignifuga.Gilbert import Gilbert, createNode
from ignifuga.Log import debug, error
from SDL import *

cdef class DataCache(_DataCache):
    pass

cdef class DataManager(DataManagerBase):
    cpdef str readFile(self, str name):
        cdef bytes contents = bytes()
        cdef bytes filename = <bytes>name
        cdef SDL_RWops *ctx = SDL_RWFromFile(filename, 'r')
        cdef char *buf
        cdef size_t bytesread
        if ctx != NULL:
            buf = <char*>malloc(1025)
            bytesread = ctx.read(ctx, buf, 1, 1024)
            while bytesread > 0:
                buf[bytesread] = 0
                contents += buf
                bytesread = ctx.read(ctx, buf, 1, 1024)

            ctx.close(ctx)
            free(buf)
            return str(contents)
        return None
        
    cpdef Node loadScene(self, str name):
            return self.processScene(json.loads(self.readFile('data/scenes/'+name+'.json')))
        
    cpdef dict getSprite(self, url):
        if url not in self.cache:
            dc = DataCache()
            data = json.loads(self.readFile(str(url)))
            dc.data = data
            self.cache[url] = dc
        else:
            dc = self.cache[url]
            dc.addRef()
            
        return dc.data

    cpdef CanvasBase getImage(self, url):
        if url not in self.cache:
            dc = DataCache()
            dc.canvas = Canvas(srcURL=url)
            self.cache[url] = dc
        else:
            dc = self.cache[url]
            dc.addRef()
            
        return dc.canvas
        
    cpdef Node processScene(self, dict data):
        createNode(None, data)

    cpdef FontBase getFont(self, url, size):
        cdef bytes burl
        cdef DataCache dc
        cdef TTF_Font *ttf_font
        cdef Font font
        
        cache_url = '%s+%d' % (url, size)
        if cache_url not in self.cache:
            dc = DataCache()
            font = Font()
            burl = bytes(url)
            ttf_font = TTF_OpenFont(burl, size)
            if ttf_font != NULL:
                font.ttf_font = ttf_font
                dc.font = font
                self.cache[cache_url] = dc
            else:
                error('Error loading font %s: %s' % (url, SDL_GetError()) )
                return None
        else:
            dc = self.cache[cache_url]
            dc.addRef()
            
        return dc.font

    cpdef releaseFont(self, url, size):
        cache_url = '%s+%d' % (url, size)
        if cache_url in self.cache:
            self.cache[cache_url].removeRef()