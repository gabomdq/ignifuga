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

from ignifuga.Gilbert import createNode, Event, Gilbert
from ignifuga.Task import *
from pickle import dumps
from copy import deepcopy
from Log import error

cdef class Node(object):
    STATE_DEFAULT = 'default'
    
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
        self.actions = []

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
        states = {}
        # Load all the initial information
        if 'states' in data:
            states = deepcopy(data['states'])
            del data['states']
            
            if Node.STATE_DEFAULT in states:
                self._states[Node.STATE_DEFAULT].update(states[Node.STATE_DEFAULT])
                del states[Node.STATE_DEFAULT]

        self._states[Node.STATE_DEFAULT].update(data)

        for state, values in states.items():
            self._states[state] = deepcopy(self._states[Node.STATE_DEFAULT])
            self._states[state].update(values)
        
        self.state = Node.STATE_DEFAULT

        self.createChildren()

    def __del__(self):
        if not self._released:
            self.free()
        
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

    cpdef free(self):
        """ Release external (Cython based, not Python) data """
        if self._released:
            error("Node %s released more than once" % self.id)

        self.parent = None
        self.actions = []
        self.states = {}
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

    def update(self, data):
        """ Update node """
        now = data['now']
        for action in self.actions[:]:
            if action.isRunning:
                action.update(now)
            else:
                # action expired, remove it
                self.actions.remove(action)
        
        return self

    property z:
        def __get__(self):
            return None
        def __set__(self, value):
            pass
        
    property state:
        """ The state is a full copy of the Node dictionary """
        def __get__(self):
            return self._state
        def __set__(self,value):
            if self._state != value:
                # Save current state
                if self._state != None:
                    self._states[self._state] = deepcopy(getattr(self, '__dict__', {}))
                # Load new state
                if value not in self._states:
                    # State is new, just make a new copy of the current state
                    #print "CREATING NEW STATE: ", value,
                    self._states[value] = deepcopy(self._states[Node.STATE_DEFAULT])
                    #print "NEW STATE: ", self._states[value]

                for k,v in self._states[value].items():
                    setattr(self, k, v)

                self._state = value

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
            self.actions.append(action)

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
        for k,v in data.items():
            if k not in self.__dict__:
                self.__dict__[k] = v

    def __getstate__(self):
        odict = self.__dict__.copy()
        odict['id'] = self.id
        odict['parent'] = self.parent
        odict['children'] = self.children
        odict['actions'] = self.actions
        return odict


    def __reduce__(self):
        return type(self), (self.parent,), self.__getstate__()
            
    def __setstate__(self, data):
        for k,v in data.iteritems():
            setattr(self, k, v)


    def __str__(self):
        return "Gilbert node of type %s" % (self.__class__.__name__,)
