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
    def loadSceneData(self, filename):
        url = 'data/scenes/'+filename+'.json'
        return url, self.loadJsonFile(url)

    def loadJsonFile(self, url):
        if url not in self.cache:
            data = json.loads(readFile(url))
            ret_data = {}
            for k,v in data.items():
                key, value = sanitizeData(k,v)
                ret_data[key] = value

            self.cache[url] = ret_data
            Gilbert().gameLoop.addWatch(url)

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
                self.cache[url] = Canvas(srcURL=url)
                Gilbert().gameLoop.addWatch(url)

        return self.cache[url]

    def getFont(self, url, size):
        cache_url = '%s+%d' % (url, size)
        if cache_url not in self.cache:
            self.cache[cache_url] = Font(url, size)
        return self.cache[cache_url]

    def urlReloaded(self, url):
        reload = []
        if url in self.cache:
            if url in self.notifications:
                for ref in self.notifications[url]:
                    if hasattr(ref, 'reload') and ref not in reload:
                        reload.append(ref)

            if isinstance(self.cache[url], Canvas):
                # Reload the canvas before issuing the notifications
                self.cache[url].reload(url)
            else:
                del self.cache[url]

            for ref in reload:
                ref.reload(url)


