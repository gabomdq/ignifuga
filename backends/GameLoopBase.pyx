#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


# Ignifuga Game Engine
# Game Loop
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

cdef class GameLoopBase(object):
    def __init__(self, fps = 30.0):
        # SDL should be initialized at this point when Target was instantiated
        self.quit = False
        self.fps = fps

    def run(self):
        raise Exception('not implemented')

    property fps:
        def __get__(self):
            return self._fps
        def __set__(self, fps):
            self._fps = float(fps)
            self._interval = 1000.0 / fps
        
