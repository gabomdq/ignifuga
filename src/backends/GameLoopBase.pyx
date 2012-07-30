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

cdef bint isdead(PyGreenlet* greenlet):
    ##define PyGreenlet_STARTED(op)    (((PyGreenlet*)(op))->stack_stop != NULL)
    ##define PyGreenlet_ACTIVE(op)     (((PyGreenlet*)(op))->stack_start != NULL)

    #if (PyGreenlet_ACTIVE(self) || !PyGreenlet_STARTED(self)):
    if greenlet.stack_start != NULL or greenlet.stack_stop == NULL:
        return False

    return True


cdef class GameLoopBase(object):
    def __init__(self, fps = 30.0):
        # SDL should be initialized at this point when Renderer was instantiated
        self.quit = False
        self.fps = fps
        self.frame_time = 0
        self.freezeRenderer = True

        self.loading = new deque[_Task]()
        self.loading_tmp = new deque[_Task]()
        self.running = new deque[_Task]()
        self.running_tmp = new deque[_Task]()

        PyGreenlet_Import()
        self.main_greenlet = PyGreenlet_GetCurrent()
        Py_XINCREF(<PyObject*>self.main_greenlet)

    def __dealloc__(self):
        debug("Releasing Game Loop data")

        cdef _Task *task
        cdef task_iterator iter


        Py_XDECREF(<PyObject*>self.main_greenlet)

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

        del self.loading
        del self.loading_tmp
        del self.running
        del self.running_tmp

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
        cdef PyObject *obj = <PyObject*> entity


        new_task.release = False
        new_task.req = REQUEST_NONE
        new_task.entity = obj
        # Note: Got to do this assignment with an intermediary object, otherwise Cython just can't take it!
        if load_phase:
            runnable = entity.init
        else:
            runnable = entity.update

        new_task.runnable = <PyObject*>runnable
        new_task.data = NULL
        Py_XINCREF(new_task.entity)
        Py_XINCREF(new_task.runnable)
        new_task.greenlet = PyGreenlet_New(new_task.runnable, self.main_greenlet )
        Py_XINCREF(<PyObject*>new_task.greenlet)

        # We don't directly add new tasks to self.loading or self.running to avoid invalidating iterators or pointers in self.update
        # Instead, we add them to a temporary list which will be processed in self.update.
        if load_phase:
            self.loading_tmp.push_back(new_task)
        else:
            self.running_tmp.push_back(new_task)

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
        Py_XDECREF(<PyObject*>taskp.greenlet)
        Py_XDECREF(taskp.runnable)
        Py_XDECREF(taskp.entity)

    cpdef update(self, int now=0, bint wrapup=False):
        """ Update everything, then render the scene
        now is the current time, specified in milliseconds
        wrapup = True forces the update loop to be broken, all running entities eventually stop running
        """
        cdef _Task *taskp
        cdef deque[_Task].iterator iter, iter_end
        cdef PyObject *entity

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
            if taskp.release or not self._processTask(taskp, now, wrapup, True):
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
            if taskp.release or not self._processTask(taskp, now, wrapup, False):
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
            return False

        ret = None
        if retp != NULL:
            Py_XINCREF(retp)
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

        return False


    cdef bint _processTask(self, _Task *task, int now=0, bint wrapup=False, bint init=False):
        cdef PyObject *args, *kwargs
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

        cdef PyObject *retp
        if task.req == REQUEST_NONE:
            if self._doSwitch(task, args, kwargs):
                if init and task.req == REQUEST_ERROR:
                    # There was a problem with initialization, let's try again from scratch
                    Py_XDECREF(<PyObject*>task.greenlet)
                    task.req = REQUEST_NONE
                    task.greenlet = PyGreenlet_New(task.runnable, self.main_greenlet)
                    Py_XINCREF(<PyObject*>task.greenlet)
                    return True
            else:
                return False

        if task.req == REQUEST_DONE:
            if init:
                # Entity is ready, start the update loop for it
                return False
            else:
                if wrapup:
                    return False
                else:
                    # Restart the update loop
                    Py_XDECREF(<PyObject*>task.greenlet)
                    task.greenlet = PyGreenlet_New(task.runnable, self.main_greenlet)
                    Py_XINCREF(<PyObject*>task.greenlet)
                    return self._doSwitch(task, args, kwargs)
        elif task.req == REQUEST_SKIP:
            # Normal operation continues
            task.req = REQUEST_NONE
            return True
        elif task.req == REQUEST_STOP:
            # Stop entity from updating
            task.release = True
            return False
        elif task.req == REQUEST_LOADIMAGE:
            # Load an image
            data = <object>task.data
            if isinstance(data, dict) and data.has_key('url') and data['url'] != None:
                # Try to load an image
                img = (Gilbert().dataManager.getImage(data['url']),)
                if img is not None:
                    return self._doSwitch(task, <PyObject*>img, NULL)
                return True
            else:
                # URL is invalid, just keep going
                task.req = REQUEST_NONE
                return True
        else:
            # Unrecognized request
            return self._doSwitch(task, args, kwargs)

    cpdef addWatch(self, filename):
        raise Exception('not implemented')

    cpdef removeWatch(self, filename):
        raise Exception('not implemented')