#Copyright (c) 2010,2011, Gabriel Jacobo
#All rights reserved.

#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions are met:

    #* Redistributions of source code must retain the above copyright
      #notice, this list of conditions and the following disclaimer.
    #* Redistributions in binary form must reproduce the above copyright
      #notice, this list of conditions and the following disclaimer in the
      #documentation and/or other materials provided with the distribution.
    #* Altered source versions must be plainly marked as such, and must not be
      #misrepresented as being the original software.
    #* Neither the name of Gabriel Jacobo, MDQ Incorporeo, Ignifuga Game Engine
      #nor the names of its contributors may be used to endorse or promote
      #products derived from this software without specific prior written permission.
    #* You must NOT, under ANY CIRCUMSTANCES, remove, modify or alter in any way
      #the duration, code functionality and graphic or audio material related to
      #the "splash screen", which should always be the first screen shown by the
      #derived work and which should ALWAYS state the Ignifuga Game Engine name,
      #original author's URL and company logo.

#THIS LICENSE AGREEMENT WILL AUTOMATICALLY TERMINATE UPON A MATERIAL BREACH OF ITS
#TERMS AND CONDITIONS

#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL GABRIEL JACOBO NOR MDQ INCORPOREO NOR THE CONTRIBUTORS
#BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# Ignifuga Game Engine
# Base Action class
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import pickle
from copy import deepcopy
from Component import Component

class Action(Component):
    """
    Action component
    This component behaves a bit different from other components as it chains itself. Only the main action is "active" in the entity.
    The rest of the chain is inactive and only gets updates via the chain.

    TODO: Separate the Component part from the actual chain of actions... Entitiy->Action Component->Actions (like Sprite does)

    duration: The duration of the action
    relative: If true, the final value is that of target+initial value, if false, the final value is the target value
    increase: A function that affects the function. Possible values: 'linear', 'square'
    """
    def __init__(self, id=None, entity=None, active=True, frequency=15.0, duration=0.0, relative=False, increase='linear', stopCallback=None, loop=1, persistent=False, root=True, runWith=None, runNext=None, **data):
    #def __init__(self, id=None, duration=0.0, relative=False, increase='linear', stopCallback=None, loop=1, persistent=False, *args, **kwargs):

        self._tasks = data
        self._runWith = []     # Action/s to be run in parallel to this one
        self._runNext = None    # Action to be run after this one
        self._loopMax = loop if loop >= 0 else None
        self._duration = float(duration)
        self._loop = 0
        self._relative = relative
        self._increase = increase.lower()
        self._stopCallback = stopCallback
        self._persistent = persistent
        self._running = False
        self._root = root
        self.reset()
        super(Action, self).__init__(id, entity, active, frequency, **data)

        # Process runWith and runNext
        if runWith != None:
            for rw in runWith:
                self._runWith.append(Action(root=False, entity=entity, **rw))

        if runNext != None:
            self._runNext = Action(root=False, entity=entity, **runNext)

    @Component.active.setter
    def active(self, active):
        if active == self._active or self._entity == None:
            return
        if active:
            self.start()
        else:
            self.stop()

        Component.active.fset(self, active)

    @Component.entity.setter
    def entity(self, entity):
        """ Actions do not add themselves to the entity unless they are a root action, the rest takes updates via the chain of actions"""
        if self._entity == entity:
            return

        if not self._running:
            if self._root:
                Component.entity.fset(self, entity)
            else:
                self._entity = entity

            self.reset()
            for a in self._runWith:
                a.entity = entity
            if self._runNext != None:
                self._runNext.entity = entity
        else:
            raise Exception('Tried to assign a running action to a entity')

    @property
    def persistent(self):
        return self._persistent

    @property
    def root(self):
        return self._root

    @root.setter
    def root(self, root):
        if self._root == root:
            return
        self._root = root
        if self._entity != None:
            if self._root:
                self._entity.add(self)
            else:
                self._entity.remove(self)

    def start(self, stopCallback=None):
        """ Fire up the action chain """
        if stopCallback != None:
            self._stopCallback = stopCallback
        if not self._running and not self._done and self._entity != None:
            if self._entity != None:
                self._tasksStatus = {}
                for task in self._tasks:
                    self._tasksStatus[task] = {
                        'targetValue': self._tasks[task],
                        'initValue': getattr(self._entity, task)
                    }

            self._running = True
            for a in self._runWith:
                a.start()
    
    def reset(self):
        """ Reset the internal status """
        self._startTime = None  # Indicates when the action started
        self._running = False   # Indicates if the action chain is running
        self._done = False      # Indicates if the current action is finished
        self._dt = 0            # Indicates total elapsed time since start

    def stop(self):
        """ Stop the action chain """
        if self._running:
            for a in self._runWith:
                a.stop()
            if self._runNext !=  None:
                self._runNext.stop()
            self.reset()

            # The associated entity doesnt need to get a callback, it polls the action status on each update
            if self._stopCallback != None:
                self._stopCallback(self)

    def update(self, now=0):
        """ Update the action, dt is float specifying elapsed seconds """
        if self._running:
            if not self._done:
                if self._startTime != None:
                    dt = now - self._startTime
                    if dt > 0:
                        self._dt = dt
                        self._step(dt)
                else:
                    if self._dt == 0:
                        # Initialize the start time, the action will run from the next update call
                        self._startTime = now
                    else:
                        # _dt is not zero but _startTime is, so the action was frozen, restore the start time to a proper value
                        self._startTime = now - self._dt

            # Pass the torch to our parallel action
            for a in self._runWith:
                a.update(now)
                
            # If we are finished and our parallel action is finished too, pass the torch to the next action
            parallelActionsFinished = True
            for a in self._runWith:
                if a.isRunning:
                    parallelActionsFinished = False
                    break

            if self._done and parallelActionsFinished:
                if self._runNext != None:
                    if not self._runNext.isRunning:
                        # Start the next action
                        self._runNext.start()
                    else:
                        # Update the next action
                        self._runNext.update(now)
                        
                    # After updating the next action, we check again
                    # If the action that comes next has stopped, stop everything as we reached the end of the line
                    if not self._runNext.isRunning:
                        self.stop()
                else:
                    # No action follows ourselves, and we are done, so we stop here.
                    self.stop()

            # Check if we need to loop the action
            if not self._running:
                # Check if we need to loop the action
                self._loop+=1
                if self._loopMax == None or self._loop < self._loopMax:
                    self.reset()
                    if self._relative:
                        self.start()
                    else:
                        # Don't reload initial values!
                        self._running = True
                else:
                    self._loop = 0
                    # The associated entity doesnt need to get a callback, it polls the action status on each update
                    if self._stopCallback != None:
                        self._stopCallback(self)
                    self.reset()

            
    def _step(self, dt):
        """ Increase parameters by delta time (in seconds, elapsed since the start of the action) """
        if dt < self._duration:
            step = self._modifyStep(dt/self._duration)
            for task in self._tasksStatus:
                init = self._tasksStatus[task]['initValue']
                target = self._tasksStatus[task]['targetValue']
                if self._relative:
                    setattr(self._entity, task, init + (target*step))
                else:
                    setattr(self._entity, task, init+(target-init)*step)
        else:
            # The action should stop, set everything at their final value
            for task in self._tasksStatus:
                init = self._tasksStatus[task]['initValue']
                target = self._tasksStatus[task]['targetValue']
                if self._relative:
                    setattr(self._entity, task, init+target)
                else:
                    setattr(self._entity, task, target)
                    
            self._done = True
            
    def _modifyStep(self, step):
        """ Apply a modification to the stepping value according to the increase type
            step values: 0 >= step >= 1
        """
        if self._increase == 'square':
            return step*step
        
        # Default to linear stepping
        return step

    @property    
    def isRunning(self):
        """ Returns true if the action chain is currently running"""
        return self._running

    @property
    def isDone(self):
        """ Returns true if the current action (not the chain) is finished"""
        return self._done

    @property
    def forever(self):
        """ Loop action forever """
        self._loopMax = None
    
    def __add__(self, action):
        """ Add an enclosing dummy action in line that harbors the two added actions, returns a new Action"""
        new_action = Action(id = self.id, entity=self._entity, persistent=self.persistent)
        self.root = False
        action.root = False
        a = new_action._runNext = deepcopy(self)

        while True:
            # Find a spot in the chain where to attach the new member of the chain
            if a._runNext == None:
                a._runNext = deepcopy(action)
                break
            a = a._runNext
        print new_action
        return new_action

    def __or__(self, action):
        """ Add an enclosing dummy action in parallel that harbors the two or'ed actions, returns a new Action"""
        new_action = Action(id = self.id, entity=self._entity, persistent=self.persistent)
        self.root = False
        action.root = False
        new_action._runWith.append(deepcopy(self))
        new_action._runWith.append(deepcopy(action))
        print new_action
        return new_action

    def __mul__(self, other):
        """ Loop current action several times. If other=0, run the action in loop forever """
        try:
            other = int(other)
        except:
            return
        
        if self._loopMax == None:
            self._loopMax = 1

        if other > 0:
            self._loopMax *= other
        else:
            self._loopMax = None

        return self

    def __getstate__(self):
        odict = self.__dict__.copy()
        # Remove non pickable elements
        return odict

    def __setstate__(self, data):
        """ Restore action from data """
        self.__dict__.update(data)
        self.unfreeze()

    def unfreeze(self):
        # Fix timing by invalidating _startTime, it will be regenerated to a proper value on the next update call
        self._startTime = None
        for a in self._runWith:
            a.unfreeze()
        if self._runNext != None:
            self._runNext.unfreeze()

    def __repr__(self):
        retval = ''
        retval += "|Action with ID: %s -> %s Target: %s Duration: %s Loop: %s Root: %s\n" % (self.id, self._tasks, self._entity.id if self._entity != None else '',self._duration, self._loopMax, self._root)
        if len(self._runWith) > 0:
            retval += "|Runs With:\n"
            for a in self._runWith:
                retval += '* ' + str(a)
            retval += "\n"
        
        if self._runNext != None:
            for l in str(self._runNext).split('\n'):
                retval += '---->' + l + '\n'
            

        return retval
            