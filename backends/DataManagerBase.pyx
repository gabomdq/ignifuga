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
# Data Manager Base
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.Log import debug, error

cdef class DataCache(object):
    def __init__(self):
        self.owners = list()
        self.canvas = None
        self.data = None
        self.font = None

    def __dealloc__(self):
        if len(self.owners) != 0:
            error('Releasing DataCache with Ref Count: %d' % len(self.owners))
            
        if self.canvas != None:
            self.canvas.free()
            self.canvas = None

        if self.font != None:
            self.font.free()
            self.font = None

        if self.data != None:
            self.data = None


cdef class DataManagerBase(object):
    def __init__(self):
        self.cache = {}

    def __del__(self):        
        self.free(True)

    def free(self, force = False):
        debug('Releasing Data Manager contents %s' % ('(forced)' if force else '',))
        keys = []
        for k, dc in self.cache.iteritems():
            if force or dc.refCount == 0:
                keys.append(k)

        for k in keys:
            del self.cache[k]
  
    cpdef Node loadScene(self, str name):
        raise Exception('method not implemented')
        
    cpdef dict getSprite(self, url):
        raise Exception('method not implemented')

    cpdef CanvasBase getImage(self, url):
        raise Exception('method not implemented')
        
    cpdef Node processScene(self, dict data):
        raise Exception('method not implemented')

    cpdef FontBase getFont(self, url, size):
        raise Exception('method not implemented')

    cpdef release(self, url):
        if url in self.cache:
            self.cache[url].removeRef()
