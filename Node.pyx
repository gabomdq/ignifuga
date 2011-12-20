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
# Base Node class
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

# NOTES:
# Node actions exist "per state", so even if two actions of the same id exist in different states, they act independently
# Once a state is switched, actions on that state are automatically paused, and actions on the new state automatically resumed.
# The only exception to this are actions marked as "persistent", which can trascend state switches.
# Actions can be defined per state. If you don't define actions for a given state, they have access to *CLONES* of the
# default state actions.

from ignifuga.Gilbert import createNode, Event, Gilbert
from ignifuga.Task import *
from pickle import dumps
from copy import deepcopy
from Log import error
from Action import Action

cdef class Node(object):
    STATE_DEFAULT = 'default'
    STATE_HOVER = 'hover'
    
    def __init__(self, parent, **kwargs):
        super(Node, self).__init__()
        self._released = False
        """ kwargs can be of the form:
        {
            'node-id': {
                'data1': 'value1',
                etc etc
            }
        }
        
        or
        {
            'id': 'node-id',
            'data1': 'value1',
            etc etc
        }

        """
        
        # Fields
        self.children = {}
        self.parent = parent
        self.actions = {}
        self.persistentActions = {}
        self.runningActions = []
        self.onEntryStartActions = []
        self.onEntryStopActions = []
        self.onExitStartActions = []
        self.onExitStopActions = []

        # Preprocess kwargs
        """kwargs may be:
            {'type': nodetype, 'id': nodeid, 'position': 1.0, etc, etc} or
            { 'nodeid': {'type':nodetype, position: 1.0, etc,etc} }"""
        data = {}
        
        if kwargs.has_key('id'):
            self.id = unicode(kwargs['id'])
            del kwargs['id']
            data = kwargs
        elif len(kwargs.keys())==1:
            self.id = unicode(kwargs.keys()[0])
            data = kwargs[self.id]
        else:
            data = kwargs
            self.id = None

        self._state = None
        self._states = { Node.STATE_DEFAULT: {} }
        self._stateKeys = ['actions', 'runningActions', 'onEntryStartActions', 'onEntryStopActions', 'onExitStartActions', 'onExitStopActions']
        states = {}

        # Parse actions
        if 'actions' in data:
            self.actions = self._parseActions(data['actions'])
            for action in self.actions.itervalues():
                if action.persistent:
                    self.persistentActions[action.id] = action
            del data['actions']

        # Load all the initial information
        if 'states' in data:
            states = data['states']
            del data['states']

            # If the states data contains a default state, pick that information up and remove it from the states data
            if Node.STATE_DEFAULT in states:
                self._states[Node.STATE_DEFAULT].update(states[Node.STATE_DEFAULT])
                del states[Node.STATE_DEFAULT]

        # Enter the "not per state" data into the default state
        self._states[Node.STATE_DEFAULT].update(data)
        self._states[Node.STATE_DEFAULT]['actions'] = self.actions
        self._states[Node.STATE_DEFAULT]['runningActions'] = []

        for state, values in states.items():
            # Make a copy of the default state into each state, THEN copy the state values on top of that
            self._states[state] = deepcopy(self._states[Node.STATE_DEFAULT])
            self._states[state].update(values)
            if 'actions' in values:
                self._states[state]['actions'] = self._parseActions(values['actions'])
                for action in self._states[state]['actions'].itervalues():
                    if action.persistent:
                        self.persistentActions[action.id] = action

        self.state = Node.STATE_DEFAULT

        self.createChildren()

    def __del__(self):
        if not self._released:
            self.__free__()

    cpdef Node init(self, dict data):
        """ Initialize the required external data """
        return self
    
    def remove(self):
        """ Unregister node in Gilbert and in parent node, keep data """
        if self.parent != None:
            self.parent.removeChild(self.id)
            self.parent = None
            # Unregister node frees the data
        self.unregisterNode()

    cpdef __free__(self):
        """ This free function exists to break the dependency cycle among nodes, data, states, actions, etc.
        If we wait to do what's done here in __del__ the cycle of dependencies is never broken and the data
        won't be garbage collected. It should be only called from __del__ or unregisterNode """

        if self._released:
            error("Node %s released more than once" % self.id)

        self.parent = None
        self._states = {}
        self.actions = {}
        self.runningActions = []
        self.persistentActions = {}
        self._released = True

    def getType(self):
        return self.__class__.__name__
    
    def createChildren(self):
        # No restore data available, create nodes from the initial static data only
        if hasattr(self,'_nodes'):
            if isinstance(self._nodes, dict):
                """ data follows the template {'nodeid1':{'type':nodetype, etcetc}, 'nodeid2':{'type':nodetype, etc}, etc}"""
                for nid in self._nodes.keys():
                    data = self._nodes[nid]
                    data['id'] = nid
                    node = createNode(self, data)
                    if node != None:
                        self.children[node.id] = node
                    else:
                        error('Problem trying to create node from: ' + str(data))
            else:
                """ data follows the template [{'id':'nodeid1','type':nodetype, etcetc}, {'id':'nodeid2', 'type':nodetype, etc}, etc]"""
                for data in self._nodes:
                    node = createNode(self, data)
                    if node != None:
                        self.children[node.id] = node
                    else:
                        error('Problem trying to create node from: ' + str(data))

    
    def addChild(self, node):
        node.parent = self
        self.children[node.id] = node
        return True
        
    def removeChild(self, node_id, persist=True):
        """ If persist is true the child will be removed from the children list but it won't be unregistered"""
        if node_id in self.children:
            if not persist:
                self.children[node_id].remove()
            
            self.children[node_id].parent = None
            del self.children[node_id]
            return True
        return False
    
    def registerNode(self):
        """ Register Node with the Overlord """
        Gilbert().registerNode(self)
        
    def unregisterNode(self):
        """ Unregister Node with the Overlord """
        Gilbert().unregisterNode(self)
        # Break dependency cycles
        if not self._released:
            self.__free__()

    def update(self, data):
        """ Update node """
        now = data['now']
        stoppedActions = []
        for action in self.runningActions:
            if action.isRunning:
                action.update(now)
            else:
                # action expired, remove it
                stoppedActions.append(action)

        for action in stoppedActions:
            self.runningActions.remove(action)
        
        return self

    property z:
        def __get__(self):
            return None
        def __set__(self, value):
            pass
        
    property state:
        """ The state is a full copy of the values mentioned in _stateKeys """
        def __get__(self):
            return self._state
        def __set__(self,value):
            if self._state != value and value != None:
                # Pre and post states
                persistentActions = []
                if self._state != None:
                    fpreexit = getattr(self, 'preExitState_'+self._state, None)
                    fpostexit = getattr(self, 'postExitState_'+self._state, None)
                    for action in self.runningActions:
                        if action.persistent:
                            persistentActions.append(action)
                else:
                    fpreexit = fpostexit = None

                fpreenter = getattr(self, 'preEnterState_'+value, None)
                fpostenter = getattr(self, 'postEnterState_'+value, None)

                if fpreexit != None:
                    save_current = fpreexit()
                else:
                    save_current = True
                self._exitState()
                if save_current:
                    # Save current state
                    if self._state != None:
                        for k in self._stateKeys:
                            self._states[self._state][k] = getattr(self, k, None)
                if fpostexit != None:
                    fpostexit()

                if fpreenter != None:
                    load_new_state = fpreenter()
                else:
                    load_new_state = True
                if load_new_state:
                    # Load new state
                    if value not in self._states:
                        # State is new, just make a new copy of the current state
                        self._states[value] = deepcopy(self._states[self._state if self._state != None else Node.STATE_DEFAULT])
                    for k,v in self._states[value].iteritems():

                        setattr(self, k, v)

                self._state = value

                # Restore persistent actions
                for action in persistentActions:
                    if action not in self.runningActions:
                        self.runningActions.append(action)

                # Force a fix in the timing in all running actions to prevent abrupt
                # jumps due to the action being paused. Similar to what it's done when unserializing actions
                for action in self.runningActions:
                    if not action.persistent:
                        action.unfreeze()

                self._enterState()
                if fpostenter != None:
                    fpostenter()

    property nodes:
        def __get__(self):
            return self._nodes
        def __set__(self,val):
            self._nodes = val
        
    def hits(self, x, y):
        # Check if x,y hits the node
        return False
    
    def event(self, event):
        # Handle an event, return: bool1, bool2
        #bool1: False if the event has to cancel propagation
        #bool2: True if the node wants to capture the subsequent events
        if event.type == Event.TYPE.touchdown:
            return self.onTouchDown(event)
        elif event.type == Event.TYPE.touchup:
            return self.onTouchUp(event)
        elif event.type == Event.TYPE.touchmove:
            return self.onTouchMove(event)
            
        #Don't capture ethereal events
        return event.ethereal, False
    
    def do(self, action):
        """ Assign an action to the node """
        if not action.isRunning:
            action.target = self
            action.start()
            if action.id not in self.actions:
                self.actions[action.id] = action
            self.runningActions.append(action)

    def detachAction(self, action):
        """ Remove action-node assignment """
        if action.id in self.actions:
            del self.actions[action.id]
        if action in self.runningActions:
            self.runningActions.remove(action)
            action.stop()

    def onTouchDown(self, event):
        # A finger or mouse touched on the node
        return False, False
    
    def onTouchUp(self, event):
        # A finger or mouse lifted touch from the node
        return False, False
    
    def onTouchMove(self, event):
        # A finger or mouse is moving across the node
        return False, False

    def loadDefaults(self, data = {}):
        """ Load a dict of default values IF THEY DONT ALREADY EXIST """
        for k,v in data.iteritems():
            if k not in self.__dict__:
                self.__dict__[k] = v

    def __getstate__(self):
        odict = self.__dict__.copy()
        # These dont exist in self.__dict__ as they come from Cython (some weird voodoo, right?)...
        # So, we have to add them by hand for them to be pickled correctly
        odict['id'] = self.id
        odict['parent'] = self.parent
        odict['children'] = self.children
        odict['actions'] = self.actions
        odict['persistentActions'] = self.persistentActions
        odict['runningActions'] = self.runningActions
        odict['_stateKeys'] = self._stateKeys
        odict['_state'] = self._state
        odict['_states'] = self._states
        odict['onEntryStartActions'] = self.onEntryStartActions
        odict['onEntryStopActions'] = self.onEntryStopActions
        odict['onExitStartActions'] = self.onExitStartActions
        odict['onExitStopActions'] = self.onExitStopActions
        return odict

    def __reduce__(self):
        return type(self), (self.parent,), self.__getstate__()
            
    def __setstate__(self, data):
        for k,v in data.iteritems():
            setattr(self, k, v)

    def __str__(self):
        return "Gilbert node of type %s" % (self.__class__.__name__,)

    def _parseActions(self, data):
        """ Actions have the format:
        {
        'id': { duration=0.0, relative=False, increase='linear', loop=1, runNext: {another action}, runWith: {another action} }
        }
        """
        actions = {}
        for action_id, action_data in data.iteritems():
            action = self._parseAction(action_data)
            action.id = action_id
            actions[action_id] = action
        return actions

    def _parseAction(self, action_data):
        """ Parse a single action """
        data = deepcopy(action_data)

        if 'runWith' in data:
            runWith = data['runWith']
            del data['runWith']
        else:
            runWith = None

        if 'runNext' in data:
            runNext = data['runNext']
            del data['runNext']
        else:
            runNext = None

        action = Action(**data)

        if runWith != None:
            action = action | self._parseAction(runWith)

        if runNext != None:
            action = action + self._parseAction(runNext)

        return action

    def _enterState(self):
        """ Start and stop actions for the new state """
        for action_id in self.onEntryStartActions:
            if action_id in self.actions:
                action = self.actions[action_id]
                if not action.isRunning:
                    self.do(action)
            elif action_id in self.persistentActions:
                action = self.persistentActions[action_id]
                if not action.isRunning:
                    self.do(action)

        for action_id in self.onEntryStopActions:
            if action_id in self.actions:
                action = self.actions[action_id]
                if action.isRunning and action.target == self:
                    action.stop()
            elif action_id in self.persistentActions:
                action = self.persistentActions[action_id]
                if action.isRunning and action.target == self:
                    action.stop()


    def _exitState(self):
        """ Start and stop actions for the old state """
        for action_id in self.onExitStartActions:
            if action_id in self.actions:
                action = self.actions[action_id]
                if not action.isRunning:
                    self.do(action)
            elif action_id in self.persistentActions:
                action = self.persistentActions[action_id]
                if not action.isRunning:
                    self.do(action)

        for action_id in self.onExitStopActions:
            if action_id in self.actions:
                action = self.actions[action_id]
                if action.isRunning and action.target == self:
                    action.stop()
            elif action_id in self.persistentActions:
                action = self.persistentActions[action_id]
                if action.isRunning and action.target == self:
                    action.stop()

