#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


# Ignifuga Game Engine
# Task Utility functions
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import greenlet
from ignifuga.Gilbert import REQUESTS

class Task(greenlet.greenlet):
    def __init__(self, entity_wr, run=None, parent=None):
        # A ref or weakref to the associated entity
        self.entity = entity_wr
        self.runnable = run
        super(Task, self).__init__(run,parent)

    def wakeup(self, data=None):
        value = self.switch(data)
        if self.dead:
            req = REQUESTS.done
            data = value
        else:
            req, data = value
            
        return req,data
        

def DONE(entity):
    g = greenlet.getcurrent()
    return g.parent.switch((REQUESTS.done, None))
    
def LOAD_IMAGE(url):
    g = greenlet.getcurrent()
    return g.parent.switch((REQUESTS.loadImage, {'url': url}))
    
#def LOAD_SPRITE(url):
#    g = greenlet.getcurrent()
#    return g.parent.switch((REQUESTS.loadSprite, {'url': url}))
    
    
#def NATIVE_RESOLUTION(w, h, keep_aspect):
#    g = greenlet.getcurrent()
#    return g.parent.switch((REQUESTS.nativeResolution, (w, h, keep_aspect)))
#
#def SCENE_SIZE(w, h):
#    g = greenlet.getcurrent()
#    return g.parent.switch((REQUESTS.sceneSize, (w, h)))

    
#def DIRTY_RECTS (rects):
#    g = greenlet.getcurrent()
#    return g.parent.switch((REQUESTS.dirtyRects, rects))
