#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


# Ignifuga Game Engine
# Game Loop
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

# xcython: profile=True
from cython.operator cimport dereference as deref, preincrement as inc #dereference and increment operators
from ignifuga.Gilbert import Gilbert
from ignifuga.Log import debug, error


# Python enum exports
EVENT_TYPE_TOUCH_DOWN = EVENT_TOUCH_DOWN
EVENT_TYPE_TOUCH_UP = EVENT_TOUCH_UP
EVENT_TYPE_TOUCH_MOTION = EVENT_TOUCH_MOTION
EVENT_TYPE_TOUCH_LAST = EVENT_TOUCH_LAST
EVENT_TYPE_ETHEREAL_ZOOM_IN = EVENT_ETHEREAL_ZOOM_IN
EVENT_TYPE_ETHEREAL_ZOOM_OUT = EVENT_ETHEREAL_ZOOM_OUT
EVENT_TYPE_ETHEREAL_SCROLL = EVENT_ETHEREAL_SCROLL

TASK_REQUEST_NONE = REQUEST_NONE
TASK_REQUEST_DONE = REQUEST_DONE
TASK_REQUEST_SKIP = REQUEST_SKIP
TASK_REQUEST_STOP = REQUEST_STOP
TASK_REQUEST_LOADIMAGE = REQUEST_LOADIMAGE
TASK_REQUEST_ERROR = REQUEST_ERROR


cdef bint isdead(PyGreenlet* greenlet):
    ##define PyGreenlet_STARTED(op)    (((PyGreenlet*)(op))->stack_stop != NULL)
    ##define PyGreenlet_ACTIVE(op)     (((PyGreenlet*)(op))->stack_start != NULL)

    ##if (PyGreenlet_ACTIVE(self) || !PyGreenlet_STARTED(self)):
    ##if greenlet.stack_start != NULL or greenlet.stack_stop == NULL:
        #return False

    if PyGreenlet_ACTIVE(greenlet) or not PyGreenlet_STARTED(greenlet):
        return False

    return True


cdef class GameLoopBase(object):
    def __init__(self, fps = 30.0):
        # SDL should be initialized at this point when Renderer was instantiated
        self.quit = False
        self.fps = fps
        self.frame_time = 0
        self.freezeRenderer = True
        self.released = False

        self.loading = new deque[_Task]()
        self.loading_tmp = new deque[_Task]()
        self.running = new deque[_Task]()
        self.running_tmp = new deque[_Task]()

        PyGreenlet_Import()
        self.main_greenlet = PyGreenlet_GetCurrent()

    def __dealloc__(self):
        self.free()

    cpdef free(self):
        cdef _Task *task
        cdef task_iterator iter

        if not self.released:
            debug("Releasing Game Loop data")
            # Release sprites in use
            iter = self.loading.begin()
            while iter != self.loading.end():
                task = &deref(iter)
                self.taskDecRef(task)
                inc(iter)

            iter = self.loading_tmp.begin()
            while iter != self.loading_tmp.end():
                task = &deref(iter)
                self.taskDecRef(task)
                inc(iter)

            iter = self.running.begin()
            while iter != self.running.end():
                task = &deref(iter)
                self.taskDecRef(task)
                inc(iter)

            iter = self.running_tmp.begin()
            while iter != self.running_tmp.end():
                task = &deref(iter)
                self.taskDecRef(task)
                inc(iter)

            Py_CLEAR(self.main_greenlet)

            del self.loading
            del self.loading_tmp
            del self.running
            del self.running_tmp

            self.released = True

    def run(self):
        raise Exception('not implemented')

    property fps:
        def __get__(self):
            return self._fps
        def __set__(self, fps):
            self._fps = float(fps)
            self._interval = 1000 / fps

    cpdef startEntity(self, entity, bint load_phase=True):
        """ Put an entity in the loading or running queue"""
        cdef _Task new_task, *taskp

        new_task.release = False
        new_task.req = REQUEST_NONE
        new_task.entity = <PyObject*> entity
        Py_XINCREF(new_task.entity)

        # Note: Got to do this assignment with an intermediary object, otherwise Cython just can't take it!
        runnable = None
        if load_phase:
            runnable = entity.init
        else:
            runnable = entity.update

        new_task.runnable = <PyObject*>runnable
        new_task.data = NULL
        Py_XINCREF(new_task.runnable)
        new_task.greenlet = PyGreenlet_New(new_task.runnable, self.main_greenlet )

        # We don't directly add new tasks to self.loading or self.running to avoid invalidating iterators or pointers in self.update
        # Instead, we add them to a temporary list which will be processed in self.update.
        if load_phase:
            self.loading_tmp.push_back(new_task)
        else:
            self.running_tmp.push_back(new_task)

        del runnable

    cpdef startComponent(self, component):
        """ Components hit the ground running, their initialization was handled by their entity"""
        self.startEntity(component, False)

    cpdef bint stopEntity(self, entity):
        cdef _Task *taskp
        cdef task_iterator iter
        cdef PyObject *obj = <PyObject*> entity
        cdef bint eraseEntity = True

        # Release tasks in use
        iter = self.loading.begin()
        while iter != self.loading.end():
            taskp = &deref(iter)
            if taskp.entity == obj:
                taskp.release = True

            inc(iter)

        iter = self.running.begin()
        while iter != self.running.end():
            taskp = &deref(iter)
            if taskp.entity == obj:
                taskp.release = True

            inc(iter)

    cpdef bint stopComponent(self, component):
        return self.stopEntity(component)


    cdef taskDecRef (self, _Task* taskp):
        Py_XDECREF(taskp.data)
        Py_XDECREF(taskp.entity)
        Py_XDECREF(taskp.greenlet)
        Py_XDECREF(taskp.runnable)


    cpdef update(self, int now=0, bint wrapup=False):
        """ Update everything, then render the scene
        now is the current time, specified in milliseconds
        wrapup = True forces the update loop to be broken, all running entities eventually stop running
        """
        cdef _Task *taskp
        cdef deque[_Task].iterator iter, iter_end
        cdef PyObject *entity
        cdef bint task_ret

        # Add loading and running tasks from the temporary queues
        while self.loading_tmp.size() > 0:
            self.loading.push_back(self.loading_tmp.back())
            self.loading_tmp.pop_back()

        while self.running_tmp.size() > 0:
            self.running.push_back(self.running_tmp.back())
            self.running_tmp.pop_back()

        # Initialize objects
        iter = self.loading.begin()
        iter_end = self.loading.end()

        while iter != iter_end:
            taskp = &deref(iter)
            task_ret = self._processTask(taskp, now, wrapup, True)

            if isdead(taskp.greenlet):
                # Remove the task from the loading deque, start it in the running deque

                # Release the reference we held to data
                obj = <object>taskp.entity
                self.taskDecRef(taskp)
                iter = self.loading.erase(iter)
                iter_end = self.loading.end()
                if wrapup:
                    self.stopEntity(obj)
                else:
                    self.startEntity(obj, False)
            else:
                # Someone may have deleted a loading task in the middle of this!
                if iter == self.loading.end():
                    break
                inc(iter)

        if self.freezeRenderer and self.loading.empty() and self.loading_tmp.empty():
            self.freezeRenderer = False

        # Update objects
        iter = self.running.begin()
        iter_end = self.running.end()
        while iter != iter_end:
            taskp = &deref(iter)
            task_ret = self._processTask(taskp, now, wrapup, False)

            if isdead(taskp.greenlet):
                # Remove the task from the indexes
                # Release the reference we held to data
                self.taskDecRef(taskp)
                iter = self.running.erase(iter)
                iter_end = self.running.end()
            else:
                # Someone may have deleted a running task in the middle of this!
                if iter == self.running.end():
                    break
                inc(iter)

    cdef bint _doSwitch(self, _Task *task, PyObject *args, PyObject *kwargs):
        cdef PyObject *retp = NULL

        # Switch to the greenlet
        retp = PyGreenlet_Switch(task.greenlet, args, kwargs)
        if task.release:
            # The task was marked for release at some point during the switch, don't use it further
            Py_XDECREF(retp)
            return False

        ret = None
        if retp != NULL:
            ret = <object>retp

        if isdead(task.greenlet) or ret is None:
            # The greenlet is dead, assume it was done
            task.req = REQUEST_DONE
            Py_XDECREF(task.data)
            task.data = NULL
            Py_XDECREF(retp)
            return True

        if retp != NULL:
            task.req = <REQUESTS> ret[0]
            Py_XDECREF(task.data)
            task.data = <PyObject*> ret[1]
            Py_XINCREF(task.data)
            Py_XDECREF(retp)
            return True

        Py_XDECREF(retp)
        return False


    cdef bint _processTask(self, _Task *task, int now=0, bint wrapup=False, bint init=False):
        cdef PyObject *args, *kwargs


        # Prepare some standard arguments
        if init:
            # Init functions have the format self.init(**data), so we pass now in the kwargs
            kw_data = {'now':now}
            kwargs = <PyObject*> kw_data
            args = NULL
        else:
            # Update functions have the format self.update(now, **data), so we pass now as a arg
            kw_data = {}
            kwargs = <PyObject*>kw_data
            data = (now,)
            args = <PyObject*>data


        # This is for tasks on their way out! They've been marked for release but we have to keep them looping until they die
        if task.release and not isdead(task.greenlet):
            return self._doSwitch(task, args, kwargs)

        # Prepare data
        cdef PyObject *retp
        if task.req == REQUEST_SKIP:
            # Do not switch to the task in this round
            task.req = REQUEST_NONE
            return True
        elif task.req == REQUEST_LOADIMAGE:
            # Load an image
            data = <object>task.data
            if isinstance(data, dict) and data.has_key('url') and data['url'] != None:
                # Try to load an image
                img = (Gilbert().dataManager.getImage(data['url']),)
                if img is not None:
                    args = <PyObject*>img
                    kwargs = NULL
            else:
                # URL is invalid, just keep going
                task.req = REQUEST_NONE

        # Do the actual switching passing the data to the greenlet
        if self._doSwitch(task, args, kwargs):
            # Process some return values stored in task.req
            if task.req == REQUEST_ERROR:
                if init:
                    # There was a problem with initialization, let's try again from scratch
                    Py_CLEAR(task.greenlet)
                    task.req = REQUEST_NONE
                    task.greenlet = PyGreenlet_New(task.runnable, self.main_greenlet)
                    return True
            elif task.req == REQUEST_DONE:
                if not init and not wrapup:
                    # Restart the update loop
                    task.req = REQUEST_NONE
                    Py_CLEAR(task.greenlet)
                    task.greenlet = PyGreenlet_New(task.runnable, self.main_greenlet)
                    return True
            elif task.req == REQUEST_STOP:
                # Stop entity from updating
                task.release = True
                task.req = REQUEST_NONE
        else:
            return False


    cpdef addWatch(self, filename):
        raise Exception('not implemented')

    cpdef removeWatch(self, filename):
        raise Exception('not implemented')

#    cpdef checkStatus(self):
#        cdef _Task *task
#        cdef task_iterator iter
#
#        iter = self.loading.begin()
#        while iter != self.loading.end():
#            task = &deref(iter)
#            print "LOADING TASK RUNNABLE", <object> task.runnable
#            inc(iter)
#
#        iter = self.loading_tmp.begin()
#        while iter != self.loading_tmp.end():
#            task = &deref(iter)
#            print "LOADING TMP TASK RUNNABLE", <object> task.runnable
#            inc(iter)
#
#        iter = self.running.begin()
#        while iter != self.running.end():
#            task = &deref(iter)
#            print "RUNNING TASK RUNNABLE", <object> task.runnable
#            inc(iter)
#
#        iter = self.running_tmp.begin()
#        while iter != self.running_tmp.end():
#            task = &deref(iter)
#            print "RUNNING TMP TASK RUNNABLE", <object> task.runnable
#            inc(iter)
