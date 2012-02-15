#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


# Ignifuga Game Engine
# Game Loop
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from cpython cimport bool

cdef class GameLoopBase(object):
    cdef public bool quit, paused
    cdef public double _fps, _interval
    cdef str platform
