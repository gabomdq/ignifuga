#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


# Ignifuga Game Engine
# Scene class, a basic way to organize entities
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.Entity import Entity
from ignifuga.Task import *
from ignifuga.Gilbert import Gilbert

class Scene(object):
    def __init__(self, **data):

        #Load data
        for key,value in data.iteritems():
            if key != 'entities':
                setattr(self, key, value)

        # Default values
        self._loadDefaults({
            'id': hash(self),
            'entities': {},
            '_resolution': {'width': None, 'height': None},
            '_keepAspect': True,
            '_autoScale': True,
            '_autoCenter': False,
            '_userCanScroll': True,
            '_userCanZoom': True,
            '_size': {'width': None, 'height': None}
        })

        # Build entities
        if 'entities' in data:
            for entity_id, entity_data in data['entities'].iteritems():
                entity = Entity.create(id=entity_id, scene=self, **entity_data)
                if entity != None:
                    self.entities[entity_id] = entity

    def getEntity(self, id):
        """ Retrieve an entity with a given id, return None if no entity by that id is found"""
        if id in self.entities:
            return self.entities[id]

        return None

    @property
    def resolution(self):
        return self._resolution
    @resolution.setter
    def resolution(self,value):
            self._resolution = value

    @property
    def keepAspect(self):
        return self._keepAspect
    @keepAspect.setter
    def keepAspect(self, value):
            self._keepAspect = value

    @property
    def autoScale(self):
        return self._autoScale
    @autoScale.setter
    def autoScale(self, value):
        self._autoScale = value

    @property
    def size(self):
        return self._size
    @size.setter
    def size(self, value):
        self._size = value

    @property
    def autoCenter(self):
        return self._autoCenter
    @autoCenter.setter
    def autoCenter(self, value):
        self._autoCenter = value

    @property
    def userCanScroll(self):
        return self._userCanScroll
    @userCanScroll.setter
    def userCanScroll(self, value):
        self._userCanScroll = value

    @property
    def userCanZoom(self):
        return self._userCanZoom
    @userCanZoom.setter
    def userCanZoom(self, value):
        self._userCanZoom = value

    def init(self):
        """ Initialize the required external data """
        # Do our initialization
        Gilbert().renderer.setNativeResolution(self._resolution['width'], self._resolution['height'], self._keepAspect, self._autoScale)
        Gilbert().renderer.setSceneSize(self._size['width'], self._size['height'])
        if self._autoCenter:
            Gilbert().renderer.centerScene()


    def _loadDefaults(self, data):
        """ Load data into the instance if said data doesn't exist """
        for key,value in data.iteritems():
            if not hasattr(self, key):
                setattr(self, key, value)