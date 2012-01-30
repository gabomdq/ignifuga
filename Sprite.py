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
# Sprite class
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

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
import sys

class Sprite:   
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
        if self.renderer.checkLapse(self._lastUpdate, self._lapse):
            self._lastUpdate = self.renderer.getTimestamp()
            self._frame+=1
            if self._frame >= self._frameCount:
                self._frame=0
                

            # Consolidate the new sprite frame from _srcCanvas into _canvas
            for a in self._frames[self._frame]:
                sx,sy,dx,dy,w,h = a
                self._canvas.blitCanvas(self._srcCanvas, dx, dy, w, h, sx, sy, w, h, self._canvas.BLENDMODE_NONE)

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
    
    def hits(self, x, y):
        # Check if the sprite has a transparent point at x,y
        return self._hitmap[self._frame][y*self._width+x] if self._hitmap != None else False

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

"""
    def updateHitmap(self, surface, sx, sy, sw, sh):
        "" Update the hit map. Pass a software surface only! ""
        bpp = surface.format.BytesPerPixel
        for y in range(sy, sh):
            for x in range(sx, sw):
                pixel = POINTER(surface.pixels + y * surface.pitch + x * bpp).contents;
                r,g,b,a = (0,0,0,0)
                SDL_GetRGBA(pixel, surface.format, byref(r),byref(g),byref(b),byref(a))
                self._hitmap[y*self._width+x] = (a != 0) # If alpha is zero, it's totally transparent in SDL terms
"""