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
# Main Singleton
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.Rect import Rect
from ignifuga.Singleton import Singleton
from ignifuga.Log import *
import sys, pickle, os, weakref, gc

class BACKENDS:
    sdl = 'sdl'
    
class REQUESTS:
    loadImage = 'loadImage'
    loadSprite = 'loadSprite'
    dirtyRects = 'dirtyRects'
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
        
    ETHEREALS = [TYPE.accelerometer, TYPE.compass, TYPE.focus, TYPE.blur, TYPE.zoomin, TYPE.zoomout]
        
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

def Renderer():
    return Gilbert().renderer

def Canvas():
    return _Canvas

# Dynamic imported modules (they are set up depending on the backend)
GameLoop = None
DataManager = None
_Canvas = None
Target = None

def sanitizeData (k,v, p=True):
    key = str(k)
    if isinstance(v, dict):
        value = {}
        for k1, v1 in v.items():
            key1, value1 = sanitizeData(k1,v1)
            value[key1] = value1
    else:
        value = v

    return key, value

def createNode(parent, data, restore = None):
    """ Create node dynamically from given data
    
    data may be:
        {'type': nodetype, 'id': nodeid, 'position': 1.0, etc, etc} or
        { 'nodeid': {'type':nodetype, position: 1.0, etc,etc} }
    
    """
    if data.has_key('type'):
        type = data['type']
    elif len(data.keys())==1:
        id = data.keys()[0]
        data = data[id]
        data['id'] = id
        if data.has_key('type'):
            type = data['type']
        else:
            return None
    else:
        return None

    # Sanitize data, convert all the keys to strings
    nodeData = {}
    for k,v in data.items():
        key, value = sanitizeData(k,v)
        nodeData[key] = value
        

    node = None
    if type == 'Background':
        node = Background(parent, **nodeData)
    elif type == 'Scene':
        node = Scene(parent, **nodeData)
    elif type == 'SpriteNode':
        node = SpriteNode(parent, **nodeData)
    elif type == 'TextNode':
        node = TextNode(parent, **nodeData)
        
    if node != None:
        Gilbert().registerNode(node)

    return node

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
    
    def init(self, backend, scene):
        self.backend = backend
        debug ('Initializing Gilbert Overlord')
        
        # Set up dynamic imports
        global GameLoop
        global DataManager
        global _Canvas
        global Target
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

        # The only dictionary that keeps strong references to the nodes
        self.nodes = []
        # These dictionaries keep weakrefs via WeakSet
        self.nodesType = {}
        self.nodesZ = {}

        # These keep weakrefs via Task
        self.loading = []
        self.running = {}

        self._touches = {}
        self._touchCaptured = False
        self._touchCaptor = None

        
        self.renderer = _Renderer(Target())
        self.dataManager = DataManager()
        self.resetScene()
        if not self.loadState():
            debug('Failed loading previous state')
            self.dataManager.loadScene(scene)
        self.startLoop()
        # Nothing after this will get executed until the engine exits

    def startLoop(self):
        """Set up the game loop"""
        self.gameLoop = GameLoop()
        self.gameLoop.run()

        # Engine is exiting from here onwards

        debug('Saving state')
        #self.saveState()

        # Release all data
        if self.backend == BACKENDS.sdl:
            debug('Terminating backend %s' % (self.backend,))
            from backends.sdl import terminateBackend

        self.resetScene()
        # DEBUG - See what's holding on to what
        objs = gc.get_objects()
        for n in objs:
            if isinstance(n, Node):
                print 'NODE: ', n
                for ref in gc.get_referrers(n):
                    if ref != objs:
                        print '    REFERRER: ', ref.__class__, id(ref)
                        if isinstance(ref, dict):
                            print "    DICT: ", ref.keys()
                        elif isinstance(ref, list):
                            print "    LIST: ", len(ref), " items"
                        elif isinstance(ref, tuple):
                            print "    TUPLE: ", ref
                        else:
                            print "    INSTANCEMETHOD: ", ref.__name__
        self.dataManager.cleanup(True)
        terminateBackend()

        
    def endLoop(self):
        """ End the game loop, free stuff """
        self.gameLoop.quit = True

    def update(self, now=0, wrapup=False):
        """ Update everything, then render the scene
        now is the current time, specified in seconds
        wrapup = True forces the update loop to be broken, all running nodes eventually stop running
        """
        # Call the pre update so we can tally how long the whole frame processing took (logic+render)
        self.renderer.preUpdate(now)
        
        # Initialize objects
        loading_count = len(self.loading)
        lc = 0
        
        while lc < loading_count:
            task, req, data = self.loading.pop(0)
            if req == None:
                req,data = task.wakeup()
                
            if req == REQUESTS.done:
                # Node is ready, start the update loop for it
                node = data
                
                # Add it to the by type index
                nodetype = node.getType()
                if not self.nodesType.has_key(nodetype):
                    self.nodesType[nodetype] = weakref.WeakSet()
                self.nodesType[nodetype].add(node)
                #print node.save()
                # Add it to the by z ordering index
                zindex = node.z
                if zindex != None:
                    if not self.nodesZ.has_key(zindex):
                        self.nodesZ[zindex] = weakref.WeakSet()
                    if node not in self.nodesZ[zindex]:
                        self.nodesZ[zindex].add(node)
                if not wrapup:
                    # Fire up the task to update the node
                    task = Task(weakref.ref(node), node.update, parent=Task.getcurrent())
                    req, data = task.wakeup({'now': now})
                    self.running[node] = (task, req, data)

            elif req == REQUESTS.skip:
                # Just skip this turn
                self.loading.append((task, None, None))
            elif req == REQUESTS.loadImage:
                # Load an image
                if data.has_key('url') and data['url'] != None:
                    # Try to load an image
                    img = self.dataManager.getImage(data['url'])
                    if img == None:
                        self.loading.append((task, req, data))
                    else:
                        req, data = task.wakeup(img)
                        self.loading.append((task, req, data))
                else:
                    # URL is invalid, just keep going
                    self.loading.append((task, None, None))
            elif req == REQUESTS.loadSprite:
                # Load a sprite definition
                if data.has_key('url') and data['url'] != None:
                    # Try to load a sprite
                    sprite = self.dataManager.getSprite(data['url'])
                    if sprite == None:
                        self.loading.append((task, req, data))
                    else:
                        req, data = task.wakeup(sprite)
                        self.loading.append((task, req, data))
                else:
                    # URL is invalid, just keep going
                    self.loading.append((task, None, None))
            elif req == REQUESTS.nativeResolution:
                # Set the native resolution of the scene for scaling purpouses
                w,h, ar = data
                self.renderer.setNativeResolution(w,h, ar)
                self.loading.append((task, None, None))
            elif req == REQUESTS.sceneSize:
                # Set the size of the scene for scrolling purpouses
                w,h = data
                self.renderer.setSceneSize(w,h)
                self.loading.append((task, None, None))
            else:
                # Unrecognized request
                self.loading.append((task, None, None))
            
            lc+=1
        
        # Update objects
        for node in self.running.keys():
            task, req, data = self.running[node]
            if req == None:
                req, data = task.wakeup({'now': now})
            
            if req == REQUESTS.done:
                if wrapup:
                    del self.running[node]
                else:
                    # Restart the update loop
                    task = Task(weakref.ref(node), node.update, parent=Task.getcurrent())
                    req, data = task.wakeup({'now': now})
                    self.running[node] = (task, req, data)
            elif req == REQUESTS.skip:
                # Normal operation continues
                self.running[node] = (task, None, None)
            elif req == REQUESTS.stop:
                # Stop node from updating
                del self.running[node]
            elif req == REQUESTS.dirtyRects:
                if data != None:
                    # data is a ((x,y,w,h),(x,y,w,h), ...) list of rects in node coordinates
                    # Translate the dirty rectangle to scene coords position
                    if self.renderer.needsRects:
                        pos = node.position
                        for box in data:
                            self.renderer.dirty(box[0]+pos[0], box[1]+pos[1], box[2], box[3])
                self.running[node] = (task, None, None)

    def renderScene(self):
        # Render a new scene
        self.renderer.update()
        
    def registerNode(self, node):
        # Keep ONE strong reference to the node so it's not garbage collected
        self.nodes.append(node)

        # Add it to the loading queue
        task = Task(weakref.ref(node), node.init, parent=Task.getcurrent())
        self.loading.append((task, None, None))
    
    def unregisterNode(self, node):
        """ Remove node, release its data """

        # Add it to the loading queue
        if node in self.loading:
            self.loading.remove(node)
        
        node_type = node.getType()
        if node_type in self.nodesType and node in self.nodesType[node_type]:
            self.nodesType[node_type].remove(node)

        zindex = node.z
        if zindex != None and zindex in self.nodesZ and node in self.nodesZ[zindex]:
            self.nodesZ[node.z].remove(node)
        
        if node in self.running:
            del self.running[node]

        # Remove the strong reference
        if node in self.nodes:
            self.nodes.remove(node)
        else:
            debug('Tried to unregister node %s, but Gilbert didnt know about it in the first place' % node)

        #node.free()

    def changeZ(self, node, new_z):
        """ Change the node's z index ordering """
        if node in self.loading:
            return
            
        zindex = node.z
        # Remove from the old z-index
        if zindex != None and zindex in self.nodesZ and node in self.nodesZ[zindex]:
            self.nodesZ[node.z].remove(node)
           
        # Add to the new z-index
        if new_z != None:
            if not new_z in self.nodesZ:
                self.nodesZ[new_z] = weakref.WeakSet()
            self.nodesZ[new_z].add(node)

    def reportEvent(self, event):
        """ Propagate an event through the nodes """
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

            # Walk the nodes, see if the event matches one of them and inform it of the event
            scale_x, scale_y = self.renderer.scale
            # Scroll is in scene coordinates
            scroll_x, scroll_y = self.renderer.scroll
            
            x = int(event.x/scale_x) + scroll_x
            y = int(event.y/scale_y) + scroll_y
            
            if not self._touchCaptured:
                zindexs = self.nodesZ.keys()
                if len(zindexs) >0:
                    zindexs.sort(reverse=True)
                for z in zindexs:
                    if not continuePropagation:
                        break
                    for node in self.nodesZ[z]:
                        if node.hits(x, y):
                            continuePropagation, captureEvent = node.event(event)
                            if captureEvent:
                                self._touchCaptor = node
                                self._touchCaptured = True
                            if not continuePropagation:
                                break
            elif self._touchCaptor != None:
                continuePropagation, captureEvent = self._touchCaptor.event(event)
                if not captureEvent:
                    self._touchCaptured = False
                    self._touchCaptor = None

            if continuePropagation and self._touchCaptor == None:
                if event.deltax != None and event.deltay != None and event.type != Event.TYPE.touchdown:
                    if event.stream == 0 and event.stream in self._touches and len(self._touches)==1:
                        # Handle scrolling
                        self.renderer.scrollBy(event.deltax, event.deltay)
                        self._touchCaptured = True
                        self._touchCaptor = None

                    if len(self._touches) == 2 and (event.stream == 0 or event.stream == 1) and 0 in self._touches and 1 in self._touches:
                        # Handle zooming
                        prevArea = (self._touches[0].x-self._touches[1].x)**2 + (self._touches[0].y-self._touches[1].y)**2
                        if event.stream == 0:
                            currArea = (event.x-self._touches[1].x)**2 + (event.y-self._touches[1].y)**2
                        else:
                            currArea = (self._touches[0].x-event.x)**2 + (self._touches[0].y-event.y)**2
                        self.renderer.scaleBy(currArea-prevArea)
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
            # Send the event to all nodes until something stops it
            zindexs = self.nodesZ.keys()
            if len(zindexs) >0:
                zindexs.sort(reverse=True)
            for z in zindexs:
                if not continuePropagation:
                    break
                for node in self.nodesZ[z]:
                    continuePropagation, captureEvent = node.event(event)
                    if captureEvent:
                        self._touchCaptor = node
                        self._touchCaptured = True
                    if not continuePropagation:
                        break

            if continuePropagation:
                if event.type == Event.TYPE.zoomin:
                    self.renderer.scaleByFactor(1.2)
                elif event.type == Event.TYPE.zoomout:
                    self.renderer.scaleByFactor(0.8)
                    
    def resetScene(self):
        """ Reset all the scene information """
        # Make sure all nodes finished loading and running
        debug('Waiting for nodes to finish loading/running')
        tries = 0
        while self.loading or self.running:
            self.update(wrapup=True)
            tries += 1
            if tries > 100:
                debug('Still waiting for loading nodes: %s' % self.loading)
                debug('Still waiting for running nodes: %s' % self.running)
                tries = 0

        # Get rid of dirty rects
        #self.renderer.dirtyAll()

        nodes = self.nodes[:]
        for node in nodes:
            # Remove takes the node out of self.nodes and frees the data
            node.remove()

        del nodes
        del self.nodes
        del self.nodesZ
        del self.nodesType
        del self.loading
        del self.running

        # Really remove nodes and data
        gc.collect()
        # Clean up cache
        self.dataManager.cleanup()
        gc.collect()

        self.nodes = []
        self.nodesType = {}
        self.nodesZ = {}
        self.loading = []
        self.running = {}

    def _storeEvent(self, event):
        """ Store a touch/mouse event for a stream, to be used for future reference"""
        self._touches[event.stream] = event

    def _resetStream(self, stream):
        """ Reset the last stored event for the stream"""
        if stream in self._touches:
            del self._touches[stream]

    def saveState(self):
        """ Serialize the current status of the engine """
        debug('Waiting for nodes to finish loading before saving state')
        tries = 0
        while self.loading:
            self.update()
            tries += 1
            if tries > 100:
                debug('Still waiting for loading nodes: %s' % self.loading)
                tries = 0


        f = open('ignifuga.state', 'w')
        state = GilbertPickler(f, -1).dump(self.nodesType)
        f.close()

    def loadState(self):
        try:
            if os.path.isfile('ignifuga.state'):
                f = open('ignifuga.state', 'r')
                nodesType = pickle.load(f)
                f.close()

                for nodeType, nodes in nodesType.iteritems():
                    for node in nodes:
                        task = Task(weakref.ref(node), node.init, parent=Task.getcurrent())
                        self.loading.append((task, None, None))

                return True
            else:
                return False
        except:
            return False
        

# Gilbert imports
from Renderer import Renderer as _Renderer
from Log import Log

# Nodes
from Background import Background
from Scene import Scene
from SpriteNode import SpriteNode
from TextNode import TextNode
from Node import Node