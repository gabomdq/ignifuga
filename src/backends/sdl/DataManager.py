#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


# Ignifuga Game Engine
# Data Manager
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import json, gc
from ignifuga.Gilbert import Gilbert
from ignifuga.Log import debug, error
from SDL import *
from ignifuga.backends.DataManagerBase import *
from Canvas import Canvas
from Font import Font
from os.path import abspath, join, dirname, getmtime, isfile, isdir

#if __LINUX__ or __OSX__ or __MINGW__
ROOT_DIR = abspath(dirname(sys.argv[0]))
#else
ROOT_DIR = ''
#endif


def sanitizeData (k,v, p=True):
    """ Sanitize data, convert keys in the data to str"""
    key = str(k)
    if isinstance(v, dict):
        value = {}
        for k1, v1 in v.items():
            key1, value1 = sanitizeData(k1,v1)
            value[key1] = value1
    elif isinstance(v, list):
        value = []
        for v1 in v:
            k1,v1 =  sanitizeData(key, v1)
            value.append(v1)
    else:
        value = v

    return key, value

class DataManager(DataManagerBase):
    def __init__(self):
        super(DataManager, self).__init__()
        self.watches = []
        self.mtimes = {}

    def _urlToWatchUrl(self, url):
        #if DEBUG and __LINUX__
        watchURL = join(ROOT_DIR, url)
        if not isfile(watchURL):
            return None
        #endif

        #if DEBUG and (__MINGW__ or __OSX__)
        watchURL = dirname(join(ROOT_DIR, url))
        if not isfile(watchURL):
            return None
        self.mtimes[url] = getmtime(join(ROOT_DIR, url))
        #endif

        return watchURL

    def addListener(self, url, obj):
        #if DEBUG and (__LINUX__ or __OSX__ or __MINGW__)
        watchURL = self._urlToWatchUrl(url)
        if watchURL is not None and watchURL not in self.watches:
            Gilbert().gameLoop.addWatch(watchURL)
            self.watches.append(watchURL)
        #endif
        super(DataManager, self).addListener(url, obj)

    def removeListener(self, url, obj):
        # TODO: Remove watcher
        super(DataManager, self).removeListener(url, obj)

    def loadSceneData(self, filename):
        url = join('data','scenes',filename+'.json')
        return url, self.loadJsonFile(url)

    def loadJsonFile(self, url):
        if url not in self.cache:
            data = json.loads(readFile(join(ROOT_DIR, url)))
            ret_data = {}
            for k,v in data.items():
                key, value = sanitizeData(k,v)
                ret_data[key] = value

            self.cache[url] = ret_data

#if DEBUG and (__LINUX__ or __OSX__ or __MINGW__)
            watchURL = self._urlToWatchUrl(url)
            if watchURL not in self.watches:
                Gilbert().gameLoop.addWatch(watchURL)
                self.watches.append(watchURL)
#endif
        return self.cache[url]

    def getImage(self, url):
        if url not in self.cache:
            if url.startswith('embedded:'):
                data = Gilbert().getEmbedded(url[9:])
                if data != None:
                    self.cache[url] = Canvas(embedded=data)
                else:
                    error('Error loading embedded data with id: %s', url)
                    return None
            else:
                self.cache[url] = Canvas(srcURL=join(ROOT_DIR, url))

#if DEBUG and (__LINUX__ or __OSX__ or __MINGW__)
                watchURL = self._urlToWatchUrl(url)
                if watchURL not in self.watches:
                    Gilbert().gameLoop.addWatch(watchURL)
                    self.watches.append(watchURL)
#endif

        return self.cache[url]

    def getFont(self, url, size):
        cache_url = '%s+%d' % (url, size)
        if cache_url not in self.cache:
            self.cache[cache_url] = Font(url, size)
        return self.cache[cache_url]

    def urlReloaded(self, url):
        print "urlReloaded", url
#if  __MINGW__
        # On Windows and OSX, we monitor directories, not individual files, so from the files that we know exist in that dir
        # we check which ones where modified
        if url.startswith(ROOT_DIR):
            url = url[len(ROOT_DIR)+1:]

        reload = []
        for cache_url in self.cache.iterkeys():
            if dirname(cache_url) == url:
                reload.append(cache_url)

        for cache_url in reload:
            new_mtime = getmtime(join(ROOT_DIR, cache_url))
            if new_mtime > self.mtimes[cache_url]:
                self.mtimes[cache_url] = new_mtime
                self._urlReloaded(cache_url)
#else
        self._urlReloaded(url)
#endif

    def _urlReloaded(self, url):
        reload = []
        if url.startswith(ROOT_DIR):
            url = url[len(ROOT_DIR)+1:]

        if url in self.notifications:
            for ref in self.notifications[url]:
                if hasattr(ref, 'reload') and ref not in reload:
                    reload.append(ref)

        if url in self.cache:
            if isinstance(self.cache[url], Canvas):
                # Reload the canvas before issuing the notifications
                self.cache[url].reload(url)
            else:
                del self.cache[url]

        for ref in reload:
            ref.reload(url)


