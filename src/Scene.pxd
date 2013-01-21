#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Ignifuga Game Engine
# Scene class, a basic way to organize entities
# Author: Gabriel Jacobo <gabriel@mdqinc.com>


from libc.stdlib cimport *
from libc.string cimport *
from libcpp.map cimport *
from libcpp.deque cimport *
from libcpp.pair cimport *
from cpython cimport *

cdef struct _WalkAreaVertex:
    int x
    int y
    int index
    int numVertexs

ctypedef deque[_WalkAreaVertex] WalkAreaVertexDeque
ctypedef deque[_WalkAreaVertex].iterator WalkAreaVertexIterator

cdef class _Scene:
    cdef bint released
    cdef WalkAreaVertexDeque *walkAreas
    cdef int numWalkAreas

    cpdef _updateWalkAreas(self, areas)
    cdef init(self)
    cdef free(self)