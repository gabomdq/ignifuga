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
# Sprite node
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from Node import Node
from GraphicNode import GraphicNode
from Sprite import Sprite
from ignifuga.Gilbert import REQUESTS
from ignifuga.Task import *
from ignifuga.Gilbert import Gilbert
from Action import Action
import sys

class SpriteNode(GraphicNode):
    """ Sprite Node class, viewable node, potentially animated
    """
    def __init__(self, parent, **kwargs):

        # Some syntax sugar for the urls
        if 'sprite' in kwargs:
            kwargs['_spriteURL'] = kwargs['sprite']
            del kwargs['sprite']

        if 'image' in kwargs:
            kwargs['_atlasURL'] = kwargs['image']
            del kwargs['image']
        
        # Default values
        self.loadDefaults({
            '_spriteURL': None,
            '_atlasURL': None,
            '_rate': 15,
            '_spriteData': None,
            '_atlas': None,
            'sprite': None,
        })
        
        super(SpriteNode, self).__init__(parent, **kwargs)
        # Initialize fields at default if not provided via kwargs
        #self.dontsave += ['_dirty', 'canvas', '_atlas', 'sprite', 'position', 'x', 'y', '_spriteData' ]
        
        if self.id == 'ponjas':
            #a = ((Action(duration=5.0, relative=True, x=40, angle=180 ) * 2 | Action(duration=5.0, relative=True, y=100 )) + Action(duration=5.0, relative=True, x=-80, y=-100, angle=-360 ) ) * -1
            a = (Action(duration=5.0, relative=True,angle=360, alpha=-0.5, red=-0.5, blue=-0.5 ) + Action(duration=5.0, relative=True, angle=-360, alpha=0.5, red=0.5, blue=0.5 ))  * -1
            #print a
            #self.center = (0,0)
            self.fliph=True
            self.alpha = 0.5
            self.red = 0.5
            self.green = 0.5
            self.do(a)

    def free(self):
        Gilbert().dataManager.release(self._spriteURL)
        Gilbert().dataManager.release(self._atlasURL)
        super(SpriteNode, self).free()
    
    def init(self, data):
        """ Initialize the required external data """
        super(SpriteNode, self).init(data)
        
        # Do our initialization
        self._atlas = LOAD_IMAGE(self._atlasURL)
        self._spriteData = LOAD_SPRITE(self._spriteURL)
        if self._spriteData != None:
            self.sprite = Sprite(self._spriteData, self._atlas, self._rate)
            self.sprite.setColorMod(self._red, self._green, self._blue, self._alpha)
        else:
            self.sprite = None
            
        self._updateSize()
        self._dirty = [ [0, 0, self.width, self.height], ]
        
        return self
    
    def update(self, data):
        """ Initialize the required external data """
        super(SpriteNode, self).update(data)
        DIRTY_RECTS(self._dirty)
        if self.sprite != None:
            self._dirty = self.sprite.nextFrame()
        else:
            self._dirty = None
        
        return self
        
    def _updateSize(self):
        # Update our "public" width,height
        if self._width != None:
            self.width = self._width
        elif self._spriteData != None:
            self.width = self.sprite.width
        elif self._atlas != None:
            self.width = self._atlas.width
        else:
            self.width = 0
        
        if self._height != None:
            self.height = self._height
        elif self._spriteData != None:
            self.height = self.sprite.height
        elif self._atlas != None:
            self.height = self._atlas.height
        else:
            self.height = 0
        
        if self._zscale != None:
            self.width = self.width * (1.0 + self._z*self._zscale)
            self.height = self.height * (1.0 + self._z*self._zscale)

    # The current full image frame (not the animation atlas, but the consolidated final viewable image)
    @property
    def canvas(self):
        if self.sprite != None:
            return self.sprite.canvas
        elif self._atlas != None:
            return self._atlas
        else:
            return None

    @property
    def rate(self):
        return self._rate
    @rate.setter
    def rate(self, value):
        self._rate = value

    @GraphicNode.red.setter
    def red(self, value):
        GraphicNode.red.fset(self,value)
        if self.sprite != None:
            self.sprite.setColorMod(self._red, self._green, self._blue, self._alpha)

    @GraphicNode.green.setter
    def green(self, value):
        GraphicNode.green.fset(self,value)
        if self.sprite != None:
            self.sprite.setColorMod(self._red, self._green, self._blue, self._alpha)

    @GraphicNode.blue.setter
    def blue(self, value):
        GraphicNode.blue.fset(self,value)
        if self.sprite != None:
            self.sprite.setColorMod(self._red, self._green, self._blue, self._alpha)

    @GraphicNode.alpha.setter
    def alpha(self, value):
        GraphicNode.alpha.fset(self,value)
        if self.sprite != None:
            self.sprite.setColorMod(self._red, self._green, self._blue, self._alpha)
        
    def getFrameAreas(self):
        if self.sprite != None:
            return self.sprite.getFrameAreas()
        else:
            # Return a single frame area
            return [ [0,0,self._x, self._y, self.width, self.height], ]
        
    def hits(self, x, y):
        # Check if x,y hits the node
        if x>=self._x and x <= self._x+self.width and y >= self._y and y <= self._y + self.height:
            # Check if the point on the sprite is visible
            x -= self._x
            y -= self._y
            self.state='hover'
            if self.sprite != None:
                return self.sprite.hits(x,y)
            return True
        return False


    def __getstate__(self):
        odict = super(SpriteNode, self).__getstate__()
        # Remove non pickable elements
        del odict['sprite']
        del odict['_atlas']
        del odict['_spriteData']
        return odict
