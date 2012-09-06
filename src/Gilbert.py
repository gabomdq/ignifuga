#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Ignifuga Game Engine
# Main Singleton
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

#from ignifuga.Rect import *
from ignifuga.Singleton import Singleton
from ignifuga.Log import *
import sys, pickle, os, weakref, gc, platform, copy, base64
from optparse import OptionParser
from ignifuga.rfoo import QueueInetServer, LOOPBACK
from ignifuga.rfoo.utils.rconsole import ConsoleHandler
import thread, socket

class BACKENDS:
    sdl = 'sdl'

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

def getRenderer():
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
    "autoScale": True,
    "autoCenter": True,
    "userCanScroll": False,
    "userCanZoom": False,
    "size": {
        "width": 3840,
        "height": 2400
    },
    "entities": {
        "splashimg": {
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
                    "onStop": "Gilbert.startFirstScene()"
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
Renderer = None

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
        self.remoteConsole = None
        usage = "game [options]"
        self.parser = OptionParser(usage=usage, version="Ignifuga Build Utility 1.0")
        self.parser.add_option("-d", "--display", dest="display", default=0,help="Display (default: 0)")
        self.parser.add_option("--width", dest="width", default=None,help="Resolution Width")
        self.parser.add_option("--height", dest="height", default=None,help="Resolution Height")
        self.parser.add_option("-w", "--windowed", action="store_true", dest="windowed", default=False,help="Start in windowed mode (default: no)")
        self.parser.add_option("-p", "--profile", action="store_true", dest="profile", default=False,help="Do a profile (ignored by the engine, useful for apps)")
        self.parser.add_option("-c", "--capture", action="store_true", dest="capture", default=False,help="Start paused (useful for video capture)")
        self.parser.add_option("-r", "--remote", action="store_true", dest="remote", default=False,help="Enable Remote Console (http://code.google.com/p/rfoo/)")
        self.parser.add_option("--staticglobals", action="store_true", dest="staticglobals", default=False,help="Dont update the remote console globals to match the current scene")
        self.parser.add_option("--port", dest="port", default=54321,help="Remote Console Port (default: 54321)")
        self.parser.add_option("--ip", dest="ip", default='0.0.0.0',help="Remote Console IP to bind to (default: 0.0.0.0)")

    
    def init(self, backend, firstScene, scenesFile=None):
        """
        backend: 'sdl'
        firstScene: The first scene ID (a string) in which case it'll be loaded from scenesFile or a Scene object
        scenesFile: A File where to load scenes from
        """
        self.backend = backend
        debug ('Initializing Gilbert Overlord')

        (options, args) = self.parser.parse_args()


        # Set up dynamic imports
        global GameLoop
        global DataManager
        global _Canvas
        global Renderer

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
            from backends.sdl.Renderer import Renderer as renderer
            initializeBackend()
            GameLoop = gameloop
            DataManager = datamanager
            _Canvas = canvas
            Renderer = renderer
            debug('Backend %s initialized' % (backend,))
        else:
            error('Unknown backend %s. Aborting' % (backend,))
            exit()

        # The only dictionaries that keeps strong references to the entities
        self.scenes = {}
        # A pointer to the current scene stored in self.scenes
        self.scene = None
        # These dictionaries keep weakrefs via WeakSet, contain the current scene entities
        self.entitiesByTag = {}

        self._touches = {}
        self._touchCaptured = False
        self._touchCaptor = None
        self._lastEvent = None

        self.renderer = Renderer(width=options.width, height=options.height, fullscreen= not options.windowed, display=options.display)
        self.dataManager = DataManager()

        if options.remote:
            self.startRemoteConsole(options.ip, options.port, options.staticglobals)
        self.gameLoop = GameLoop(remoteConsole = self.remoteConsole)

        if options.capture:
            print "System paused, press Enter to continue"
            ch = sys.stdin.read(1)

        if not self.loadState():
            debug('Failed loading previous state')
            if scenesFile is not None:
                self.loadScenesFromFile(scenesFile)

            if isinstance(firstScene, Scene):
                self.scenes[firstScene.id] = firstScene
                self._firstScene = firstScene.id
            else:
                self._firstScene = firstScene

########################################################################################################################
# SPLASH SCENE CODE
# ANY MODIFICATION OF THE SCENE DEFINITION AND RELATED CODE AND ARTWORK RENDERS THE LICENSE TO USE THIS ENGINE VOID.
########################################################################################################################
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
        self.gameLoop.run()

        # Engine is exiting from here onwards
        debug('Saving state')
        self.saveState()

        # Release all data
        if self.backend == BACKENDS.sdl:
            from backends.sdl import terminateBackend

        self.resetScenes()
        self.renderer.free()
        del self.renderer
        self.gameLoop.free()
        del self.gameLoop

        # DEBUG - See what's holding on to what
        gc.collect()
        debug("--------->GC REMNANTS<------------")
        objs = gc.get_objects()
        for n in objs:
            if isinstance(n, Entity) or isinstance(n,Component):
                debug ('=================================================================')
                debug ('%s: %s' % (n.__class__.__name__, n))
                referrers = gc.get_referrers(n)
                for ref in referrers:
                    if ref != objs and ref != referrers:
                        debug('    REFERRER: %s %s'  % (ref.__class__, id(ref)))
                        if isinstance(ref, dict):
                            debug("    DICT: %s" % ref)
                        elif isinstance(ref, list):
                            debug("    LIST: %s items" % len(ref))
                        elif isinstance(ref, tuple):
                            debug("    TUPLE: %s" % str(ref))
                            referrers1 = gc.get_referrers(ref)
                            debug("NUMBER OF REFERRERS", len(referrers1))
                            for ref1 in referrers1:
                                if ref1 != referrers and ref1 != objs:
                                    debug(ref1)

                            del referrers1
                        elif callable(ref):
                            debug("    INSTANCEMETHOD: %s %s" % (hash(ref), str(ref)))
                            referrers1 = gc.get_referrers(ref)
                            debug("NUMBER OF REFERRERS", len(referrers1))
                            for ref1 in referrers1:
                                if ref1 != referrers and ref1 != objs:
                                    debug(ref1)

                            del referrers1
                        else:
                            debug("    OTHER: %s" % str(ref))

                del referrers

                debug ('=================================================================')
                debug(' ')

        del objs
        self.dataManager.cleanup(True)
        # Break any remaining cycles that prevent garbage collection
        del self.dataManager
        debug('Terminating backend %s' % (self.backend,))
        terminateBackend()

    def endLoop(self):
        """ End the game loop, free stuff """
        self.gameLoop.quit = True

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


    def saveState(self):
        """ Serialize the current status of the engine """
        debug('Waiting for entities to finish loading before saving state')
        tries = 0
#        while self.loading:
#            self.update()
#            tries += 1
#            if tries > 100:
#                debug('Still waiting for loading entities: %s' % self.loading)
#                tries = 0


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

    def loadScenesFromFile(self, scenesFile):
        url, scenes = self.dataManager.loadSceneData(scenesFile)
        self.loadScenes(scenes, data_url=url)

    def loadScenes(self, scenes, data_url = None):
        """ Load scenes from a dictionary like structure. The data format is...
        """
        if not isinstance(scenes, dict):
            return False

        # As scene data may be cached or still referenced when the loop ends,
        # we iterate over a deepcopy of it to avoid a reference circle with entities
        # that prevents them from being garbage collected
        for scene_id, scene_data in copy.deepcopy(scenes).iteritems():
            self.loadScene(scene_id, scene_data, data_url)

    def loadScene(self, scene_id, scene_data, data_url = None):
        scene = Scene(id=scene_id, data_url = data_url, **scene_data)
        self.scenes[scene_id] = scene

    def startScene(self, scene_id):
        if scene_id in self.scenes:
            self.scene = self.scenes[scene_id]
            self.startEntity(self.scene)
            return True

        error("COULD NOT FIND SCENE %s" % scene_id)
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
        self.gameLoop.freezeRenderer = True

        if self.scene is not None:
            self.scene.reset()

        del self.scene
        del self.entitiesByTag

        # Really remove nodes and data
        gc.collect()
        self.scene = None
        self.entitiesByTag = {}

        # Clean up cache
        # Do not clean the cache here, there may be useful data for other scenes -> self.dataManager.cleanup()
        gc.collect()

        self.renderer.cleanup()

    def changeScene(self, scene_id):
        debug("Switching scene to: %s " % scene_id)
        self.resetScene()
        self.renderer.scrollTo(0,0)
        return self.startScene(scene_id)

    def startEntity(self, entity):
        # Add it to the loading queue
        self.gameLoop.startEntity(entity)

    def stopEntity(self, entity):
        """ Remove node, release its data """
        self.gameLoop.stopEntity(entity)


    def getEmbedded(self, url):
        url = str(url)
        if url in EMBEDDED_IMAGES:
            return base64.b64decode(EMBEDDED_IMAGES[url])

        return None

    def freezeRenderer(self):
        self.gameLoop.freezeRenderer = True

    def unfreezeRenderer(self):
        self.gameLoop.freezeRenderer = False

    def startRemoteConsole(self, ip='127.0.0.1', port=54321, staticglobals=False):
        debug("Enabling Remote Console on port %d" % port)
        self.remoteConsole = QueueInetServer(ConsoleHandler, globals(), staticglobals)

        def _wrapper():
            try:
                self.remoteConsole.start(ip, port)
            except socket.error:
                error('Failed to bind rconsole to socket port, port=%r.', port)

        thread.start_new_thread(_wrapper, ())


# Gilbert imports
from Entity import Entity
from components import Component
from Scene import Scene