#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


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
        self.notifications = {}

    def __del__(self):        
        self.cleanup(True)

    def cleanup(self, force = False):
        #debug('Releasing Data Manager contents %s' % ('(forced)' if force else '',))
        keys = []
        for url in self.cache.iterkeys():
            refCnt = len(gc.get_referrers(self.cache[url]))
            if force or refCnt <= 1:
                keys.append(url)

        if keys:
            debug( "DataManager will release: %s" % keys)
        for url in keys:
            refCnt = len(gc.get_referrers(self.cache[url]))
            if refCnt > 1:
                error('Error: Releasing data for %s with ref count: %d' % (url, refCnt))
            del self.cache[url]

    def loadJsonFile(self, name):
        raise Exception('method not implemented')

    def getImage(self, url):
        raise Exception('method not implemented')

    def getFont(self, url, size):
        raise Exception('method not implemented')

    def urlReloaded(self, url):
        raise Exception('method not implemented')

    def addListener(self, url, obj):
        print "add listener", url, obj
        if url not in self.notifications:
            self.notifications[url] = []

        if obj not in self.notifications[url]:
            self.notifications[url].append(obj)

    def removeListener(self, url, obj):
        if url in self.notifications and obj in self.notifications[url]:
            self.notifications[url].remove(obj)
