#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Ignifuga Game Engine
# Pathfinder Component class
# Author: Gabriel Jacobo <gabriel@mdqinc.com>
from libc.stdlib cimport *
from libc.string cimport *
from libcpp.map cimport *
from libcpp.deque cimport *
from libcpp.pair cimport *
from cpython cimport *
from ignifuga.Scene cimport _Scene, _WalkAreaVertex, WalkAreaVertexIterator, WalkAreaVertexDeque

cdef extern from "math.h":
    double sqrt(double x)

cdef struct _PathfinderNode:
    int x
    int y
    _PathfinderNode *prev
    double distance

ctypedef deque[_PathfinderNode] PathfinderNodeDeque
ctypedef deque[_PathfinderNode].iterator PathfinderNodeIterator

cdef class _PathfinderComponent:
    cdef bint pointInArea(self, int x, int y, WalkAreaVertexDeque *areas, int numAreas)
    cdef bint lineInArea(self, int isx, int isy, int iex, int iey, WalkAreaVertexDeque *areas, int numAreas)
    cdef bint shortestPath(self, int sX, int sY, int eX, int eY, WalkAreaVertexDeque *areas, int numAreas, PathfinderNodeDeque *solution)

    cpdef path(self, int x, int y)
    cpdef bint goto(self, int x, int y)