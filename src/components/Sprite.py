#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Ignifuga Game Engine
# Sprite component
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from Viewable import Viewable
from ignifuga.Task import *
from ignifuga.Gilbert import Gilbert
import sys
from ignifuga.Gilbert import Renderer, Canvas
from ignifuga.backends.GameLoopBase import EVENT_TYPE_TOUCH_DOWN, EVENT_TYPE_TOUCH_UP, EVENT_TYPE_TOUCH_MOTION, EVENT_TYPE_TOUCH_LAST, EVENT_TYPE_ETHEREAL_ZOOM_IN, EVENT_TYPE_ETHEREAL_ZOOM_OUT, EVENT_TYPE_ETHEREAL_SCROLL

try:
    # Embedded version - Some hacking required
    from _bitarray import _bitarray
    class bitarray(_bitarray):
        pass
except:
    from bitarray import bitarray

from base64 import b64decode
#from zlib import decompress
from ignifuga.Rect import *
from ignifuga.Log import error
import sys


class Sprite(Viewable):
    """ Sprite component class, viewable, potentially animated
    """
    PROPERTIES = Viewable.PROPERTIES + ['frame', 'frameCount', 'forward', 'blur', 'overlays', 'addOverlay', 'removeOverlay', 'clearOverlays', 'updateRenderer']
    def __init__(self, id=None, entity=None, active=True, frequency=15.0, loop=-1, **data):

        # Default values
        self._loadDefaults({
            'file': None,
            '_spriteData': None,
            '_atlas': None,         # The "source" image where the sprite info comes from
            '_tmpcanvas': None,     # An internal canvas where we perform composition of overlays and do bluring
            '_canvas': None,        # A pointer to the external "face" of the sprite, it can point to self._atlas, self._tmpcanvas or self.sprite.canvas
            'sprite': None,
            'loopMax': loop if loop >= 0 else None,
            'loop': 0,
            'onStart': None,
            'onLoop': None,
            'onStop': None,
            'remainActiveOnStop': False,
            'forward': True,
            '_blur': 0.0,
            '_lastBlurAmount': None,
            '_overlays': {},
            '_rendererSpriteId': None,
            '_static': False,
            '_parent': None
            })

        super(Sprite, self).__init__(id, entity, active, frequency, **data)

        self._started = True
        self._dirty = True

    def init(self, **data):
        """ Initialize the required external data """
        # Do our initialization
        self.renderer = Gilbert().renderer
        if self.file != None:
            self._atlas = LOAD_IMAGE(self.file)
            Gilbert().dataManager.addListener(self.file, self)
            if self._atlas.spriteData != None:
                self._spriteData = self._atlas.spriteData
                self.sprite = _Sprite(self._spriteData, self._atlas, self.frequency)
                self._canvas = self.sprite.canvas
                if not self.forward:
                    self.sprite.frame = self.sprite.frameCount - 1
            else:
                self.sprite = None
                self._canvas = self._atlas
                self._static = True
        self._updateSize()

        self.show()
        super(Sprite, self).init(**data)

    def free(self, **kwargs):
        self.hide()
        self._tmpcanvas = None
        self._overlays = {}
        self.sprite = None
        self._canvas = None
        self._atlas = None
        self._spriteData = None
        Gilbert().dataManager.removeListener(self.file, self)
        super(Sprite, self).free(**kwargs)

    def update(self, now, **data):
        """ Initialize the required external data """
        super(Sprite, self).update(now, **data)

        if self._static:
            # This is a single image non animated sprite, we return with the STOP instruction so the update loop is not called
            STOP()
            return

        # Update overlayed sprites that are marked inactive as they won't be updated by the entity
        for overlay in self._overlays.itervalues():
            (id,x,y,op,_r,_g,_b,_a,sprite) = overlay
            if not sprite.active:
                sprite.update(now, **data)

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
                        if self._overlays or self._blur > 0:
                            self._doCompositing()
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
                        if self._overlays or self._blur > 0:
                            self._doCompositing()
        elif self._overlays or (self._blur > 0 and self._blur != self._lastBlurAmount):
            self._doCompositing()

        if self._dirty:
            self._updateRenderer()
            self._dirty = False

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

        self.updateRenderer()

    def _updateRenderer(self):
        if self._parent is not None:
            self._parent._doCompositing()
        elif self._rendererSpriteId:
            self.renderer.spriteDst(self._rendererSpriteId, self.x, self.y, self._width_pre, self._height_pre)

            self.renderer.spriteRot(self._rendererSpriteId,
            self._angle,
            self._center[0] if self._center != None else self._width_pre / 2,
            self._center[1] if self._center != None else self._height_pre / 2,
            (1 if self.fliph else 0) + (2 if self.flipv else 0))

            self.renderer.spriteColor(self._rendererSpriteId, self._red, self._green, self._blue, self._alpha)
            self._dirty = False

    def updateRenderer(self):
        if self._static:
            # No animation loop, directly update renderer
            self._updateRenderer()
        else:
            # Mark as dirty so we update on the next update
            self._dirty = True

    # The current composed full image frame (not the animation atlas, but the consolidated final viewable image)
    @property
    def canvas(self):
        return self._canvas

    @Viewable.red.setter
    def red(self, value):
        Viewable.red.fset(self,value)
        self.updateRenderer()

    @Viewable.green.setter
    def green(self, value):
        Viewable.green.fset(self,value)
        self.updateRenderer()

    @Viewable.blue.setter
    def blue(self, value):
        Viewable.blue.fset(self,value)
        self.updateRenderer()

    @Viewable.alpha.setter
    def alpha(self, value):
        #print "SETTING ALPHA", value
        Viewable.alpha.fset(self,value)
        self.updateRenderer()

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
            self._lastBlurAmount = None
            value = 0
        else:
            # Create a temporal canvas
            value = int(value)
        self._blur = value

        if self._static:
            self._doCompositing()

    @Viewable.x.setter
    def x(self, new_x):
        Viewable.x.fset(self, new_x)
        self.updateRenderer()

    @Viewable.y.setter
    def y(self, new_y):
        Viewable.y.fset(self, new_y)
        self.updateRenderer()

    @Viewable.z.setter
    def z(self, new_z):
        oldz = self._z
        Viewable.z.fset(self, new_z)
        if self._rendererSpriteId and oldz != self._z:
            self.renderer.spriteZ(self._rendererSpriteId,self._z)

    @Viewable.angle.setter
    def angle(self, new_angle):
        Viewable.angle.fset(self, new_angle)
        self.updateRenderer()

    @Viewable.center.setter
    def center(self, new_center):
        Viewable.center.fset(self, new_center)
        self.updateRenderer()

    #TODO: updateRenderDst on flipv, fliph

    def _doCompositing(self):
        """ Compose the external facing image from the atlas or source sprite, tag the overlays on and apply blurring"""
        use_tmpcanvas = False
        if self._tmpcanvas is None and self._width_pre > 0 and self._height_pre > 0:
            self._tmpcanvas = Canvas()(self._width_pre,self._height_pre, isRenderTarget = True)

        if self._tmpcanvas is not None:
            if self.sprite is not None:
                source = self.sprite.canvas
            elif self._atlas is not None:
                source = self._atlas
            else:
                source = None

            if source is not None:
                if self._overlays:
                    use_tmpcanvas = True
                    source.mod(1.0,1.0,1.0,1.0)
                    self._tmpcanvas.blitCanvas(source, 0, 0, self._tmpcanvas.width, self._tmpcanvas.height, 0,0,source.width,source.height, self._tmpcanvas.BLENDMODE_NONE)
                    for z in self._overlays.iterkeys():
                        (id,x,y,op,_r,_g,_b,_a,sprite) = self._overlays[z]

                        w = sprite.width
                        h = sprite.height
                        canvas = sprite.canvas
                        if canvas is not None:
                            r = sprite._red
                            g = sprite._green
                            b = sprite._blue
                            a = sprite._alpha
                            canvas.mod(_r if _r is not None else r, _g if _g is not None else g, _b if _b is not None else b, _a if _a is not None else a)
                            self._tmpcanvas.blitCanvas(canvas,0,0,w,h,x,y,w,h,op)
                            canvas.mod(r,g,b,a)

                if self._blur > 0:
                    if self._blur != self._lastBlurAmount:
                        self._doBluring(source, not use_tmpcanvas)
                    use_tmpcanvas = True

                source.mod(self._red, self._green, self._blue, self._alpha)

        if use_tmpcanvas:
            if self._canvas != self._tmpcanvas:
                self._canvas = self._tmpcanvas
                self.hide()
                self.show()
        else:
            #
            if self.sprite is not None:
                if self._canvas != self.sprite.canvas:
                    self._canvas = self.sprite.canvas
                    self.hide()
                    self.show()
            elif self._atlas is not None:
                if self._canvas != self._atlas:
                    self._canvas = self._atlas
                    self.hide()
                    self.show()
            else:
                if self._canvas is not None:
                    self._canvas = None
                    self.hide()

        self.updateRenderer()

    def _doBluring(self, source, start_clean = False):
        """ Take the current canvas and "blur it" by doing a few blits out of center"""
        if self._blur > 0 and self._tmpcanvas is not None:
            if start_clean:
                source.mod(1.0,1.0,1.0,1.0)
                self._tmpcanvas.blitCanvas(source, 0, 0, self._tmpcanvas.width, self._tmpcanvas.height, 0,0,source.width,source.height, self._tmpcanvas.BLENDMODE_NONE)
            source.mod(1.0,1.0,1.0,0.2)
            b = int (self._blur / 2)
            w = self._tmpcanvas.width-b
            h = self._tmpcanvas.height-b
            self._tmpcanvas.blitCanvas(source,0,0,w,h,b,b,w,h, self._tmpcanvas.BLENDMODE_BLEND)
            self._tmpcanvas.blitCanvas(source,b, b, w, h, 0,0,w,h, self._tmpcanvas.BLENDMODE_BLEND)
            self._tmpcanvas.blitCanvas(source,0,b,w,h,b,0,w,h, self._tmpcanvas.BLENDMODE_BLEND)
            self._tmpcanvas.blitCanvas(source,b,0,w,h,0,b,w,h, self._tmpcanvas.BLENDMODE_BLEND)
            b = self._blur
            w = self._tmpcanvas.width-b
            h = self._tmpcanvas.height-b
            source.mod(1.0,1.0,1.0,0.1)
            self._tmpcanvas.blitCanvas(source,0,0,w,h,b,b,w,h, self._tmpcanvas.BLENDMODE_BLEND)
            self._tmpcanvas.blitCanvas(source,b, b, w, h, 0,0,w,h, self._tmpcanvas.BLENDMODE_BLEND)
            self._tmpcanvas.blitCanvas(source,0,b,w,h,b,0,w,h, self._tmpcanvas.BLENDMODE_BLEND)
            self._tmpcanvas.blitCanvas(source,b,0,w,h,0,b,w,h, self._tmpcanvas.BLENDMODE_BLEND)
            # Up the alpha to 1.0
            source.mod(0.0,0.0,0.0,1.0)
            self._tmpcanvas.blitCanvas(source, 0, 0, self._tmpcanvas.width, self._tmpcanvas.height, 0,0,self._tmpcanvas.width,self._tmpcanvas.height, self._tmpcanvas.BLENDMODE_ADD)

            # Preserve the value used for bluring to save time in case it's not modified for the next cycle
            self._lastBlurAmount = self._blur
            return True
        return False

    @property
    def frameCount(self):
        return self.sprite.frameCount if self.sprite != None else 1

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

    def addOverlay(self, id, x=0, y=0, z=0, r=1.0, g=1.0, b=1.0, a=1.0, op=4, update=False):
        """ Add a sprite with component id, that will be overlayed at using the z order in the x,y using operation op and modulated with r,g,b,a
        op: SDL_BLENDMODE_NONE = 0x00000000
            SDL_BLENDMODE_BLEND = 0x00000001
            SDL_BLENDMODE_ADD = 0x00000002
            SDL_BLENDMODE_MOD = 0x00000004
        update: If True, the compositing will be updated after adding the overlay
        If an overlay of the same z exists, it'll be replaced
        If any of r,g,b,a are None, then that channel will be not modulated and the overlayed sprite setting will be used instead
        """
        if self.entity is not None:
            sprite = self.entity.getComponent(id)
            if sprite is not None and isinstance(sprite, Sprite):
                if z in self._overlays:
                    self.removeOverlay(z, update=False)
                self._overlays[z] = (id,x,y,op,r,b,g,a,sprite)
                sprite.parent = self
                if update:
                    self._doCompositing()
                return True
        return False

    def removeOverlay(self, zindex, update=False):
        """ Remove an overlay by index"""
        try:
            id,x,y,op,r,b,g,a,sprite = self._overlays[z]
            sprite.parent = None
            del self._overlays[zindex]
            if update:
                self._doCompositing()
            return retval
        except:
            return None

    def clearOverlays(self, update=False):
        for z in self._overlays.keys():
            self.removeOverlay(z, update=False)

        self._overlays = {}
        if update:
            self._doCompositing()

    @property
    def overlays(self):
        return self._overlays

    @overlays.setter
    def overlays(self, overlays):
        """ Overlays should have the format [(id, x, y, z, r, g, a, op), (id, x, y, z, r, g, a, op), ...]
        See addOverlay for the meaning of these parameters
        """
        self._overlays = {}

        for overlay in overlays:
            id,x,y,z,r,g,b,a,op = overlay
            self.addOverlay(id,int(x),int(y),int(z),float(r) if r is not None else None,float(g) if g is not None else None,float(b) if b is not None else None,float(a) if a is not None else None,int(op))

        self._doCompositing()

    def __getstate__(self):
        odict = self.__dict__.copy()
        # Remove non pickable elements
        del odict['sprite']
        del odict['_atlas']
        del odict['_spriteData']
        return odict

    def show(self):
        if self._rendererSpriteId is None and self._active and self._canvas != None:
            self._updateSize()
            self._rendererSpriteId = self.renderer.addSprite(self, self.interactive, self._canvas,
                self._z,
                0, 0, self._width_src, self._height_src,
                self._x, self._y, self._width_pre, self._height_pre,
                self._angle,
                self._center[0] if self._center != None else self._width_pre / 2,
                self._center[1] if self._center != None else self._height_pre / 2,
                (1 if self.fliph else 0) + (2 if self.flipv else 0),
                self._red, self._green, self._blue, self._alpha)

    def hide(self):
        if self._rendererSpriteId is not None:
            self.renderer.removeSprite(self._rendererSpriteId)
            self._rendererSpriteId = None

    @Viewable.active.setter
    def active(self, active):
        if active != self._active:
            Viewable.active.fset(self, active)
            if self.entity != None and self._active:
                self.show()
            else:
                self.hide()

    @Viewable.visible.setter
    def visible(self, value):
        if value != self._visible:
            self._visible = value
            if self._visible:
                self.show()
            else:
                self.hide()
    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value


    def reload(self, url):
        # The Canvas was reloaded before we get here
        if self._visible:
            self.hide()
            self.show()



    def event(self, action, sx, sy):
        """ Event processing """
        ret = super(Sprite, self).event(action, sx, sy)
        if action == EVENT_TYPE_ETHEREAL_SCROLL:
            self.updateRenderer()
        return ret

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
        self._lapse = 1000/self._rate
        self._lastUpdate = 0.0
        self._colormod = (1.0, 1.0, 1.0, 1.0)
        self.renderer = Gilbert().renderer

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
                            r = rectFromXYWH(dx,dy,w,h)
                            dr = rectFromXYWH(ddx,ddy,dw,dh)
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
