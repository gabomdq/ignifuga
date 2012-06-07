#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Ignifuga Game Engine
# Main Singleton
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.Rect import Rect
from ignifuga.Singleton import Singleton
from ignifuga.Log import *
import sys, pickle, os, weakref, gc, platform, copy, base64
from optparse import OptionParser

class BACKENDS:
    sdl = 'sdl'
    
class REQUESTS:
    loadImage = 'loadImage'
#    loadSprite = 'loadSprite'
    #dirtyRects = 'dirtyRects'
    done = 'done'
    skip = 'skip'
    stop = 'stop'
    nativeResolution = 'nativeResolution'
    iterate = 'iterate'
    sceneSize = 'sceneSize'

from Task import Task
    
class Event:
    class TYPE:
        # We don't really use these
        mouseout = 'mouseout'
        mouseover = 'mouseover'
        click = 'click'
        # The following 3 are mapped to touch events
        _mousemove = 'mousemove'
        _mousedown = 'mousedown'
        _mouseup = 'mouseup'
        # The following 3 are mapped to touch events
        _moztouchmove = 'moztouchmove'
        _moztouchdown = 'moztouchdown'
        _moztouchup = 'moztouchup'
        
        # EVENTS ACTUALLY HANDLED BY THE NODES
        
        # Interactive x/y coordinates events
        touchdown = 'touchdown'
        touchup = 'touchup'
        touchmove = 'touchmove'
        
        # Ethereal events
        accelerometer = 'accelerometer'
        compass = 'compass'
        focus = 'focus'
        blur = 'blur'
        zoomin = 'zoomin'
        zoomout = 'zoomout'
        scroll = 'scroll'
        
    ETHEREALS = [TYPE.accelerometer, TYPE.compass, TYPE.focus, TYPE.blur, TYPE.zoomin, TYPE.zoomout, TYPE.scroll]
        
    class MODIFIERS:
        ctrl = 'ctrl'
        alt = 'alt'
        shift = 'shift'
        meta = 'meta'
    
    def __init__(self, type, x=None, y=None, deltax=None, deltay=None, button=None, stream=0, pressure=None, modifiers=[]):
        self.type = str(type).lower()
        self.x = x
        self.y = y
        self.deltax = deltax
        self.deltay = deltay
        self.button = button
        self.stream = stream
        self.pressure = pressure
        self.modifiers = modifiers
        self.ethereal = type in Event.ETHEREALS
        
    def __str__(self):
        return "%s (%s,%s) btn:%s stream: %s pre: %s mod: %s ethereal: %s" % (self.type, self.x, self.y, self.button, self.stream, self.pressure, str(self.modifiers), str(self.ethereal))

class Signal(object):
    touches = 'touches'
    zoom = 'zoom'
    scroll = 'scroll'

def Renderer():
    return Gilbert().renderer

def Canvas():
    return _Canvas

########################################################################################################################
# SPLASH SCENE DEFINITION.
# ANY MODIFICATION OF THE SCENE DEFINITION AND RELATED CODE AND ARTWORK RENDERS THE LICENSE TO USE THIS ENGINE VOID.
########################################################################################################################

SPLASH_SCENE = {
    "resolution": {
        "width": 1920,
        "height": 1200,
    },
    "keepAspect": True,
    "autoScale": False,
    "autoCenter": True,
    "userCanScroll": False,
    "userCanZoom": False,
    "size": {
        "width": 3840,
        "height": 2400
    },
    "entities": {
        "splash": {
            "components": [{
                "type": "Sprite",
                "file": u"embedded:splash",
                "z": 0,
                "x": 960,
                "y": 600,
                "interactive": False
            },
            {
                "id" : "pause",
                "type": "Action",
                "duration": 2.0,
                "runNext": {
                    "duration":1.0,
                    "alpha":0.0,
                    "onStop": "Gilbert().startFirstScene()"
                }
            }]
        }
    }
}
from embedded import SPLASH
EMBEDDED_IMAGES = {
    'splash': SPLASH
}

########################################################################################################################
# END SPLASH SCENE DEFINITION
########################################################################################################################

# Dynamic imported modules (they are set up depending on the backend)
GameLoop = None
DataManager = None
_Canvas = None
Target = None

class GilbertPickler(pickle.Pickler):
    def memoize(self, obj):
        """Override the standard memoize as it contains an assertion in the wrong place (at least in Python 2.7.2) that screws up the children attribute in Node.pyx"""
        if self.fast:
            return
        if id(obj) in self.memo:
            return
        memo_len = len(self.memo)
        self.write(self.put(memo_len))
        self.memo[id(obj)] = memo_len, obj

class Gilbert:    
    __metaclass__ = Singleton

    def __init__(self):
        pass
    
    def init(self, backend, scenesFile, firstScene):
        self.backend = backend
        debug ('Initializing Gilbert Overlord')

        usage = "game [options]"
        parser = OptionParser(usage=usage, version="Ignifuga Build Utility 1.0")
        parser.add_option("-d", "--display", dest="display", default=0,help="Display (default: 0)")
        parser.add_option("--width", dest="width", default=None,help="Resolution Width")
        parser.add_option("--height", dest="height", default=None,help="Resolution Height")
        parser.add_option("-w", "--windowed", action="store_true", dest="windowed", default=False,help="Start in windowed mode (default: no)")
        (options, args) = parser.parse_args()

        # Set up dynamic imports
        global GameLoop
        global DataManager
        global _Canvas
        global Target

        self.platform = sys.platform
        if self.platform.startswith('linux'):
            self.platform = 'linux'
            self.distro_name, self.distro_version, self.distro_id = platform.linux_distribution()
            if self.distro_name.lower() == 'android':
                self.platform = 'android'
        elif self.platform == 'darwin':
            self.distro_name, self.distro_version, self.distro_id = platform.mac_ver()
        elif self.platform.startswith('win32'):
            self.distro_name, self.distro_version, self.distro_id, self.multi_cpu = platform.win32_ver()

        debug('Platform: %s' % self.platform)
        debug('Distro: %s' % self.distro_name)
        debug('Distro Ver: %s ID: %s' % (self.distro_version, self.distro_id) )

        if self.backend == BACKENDS.sdl:
            debug('Initializing backend %s' % (backend,))
            from backends.sdl import initializeBackend
            from backends.sdl.GameLoop import GameLoop as gameloop
            from backends.sdl.DataManager import DataManager as datamanager
            from backends.sdl.Canvas import Canvas as canvas
            from backends.sdl.Target import Target as target
            initializeBackend()
            GameLoop = gameloop
            DataManager = datamanager
            _Canvas = canvas
            Target = target
            debug('Backend %s initialized' % (backend,))
        else:
            error('Unknown backend %s. Aborting' % (backend,))
            exit()

        # The only dictionaries that keeps strong references to the entities
        self.scenes = {}
        # A pointer to the current scene stored in self.scenes
        self.scene = None
        # A pointer to the current scene entities
        self.entities = {}
        # These dictionaries keep weakrefs via WeakSet, contain the current scene entities
        self.entitiesByTag = {}
        self.entitiesByZ = {}

        # These keep weakrefs in the key and via Task
        self.loading = {}
        self.running = {}

        self._touches = {}
        self._touchCaptured = False
        self._touchCaptor = None
        self._lastEvent = None

        self._freezeRenderer = False

        
        self.renderer = _Renderer(Target(width=options.width, height=options.height, fullscreen= not options.windowed, display=options.display))
        self.dataManager = DataManager()

        if not self.loadState():
            debug('Failed loading previous state')
            scenes = self.dataManager.loadJsonFile(scenesFile)
            self.loadScenes(scenes)
########################################################################################################################
# SPLASH SCENE CODE
# ANY MODIFICATION OF THE SCENE DEFINITION AND RELATED CODE AND ARTWORK RENDERS THE LICENSE TO USE THIS ENGINE VOID.
########################################################################################################################
            self._firstScene = firstScene
            self.loadScene('splash', copy.deepcopy(SPLASH_SCENE))
            if not self.startScene('splash'):
                error('Could not load splash scene')
                return
########################################################################################################################
# SPLASH SCENE CODE ENDS.
########################################################################################################################

        debug('Starting Game Loop')
        self.startLoop()
        # Nothing after this will get executed until the engine exits
        debug('Ignifuga Game Engine Exits...')

    def startLoop(self):
        """Set up the game loop"""
        self.gameLoop = GameLoop()
        self.gameLoop.run()

        # Engine is exiting from here onwards

        debug('Saving state')
        self.saveState()

        # Release all data
        if self.backend == BACKENDS.sdl:
            from backends.sdl import terminateBackend

        self.resetScenes()
        # DEBUG - See what's holding on to what
        objs = gc.get_objects()
        for n in objs:
            if isinstance(n, Entity) or isinstance(n,Component):
                debug ('%s: %s' % (n.__class__.__name__, n))
                for ref in gc.get_referrers(n):
                    if ref != objs:
                        debug('    REFERRER: %s %s'  % (ref.__class__, id(ref)))
                        if isinstance(ref, dict):
                            debug("    DICT: %s" % ref.keys())
                        elif isinstance(ref, list):
                            debug("    LIST: %s" % len(ref), " items")
                        elif isinstance(ref, tuple):
                            debug("    TUPLE: %s" % ref)
                        else:
                            debug("    OTHER: %s" % ref)
        self.dataManager.cleanup(True)
        # Break any remaining cycles that prevent garbage collection
        del self.dataManager
        del self.renderer
        debug('Terminating backend %s' % (self.backend,))
        terminateBackend()

    def endLoop(self):
        """ End the game loop, free stuff """
        self.gameLoop.quit = True

    def update(self, now=0, wrapup=False):
        """ Update everything, then render the scene
        now is the current time, specified in seconds
        wrapup = True forces the update loop to be broken, all running entities eventually stop running
        """
        # Call the pre update so we can tally how long the whole frame processing took (logic+render)
        if not wrapup:
            self.renderer.preUpdate(now)

        # Initialize objects
        remove_entities = []
        for entity_ref in self.loading.iterkeys():
            task, req, data = self.loading[entity_ref]
            if task != None:
                task, req, data = self._processTask(task, req, data, now, wrapup, True)

            if task != None:
                self.loading[entity_ref] = (task, req, data)
            else:
                remove_entities.append(entity_ref)

        for entity_ref in remove_entities:
            del self.loading[entity_ref]
            if not self.loading:
                self._freezeRenderer  = False


        # Update objects
        remove_entities = []
        for entity_ref in self.running.keys():
            # This check may seem overkill, but there's situations where the ref may have been removed from self.running!
            if entity_ref in self.running:
                task1, req1, data1,task2,req2,data2 = self.running[entity_ref]
                if task1 != None:
                    task1, req1, data1 = self._processTask(task1, req1, data1, now, wrapup)

                if task2 != None:
                    task2, req2, data2 = self._processTask(task2, req2, data2, now, wrapup)

                if task1 != None or task2 != None:
                    self.running[entity_ref] = (task1, req1, data1,task2, req2, data2)
                else:
                    remove_entities.append(entity_ref)

        for entity_ref in remove_entities:
            del self.running[entity_ref]

    def _processTask(self, task, req, data, now, wrapup, init=False):
        if req == None:
            req, data = task.wakeup({'now': now})
        if req == REQUESTS.done:
            if init:
                # Entity is ready, start the update loop for it
                if not wrapup:
                    # Fire up the task to update the entity and the entity components
                    task1 = Task(task.entity, task.entity().update, parent=Task.getcurrent())
                    req1, data1 = task1.wakeup({'now': now})
                    task2 = Task(task.entity, task.entity()._update, parent=Task.getcurrent())
                    req2, data2 = task2.wakeup({'now': now})
                    self.running[task.entity] = (task1, req, data1,task2, req2, data2)
                    return (None,None,None)
            else:
                if wrapup:
                    return None,None,None
                else:
                    # Restart the update loop
                    task = Task(task.entity, task.runnable, parent=Task.getcurrent())
                    req, data = task.wakeup({'now': now})
                    return (task, req, data)
        elif req == REQUESTS.skip:
            # Normal operation continues
            return (task, None, None)
        elif req == REQUESTS.stop:
            # Stop entity from updating
            return None,None,None
        elif req == REQUESTS.loadImage:
            # Load an image
            if data.has_key('url') and data['url'] != None:
                # Try to load an image
                img = self.dataManager.getImage(data['url'])
                if img == None:
                    return (task, req, data)
                else:
                    req, data = task.wakeup(img)
                    return (task, req, data)
            else:
                # URL is invalid, just keep going
                return (task, None, None)
#            elif req == REQUESTS.loadSprite:
#                # Load a sprite definition
#                if data.has_key('url') and data['url'] != None:
#                    # Try to load a sprite
#                    sprite = self.dataManager.getSprite(data['url'])
#                    if sprite == None:
#                        self.loading[entity_ref] = (task, req, data)
#                    else:
#                        req, data = task.wakeup(sprite)
#                        self.loading[entity_ref] = (task, req, data)
#                else:
#                    # URL is invalid, just keep going
#                    self.loading[entity_ref] = (task, None, None)
#            elif req == REQUESTS.nativeResolution:
#                # Set the native resolution of the scene for scaling purpouses
#                w,h, ar = data
#                self.renderer.setNativeResolution(w,h, ar)
#                self.loading[entity_ref] = (task, None, None)
#            elif req == REQUESTS.sceneSize:
#                # Set the size of the scene for scrolling purpouses
#                w,h = data
#                self.renderer.setSceneSize(w,h)
#                self.loading[entity_ref] = (task, None, None)

        else:
            # Unrecognized request
            return (task, None, None)

    def renderScene(self):
        # Render a new scene
        if not self._freezeRenderer:
            self.renderer.update()

    def refreshEntityZ(self, entity):
        """ Change the entity's z index ordering """
        # Remove from the old z-index
        if entity.id in self.loading:
            return

        self.hideEntity(entity)
        # Add to the new z-index
        new_z = entity.z
        if new_z != None and 'viewable' in entity.tags:
            if not new_z in self.entitiesByZ:
                self.entitiesByZ[new_z] = weakref.WeakSet()
            self.entitiesByZ[new_z].add(entity)

    def hideEntity(self, entity):
        """ Check all the Z layers, remove the entity from it"""
        for z in self.entitiesByZ.keys():
            entities = self.entitiesByZ[z]
            if entity in entities:
                entities.remove(entity)
                if not entities:
                    del self.entitiesByZ[z]
                break

    def refreshEntityTags(self, entity, added_tags=[], removed_tags=[]):
        for tag in added_tags:
            if tag not in self.entitiesByTag:
                self.entitiesByTag[tag] = weakref.WeakSet()
            if entity not in self.entitiesByTag[tag]:
                self.entitiesByTag[tag].add(entity)

        for tag in removed_tags:
            if tag in self.entitiesByTag:
                if entity in self.entitiesByTag[tag]:
                    self.entitiesByTag[tag].remove(entity)

    def reportEvent(self, event):
        """ Propagate an event through the entities """
        # Do some event mapping/discarding
        if event.type == Event.TYPE._mousedown or event.type == Event.TYPE._moztouchdown:
            event.type = Event.TYPE.touchdown
        elif event.type == Event.TYPE._mouseup or event.type == Event.TYPE._moztouchup:
            event.type = Event.TYPE.touchup
        elif event.type == Event.TYPE._mousemove or event.type == Event.TYPE._moztouchmove:
            event.type = Event.TYPE.touchmove

        continuePropagation = True
        captureEvent = False
   
        if not event.ethereal and event.x != None and event.y != None:
            # See if we have a deltax,deltay
            if event.deltax == None or event.deltay == None:
                if event.stream in self._touches:
                    lastTouch = self._touches[event.stream]
                    event.deltax = event.x - lastTouch.x
                    event.deltay = event.y - lastTouch.y

            # Walk the entities, see if the event matches one of them and inform it of the event
#            scale_x, scale_y = self.renderer.scale
#            # Scroll is in scene coordinates
#            scroll_x, scroll_y = self.renderer.scroll
            
            event.scene_x, event.scene_y = self.renderer.screenToScene(event.x, event.y)
            self._lastEvent = event

            if not self._touchCaptured:
                zindexs = self.entitiesByZ.keys()
                if len(zindexs) >0:
                    zindexs.sort(reverse=True)
                for z in zindexs:
                    if not continuePropagation:
                        break
                    for entity in self.entitiesByZ[z]:
                        continuePropagation, captureEvent = entity.event(event)
                        if captureEvent:
                            self._touchCaptor = entity
                            self._touchCaptured = True
                        if not continuePropagation:
                            break
            elif self._touchCaptor is not None:
                continuePropagation, captureEvent = self._touchCaptor.event(event)
                if not captureEvent:
                    self._touchCaptured = False
                    self._touchCaptor = None

            if continuePropagation and self._touchCaptor == None:
                if event.deltax != None and event.deltay != None and event.type != Event.TYPE.touchdown:
                    if self.scene and self.scene.userCanScroll and event.stream == 0 and event.stream in self._touches and len(self._touches)==1:
                        # Handle scrolling
                        self.renderer.scrollBy(event.deltax, event.deltay)
                        self._touchCaptured = True
                        self._touchCaptor = None

                    if self.scene and self.scene.userCanZoom and len(self._touches) == 2 and (event.stream == 0 or event.stream == 1) and 0 in self._touches and 1 in self._touches:
                        # Handle zooming
                        prevArea = (self._touches[0].x-self._touches[1].x)**2 + (self._touches[0].y-self._touches[1].y)**2
                        if event.stream == 0:
                            prevTouch = self._touches[1]
                        else:
                            prevTouch = self._touches[0]

                        currArea = (event.x-prevTouch.x)**2 +(event.y-prevTouch.y)**2
                        zoomCenterX = (event.x + prevTouch.x)/2
                        zoomCenterY = (event.y + prevTouch.y)/2
                        cx,cy = self.renderer.screenToScene(zoomCenterX, zoomCenterY)
                        self.renderer.scaleBy(currArea-prevArea)
                        sx,sy = self.renderer.sceneToScreen(cx,cy)

                        self.renderer.scrollBy(zoomCenterX-sx, zoomCenterY-sy)
                        self._touchCaptured = True
                        self._touchCaptor = None

            if event.type == Event.TYPE.touchup:
                # Forget about this stream as the user lift the finger/mouse button
                self._resetStream(event.stream)
                self._touchCaptured = False
                self._touchCaptor = None
            elif event.type == Event.TYPE.touchdown or event.stream in self._touches:   # Don't store touchmove events because in a pointer based platform this gives you scrolling with no mouse button pressed
                    # Save the last touch event for the stream
                    self._storeEvent(event)
            
        elif event.ethereal:
            # Send the event to all entity until something stops it
            zindexs = self.entitiesByZ.keys()
            if len(zindexs) >0:
                zindexs.sort(reverse=True)
            for z in zindexs:
                if not continuePropagation:
                    break
                for entity in self.entitiesByZ[z]:
                    continuePropagation, captureEvent = entity.event(event)
                    if captureEvent:
                        self._touchCaptor = entity
                        self._touchCaptured = True
                    if not continuePropagation:
                        break

            if continuePropagation:
                if self.scene and self.scene.userCanZoom:
                    if event.type == Event.TYPE.zoomin:
                        if self._lastEvent:
                            cx,cy = self.renderer.screenToScene(self._lastEvent.x, self._lastEvent.y)
                        self.renderer.scaleByFactor(1.2)
                        if self._lastEvent:
                            sx,sy = self.renderer.sceneToScreen(cx,cy)
                            self.renderer.scrollBy(self._lastEvent.x-sx, self._lastEvent.y-sy)
                    elif event.type == Event.TYPE.zoomout:
                        if self._lastEvent:
                            cx,cy = self.renderer.screenToScene(self._lastEvent.x, self._lastEvent.y)
                        self.renderer.scaleByFactor(0.8)
                        if self._lastEvent:
                            sx,sy = self.renderer.sceneToScreen(cx,cy)
                            self.renderer.scrollBy(self._lastEvent.x-sx, self._lastEvent.y-sy)
                    
    def _storeEvent(self, event):
        """ Store a touch/mouse event for a stream, to be used for future reference"""
        self._touches[event.stream] = event

    def _resetStream(self, stream):
        """ Reset the last stored event for the stream"""
        if stream in self._touches:
            del self._touches[stream]

    def saveState(self):
        """ Serialize the current status of the engine """
        debug('Waiting for entities to finish loading before saving state')
        tries = 0
        while self.loading:
            self.update()
            tries += 1
            if tries > 100:
                debug('Still waiting for loading entities: %s' % self.loading)
                tries = 0


        #f = open('ignifuga.state', 'w')
        #state = GilbertPickler(f, -1).dump(self.nodes)
        #f.close()

    def loadState(self):
        pass
        # TODO!
#        try:
#            if os.path.isfile('ignifuga.state'):
#                f = open('ignifuga.state', 'r')
#                self.nodes = pickle.load(f)
#                f.close()
#
#                for node in self.nodes:
#                    task = Task(weakref.ref(node), node.init, parent=Task.getcurrent())
#                    self.loading.append((task, None, None))
#
#                return True
#            else:
#                return False
#        except:
#            return False

    def loadScenes(self, data):
        """ Load scenes from a dictionary like structure. The data format is...
        """
        if not isinstance(data, dict):
            return False

        # As scene data may be cached or still referenced when the loop ends,
        # we iterate over a deepcopy of it to avoid a reference circle with entities
        # that prevents them from being garbage collected
        for scene_id, scene_data in copy.deepcopy(data).iteritems():
            self.loadScene(scene_id, scene_data)

    def loadScene(self, scene_id, scene_data):
        scene = Scene(id=scene_id, **scene_data)
        self.scenes[scene_id] = scene

    def startScene(self, scene_id):
        if scene_id in self.scenes:
            self.scene = self.scenes[scene_id]
            self.entities = self.scene.entities
            self.scene.init()
            for entity in self.entities.itervalues():
                self.startEntity(entity)

            return True

        return False

    def startFirstScene(self):
        if not self.changeScene(self._firstScene):
            error('Error loading first scene: %s' % self._firstScene)

    def resetScenes(self):
        """ Reset all scene, garbage collect, get ready to leave! """
#        for scene_id in self.scenes.iterkeys():
#            self.resetScene(scene_id)

        self.resetScene()
        self.scenes = {}
        # Clean up cache
        self.dataManager.cleanup()
        gc.collect()

    def resetScene(self):
        """ Reset all the scene information """
        # Make sure all entities finished loading and running
        debug('Waiting for entities to finish loading/running')
        tries = 0
        self._freezeRenderer = True
        while self.loading or self.running:
            self.update(wrapup=True)
            tries += 1
            if tries > 100:
                debug('Still waiting for loading entities: %s' % self.loading)
                debug('Still waiting for running entities: %s' % self.running)
                tries = 0


        for entity in self.entities.values():
            # Forget about the entity and release data
            entity.unregister()

        del self.entities
        del self.scene
        del self.entitiesByZ
        del self.entitiesByTag
        del self.loading
        del self.running

        # Really remove nodes and data
        gc.collect()

        self.scene = None
        self.entities = {}
        self.entitiesByZ = {}
        self.entitiesByTag = {}
        self.loading = {}
        self.running = {}

        # Clean up cache
        # Do not clean the cache here, there may be useful data for other scenes -> self.dataManager.cleanup()
        gc.collect()

    def changeScene(self, scene_id):
        debug("Switching scene to: %s " % scene_id)
        self.resetScene()
        self.renderer.scrollTo(0,0)
        return self.startScene(scene_id)

    def startEntity(self, entity):
        # Add it to the loading queue
        wr = weakref.ref(entity)
        task = Task(wr, entity.init, parent=Task.getcurrent())
        self.loading[wr] = (task, None, None)
        entity.loading = True

    def stopEntity(self, entity):
        """ Remove node, release its data """

        # Add it to the loading queue
        wr = weakref.ref(entity)
        if wr in self.loading:
            del self.loading[wr]

        self.hideEntity(entity)
        self.refreshEntityTags(entity, [], entity.tags)

        if wr in self.running:
            del self.running[wr]


    def getEmbedded(self, url):
        url = str(url)
        if url in EMBEDDED_IMAGES:
            return base64.b64decode(EMBEDDED_IMAGES[url])

        return None


# Gilbert imports
from Renderer import Renderer as _Renderer
from Log import Log
from Entity import Entity
from components import Component
from Scene import Scene