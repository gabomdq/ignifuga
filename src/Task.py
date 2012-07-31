#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


# Ignifuga Game Engine
# Task Utility functions
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import greenlet
from ignifuga.backends.GameLoopBase import TASK_REQUEST_DONE, TASK_REQUEST_LOADIMAGE, TASK_REQUEST_ERROR, TASK_REQUEST_STOP, TASK_REQUEST_SKIP

def DONE(data=None):
    g = greenlet.getcurrent()
    return g.parent.switch((TASK_REQUEST_DONE, data))

def ERROR(data=None):
    g = greenlet.getcurrent()
    return g.parent.switch((TASK_REQUEST_ERROR, data))

def STOP(data=None):
    g = greenlet.getcurrent()
    return g.parent.switch((TASK_REQUEST_STOP, data))

def SKIP(data=None):
    g = greenlet.getcurrent()
    return g.parent.switch((TASK_REQUEST_SKIP, data))

def LOAD_IMAGE(url):
    g = greenlet.getcurrent()
    return g.parent.switch((TASK_REQUEST_LOADIMAGE, {'url': url}))

