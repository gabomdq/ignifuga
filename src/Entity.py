#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Ignifuga Game Engine
# Base Entity class
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.Gilbert import Event, Gilbert
from ignifuga.Log import error, debug
from ignifuga.components.Component import Component
from Task import *

import weakref,traceback
from copy import deepcopy



class Entity(object):

    class __metaclass__(type):
        # Metaclass builds a list of all the components in __inheritors__
        __inheritors__ = {}
        def __new__(meta, name, bases, dct):
            klass = type.__new__(meta, name, bases, dct)
            meta.__inheritors__[name] = klass
            return klass

    @classmethod
    def create(cls, type='Entity', **data):
        """ Create component based on a data dict """
        if type in Entity.__inheritors__:
            entity = Entity.__inheritors__[type](**data)
            return entity
        return None


    ###########################################################################
    # Initialization, deletion, overlord registration functions
    ###########################################################################
    def __init__(self, **kwargs):
        # Initialize internal fields
        self.id = None
        self._released = False
        self._initialized = False
        self._components = {}
        self._componentsByTag = {}
        self._properties = {}
        self.tags = []
        self._initFailCount = 0
        self._initialComponents = []

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
        self.setup(**data)
        self.load()

        # Fix the id in case it wasn't specified
        if self.id == None:
            self.id = hash(self)

    def __del__(self):
        if not self._released:
            self.free()

    def free(self):
        """ This free function exists to break the dependency cycle among entities, components, etc
        If we wait to do what's done here in __del__ the cycle of dependencies is never broken and the data
        won't be garbage collected. It should be only called from __del__ or unregister """

        if self._released:
            error("Node %s released more than once" % self.id)

        self._data = {}
        self.scene = None

        for component in self._components.itervalues():
            component.free()

        self._components = {}
        self._componentsByTag = {}
        self._properties = {}
        self._released = True
        self._initialComponents = []


    def __str__(self):
        return "Entity with ID %s (%s)" % (self.id,hash(self))

    def init(self,**data):
        """ Initialize the required external data, take into account that this function may be called more than once if initialization fails """
        if not self._initialComponents and 'components' in self._data:
            if isinstance(self._data['components'], dict):
                for c_id, c_data in self._data['components'].iteritems():
                    c_data['id'] = c_id
                    c_data['entity'] = self
                    self._initialComponents.append(Component.create(**c_data))
            elif isinstance(self._data['components'], list):
                for c_data in self._data['components']:
                    c_data['entity'] = self
                    self._initialComponents.append(Component.create(**c_data))

        failcount = {}
        while self._initialComponents:
            component = self._initialComponents.pop(0)
            try:
                component.init(**data)
            except Exception, ex:
                #debug(traceback.format_exc())
                # Something failed, try it again later
                self._initialComponents.append(component)
                if component not in failcount:
                    failcount[component] = 1
                else:
                    failcount[component] += 1

                if failcount[component] >= 10:
                    debug('Temporarily failed initializing Entity %s because of component %s' % (self.id, component))
                    debug(traceback.format_exc())
                    self._initFailCount+=1
                    if self._initFailCount > 10:
                        self._initFailCount = 0
                        error('Ignoring Entity %s, could not initialize it because of component %s' % (self.id, component))
                        error(traceback.format_exc())
                        DONE()
                        return
                    else:
                        failcount[component] = 0
                        # Allow other entities to initialize, then come back here
                        SKIP()

        self._initialized = True


#    def register(self):
#        """ Register Entity with the Overlord """
#        Gilbert().registerNode(self)

    def setup(self, **data):
        self._data = deepcopy(data)

    def reset(self):
        Gilbert().gameLoop.stopEntity(self)
        for component in self._components.itervalues():
            Gilbert().gameLoop.stopEntity(component)

    def unregister(self):
        """ Unregister Entity with the Overlord """
        self.reset()

        # Break dependency cycles
        if not self._released:
            self.free()

    ###########################################################################
    # Persistence, serialization related functions
    ###########################################################################
    def _loadDefaults(self, data):
        """ Load data into the instance if said data doesn't exist """
        for key,value in data.iteritems():
            if not hasattr(self, key):
                setattr(self, key, value)

    def load(self):
        """ Load components from given data
        data has the format may be:
        { 'components': [{'id':'something', 'type':'position','x':1.0,'y':1.0}, {id:'somethingelse', 'type':'sprite',image:'test.png'}, etc], otherdata }
        { 'components': {'something':{'type':'position','x':1.0,'y':1.0}, 'somethingelse': {'type':'sprite',image:'test.png'}, etc}, otherdata }

        The key of each entry
        """
        #Load attributes from data
        for key,value in self._data.iteritems():
            if key not in ['entities', 'components']:
                setattr(self, key, value)

        self._initialComponents = []

    def __getstate__(self):
        odict = self.__dict__.copy()
        # These dont exist in self.__dict__ as they come from Cython (some weird voodoo, right?)...
        # So, we have to add them by hand for them to be pickled correctly
#        odict['id'] = self.id
#        odict['released'] = self._released
#        odict['components'] = self._components
#        odict['componentsByTag'] = self._componentsByTag
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

    @property
    def components(self):
        return self._components

    def getComponent(self, id):
        """ Retrieve a component with a given id, return None if no component by that id is found"""
        if id in self._components:
            return self._components[id]

        return None

    def getComponentsByTag(self, tags):
        """ Return a unique list of the components matching the tags or tag provided """
        if isinstance(tags, basestring):
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
        if component.id in self._components and self._components[component.id] != component:
            error('Entity %s already has a different component with id %s' % (self, component.id))
            return
        self._components[component.id] = component

        if component.entity != self:
            component.entity = self

        if component.active:
            self.addProperties(component)
            self.addTags(component.entityTags)
            for tag in component.tags:
                if tag not in self._componentsByTag:
                    self._componentsByTag[tag] = []
                self._componentsByTag[tag].append(component)



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
            if hasattr(self, property):
                setattr(component, property, getattr(self, property))
                delattr(self, property)
            self._properties[property] = component

    def removeProperties(self, component):
        """ Remove the component public properties"""
        for property in component.properties:
            if property in self._properties and self._properties[property] == component:
                del self._properties[property]

    def addTags(self, tags):
        """ Add one tag or a list of tags to the entity"""
        if isinstance(tags, basestring):
            tags = [tags,]

        for tag in tags:
            if tag not in self.tags:
                self.tags.append(tag)

        Gilbert().refreshEntityTags(self, tags)

    def removeTags(self, tags):
        """ Remove one tag or a list of tags to the entity"""
        if isinstance(tags, basestring):
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
    def update(self, now, **data):
        """ Public customizable update function """

        # By default we don't need an entity update loop
        STOP()

    # Events from the overlord
    def event(self, action, x, y):
        # Handle an event, return: bool1, bool2
        #bool1: False if the event has to cancel propagation
        #bool2: True if the node wants to capture the subsequent events

        #Don't capture ethereal events
        return True, False

    ###########################################################################
    # Properties routing
    ###########################################################################
    def __getattr__( self, name):
        if name == "_properties":
            # If a request for _properties arrives here it means it doesn't yet exist. So, we just create it
            self.__dict__['_properties'] =  {}
            return self.__dict__['_properties']
        if name == '_components':
            self.__dict__['_components'] =  {}
            return self.__dict__['_components']

        if name in self._properties:
            return getattr(self._properties[name], name)

        if name in self._components:
            return self._components[name]

        raise AttributeError('%s does not have a "%s" attribute. Properties are: %s ' % (self, name, self._properties))

    def __setattr__( self, name, value):
        if name in self._properties:
            return setattr(self._properties[name], name, value)
        super(Entity, self).__setattr__(name, value)


    def __repr__(self):
        return 'Entity with ID: %s (%s)' % (self.id,hash(self))