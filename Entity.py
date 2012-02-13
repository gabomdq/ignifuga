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
# Base Entity class
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.Gilbert import Event, Gilbert
from ignifuga.Log import error
from ignifuga.components.Component import Component

import weakref
class Entity(object):
    ###########################################################################
    # Initialization, deletion, overlord registration functions
    ###########################################################################
    def __init__(self, **kwargs):
        # Initialize internal fields
        self.id = None
        self._released = False
        self._components = {}
        self._componentsByTag = {}
        self._componentsBySignal = {}
        self._properties = {}
        self.tags = []
        self.signalQueue = []

        """
        Preprocess kwargs

        kwargs may be:
            {'id': nodeid, 'components': [{'type':'position','x':1.0,'y':1.0}, {'type':'sprite',image:'test.png'}, etc]} or
            {'nodeid': {'components': [{'type':'position','x':1.0,'y':1.0}, {'type':'sprite',image:'test.png'}, etc] }

        """
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

        if 'scene' in kwargs:
            self.scene = weakref.ref(kwargs['scene'])
            del kwargs['scene']
        else:
            self.scene = None

        # Process the data, load the components from it
        self.load(data)

        # Fix the id in case it wasn't specified
        if self.id == None:
            self.id = hash(self)

    def __del__(self):
        if not self._released:
            self.__free__()

    def __free__(self):
        """ This free function exists to break the dependency cycle among entities, components, etc
        If we wait to do what's done here in __del__ the cycle of dependencies is never broken and the data
        won't be garbage collected. It should be only called from __del__ or unregister """

        if self._released:
            error("Node %s released more than once" % self.id)

        self._components = {}
        self._componentsByTag = {}
        self._componentsBySignal = {}
        self._properties = {}
        self._released = True

    def __str__(self):
        return "Entity with ID %s" % (self.id,)

    def init(self,data):
        """ Initialize the required external data """
        components = self._components.keys()
        failcount = {}
        while components:
            component = components.pop()
            try:
                self._components[component].init(**data)
            except:
                # Something failed, try it again later
                if component not in failcount:
                    failcount[component] = 1
                else:
                    failcount[component] += 1
                if failcount[component] < 10:
                    components.append(component)
        return self

    def register(self):
        """ Register Entity with the Overlord """
        Gilbert().registerNode(self)

    def unregister(self):
        """ Unregister Entity with the Overlord """
        Gilbert().stopEntity(self)
        # Break dependency cycles
        if not self._released:
            self.__free__()

    ###########################################################################
    # Persistence, serialization related functions
    ###########################################################################
    def load(self, data):
        """ Load components from given data
        data has the format may be:
        { 'components': [{'id':'something', 'type':'position','x':1.0,'y':1.0}, {id:'somethingelse', 'type':'sprite',image:'test.png'}, etc], otherdata }
        { 'components': {'something':{'type':'position','x':1.0,'y':1.0}, 'somethingelse': {'type':'sprite',image:'test.png'}, etc}, otherdata }

        The key of each entry
        """
        if 'components' in data:
            if isinstance(data['components'], dict):
                for c_id, c_data in data['components'].iteritems():
                    c_data['id'] = c_id
                    c_data['entity'] = self
                    Component.create(**c_data)
            elif isinstance(data['components'], list):
                for c_data in data['components']:
                    c_data['entity'] = self
                    Component.create(**c_data)

    def __getstate__(self):
        odict = self.__dict__.copy()
        # These dont exist in self.__dict__ as they come from Cython (some weird voodoo, right?)...
        # So, we have to add them by hand for them to be pickled correctly
#        odict['id'] = self.id
#        odict['released'] = self._released
#        odict['components'] = self._components
#        odict['componentsByTag'] = self._componentsByTag
#        odict['componentsBySignal'] = self._componentsBySignal
#        odict['tags'] = self.tags
        return odict

#    def __reduce__(self):
#        return type(self), (None,), self.__getstate__()

    def __setstate__(self, data):
        for k,v in data.iteritems():
            setattr(self, k, v)


    ###########################################################################
    # Component handling, tags, properties
    ###########################################################################

    def getComponent(self, id):
        """ Retrieve a component with a given id, return None if no component by that id is found"""
        if id in self._components:
            return self._components[id]

        return None

    def getComponentsByTag(self, tags):
        """ Return a unique list of the components matching the tags or tag provided """
        if not hasattr(tags, '__contains__'):
            tags = [tags,]

        components = []
        for tag in tags:
            if tag in self._componentsByTag:
                for component in self._componentsByTag[tag]:
                    if component not in components:
                        components.append(component)
        return components

    def add(self, component):
        """ Add a component to the entity"""
        if component.id in self._components:
            error('Entity %s already has a component with id %s' % (self, component.id))
            return
        self._components[component.id] = component
        component.entity = self
        if component.active:
            self.addTags(component.entityTags)
            for tag in component.tags:
                if tag not in self._componentsByTag:
                    self._componentsByTag[tag] = []
                self._componentsByTag.append(component)

            self.addProperties(component)

    def remove(self, component):
        """ Remove a component from the entity (accepts either the component object or the id) """
        if not isinstance(component, Component):
            if component in self._components:
                component = self._components[component]
            else:
                return

        if component in self._components:
            del self._components[component]
            self.removeProperties(component)

        self.refreshTags()

    def addProperties(self, component):
        """ Adopt the component public properties"""
        for property in component.properties:
            self._properties[property] = component

    def removeProperties(self, component):
        """ Remove the component public properties"""
        for property in component.properties:
            if property in self._properties and self._properties[property] == component:
                del self._properties[property]

    def addTags(self, tags):
        """ Add one tag or a list of tags to the entity"""
        if not hasattr(tags, '__contains__'):
            tags = [tags,]

        for tag in tags:
            if tag not in self.tags:
                self.tags.append(tag)

        Gilbert().refreshEntityTags(self, tags)

    def removeTags(self, tags):
        """ Remove one tag or a list of tags to the entity"""
        if not hasattr(tags, '__contains__'):
            tags = [tags,]

        for tag in tags:
            if tag in self.tags:
                self.tags.remove(tag)

        Gilbert().refreshEntityTags(self, [], tags)

    def refreshTags(self):
        # Refresh the entity tags
        oldTags = set(self.tags)
        self.tags = []
        for component in self._components.itervalues():
            if component.active:
                self.addTags(component.entityTags)

        # Update tag index in the Gilbert overlord
        newTags = set(self.tags)
        Gilbert().refreshEntityTags(self, list(newTags-oldTags), list(oldTags-newTags))

    ###########################################################################
    # Update functions
    ###########################################################################
    def update(self, data):
        """ Public customizable update function """
        pass

    def _update(self, data):
        """ Internal update function, updates components, etc, runs IN PARALLEL with update """
        # Dispatch signals
        for signal in self.signalQueue:
            self.directSignal(signal['signal'], signal['target'], signal['tags'], signal['data'])

        self.signalQueue = []

        # Run the active components update loop
        for component in self._components.itervalues():
            if component.active:
                component.update(**data)

    # Events from the overlord
    def event(self, event):
        # Handle an event, return: bool1, bool2
        #bool1: False if the event has to cancel propagation
        #bool2: True if the node wants to capture the subsequent events
#        if event.type == Event.TYPE.touchdown:
#            return self.onTouchDown(event)
#        elif event.type == Event.TYPE.touchup:
#            return self.onTouchUp(event)
#        elif event.type == Event.TYPE.touchmove:
#            return self.onTouchMove(event)

        #Don't capture ethereal events
        return event.ethereal, False


    ###########################################################################
    # Signal handling
    ###########################################################################

    def subscribe(self, component, signal):
        """ Components subscribe to signals using this function """
        if signal not in self._componentsBySignal:
            self._componentsBySignal[signal] = []

        if component not in self._componentsBySignal[signal]:
            self._componentsBySignal[signal].append(component)

    def unsubscribe(self, component, signal=None):
        """ Components unsubscribe to signals using this function, if signal=None, unsubscribe from all signals """
        if signal == None:
            signals = self._componentsBySignal
        else:
            signals = [signal,]

        for signal in signals:
            if signal in self._componentsBySignal:
                if component in self._componentsBySignal[signal]:
                    self._componentsBySignal[signal].remove(component)
                    if not self._componentsBySignal[signal]:
                        del self._componentsBySignal[signal]

    def signal(self, signal_name, target=None, tags = [], **data):
        """ Function used to send signals to components via a queue (signals are processed in the next update) """
        self.signalQueue.append({'signal': signal_name, 'target': target, 'tags': tags, 'data': data})

    def directSignal(self, signal_name, target=None, tags = [], **data):
        """ Function used to send direct signals to components """
        targets = []
        # Send to target
        if target != None and not isinstance(target, Component):
            if target in self._components:
                target = self._components[target]
            else:
                target=None
        if target != None:
            targets.append(target)

        # Send to tags
        if not hasattr(tags, '__contains__'):
            tags = [tags,]
        for tag in tags:
            if tag in self._componentsByTag:
                for component in self._componentsByTag[tag]:
                    if component not in targets:
                        targets.append(component)
        for component in targets:
            if component.active:
                component.signal(signal_name, **data)

    ###########################################################################
    # Properties routing
    ###########################################################################
    def __getattr__( self, name):
        if name == "_properties":
            # If a request for _properties arrives here it means it doesn't yet exist. So, we just create it
            self.__dict__['_properties'] =  {}
            return self.__dict__['_properties']
        if name in self._properties:
            return getattr(self._properties[name], name)

        raise AttributeError('%s does not have a "%s" attribute. Properties are: %s ' % (self, name, self._properties))

    def __setattr__( self, name, value):
        if name in self._properties:
            return setattr(self._properties[name], name, value)
        super(Entity, self).__setattr__(name, value)

