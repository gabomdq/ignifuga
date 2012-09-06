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
            '_scale': (None, None),
            '_scrollX': None,
            '_scrollY': None,
            '_ready': False,
            'reloadPreserveCamera': True,
            'data_url': None,
            'isolateEntities': False,
            'runEnv': {}
        })
        # Add the Scene entity
        super(Scene, self).__init__(**data)
        #self.data_url = data['data_url']

        self.setup(**data)

    def __del__(self):
        self.reset()
        super(Scene, self).__del__()

    def free(self):
        # Scenes are not released as they are re entrant
        super(Scene, self).free()
        self._released = False

    def reset(self):
        # Remove existing entities
        if self._ready:
            self._ready = False
            self.runEnv = {}
            super(Scene, self).reset()

            for entity in self.entities.itervalues():
                entity.unregister()
            self.entities = {}
            self.cache_ref = None
            if self.data_url is not None:
                Gilbert().dataManager.removeListener(self.data_url, self)

            self.free()

    def reload(self, source):
        # If the scene is not ready, ignore the reload...TODO: Should we schedule a reload for later?
        if self._ready:
            Gilbert().freezeRenderer()
            self.reset()

            new_data = Gilbert().dataManager.loadJsonFile(source)
            if self.id in new_data:
                if self.reloadPreserveCamera:
                    new_data[self.id]['scale'] = self.scale
                    new_data[self.id]['scroll'] = self.scroll
                    new_data[self.id]['autoCenter'] = False
                self.source = source
                self.setup(**new_data[self.id])
                self.load()
                Gilbert().startEntity(self)

    def getEntity(self, id):
        """ Retrieve an entity with a given id, return None if no entity by that id is found"""
        if id in self.entities:
            return self.entities[id]

        return None

    def init(self,**data):
        """ Initialize the required external data """

        # Prepare a basic run environment for components to execute commands
        self.runEnv['scene'] = self
        self.runEnv['Gilbert'] = Gilbert()
        self.runEnv['DataManager'] = Gilbert().dataManager
        self.runEnv['Renderer'] = Gilbert().renderer
        # Some task helper functions
        self.runEnv['SKIP'] = SKIP
        self.runEnv['DONE'] = DONE
        self.runEnv['ERROR'] = ERROR

        from ignifuga.pQuery import pQuery
        self.runEnv['_'] = pQuery

        # Build entities
        if 'entities' in self._data:
            for entity_id, entity_data in self._data['entities'].iteritems():
                entity = Entity.create(id=entity_id, scene=self, **entity_data)
                if entity != None:
                    self.entities[entity_id] = entity
                    if not self.isolateEntities and not str(entity.id).isdigit():
                        self.runEnv[entity.id] = entity

        for entity in self.entities.itervalues():
            Gilbert().startEntity(entity)

        if self.data_url is not None:
            Gilbert().dataManager.addListener(self.data_url, self)

        Gilbert().renderer.setNativeResolution(self._resolution['width'], self._resolution['height'], self._keepAspect, self._autoScale)
        Gilbert().renderer.setSceneSize(self._size['width'], self._size['height'])
        if self._autoCenter:
            Gilbert().renderer.centerScene()

        self._ready = True
        # Apply scaling and scrolling
        self.scale = self._scale
        self.userCanScroll = self._userCanScroll
        self.userCanZoom = self._userCanZoom
        if self._scrollX is not None and self._scrollY is not None:
            self.scroll = self._scrollX, self._scrollY

        super(Scene, self).init(**data)

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
        if self._ready:
            Gilbert().renderer.userCanScroll = value

    @property
    def userCanZoom(self):
        return self._userCanZoom
    @userCanZoom.setter
    def userCanZoom(self, value):
        self._userCanZoom = value
        if self._ready:
            Gilbert().renderer.userCanZoom = value

    @property
    def scaleX(self):
        return self.scale[0]

    @scaleX.setter
    def scaleX(self, value):
        self.scale = (value, self._scale[1])

    @property
    def scaleY(self):
        return self.scale[1]

    @scaleY.setter
    def scaleY(self, value):
        self.scale = (self._scale[0], value)

    @property
    def scale(self):
        self._scale = Gilbert().renderer.scale
        return self._scale

    @scale.setter
    def scale(self, value):
        if (isinstance(value, tuple) or isinstance(value, list)) and len(value) == 2:
            self._scale = value
            if self._ready and self._scale[0] is not None and self._scale[1] is not None:
                Gilbert().renderer.scaleTo(self._scale[0],self._scale[1])
        else:
            try:
                value = float(value)
                self._scale = value, value
                if self._ready:
                    Gilbert().renderer.scaleTo(value, value)
            except:
                self._scale = None, None

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
        return 'Scene with ID: %s, Resolution %sx%s, KeepAspect: %s, AutoScale: %s, AutoCenter: %s, Size: %sx%s' % \
        (self.id,self._resolution['width'], self._resolution['height'], self._keepAspect, self._autoScale, self._autoCenter, self._size['width'], self._size['height'])
