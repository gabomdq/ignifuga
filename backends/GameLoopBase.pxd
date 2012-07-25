#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


# Ignifuga Game Engine
# Game Loop
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from cpython cimport *
from libc.stdlib cimport *
from libc.string cimport *
from libcpp.map cimport *
from libcpp.deque cimport *
from libcpp.pair cimport *

cdef extern from "Python.h":
    struct _frame

cdef extern from "Modules/greenlet.h":
    cdef struct _greenlet
    cdef struct _greenlet:
        PyObject head
        char* stack_start
        char* stack_stop
        char* stack_copy
        long stack_saved
        _greenlet* stack_prev
        _greenlet* parent
        PyObject* run_info
        _frame* top_frame
        int recursion_depth
        PyObject* weakreflist

    ctypedef _greenlet PyGreenlet
    PyGreenlet * PyGreenlet_New(PyObject *run, PyGreenlet *parent)
    PyGreenlet * PyGreenlet_GetCurrent()
    PyObject * PyGreenlet_Switch(PyGreenlet *greenlet, PyObject *args, PyObject *kwargs)
    void PyGreenlet_Import()

ctypedef enum REQUESTS:
    REQUEST_NONE = 0x00000000
    REQUEST_DONE = 0x00000001
    REQUEST_SKIP = 0x00000002
    REQUEST_STOP = 0x00000004
    REQUEST_LOADIMAGE = 0x0000008
    REQUEST_ERROR = 0x80000000

cdef struct _Task:
    PyGreenlet *greenlet
    REQUESTS req
    PyObject *entity
    PyObject *runnable
    PyObject *data
    bint release

ctypedef _Task*  _Task_p

cdef struct _EntityTasks:
    _Task *loading
    _Task *running

ctypedef PyObject* PyObject_p

ctypedef map[PyObject_p, _EntityTasks].iterator entities_iterator
ctypedef deque[_Task].iterator task_iterator

cdef class GameLoopBase(object):
    cdef public bint quit, paused, freezeRenderer
    cdef public double _fps
    cdef str platform
    cdef deque[_Task] *loading
    cdef deque[_Task] *running
    cdef map[PyObject_p, _EntityTasks] *entities
    cdef readonly unsigned long frame_time, _interval, ticks_second
    cdef PyGreenlet *main_greenlet

    cpdef startEntity(self, entity)
    cpdef startComponent(self, component)
    cpdef bint stopEntity(self, entity)
    cpdef bint stopComponent(self, component)
    cpdef update(self, int now=*, bint wrapup=*)
    cdef bint _doSwitch(self, _Task *task, PyObject *args, PyObject *kwargs)
    cdef bint _processTask(self, _Task *task, int now=*, bint wrapup=*, bint init=*)
