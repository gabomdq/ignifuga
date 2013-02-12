#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Ignifuga Game Engine
# Game Loop
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

cdef public enum EventType:
    EVENT_TOUCH_DOWN = 1
    EVENT_TOUCH_UP = 2
    EVENT_TOUCH_MOTION = 3
    EVENT_TOUCH_LAST = 4
    EVENT_ETHEREAL_ZOOM_IN = 5
    EVENT_ETHEREAL_ZOOM_OUT = 6
    EVENT_ETHEREAL_SCROLL = 7

from cpython cimport *
from libc.stdlib cimport *
from libc.string cimport *
from libcpp.map cimport *
from libcpp.deque cimport *
from libcpp.pair cimport *

cdef extern from "Python.h":
    struct _frame

cdef extern from "Modules/greenlet.h":
#    cdef struct _greenlet:
#        PyObject head
#        char* stack_start
#        char* stack_stop
#        char* stack_copy
#        long stack_saved
#        _greenlet* stack_prev
#        _greenlet* parent
#        PyObject* run_info
#        _frame* top_frame
#        int recursion_depth
#        PyObject* weakreflist

    #ctypedef _greenlet PyGreenlet
    ctypedef PyObject PyGreenlet
    PyGreenlet * PyGreenlet_New(PyObject *run, PyGreenlet *parent)
    PyGreenlet * PyGreenlet_GetCurrent()
    PyObject * PyGreenlet_Switch(PyGreenlet *greenlet, PyObject *args, PyObject *kwargs)
    void PyGreenlet_Import()
    bint PyGreenlet_ACTIVE(PyGreenlet *greenlet)
    bint PyGreenlet_STARTED(PyGreenlet *greenlet)
    void PyGreenlet_GET_EXCEPTION(PyGreenlet *greenlet, PyObject *type, PyObject *value, PyObject *tb)

ctypedef enum REQUESTS:
    REQUEST_NONE = 0x00000000
    REQUEST_DONE = 0x00000001
    REQUEST_SKIP = 0x00000002
    REQUEST_STOP = 0x00000004
    REQUEST_LOADIMAGE = 0x0000008
    REQUEST_ERROR = 0x0000010

cdef struct _Task:
    PyGreenlet *greenlet
    REQUESTS req
    PyObject *entity
    PyObject *runnable
    PyObject *data
    bint release

ctypedef _Task*  _Task_p

ctypedef PyObject* PyObject_p

ctypedef deque[_Task].iterator task_iterator

cdef class GameLoopBase(object):
    cdef public bint quit, paused, freezeRenderer, released
    cdef public double _fps
    cdef str platform
    cdef deque[_Task] *loading, *loading_tmp, *running, *running_tmp
    cdef readonly unsigned long frame_time, _interval, ticks_second
    cdef PyGreenlet *main_greenlet
    cdef bint updateRemoteConsole
    cdef object remoteConsole
    cdef bint enableRemoteScreen, pauseOnFocusLost
    cdef object remoteScreenServer, remoteScreenHandlers


    cpdef startEntity(self, entity, bint load_phase=*)
    cpdef startComponent(self, component)
    cdef startRunnable(self, entity, bint load_phase=*, runnable=*)
    cpdef bint stopEntity(self, entity)
    cpdef bint stopComponent(self, component)
    cpdef update(self, unsigned long now=*, bint wrapup=*)
    cdef bint _doSwitch(self, _Task *task, PyObject *args, PyObject *kwargs)
    cdef bint _processTask(self, _Task *task, unsigned long now=*, bint wrapup=*, bint init=*)
    cpdef addWatch(self, filename)
    cpdef removeWatch(self, filename)
    cdef taskDecRef (self, _Task* taskp)
    cpdef free(self)
    cpdef addRemoteScreenHandler(self, handler)
    cpdef removeRemoteScreenHandler(self, handler)
    cpdef run(self)
    cpdef cleanup(self)