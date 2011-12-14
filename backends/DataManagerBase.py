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
import weakref, sys, gc

class WRDict(dict):
    # We need this subclass because pure dict is not weakref-able
    pass

#class DataCache(object):
#    def __init__(self, data=None, url=None):
#        self.owners = []
#        self.data = data
#        self.url = url
#
#    def __del__(self):
#        for o in self.owners:
#            if o() != None:
#                debug('Releasing %s still owned by %s' % (self.data, o))
#
#        if self.data != None:
#            if hasattr(self.data, 'free'):
#                self.data.free()
#            del self.data
#            self.data = None
#
#    def addOwner(self, owner):
#        if owner == None:
#            error('Trying to add None owner to DataCache')
#            return
#
#        if isinstance(owner, weakref.ref):
#            self.owners.append(owner)
#        else:
#            self.owners.append(weakref.ref(owner))
#
#    def removeOwner(self, owner):
#        if owner == None:
#            error('Trying to remove None owner from DataCache')
#            return
#        for o in self.owners:
#            if o() == owner:
#                self.owners.remove(o)
#                break
#
#    def cleanOwners(self):
#        """ Clean up the owner data, remove the non existent ones """
#        _owners = []
#        while len(self.owners) > 0:
#            o = self.owners.pop()
#            if o() != None:
#                _owners.append(o)
#
#        self.owners = _owners
#
#    @property
#    def ownerCount(self):
#        return len(self.owners)
#
#    def __eq__(self, other):
#        """ Compare against the data"""
#        return self.data == other
from ignifuga.Log import *

class DataManagerBase(object):
    def __init__(self):
        self.cache = {}

    def __del__(self):        
        self.cleanup(True)

    def cleanup(self, force = False):
        debug('Releasing Data Manager contents %s' % ('(forced)' if force else '',))
        keys = []
        for url in self.cache.iterkeys():
            refCnt = len(gc.get_referrers(self.cache[url]))
            if force or refCnt <= 1:
                keys.append(url)

        debug( "DataManager will release: %s" % keys)
        for url in keys:
            refCnt = len(gc.get_referrers(self.cache[url]))
            if refCnt > 1:
                error('Error: Releasing data for %s with ref count: %d' % (url, refCnt))
            del self.cache[url]

    def loadScene(self, name):
        raise Exception('method not implemented')
        
    def getSprite(self, url):
        raise Exception('method not implemented')

    def getImage(self, url):
        raise Exception('method not implemented')

    def getFont(self, url, size):
        raise Exception('method not implemented')
