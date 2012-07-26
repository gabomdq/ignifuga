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

class Scene(Entity):
    def __init__(self, **data):
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
            '_size': {'width': None, 'height': None},
            '_scale': None,
            '_scrollX': None,
            '_scrollY': None,
            '_ready': False
        })
        # Add the Scene entity
        #self.entities[self.id] = self

        super(Scene, self).__init__(**data)


        #Load data
        for key,value in data.iteritems():
            if key != 'entities':
                setattr(self, key, value)

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

    def sceneInit(self):
        Gilbert().renderer.setNativeResolution(self._resolution['width'], self._resolution['height'], self._keepAspect, self._autoScale)
        Gilbert().renderer.setSceneSize(self._size['width'], self._size['height'])
        if self._scale is not None:
            Gilbert().renderer.scaleTo(self._scale,self._scale)
        if self._scrollX is not None and self._scrollY is not None:
            print "SCROLL TO",self._scrollX, self._scrollY
            Gilbert().renderer.scrollTo(self._scrollX, self._scrollY)
        if self._autoCenter:
            Gilbert().renderer.centerScene()

        self._ready = True

#    def init(self,data={}):
#        """ Initialize the required external data """
#        super(Scene, self).init(data)
#        print "SCENE ", self.id, self.entities

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

    @property
    def scale(self):
        return self._scale
    @scale.setter
    def scale(self, value):
        self._scale = value
        if self._ready:
            Gilbert().renderer.scaleTo(self._scale,self._scale)

    @property
    def scrollX(self):
        return self._scrollX
    @scrollX.setter
    def scrollX(self, value):
        self._scrollX = value
        if self._ready:
            Gilbert().renderer.scrollTo(self._scrollX, self._scrollY)

    @property
    def scrollY(self):
        return self._scrollY
    @scrollY.setter
    def scrollY(self, value):
        self._scrollY = value
        if self._ready:
            Gilbert().renderer.scrollTo(self._scrollX, self._scrollY)

    @property
    def scroll(self):
        return self._scrollX, self._scrollY
    @scroll.setter
    def scroll(self, value):
        self._scrollX, self._scrollY = value
        if self._ready:
            Gilbert().renderer.scrollTo(self._scrollX, self._scrollY)



    def __repr__(self):
        return 'Scene with ID: %s, Resolution %dx%d, KeepAspect: %s, AutoScale: %s, AutoCenter: %s, Size: %dx%d' % \
        (self.id,self._resolution['width'], self._resolution['height'], self._keepAspect, self._autoScale, self._autoCenter, self._size['width'], self._size['height'])
