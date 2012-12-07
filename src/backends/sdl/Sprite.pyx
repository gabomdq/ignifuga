#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Ignifuga Game Engine
# SDL Sprite component
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.Gilbert import Gilbert
from ignifuga.components.Viewable import Viewable
from ignifuga.Task import *
import sys
from ignifuga.backends.GameLoopBase import EVENT_TYPE_TOUCH_DOWN, EVENT_TYPE_TOUCH_UP, EVENT_TYPE_TOUCH_MOTION, EVENT_TYPE_TOUCH_LAST, EVENT_TYPE_ETHEREAL_ZOOM_IN, EVENT_TYPE_ETHEREAL_ZOOM_OUT, EVENT_TYPE_ETHEREAL_SCROLL
from cython.operator cimport dereference as deref, preincrement as inc
from base64 import b64decode
from ignifuga.Log import error


cdef class _SpriteComponent:
    def __init__(self):
        self._started = False
        self._dirty = True
        self._rendererSprite = NULL
        self.overlays = new map[int,SPRITE_OVERLAY]()

    cpdef init(self):
        self.renderer = <Renderer>Gilbert().renderer
        if self.file != None:
            self._atlas = LOAD_IMAGE(self.file)
            Gilbert().dataManager.addListener(self.file, self)
            if self._atlas.spriteData != None:
                self._spriteData = self._atlas.spriteData
                self.sprite = _Sprite(self._spriteData, self._atlas)
                self._canvas = self.sprite.canvas
                if not self.forward:
                    self.sprite._frame = self.sprite.numFrames - 1
            else:
                self.sprite = None
                self._canvas = self._atlas
                self._static = True
        self._updateSize()
        self.show()

    cpdef free(self):
        self.hide()
        self._tmpcanvas = None
        self.sprite = None
        self._canvas = None
        self._atlas = None
        self._spriteData = None
        self.clearOverlays()
        Gilbert().dataManager.removeListener(self.file, self)

    cpdef _update(self, unsigned long now):
        """ Initialize the required external data """
        cdef overlay_iterator iter
        cdef SPRITE_OVERLAY *_sprite

        if self._static:
            # This is a single image non animated sprite, we return with the STOP instruction so the update loop is not called
            self._doCompositing()
            STOP()
            return

        # Update overlayed sprites that are marked inactive as they won't be updated by the entity
        iter = self.overlays.begin()
        while iter != self.overlays.end():
            _sprite = &deref(iter).second
            sprite = <object> _sprite.sprite
            if not sprite.active:
                sprite.update(now)
            inc(iter)

        if self.sprite != None and not self._paused:
            if self.sprite._frame == 0 and self.loop == 0 and not self._started:
                self._started = True
                self.run(self.onStart)

            if self.loopMax == None or self.loop < self.loopMax:
                if self.forward:
                    if self.sprite.nextFrame():
                        if self.sprite._frame == 0:
                            self.loop +=1
                            self.run(self.onLoop)
                        if self.loop == self.loopMax:
                            self.run(self.onStop)
                            if not self.remainActiveOnStop:
                                self.active = False
                                self.loop = 0
                                self.frame = 0
                        if not self.overlays.empty() or self._blur > 0:
                            self._doCompositing()
                else:
                    if self.sprite.prevFrame():
                        if self.sprite._frame == self.sprite.numFrames - 1:
                            self.loop +=1
                            self.run(self.onLoop)
                        if self.loop == self.loopMax:
                            self.run(self.onStop)
                            if not self.remainActiveOnStop:
                                self.active = False
                                self.loop = 0
                                self.frame = self.sprite.numFrames - 1
                        if not self.overlays.empty() or self._blur > 0:
                            self._doCompositing()
        elif not self.overlays.empty() or (self._blur > 0 and self._blur != self._lastBlurAmount):
            self._doCompositing()

        if self._dirty:
            self._updateRenderer()
            self._dirty = False

    cdef _updateSize(self):
        # Update our "public" width,height

        if self._width != None:
            self._width_pre = self._width
        elif self._spriteData != None:
            self._width_pre = self.sprite.width
        elif self._atlas != None:
            self._width_pre = self._atlas._width
        else:
            self._width_pre = 0

        if self._height != None:
            self._height_pre = self._height
        elif self._spriteData != None:
            self._height_pre = self.sprite.height
        elif self._atlas != None:
            self._height_pre = self._atlas._height
        else:
            self._height_pre = 0

        if self.zscale != None:
            self._width_pre = self.width * (1.0 + self._z*self.zscale)
            self._height_pre = self.height * (1.0 + self._z*self.zscale)

        if self._spriteData != None:
            self._width_src = self.sprite.width
        elif self._atlas != None:
            self._width_src = self._atlas._width

        if self._spriteData != None:
            self._height_src = self.sprite.height
        elif self._atlas != None:
            self._height_src = self._atlas._height

        self.updateRenderer()

    cdef _updateRenderer(self):
        if self._parent is not None:
            self._parent._doCompositing()
        elif self._rendererSprite != NULL:
            self.renderer._spriteDst(self._rendererSprite, <int>self.x, <int>self.y, self._width_pre, self._height_pre)
            self.renderer._spriteRot(self._rendererSprite,
                self._angle,
                self._center[0] if self._center != None else self._width_pre / 2,
                self._center[1] if self._center != None else self._height_pre / 2,
                (1 if self.fliph else 0) + (2 if self.flipv else 0))

            self.renderer._spriteColor(self._rendererSprite, <Uint8>(self._red*255), <Uint8>(self._green*255), <Uint8>(self._blue*255), <Uint8>(self._alpha*255))
            self._dirty = False

    cpdef updateRenderer(self):
        if self._static:
            # No animation loop, directly update renderer
            self._updateRenderer()
        else:
            # Mark as dirty so we update on the next update
            self._dirty = True

    cpdef updateRendererZ(self):
        if self._rendererSprite != NULL:
            self.renderer._spriteZ(self._rendererSprite,self._z)

    cpdef reset(self):
        # Reset sprite
        cdef overlay_iterator iter
        cdef SPRITE_OVERLAY *_sprite

        self.frame = 0
        self._started = False
        self.loop = 0

        iter = self.overlays.begin()
        while iter != self.overlays.end():
            _sprite = &deref(iter).second
            sprite = <object> _sprite.sprite
            sprite.reset()
            inc(iter)

    #TODO: updateRenderDst on flipv, fliph

    cdef _doCompositing(self):
        """ Compose the external facing image from the atlas or source sprite, tag the overlays on and apply blurring"""
        cdef bint use_tmpcanvas = False
        cdef overlay_iterator iter
        cdef SPRITE_OVERLAY *_sprite
        cdef float r,g,b,a
        cdef int w, h

        if self._tmpcanvas is None and self._width_pre > 0 and self._height_pre > 0:
            self._tmpcanvas = Canvas(self._width_pre,self._height_pre, isRenderTarget = True)

        if self._tmpcanvas is not None:
            if self.sprite is not None:
                source = self.sprite.canvas
            elif self._atlas is not None:
                source = self._atlas
            else:
                source = None

            if source is not None:
                if not self.overlays.empty():
                    use_tmpcanvas = True
                    source.mod(1.0,1.0,1.0,1.0)
                    self._tmpcanvas.blitCanvas(source, 0, 0, self._tmpcanvas.width, self._tmpcanvas.height, 0,0,source.width,source.height, self._tmpcanvas.BLENDMODE_NONE)
                    iter = self.overlays.begin()
                    while iter != self.overlays.end():
                        _sprite = &deref(iter).second
                        sprite = <object> _sprite.sprite

                        w = sprite.width
                        h = sprite.height
                        canvas = sprite.canvas
                        if canvas is not None:
                            r = sprite._red
                            g = sprite._green
                            b = sprite._blue
                            a = sprite._alpha
                            canvas.mod(_sprite.r if _sprite.r >= 0.0 else r, _sprite.g if _sprite.g >= 0.0 else g, _sprite.b if _sprite.b >= 0.0 else b, _sprite.a if _sprite.a >= 0.0 else a)
                            self._tmpcanvas.blitCanvas(canvas,0,0,w,h,_sprite.x,_sprite.y,w,h,_sprite.op)
                            canvas.mod(r,g,b,a)
                        inc(iter)

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

    cpdef hits(self, x, y):
        """ x,y are in sprite coords"""
        if self.interactive and x>=0 and x <= self._width_src and y >= 0 and y <= self._height_src:
            # Check if the point on the sprite is visible
            if self.sprite is not None:
                return self.sprite.hits(x,y)
            return True
        return False

    cpdef addOverlay(self, id, int x=0, int y=0, int z=0, float r=-1.0, float g=-1.0, float b=-1.0, float a=-1.0, int op=4, bint update=False):
        """ Add a sprite with component id, that will be overlayed at using the z order in the x,y using operation op and modulated with r,g,b,a
        op: SDL_BLENDMODE_NONE = 0x00000000
            SDL_BLENDMODE_BLEND = 0x00000001
            SDL_BLENDMODE_ADD = 0x00000002
            SDL_BLENDMODE_MOD = 0x00000004
        update: If True, the compositing will be updated after adding the overlay
        If an overlay of the same z exists, it'll be replaced
        If any of r,g,b,a are None, then that channel will be not modulated and the overlayed sprite setting will be used instead
        """
        cdef overlay_iterator iter
        cdef SPRITE_OVERLAY _sprite
        if self.entity is not None:
            sprite = self.entity.getComponent(id)
            if sprite is not None and isinstance(sprite, Sprite):

                iter = self.overlays.find(z)
                if iter != self.overlays.end():
                    self.removeOverlay(z, False)

                _sprite.x = x
                _sprite.y = y
                _sprite.r = r
                _sprite.g = g
                _sprite.b = b
                _sprite.a = a
                _sprite.op = op
                _sprite.sprite = <PyObject*> sprite
                Py_XINCREF(_sprite.sprite)
                self.overlays.insert(pair[int,SPRITE_OVERLAY](z,_sprite))
                sprite.parent = self
                if update:
                    self._doCompositing()
                return True
        return False

    cpdef removeOverlay(self, int zindex, bint update=False):
        """ Remove an overlay by index"""
        cdef overlay_iterator iter
        cdef SPRITE_OVERLAY *_sprite

        iter = self.overlays.find(zindex)
        if iter != self.overlays.end():
            _sprite = &deref(iter).second
            sprite = <object> _sprite.sprite
            sprite.parent = None
            Py_XDECREF(_sprite.sprite)
            self.overlays.erase(iter)

        if update:
            self._doCompositing()


    cpdef clearOverlays(self, update=False):
        cdef overlay_iterator iter
        cdef SPRITE_OVERLAY *_sprite

        iter = self.overlays.begin()
        while iter != self.overlays.end():
            self.removeOverlay(deref(iter).first, False)
            inc(iter)

        self.overlays.clear()
        if update:
            self._doCompositing()

    cpdef show(self):
        if self._rendererSprite == NULL and self._active and self._canvas != None:
            self._updateSize()
            self._rendererSprite = self.renderer._addSprite(self, self.interactive, self._canvas,
                self._z,
                0, 0, self._width_src, self._height_src,
                self._x, self._y, self._width_pre, self._height_pre,
                self._angle,
                self._center[0] if self._center != None else self._width_pre / 2,
                self._center[1] if self._center != None else self._height_pre / 2,
                (1 if self.fliph else 0) + (2 if self.flipv else 0),
                self._red, self._green, self._blue, self._alpha)

    cpdef hide(self):
        if self._rendererSprite != NULL:
            self.renderer._removeSprite(self._rendererSprite)
            self._rendererSprite = NULL

    cpdef reload(self, url):
        # The Canvas was reloaded before we get here
        if self._visible:
            self.hide()
            self.show()

    cpdef event(self, action, sx, sy):
        """ Event processing """
        ret = super(Sprite, self).event(action, sx, sy)
        if action == EVENT_TYPE_ETHEREAL_SCROLL:
            self.updateRenderer()
        return ret

#    def __getstate__(self):
#        odict = self.__dict__.copy()
#        # Remove non pickable elements
#        del odict['sprite']
#        del odict['_atlas']
#        del odict['_spriteData']
#        return odict


    cdef _doBluring(self, Canvas source, bint start_clean = False):
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


    ##############
    # PROPERTIES #
    ##############

    # The current composed full image frame (not the animation atlas, but the consolidated final viewable image)
    property canvas:
        def __get__(self):
            return self._canvas

    property frame:
        def __get__(self):
            return self.sprite._frame if self.sprite != None else 0
        def __set__(self, frame):
            if self.sprite != None:
                self.sprite.frame(frame)

            if frame == 0:
                self._started = False

            for overlay in self._overlays.itervalues():
                (id,x,y,op,_r,_g,_b,_a,sprite) = overlay
                sprite._frame(frame)

    property frameCount:
        def __get__(self):
            return self.sprite.numFrames if self.sprite != None else 1


#    property parent:
#        def __get__(self):
#            return self._parent
#
#        def __set__(self, value):
#            self._parent = value

    property paused:
        def __get__(self):
            return self._paused

        def __set__(self, value):
            # Pause/unpause the overlays
            for overlay in self._overlays.itervalues():
                (id,x,y,op,_r,_g,_b,_a,sprite) = overlay
                sprite.paused = value
            self._paused = value

    property overlays:
        def __get__(self):
            return self._overlays

        def __set__(self, overlays):
            """ Overlays should have the format [(id, x, y, z, r, g, a, op), (id, x, y, z, r, g, a, op), ...]
            See addOverlay for the meaning of these parameters
            ie: "overlays":[["ci_ovl", 0,0,0,null, null, null, null, 2]]
            """
            self._overlays = {}

            for overlay in overlays:
                id,x,y,z,r,g,b,a,op = overlay
                self.addOverlay(id,int(x),int(y),int(z),float(r) if r is not None else -1.0,float(g) if g is not None else -1.0,float(b) if b is not None else -1.0,float(a) if a is not None else -1.0,int(op))

            self._doCompositing()

    property blur:
        def __get__(self):
            return self._blur

        def __set__(self, value):
            """ Set the blur amount, this is actually an integer value that equals the pixel displacement used to simulate bluring"""
            if value <= 0:
                # Remove the temporal canvas
                self._lastBlurAmount = -1
                value = 0
            else:
                # Create a temporal canvas
                value = int(value)
            self._blur = value

            if self._static:
                self._doCompositing()


class Sprite(Viewable, _SpriteComponent):
    """ Sprite component class, viewable, potentially animated
    """
    PROPERTIES = Viewable.PROPERTIES + ['frame', 'frameCount', 'forward', 'blur', 'overlays', 'addOverlay', 'removeOverlay', 'clearOverlays', 'updateRenderer']
    PROPERTIES_PERSIST = Viewable.PROPERTIES_PERSIST + ['forward', 'blur']

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
            '_blur': 0,
            '_lastBlurAmount': -1,
            '_overlays': {},
            '_static': False,
            '_parent': None,
            '_paused': False,
            })

        _SpriteComponent.__init__(self)
        super(Sprite, self).__init__(id, entity, active, frequency, **data)

    def init(self, **data):
        """ Initialize the required external data """
        _SpriteComponent.init(self)
        super(Sprite, self).init(**data)

    def free(self, **kwargs):
        _SpriteComponent.free(self)
        super(Sprite, self).free(**kwargs)

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
        Viewable.alpha.fset(self,value)
        self.updateRenderer()

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
        if oldz != self._z:
            self.updateRendererZ()

    @Viewable.angle.setter
    def angle(self, new_angle):
        Viewable.angle.fset(self, new_angle)
        self.updateRenderer()

    @Viewable.center.setter
    def center(self, new_center):
        Viewable.center.fset(self, new_center)
        self.updateRenderer()

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

    def update(self, now, **data):
        self._update(now)

cdef class _Sprite:
    """ Internal sprite implementation with animation"""
    def __init__(self, data, srcCanvas):
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
        self.released = False

        self.numFrames = len(data['frames']) if 'frames' in data else 0
        self._frame = 0

        if 'type' in data:
            if data['type'] == 'atlas':
                self.type = SPRITE_TYPE_ATLAS
            elif data['type'] == 'deltap':
                self.type = SPRITE_TYPE_DELTAP
            elif data['type'] == 'deltak':
                self.type = SPRITE_TYPE_DELTAK
                error("Deltak no longer supported")
                return
        else:
            self.type = SPRITE_TYPE_ATLAS

        self.keyframes = new deque[int]()
        if 'keyframes' in data:
            for keyf in data['keyframes']:
                self.keyframes.push_back(<int>keyf)
        else:
            self.keyframes.push_back(0)

        self.frames = new map[int,deque[SPRITE_FRAME]]()

        cdef frame_iterator iter
        cdef SPRITE_FRAME sf
        cdef int nframe
        cdef hitmap_iterator hiter

        if 'frames' in data:
            nframe = 0
            for frame in data['frames']:
                iter = self.frames.insert(pair[int, deque[SPRITE_FRAME]](nframe, deque[SPRITE_FRAME]())).first
                for box in frame:
                    sx,sy,dx,dy,w,h = box
                    sf.src_x = sx
                    sf.src_y = sy
                    sf.dst_x = dx
                    sf.dst_y = dy
                    sf.w = w
                    sf.h = h
                    deref(iter).second.push_back(sf)
                nframe +=1
            # Get the w,h from the first frame which should be a full frame
            sx,sy,dx,dy,w,h = data['frames'][0][0]
        else:
            error("Frames specification not found in data")
            return


        self._hitmap = []
        self.hitmap = new map[int,char_p]()
        if 'hitmap' in data:
            # We need to keep the hitmap stored as a Python string, even though we never use it as such
            for frameHitmap in data['hitmap']:
                self._hitmap.append(b64decode(frameHitmap))

            # Map the strings to char* which we will actually use
            nframe = 0
            for frameHitmap in self._hitmap:
                self.hitmap.insert(pair[int, char_p](nframe, <char_p>frameHitmap))


        hiter = self.hitmap.find(0)
        if hiter != self.hitmap.end():
            self.current_hitmap = deref(hiter).second
        else:
            self.current_hitmap = NULL

        # Frame width and height
        self.width = w
        self.height = h

        # Create the sprite canvas
        # We need two canvas, the source canvas and the "presentation" canvas
        self.canvas = Canvas(width=w, height=h, isRenderTarget = True)
        self.srcCanvas = <Canvas>srcCanvas
        self.canvas.blitCanvas(self.srcCanvas, dx, dy, w, h, sx, sy, w, h, self.canvas.BLENDMODE_NONE)

    def __dealloc__(self):
        self.free()

    cpdef free(self):
        if not self.released:
            del self.keyframes
            del self.frames
            del self.hitmap
            self._hitmap = None
            self.canvas = None
            self.srcCanvas = None
            self.released = True

    cdef bint nextFrame(self):
        """ Forward to next frame or restart loop"""
        cdef frame_iterator iter
        cdef deque[SPRITE_FRAME] *boxes
        cdef deque[SPRITE_FRAME].iterator box_iter
        cdef SPRITE_FRAME *sf

        self._frame+=1
        if self._frame >= self.numFrames:
            self._frame=0


        iter = self.frames.find(self._frame)
        if iter != self.frames.end():
            return False

        boxes = &deref(iter).second
        box_iter = boxes.begin()

        # Consolidate the new sprite frame from srcCanvas into canvas
        while box_iter != boxes.end():
            sf = &deref(box_iter)
            self.canvas.blitCanvas(self.srcCanvas, sf.dst_x, sf.dst_y, sf.w, sf.h, sf.src_x, sf.src_y, sf.w, sf.h, self.canvas.BLENDMODE_NONE)
            inc(box_iter)

        return True

    cdef bint prevFrame(self):
        """ Back to prev frame or restart loop"""
        cdef int prevFrame
        prevFrame = self._frame -1
        if prevFrame < 0:
            prevFrame=self.numFrames -1

        # Go back to the previous frame
        self.frame(prevFrame)
        return True

    cdef frame(self, int frame):
        cdef frame_iterator iter
        cdef deque[SPRITE_FRAME] *boxes
        cdef deque[SPRITE_FRAME].iterator box_iter
        cdef SPRITE_FRAME *sf
        cdef hitmap_iterator hiter

        if frame < self.numFrames:
            if self.type == SPRITE_TYPE_ATLAS or self.type == SPRITE_TYPE_DELTAP:
                iter = self.frames.find(0)
                if iter != self.frames.end():
                    return False

                boxes = &deref(iter).second
                box_iter = boxes.begin()
                if box_iter != boxes.end():
                    sf = &deref(box_iter)
                    self.canvas.blitCanvas(self.srcCanvas, sf.dst_x, sf.dst_y, sf.w, sf.h, sf.src_x, sf.src_y, sf.w, sf.h, self.canvas.BLENDMODE_NONE)
                self._frame = frame

            if self.type == SPRITE_TYPE_DELTAP:
                # The first frame is in place, render every frame from the second one onwards
                for f in range(1,frame):
                    self.nextFrame()

            hiter = self.hitmap.find(frame)
            if hiter != self.hitmap.end():
                self.current_hitmap = deref(hiter).second
            else:
                self.current_hitmap = NULL
            return True

        return False

    cdef bint hits(self, int x, int y):
        # Check if the sprite has a transparent point at x,y
        if y< 0 or y>self.height or x<0 or x>self.width:
            error('Tried to check %d,%d coords in a %d,%d sprite ' % (x,y, self.width, self.height))
            return False

        if self.current_hitmap == NULL:
            return False

        # See _bitarray.c -> getbit(bitarrayobject *self, idx_t i)
        cdef int ndx = y*self.width+x
        return self.current_hitmap[ndx / 8] & (1 << ndx % 8)





#    cdef _precomputeFrameAreas(self):
#        """ Organize the frame areas, see getFrameAreas for the format of the area array """
#        lastKeyframe=0
#        self._areas = {}
#        for frame in range(0, self.numFrames):
#            if self.type == SPRITE_TYPE_ATLAS:
#                # Every frame is a keyframe, one box per frame and that's it
#                self._areas[frame] = [self.frames[frame][0],]
#            elif self.type == SPRITE_TYPE_DELTAP:
#                # We consolidate the frame ourselves in each nextFrame()
#                # So we report to the renderer *as if* every frame was a keyframe identical to the first frame
#                self._areas[frame] = [self.frames[0][0],]
#
#            elif self.type == SPRITE_TYPE_DELTAK:
#                if frame in self.keyframes:
#                    # We are on a keyframe, we only need to pass this box
#                    self._areas[frame] = [self.frames[frame][0],]
#                    lastKeyframe = frame
#                else:
#                    # We have to pass the last keyframe box and the current one in a non overlapping way
#                    keyframeareas = []
#                    areas = []
#
#                    # Append the keyframe areas
#                    for diffbox in self.frames[lastKeyframe]:
#                        keyframeareas.append(diffbox)
#
#                    for diffbox in self.frames[frame]:
#                        # Cut out the previous areas
#                        dsx,dsy,ddx,ddy,dw,dh = diffbox
#
#                        newareas = []
#                        for a in keyframeareas:
#                            sx,sy,dx,dy,w,h = a
#                            r = rectFromXYWH(dx,dy,w,h)
#                            dr = rectFromXYWH(ddx,ddy,dw,dh)
#                            #print "intersecting ", r, " with ", dr, " results in ", r.cutout(dr)
#                            for cr in r.cutout(dr):
#                                newareas.append((cr.left-dx+sx, cr.top-dy+sy, cr.left, cr.top, cr.width, cr.height))
#
#                        areas.append(diffbox)
#
#                        keyframeareas = newareas
#                    self._areas[frame] = keyframeareas + areas




