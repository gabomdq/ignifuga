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

        self.loading = new deque[_Task_p]()
        self.running = new deque[_Task_p]()
        self.entities = new map[PyObject_p, _EntityTasks]()
        self.free_tasks = new deque[_Task_p]()

        PyGreenlet_Import()

    def __dealloc__(self):
        print "Releasing Game Loop data"

        cdef _Task *task
        cdef entities_iterator iter
        cdef _EntityTasks *et

        # Release unused sprites
        while not self.free_tasks.empty():
            task = self.free_tasks.back()
            free(task)
            self.free_tasks.pop_back()

        # Release sprites in use
        iter = self.entities.begin()
        while iter != self.entities.end():
            et = &deref(iter).second
            if et.loading != NULL:
                Py_XDECREF(et.loading.data)
                Py_XDECREF(<PyObject*>et.loading.greenlet)
                Py_XDECREF(et.loading.runnable)
                Py_XDECREF(et.loading.entity)
                free(et.loading)
            if et.running != NULL:
                Py_XDECREF(et.running.data)
                Py_XDECREF(<PyObject*>et.running.greenlet)
                Py_XDECREF(et.running.runnable)
                Py_XDECREF(et.running.entity)
                free(et.running)

        del self.free_tasks
        del self.loading
        del self.running
        del self.entities


    cdef bint _allocTasks(self, int num=100):
        cdef size_t nbytes = sizeof(_Task)*num
        cdef _Task *tasks = <_Task*>malloc(nbytes)
        cdef int i

        if tasks != NULL:
            memset(<void *>tasks, 0, nbytes)
            for i in range(0,num):
                self.free_tasks.push_back(&tasks[i])

            return True

        return False

    def run(self):
        raise Exception('not implemented')

    property fps:
        def __get__(self):
            return self._fps
        def __set__(self, fps):
            self._fps = float(fps)
            self._interval = 1000.0 / fps

    cpdef startEntity(self, entity):
        cdef _Task *task
        cdef entities_iterator iter
        cdef PyObject *obj = <PyObject*> entity
        cdef _EntityTasks *et = NULL, newtask

        if self.free_tasks.empty():
            self._allocTasks()

        if not self.free_tasks.empty():
            task = self.free_tasks.back()
            self.free_tasks.pop_back()
            task.req = REQUEST_NONE
            task.entity = obj
            Py_XINCREF(task.entity)
            # Note: Got to do this assignment with an intermediary object, otherwise Cython just can't take it!
            runnable = entity.init
            task.runnable = <PyObject*>runnable
            Py_XINCREF(task.runnable)
            task.greenlet = PyGreenlet_New(task.runnable, NULL )
            Py_XINCREF(<PyObject*>task.greenlet)
            task.data = NULL
            self.loading.push_back(task)

            iter = self.entities.find(obj)
            if iter == self.entities.end():
                self.entities.insert(pair[PyObject_p,_EntityTasks](obj,newtask))
                iter = self.entities.find(obj)

            et = &(deref(iter).second)
            et.loading = task
            et.running = NULL

    cpdef startComponent(self, component):
        """ Components hit the ground running, their initialization was handled by their entity"""
        cdef _Task *task
        cdef entities_iterator iter
        cdef PyObject *obj = <PyObject*> component
        cdef _EntityTasks *et = NULL, newtask

        if self.free_tasks.empty():
            self._allocTasks()

        if not self.free_tasks.empty():
            task = self.free_tasks.back()
            self.free_tasks.pop_back()
            task.req = REQUEST_NONE
            task.entity = obj
            Py_XINCREF(task.entity)
            # Note: Got to do this assignment with an intermediary object, otherwise Cython just can't take it!
            runnable = component.update
            task.runnable = <PyObject*>runnable
            Py_XINCREF(task.runnable)
            task.greenlet = PyGreenlet_New(task.runnable, NULL )
            Py_XINCREF(<PyObject*>task.greenlet)
            task.data = NULL
            self.running.push_back(task)

            iter = self.entities.find(obj)
            if iter == self.entities.end():
                self.entities.insert(pair[PyObject_p,_EntityTasks](obj,newtask))
                iter = self.entities.find(obj)

            et = &(deref(iter).second)
            et.loading = NULL
            et.running = task

    cpdef bint stopEntity(self, entity):
        cdef _Task *task
        cdef entities_iterator iter
        cdef task_iterator titer
        cdef _EntityTasks *et
        cdef PyObject *obj = <PyObject*> entity
        cdef bint eraseEntity = True

        # Release tasks in use
        iter = self.entities.find(obj)
        if iter != self.entities.end():
            et = &deref(iter).second
            # The tasks may be in use, if that's the case we mark them for release and wait for the update loop to release them and call us back
            if et.loading != NULL:
                et.loading.release = True
                eraseEntity = False
            if et.running != NULL:
                et.running.release = True
                eraseEntity = False

            if eraseEntity:
                self.entities.erase(iter)
            return True

        return False

    cpdef bint stopComponent(self, component):
        return self.stopEntity(component)


    cpdef update(self, int now=0, bint wrapup=False):
        """ Update everything, then render the scene
        now is the current time, specified in milliseconds
        wrapup = True forces the update loop to be broken, all running entities eventually stop running
        """
        #cdef deque[_Task_p] remove_entities = new deque[_Task_p]()
        cdef _Task *task, *task_aux
        cdef _EntityTasks *et
        cdef entities_iterator eiter
        cdef task_iterator iter
        cdef PyObject *entity

        # Initialize objects
        iter = self.loading.begin()
        while iter != self.loading.end():
            task = deref(iter)

            if task.release or not self._processTask(task, now, wrapup, True):
                # Remove the task from the loading deque, start it in the running deque
                iter = self.loading.erase(iter)

                # No need to double check here, task.entity was added in self.entities when startEntity was called
                eiter = self.entities.find(task.entity)
                et = &(deref(eiter).second)
                et.loading = NULL
                if et.running == NULL and et.loading == NULL:
                    obj = <object>task.entity
                    self.stopEntity(obj)

                # Release the reference we held to data
                entity = task.entity
                Py_XDECREF(task.data)
                Py_XDECREF(<PyObject*>task.greenlet)
                Py_XDECREF(task.runnable)
                Py_XDECREF(task.entity)
                task.data = NULL
                task.greenlet = NULL
                task.runnable = NULL
                task.entity = NULL
                task.release = False

                if wrapup:
                    self.free_tasks.push_back(task)
                else:
                    # Reuse the task pointer for the first running task of the entity
                    task.entity = entity
                    Py_XINCREF(task.entity)
                    # Note: Got to do this assignment with an intermediary object, otherwise Cython just can't take it!
                    tentity = <object>task.entity
                    runnable = tentity.update
                    task.runnable = <PyObject*>runnable
                    Py_XINCREF(task.runnable)
                    task.greenlet = PyGreenlet_New(task.runnable, NULL)
                    Py_XINCREF(<PyObject*>task.greenlet)
                    task.req = REQUEST_NONE
                    task.data = NULL
                    self.running.push_back(task)
                    et.running = task

                    if self.free_tasks.empty():
                        self._allocTasks()
            else:
                # Someone may have deleted a loading task in the middle of this!
                if iter == self.loading.end():
                    break
                inc(iter)

        if self.loading.empty() and self.freezeRenderer:
            self.freezeRenderer = False

        # Update objects
        iter = self.running.begin()
        while iter != self.running.end():
            task = deref(iter)
            if task.release or not self._processTask(task, now, wrapup, False):
                # Remove the task from the indexes

                # No need to double check here, task.entity was added in self.entities when startEntity was called
                eiter = self.entities.find(task.entity)
                et = &(deref(eiter).second)
                et.running = NULL
                if et.running == NULL and et.loading == NULL:
                    obj = <object>task.entity
                    self.stopEntity(obj)

                # Release the reference we held to data
                Py_XDECREF(task.data)
                Py_XDECREF(<PyObject*>task.greenlet)
                Py_XDECREF(task.runnable)
                Py_XDECREF(task.entity)
                task.data = NULL
                task.greenlet = NULL
                task.runnable = NULL
                task.entity = NULL

                iter = self.running.erase(iter)
                task.release = False
                self.free_tasks.push_back(task)
            else:
                # Someone may have deleted a loading task in the middle of this!
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
        if isdead(task.greenlet):
            # The greenlet is dead, assume it was done
            task.req = REQUEST_DONE
            Py_XDECREF(task.data)
            task.data = NULL
            return True

        if retp != NULL:
            Py_XINCREF(retp)
            ret = <object>retp
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
                    # There was a problem with initialization, let's try again
                    Py_XDECREF(<PyObject*>task.greenlet)
                    task.req = REQUEST_NONE
                    task.greenlet = PyGreenlet_New(task.runnable, NULL)
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
                    task.greenlet = PyGreenlet_New(task.runnable, NULL)
                    Py_XINCREF(<PyObject*>task.greenlet)
                    return self._doSwitch(task, args, kwargs)
        elif task.req == REQUEST_SKIP:
            # Normal operation continues
            task.req = REQUEST_NONE
            return True
        elif task.req == REQUEST_STOP:
            # Stop entity from updating
            return False
        elif task.req == REQUEST_LOADIMAGE:
            # Load an image
            data = <object>task.data
            if data.has_key('url') and data['url'] != None:
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


