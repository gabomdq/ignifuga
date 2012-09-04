#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Ignifuga Game Engine
# Base Action class
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import pickle, math
from copy import deepcopy
from Component import Component
from ignifuga.Gilbert import Gilbert
from ignifuga.Task import STOP


# Tweening functions, based on several sources but most seem to cite Robert Penner's equations (http://www.robertpenner.com/easing/)
# A nice graph of these functions: http://jqueryui.com/demos/effect/easing.html
# IN_XXX functions are straight up transitions
# OUT_XXX functions are inverted amplitude wise, so if an IN_XXX function goes from 0 to 1, the equivalent OUT_XXX will go from 1 to 0
# TODO: Add the INOUT AND OUTIN combinations

def EASING_LINEAR(init, dest, step, relative):
    if relative:
        return init + (dest*step)
    else:
        return init+(dest-init)*step

# Exponential functions
def EASING_INEXPO(init, dest, step, relative):
    step = 2**(10 * (step-1.0))
    return EASING_LINEAR(init, dest, step, relative)

def EASING_OUTEXPO(init, dest, step, relative):
    step = 1.001 * -((2**(-10 * step)) + 1)
    return EASING_LINEAR(init, dest, step, relative)

# Quadratic functions
def EASING_INQUAD(init, dest, step, relative):
    step *= step
    return EASING_LINEAR(init, dest, step, relative)

def EASING_OUTQUAD(init, dest, step, relative):
    step = -step*(step-2)
    return EASING_LINEAR(init, dest, step, relative)

# Cubic functions

def EASING_INCUBIC(init, dest, step, relative):
    step = step**3
    return EASING_LINEAR(init, dest, step, relative)

def EASING_OUTCUBIC(init, dest, step, relative):
    step = (step-1)**3+1
    return EASING_LINEAR(init, dest, step, relative)

# Quaternary functions
def EASING_INQUART(init, dest, step, relative):
    step = step**4
    return EASING_LINEAR(init, dest, step, relative)

def EASING_OUTQUART(init, dest, step, relative):
    step = (step-1)**4-1
    return EASING_LINEAR(init, dest, step, relative)

# Quinternary functions
def EASING_INQUINT(init, dest, step, relative):
    step = step**5
    return EASING_LINEAR(init, dest, step, relative)

def EASING_OUTQUINT(init, dest, step, relative):
    step = (step-1)**5+1
    return EASING_LINEAR(init, dest, step, relative)

# Elastic
def EASING_INELASTIC(init, dest, step, relative):
    if step == 0.0 or step == 1.0:
        return EASING_LINEAR(init, dest, step, relative)
    p=0.3
    s = p/4
    step -= 1
    step = -(2**(10*step)) * math.sin((step-s)*(2*math.pi)/p )
    return EASING_LINEAR(init, dest, step, relative)

def EASING_OUTELASTIC(init, dest, step, relative):
    if step == 0.0 or step == 1.0:
        return EASING_LINEAR(init, dest, step, relative)
    p=0.3
    s = p/4
    step = 1.0 + (2**(-10*step)) * math.sin((step-s)*(2*math.pi)/p )
    return EASING_LINEAR(init, dest, step, relative)

# Elastic
def EASING_INBACK(init, dest, step, relative):
    s = 1.70158;
    step = step * ((s+1) - s)
    return EASING_LINEAR(init, dest, step, relative)

def EASING_OUTBACK(init, dest, step, relative):
    s = 1.70158;
    step = ((step-1)*((s+1) + s) + 1)
    return EASING_LINEAR(init, dest, step, relative)

class Action(Component):
    """
    Action component
    This component behaves a bit different from other components as it chains itself. Only the main action is "active" in the entity.
    The rest of the chain is inactive and only gets updates via the chain.

    TODO: Would it be better to separate the Component part from the actual chain of actions... Entitiy->Action Component->Actions (like Sprite does)

    duration: The duration of the action
    relative: If true, the final value is that of target+initial value, if false, the final value is the target value
    increase: A function that affects the function. Possible values: 'linear', 'square'
    targets: The targets where the action will be applied. If not provided the action applies to its entity.
             If the action is owned by an entity, targets can be a list with None (to mark the owner entity), a Component instance or a component id
             If the action is owned by a scene, targets can be a list with None (to mark the owner scene), a component or entity instance, or an entity or component id (ie entity.component)
    """
    def __init__(self, id=None, entity=None, active=True, targets=None, frequency=15.0, duration=0.0, relative=False, easing='linear', onStart=None, onStop=None, onLoop=None, loop=1, persistent=False, root=True, runWith=None, runNext=None, **data):
        # Store some parameters for use in the actual initialization
        self._initParams = {
            'targets': targets,
        }

        self._tasks = deepcopy(data)
        self._targets = []
        self._runWith = []     # Action/s to be run in parallel to this one
        self._runNext = None    # Action to be run after this one
        self._loopMax = loop if loop >= 0 else None
        self._duration = float(duration*1000)
        self._loop = 0
        self._relative = relative
        self._easing = easing.lower()
        self._easingFunc = EASING_LINEAR
        ef = "EASING_" + easing.upper()
        if ef in globals():
            self._easingFunc = globals()[ef]

        self._onStop = onStop
        self._onStart = onStart
        self._onLoop = onLoop
        self._persistent = persistent
        self._running = False
        self._root = root
        self._cancelUpdate = False
        self._freePending = False

        # Process runWith and runNext
        if runWith != None:
            for rw in runWith:
                if 'targets' not in rw:
                    rw['targets'] = targets
                action = Action(root=False, entity=entity, active=False, **deepcopy(rw))
                self._runWith.append(action)

        if runNext != None:
            if 'targets' not in runNext:
                runNext['targets'] = targets
            self._runNext = Action(root=False, entity=entity, active=False, **deepcopy(runNext))

        self.reset()
        super(Action, self).__init__(id, entity, active, frequency, **data)


    def init(self, **kwargs):
        targets = self._initParams['targets']
        self._targets = [] # init needs to be reentrant because if we fail to initialize it will be called again!

        if targets is None:
            self._targets = [self.entity,]
        else:
            from ignifuga.Entity import Entity
            from ignifuga.Scene import Scene
            if isinstance(self.entity, Scene):
                # Targets can be other entities or components (by id or by object), None for the scene
                for target in targets:
                    if target is None:
                        self._targets.append(self.entity)
                    elif isinstance(target, Component) or isinstance(target, Entity):
                        self._targets.append(target)
                    elif isinstance(target, str) or isinstance(target, unicode):
                        target_parts = str(target).split('.')
                        target_entity = self.entity.getEntity(target_parts[0])
                        if target_entity != None:
                            if len(target_parts) == 2:
                                component = target_entity.getComponent(target_parts[1])
                                if component is not None:
                                    self._targets.append(component)
                                else:
                                    raise Exception('Action target entity %s does not have a component %s' % (target_parts[0], target_parts[1]))
                            else:
                                self._targets.append(target_entity)
                        else:
                            raise Exception('Action target %s (Entity %s) not found' % (target, target_parts[0]))
                    else:
                        raise Exception('Can not determine which type of target is %s' % target)
            elif isinstance(self.entity, Entity):
                # Targets can be other components owned by the entity (passed by id or by object) or the entity itself if target=None
                for target in targets:
                    if target is None:
                        self._targets.append(self.entity)
                    elif isinstance(target, Component) and target.entity == self.entity:
                        self._targets.append(target)
                    elif isinstance(target, str) or isinstance(target, unicode):
                        component = self.entity.getComponent(str(target))
                        if component is not None:
                            self._targets.append(component)
                        else:
                            raise Exception('Action target %s not found' % target)
                    else:
                        raise Exception('Action target %s not found' % target)

        # Process runWith and runNext
        for action in self._runWith:
            action.init(**deepcopy(kwargs))

        if self._runNext is not None:
            self._runNext.init(**deepcopy(kwargs))

        super(Action, self).init(**kwargs)

    @Component.active.setter
    def active(self, active):
        if self._root:
            if active == self._active or self._entity == None:
                self._active = active
                return
            try:
                self._active = active
                if active and not self._running:
                    self.start()
                elif not active and self._running:
                    self.stop()
                if self._active:
                    # Root action being activated, add component, tags and properties to entity
                    self.entity.add(self)
                else:
                    # Root action being deactivated, remove tags and properties from entity
                    self.entity.refreshTags()
                    self.entity.removeProperties(self)
            except Exception, ex:
                self._active = False
                raise ex

        elif self._active:
                self._active = False

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

    def start(self, onStart=None, onStop=None, onLoop=None):
        """ Fire up the action chain """
        if onStart != None:
            self._onStart = onStart
        if onStop != None:
            self._onStop = onStop
        if onLoop != None:
            self._onLoop = onLoop

        if not self._running and not self._done and self._entity != None:
            self._tasksStatus = {}
            for target in self._targets:
                self._tasksStatus[target] = {}
                for task in self._tasks:
                    if not hasattr(target, task):
                        raise Exception("Could not start action %s, %s does not have an attribute %s" % (self, target, task))
                    self._tasksStatus[target][task] = {
                        'targetValue': self._tasks[task],
                        'initValue': getattr(target, task)
                    }
            self._running = True
            for a in self._runWith:
                a.start()
            self.run(self._onStart)
            if self._root:
                Gilbert().gameLoop.startComponent(self)

    def reset(self):
        """ Reset the internal status """
        self._startTime = None  # Indicates when the action started
        self._running = False   # Indicates if the action chain is running
        self._done = False      # Indicates if the current action is finished
        self._dt = 0            # Indicates total elapsed time since start
        for action in self._runWith:
            action.reset()

        if self._runNext is not None:
            self._runNext.reset()

    def stop(self):
        """ Stop the action chain """
        if self._running:
            for a in self._runWith:
                a.stop()
            if self._runNext !=  None:
                self._runNext.stop()
            self.reset()

            # Signal the update loop to stop
            self._cancelUpdate = True

    def update(self, now, **kwargs):
        """ Update the action, now is a integer in milliseconds, dt is float specifying elapsed seconds """
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
                if a is not None:
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
                    # WARNING: self._runNext may have turned None here after running update!
                    if self._runNext and not self._runNext.isRunning:
                        self._running = False
                else:
                    # No action follows ourselves, and we are done, so we stop here.
                    self._running = False

            if not self._running:
                # Check if we need to loop the action
                self._loop+=1
                self.reset()
                if self._loopMax == None or self._loop < self._loopMax:
                    if self._relative:
                        self.start()
                    else:
                        # Don't reload initial values!
                        self._running = True
                    self.run(self._onLoop)
                else:
                    self._loop = 0
                    # Stop the update loop
                    self._cancelUpdate = True

        # Handle exiting of the action (via stop() or by the natural course of the action)
        if self._cancelUpdate:
            self.run(self._onStop)
            self._cancelUpdate = False
            self._running = False
            # The root action needs to start the freeing chaing and signal that we don't want to be updated anymore
            if self._root:
                if self._freePending:
                    self.free()
                self.active=False
                return STOP()

    def _step(self, dt):
        """ Increase parameters by delta time (in seconds, elapsed since the start of the action) """
        if dt < self._duration:
            step = dt/self._duration
            for target in self._tasksStatus:
                for task in self._tasksStatus[target]:
                    init = self._tasksStatus[target][task]['initValue']
                    dest = self._tasksStatus[target][task]['targetValue']
                    setattr(target, task, self._easingFunc(init, dest, step, self._relative))
        else:
            # The action should stop, set everything at their final value
            for target in self._tasksStatus:
                for task in self._tasksStatus[target]:
                    init = self._tasksStatus[target][task]['initValue']
                    dest = self._tasksStatus[target][task]['targetValue']
                    if self._relative:
                        setattr(target, task, init+dest)
                    else:
                        setattr(target, task, dest)
                    
            self._done = True

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
        return new_action

    def __or__(self, action):
        """ Add an enclosing dummy action in parallel that harbors the two or'ed actions, returns a new Action"""
        new_action = Action(id = self.id, entity=self._entity, persistent=self.persistent)
        self.root = False
        action.root = False
        new_action._runWith.append(deepcopy(self))
        new_action._runWith.append(deepcopy(action))
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

    def free(self, **kwargs):
        if self._running:
            self._freePending = True
            self.stop()
            return

        for action in self._runWith:
            action.free()
        self._runWith = []

        if self._runNext is not None:
            self._runNext.free()
            self._runNext = None

        self._tasks = {}
        self._targets = []

        self._initParams = {}
        self._freePending = False
        super(Action, self).free(**kwargs)

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
        if self._runNext is not None:
            self._runNext.unfreeze()

    def __repr__(self):
        retval = ''
        retval += "|Action with ID: %s -> %s Active: %s Targets: %s Duration: %s Loop: %s Root: %s Running: %s\n" % (self.id, self._tasks, self.active, self._targets,self._duration, self._loopMax, self._root, self._running)
        if len(self._runWith) > 0:
            retval += "|Runs With:\n"
            for a in self._runWith:
                retval += '* ' + str(a)
            retval += "\n"
        
        if self._runNext is not None:
            for l in str(self._runNext).split('\n'):
                retval += '---->' + l + '\n'
            

        return retval
            