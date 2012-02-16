#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Ignifuga Game Engine
# Base Component class
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.Log import error

class Component(object):
    TYPE = None
    TAGS = []
    ENTITY_TAGS = []
    PROPERTIES = []

    class __metaclass__(type):
        # Metaclass builds a list of all the components in __inheritors__
        __inheritors__ = {}
        def __new__(meta, name, bases, dct):
            klass = type.__new__(meta, name, bases, dct)
            meta.__inheritors__[name] = klass
            return klass

    @classmethod
    def create(cls, type=None, **data):
        """ Create component based on a data dict """
        if type in Component.__inheritors__:
            component = Component.__inheritors__[type](**data)
            return component
        return None

    def __init__(self, id=None, entity=None, active=True, frequency=15.0, **data):
        self._id = id if id != None else hash(self)
        self._entity = None
        self._active = False
        self._initiallyActive = active
        self.entity = entity
        self.frequency = frequency
        self.tags = []
        self.entityTags = []
        self.properties = []

        self.load(data)

        # Add some tags that may not have been specified
        self.tags += self.TAGS
        self.entityTags += self.ENTITY_TAGS
        self.properties += self.PROPERTIES


    def _loadDefaults(self, data):
        """ Load data into the instance if said data doesn't exist """
        for key,value in data.iteritems():
            if not hasattr(self, key):
                setattr(self, key, value)

    def load(self, data):
        #Load data into the current instance
        for key,value in data.iteritems():
            setattr(self, key, value)

    @property
    def id(self):
        return self._id

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, active):
        if active != self._active:
            self._active = active
            if self.entity != None:
                if self._active:
                    self.entity.addTags(self.entityTags)
                    self.entity.addProperties(self)
                else:
                    self.entity.refreshTags()
                    self.entity.removeProperties(self)

    @property
    def entity(self):
        return self._entity

    @entity.setter
    def entity(self, entity):
        if self._entity == entity:
            return

        if entity == None:
            # Signal the entity that we are leaving
            e = self._entity
            self._entity = None
            e.remove(self)
            return

        # Check that the component is not assigned to another entity
        if self._entity != None:
            error('Component %s was assigned to entity %s, but it already belongs to %s' % (self, entity, self._entity))
            return

        # Check the entity components to verify that there's not another component with the same id
        if entity.getComponent(self._id) != None:
            error('Entity %s already has a component with id %s' % (entity, self._id))

        self._entity = entity
        entity.add(self)

    @property
    def period(self):
        """ Returns the update rate in ms"""
        return self._period
    @period.setter
    def period(self, value):
        """ Sets the update rate in ms"""
        self._period = value

    @property
    def frequency(self):
        """ Returns the update rate in hz"""
        return 1000.0 / self._period
    @frequency.setter
    def frequency(self, value):
        """ Sets the update rate in hz"""
        self._period = 1000.0 / value

    def init(self, **kwargs):
        self.active = self._initiallyActive

    def update(self, now, **kwargs):
        """ Update the component"""
        pass

    def slot(self, signal, sender=None, **data):
        """ Receives signals from the entity"""
        pass
