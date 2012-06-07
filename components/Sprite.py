#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Ignifuga Game Engine
# Sprite component
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from Viewable import Viewable
from ignifuga.Gilbert import REQUESTS
from ignifuga.Task import *
from ignifuga.Gilbert import Gilbert
import sys

from ignifuga.Gilbert import Renderer, Canvas
try:
    # Embedded version - Some hacking required
    from _bitarray import _bitarray
    class bitarray(_bitarray):
        pass
except:
    from bitarray import bitarray

from base64 import b64decode
#from zlib import decompress
from ignifuga.Rect import Rect
from ignifuga.Log import error
import sys


class Sprite(Viewable):
    """ Sprite component class, viewable, potentially animated
    """
    PROPERTIES = Viewable.PROPERTIES + ['frame', 'frameCount', 'forward', 'blur']
    def __init__(self, id=None, entity=None, active=True, frequency=15.0, loop=-1, **data):

        # Default values
        self._loadDefaults({
            'file': None,
            '_spriteData': None,
            '_atlas': None,
            '_canvas': None,
            'sprite': None,
            'loopMax': loop if loop >= 0 else None,
            'loop': 0,
            'onStart': None,
            'onLoop': None,
            'onStop': None,
            'remainActiveOnStop': False,
            'forward': True,
            '_blur': 0.0,
            '_canvasBlur': None
            })

        super(Sprite, self).__init__(id, entity, active, frequency, **data)

        self._started = True

    def init(self, **data):
        """ Initialize the required external data """
        # Do our initialization
        if self.file != None:
            self._atlas = LOAD_IMAGE(self.file)
            if self._atlas.spriteData != None:
                self._spriteData = self._atlas.spriteData
                self.sprite = _Sprite(self._spriteData, self._atlas, self.frequency)
                self._updateColorModulation()
                if not self.forward:
                    self.sprite.frame = self.sprite.frameCount - 1
            else:
                self.sprite = None
        self._updateColorModulation()

        self._updateSize()
        super(Sprite, self).init(**data)

    def update(self, **data):
        """ Initialize the required external data """
        super(Sprite, self).update(**data)
        if self.sprite != None:
            if self.sprite.frame == 0 and self.loop == 0 and not self._started:
                self._started = True
                self.run(self.onStart)

            if self.loopMax == None or self.loop < self.loopMax:
                if self.forward:
                    if self.sprite.nextFrame():
                        if self.sprite.frame == 0:
                            self.loop +=1
                            self.run(self.onLoop)
                        if self.loop == self.loopMax:
                            self.run(self.onStop)
                            if not self.remainActiveOnStop:
                                self.active = False
                                self.loop = 0
                                self.frame = 0
                        if self._blur > 0:
                            self._doBluring()
                else:
                    if self.sprite.prevFrame():
                        if self.sprite.frame == self.sprite.frameCount - 1:
                            self.loop +=1
                            self.run(self.onLoop)
                        if self.loop == self.loopMax:
                            self.run(self.onStop)
                            if not self.remainActiveOnStop:
                                self.active = False
                                self.loop = 0
                                self.frame = self.sprite.frameCount - 1
                        if self._blur > 0:
                            self._doBluring()
        elif self._blur > 0 and self._blur != self._canvasBlur:
            self._doBluring()

    def _updateSize(self):
        # Update our "public" width,height
        if self._width != None:
            self._width_pre = self._width
        elif self._spriteData != None:
            self._width_pre = self.sprite.width
        elif self._atlas != None:
            self._width_pre = self._atlas.width
        else:
            self._width_pre = 0

        if self._height != None:
            self._height_pre = self._height
        elif self._spriteData != None:
            self._height_pre = self.sprite.height
        elif self._atlas != None:
            self._height_pre = self._atlas.height
        else:
            self._height_pre = 0

        if self.zscale != None:
            self._width_pre = self.width * (1.0 + self._z*self.zscale)
            self._height_pre = self.height * (1.0 + self._z*self.zscale)

        if self._spriteData != None:
            self._width_src = self.sprite.width
        elif self._atlas != None:
            self._width_src = self._atlas.width

        if self._spriteData != None:
            self._height_src = self.sprite.height
        elif self._atlas != None:
            self._height_src = self._atlas.height

    # The current full image frame (not the animation atlas, but the consolidated final viewable image)
    @property
    def canvas(self):
        if self._canvas != None:
            return self._canvas
        elif self.sprite != None:
            return self.sprite.canvas
        elif self._atlas != None:
            return self._atlas
        else:
            return None

    @Viewable.red.setter
    def red(self, value):
        Viewable.red.fset(self,value)
        self._updateColorModulation()

    @Viewable.green.setter
    def green(self, value):
        Viewable.green.fset(self,value)
        self._updateColorModulation()

    @Viewable.blue.setter
    def blue(self, value):
        Viewable.blue.fset(self,value)
        self._updateColorModulation()

    @Viewable.alpha.setter
    def alpha(self, value):
        Viewable.alpha.fset(self,value)
        self._updateColorModulation()

    @property
    def frame(self):
        return self.sprite.frame if self.sprite != None else 1

    @frame.setter
    def frame(self, frame):
        if self.sprite != None:
            self.sprite.frame = frame
            if frame == 0:
                self._started = False
    @property
    def blur(self):
        return self._blur

    @blur.setter
    def blur(self, value):
        """ Set the blur amount, this is actually an integer value that equals the pixel displacement used to simulate bluring"""
        if value <= 0:
            # Remove the temporal canvas
            self._canvas = None
            self._canvasBlur = None
            value = 0
        else:
            # Create a temporal canvas
            value = int(value)
        self._blur = value

    def _doBluring(self):
        """ Take the current canvas and "blur it" by doing a few blits out of center"""
        if self._blur > 0:
            if self._canvas is None:
                self._canvas = Canvas()(self._width_pre,self._height_pre, isRenderTarget = True)

            # Determine the source for the bluring
            if self.sprite is not None:
                source = self.sprite.canvas
            elif self._atlas is not None:
                source = self._atlas
            else:
                return

            source.mod(1.0,1.0,1.0,1.0)
            self._canvas.blitCanvas(source, 0, 0, self._canvas.width, self._canvas.height, 0,0,self._canvas.width,self._canvas.height, self._canvas.BLENDMODE_NONE)
            source.mod(1.0,1.0,1.0,0.2)
            b = int (self._blur / 2)
            w = self._canvas.width-b
            h = self._canvas.height-b
            self._canvas.blitCanvas(source,0,0,w,h,b,b,w,h, self._canvas.BLENDMODE_BLEND)
            self._canvas.blitCanvas(source,b, b, w, h, 0,0,w,h, self._canvas.BLENDMODE_BLEND)
            self._canvas.blitCanvas(source,0,b,w,h,b,0,w,h, self._canvas.BLENDMODE_BLEND)
            self._canvas.blitCanvas(source,b,0,w,h,0,b,w,h, self._canvas.BLENDMODE_BLEND)
            b = self._blur
            w = self._canvas.width-b
            h = self._canvas.height-b
            source.mod(1.0,1.0,1.0,0.1)
            self._canvas.blitCanvas(source,0,0,w,h,b,b,w,h, self._canvas.BLENDMODE_BLEND)
            self._canvas.blitCanvas(source,b, b, w, h, 0,0,w,h, self._canvas.BLENDMODE_BLEND)
            self._canvas.blitCanvas(source,0,b,w,h,b,0,w,h, self._canvas.BLENDMODE_BLEND)
            self._canvas.blitCanvas(source,b,0,w,h,0,b,w,h, self._canvas.BLENDMODE_BLEND)
            # Up the alpha to 1.0
            source.mod(0.0,0.0,0.0,1.0)
            self._canvas.blitCanvas(source, 0, 0, self._canvas.width, self._canvas.height, 0,0,self._canvas.width,self._canvas.height, self._canvas.BLENDMODE_ADD)

            source.mod(self._red, self._green, self._blue, self._alpha)
            self._updateColorModulation()

            # Preserve the value used for bluring to save time in case it's not modified for the next cycle
            self._canvasBlur = self._blur

    @property
    def frameCount(self):
        return self.sprite.frameCount if self.sprite != None else 1

    def _updateColorModulation(self):
        if self.canvas != None:
            self.canvas.mod(self._red, self._green, self._blue, self._alpha)

    def getRenderArea(self):
        return [0, 0, self._width_src, self._height_src, self.x, self.y, self.width, self.height]

    def hits(self, x, y):
        """ x,y are in sprite coords"""
        if self.interactive and x>=0 and x <= self._width_src and y >= 0 and y <= self._height_src:
            # Check if the point on the sprite is visible
            if self.sprite != None:
                return self.sprite.hits(x,y)
            return True
        return False


    def __getstate__(self):
        odict = self.__dict__.copy()
        # Remove non pickable elements
        del odict['sprite']
        del odict['_atlas']
        del odict['_spriteData']
        return odict

class _Sprite(object):
    """ Internal sprite implementation with animation"""
    def __init__(self, data, srcCanvas, rate=30):
        """ Data format is:

        {
            type: atlas -> Each frame is a full frame (1 box per frame, all boxes are of the size of the first frame, every frame is a keyframe)
                  deltap -> First frame is full, the rest are the difference boxes with the prior frame (it can include one or more keyframes)
                  NO LONGER SUPPORTED: deltak -> First frame is full, and every frame mentioned in "keyframes" is a full frame as well. The rest are difference boxes against the last keyframe.

            keyframes: [0, ...] -> Keyframes (if type=atlas every frame is a keyframe)
            frames:
        [ /*Frames*/
            [/* Frame: contains changed boxes*/
                [/* Changed box*/
                    src_x, src_y, dst_x, dst_y, w,h
                ],
                [/* Changed box*/
                    src_x, src_y, dst_x, dst_y, w,h
                ],
                ...
            ],
            ...
        ],
        hitmap:
        [
            [ 101010101010 hitmap for frame 0],
            [ 101010101010 hitmap for frame 1],
            etc
        ]

        }

        src means the big sprite image
        dst means the destination animated sprite
        """

        self._frameCount = len(data['frames']) if 'frames' in data else 0
        self._frame = 0
        self._width = None
        self._height = None
        self._type = data['type'] if 'type' in data else 'atlas'
        self._keyframes = data['keyframes'] if 'keyframes' in data else [0,]
        self._frames = data['frames'] if 'frames' in data else []
        if 'hitmap' in data:
            self._hitmap = []
            for frameHitmap in data['hitmap']:
                hitmap = bitarray()
                #hitmap.fromstring(decompress(b64decode(frameHitmap)))
                hitmap.fromstring(b64decode(frameHitmap))
                self._hitmap.append(hitmap)
        else:
            self._hitmap = None

        self._rate = rate
        self._lapse = 1.0/self._rate
        self._lastUpdate = 0.0
        self._colormod = (1.0, 1.0, 1.0, 1.0)
        self.renderer = Renderer()

        # Get the w,h from the first frame which should be a full frame
        sx,sy,dx,dy,w,h = self._frames[0][0]
        # Frame width and height
        self._width = w
        self._height = h

        # Create the sprite canvas
        # We need two canvas, the source canvas and the "presentation" canvas
        self._canvas = Canvas()(w,h, isRenderTarget = True)
        self._srcCanvas = srcCanvas
        sx,sy,dx,dy,w,h = self._frames[0][0]
        self._canvas.blitCanvas(self._srcCanvas, dx, dy, w, h, sx, sy, w, h, self._canvas.BLENDMODE_NONE)
        self._precomputeFrameAreas()

    def nextFrame(self):
        """ Forward to next frame or restart loop"""
        if self.renderer.checkLapse(self._lastUpdate, self._lapse) and self._frameCount > 1:
            self._lastUpdate = self.renderer.getTimestamp()
            self._frame+=1
            if self._frame >= self._frameCount:
                self._frame=0

            # Consolidate the new sprite frame from _srcCanvas into _canvas
            for a in self._frames[self._frame]:
                sx,sy,dx,dy,w,h = a
                self._canvas.blitCanvas(self._srcCanvas, dx, dy, w, h, sx, sy, w, h, self._canvas.BLENDMODE_NONE)
            return True

        return False

    def prevFrame(self):
        """ Back to prev frame or restart loop"""
        if self.renderer.checkLapse(self._lastUpdate, self._lapse) and self._frameCount > 1:
            self._lastUpdate = self.renderer.getTimestamp()
            prevFrame = self.frame -1
            if prevFrame < 0:
                prevFrame=self._frameCount -1

            # Go back to the previous frame
            self.frame = prevFrame
            return True
        return False

    def getFrameAreas(self):
        """ Return a set of areas from the Atlas that need to be renderer to conform the current sprite frame.
        This stuff is precomputed in _precomputeFrameAreas

        areas = [
            [sx,sy,dx,dy,w,h]
            [sx,sy,dx,dy,w,h]
            [sx,sy,dx,dy,w,h]

            sx,sy -> source coordinates on the atlas
            dx,dy -> destination coordinates in frame coordinates (always based on a 0,0 origin)
            w,h -> width and height of the area
        ]
        """
        return self._areas[self._frame]

    def _precomputeFrameAreas(self):
        """ Organize the frame areas, see getFrameAreas for the format of the area array """
        lastKeyframe=0
        self._areas = {}
        for frame in range(0, self._frameCount):
            if self._type == 'atlas':
                # Every frame is a keyframe, one box per frame and that's it
                self._areas[frame] = [self._frames[frame][0],]
            elif self._type == 'deltap':
                # We consolidate the frame ourselves in each nextFrame()
                # So we report to the renderer *as if* every frame was a keyframe identical to the first frame
                self._areas[frame] = [self._frames[0][0],]

            elif self._type == 'deltak':
                if frame in self._keyframes:
                    # We are on a keyframe, we only need to pass this box
                    self._areas[frame] = [self._frames[frame][0],]
                    lastKeyframe = frame
                else:
                    # We have to pass the last keyframe box and the current one in a non overlapping way
                    keyframeareas = []
                    areas = []

                    # Append the keyframe areas
                    for diffbox in self._frames[lastKeyframe]:
                        keyframeareas.append(diffbox)

                    for diffbox in self._frames[frame]:
                        # Cut out the previous areas
                        dsx,dsy,ddx,ddy,dw,dh = diffbox

                        newareas = []
                        for a in keyframeareas:
                            sx,sy,dx,dy,w,h = a
                            r = Rect((dx,dy,w,h))
                            dr = Rect((ddx,ddy,dw,dh))
                            #print "intersecting ", r, " with ", dr, " results in ", r.cutout(dr)
                            for cr in r.cutout(dr):
                                newareas.append((cr.left-dx+sx, cr.top-dy+sy, cr.left, cr.top, cr.width, cr.height))

                        areas.append(diffbox)

                        keyframeareas = newareas

                    #print 'frame: ', frame
                    #print 'kf ', keyframeareas
                    #print 'a ', areas

                    self._areas[frame] = keyframeareas + areas

    @property
    def canvas(self):
        """ Return the Sprite's canvas, which is the "face" of the sprite"""
        return self._canvas

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def frame(self):
        return self._frame

    @frame.setter
    def frame(self, frame):
        if frame < self._frameCount:
            if self._type == 'atlas':
                sx,sy,dx,dy,w,h = self._frames[frame][0]
                self._canvas.blitCanvas(self._srcCanvas, dx, dy, w, h, sx, sy, w, h, self._canvas.BLENDMODE_NONE)
                self._frame = frame
            elif self._type == 'deltap':
                sx,sy,dx,dy,w,h = self._frames[0][0]
                self._canvas.blitCanvas(self._srcCanvas, dx, dy, w, h, sx, sy, w, h, self._canvas.BLENDMODE_NONE)
                for f in range(1,frame):
                    for a in self._frames[f]:
                        sx,sy,dx,dy,w,h = a
                        self._canvas.blitCanvas(self._srcCanvas, dx, dy, w, h, sx, sy, w, h, self._canvas.BLENDMODE_NONE)
                self._frame = frame



    @property
    def frameCount(self):
        return self._frameCount

    def hits(self, x, y):
        # Check if the sprite has a transparent point at x,y
        if y< 0 or y>self._height or x<0 or x>self._width:
            error('Tried to check %d,%d coords in a %d,%d sprite ' % (x,y, self._width, self._height))
            return False
        return self._hitmap[self._frame][int(y*self._width+x)] if self._hitmap != None else False

    @property
    def mod(self, colormod):
        return self._colormod

    @mod.setter
    def mod(self, colormod):
        """ Modulate the sprite canvas with (r,g,b,a)"""
        if len(colormod) != 4:
            return
        r,g,b,a = colormod

        self.setColorMod(r,g,b,a)

    def setColorMod(self, r,g,b,a):
        if self._canvas != None:
            self._canvas.mod(r,g,b,a)

