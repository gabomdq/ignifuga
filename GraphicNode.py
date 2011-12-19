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
from Sprite import Sprite
from ignifuga.Gilbert import REQUESTS, Gilbert
from ignifuga.Task import *

from Action import Action
import sys

class GraphicNode(Node):
    """ Graphic Node class, basic "viewable" class (though it has not content itself!)
    Properties:
    x, y: Scene coordinates (not screen coordinates!) Children nodes can be outside the bounds of the parent, but when the parent moves, they move with it.
    z: z ordering, zero is at the bottom, positive values means higher up stacking. Z index is relative to the parent (A parent with z=1 and a child with z=1, produces a child with an onscreen z=2)
    """
    def __init__(self, parent, **kwargs):
        self.loadDefaults({
            '_x': 0,
            '_y': 0,
            '_z': 0,
            '_angle': 0,
            '_center': None,
            '_zscale': None,
            '_width': None,
            '_height': None,
            'width': 0,
            'height': 0,
            '_hidden': False,
            '_dirty': None,
            '_flipv' : False,
            '_fliph' : False,
            '_alpha': 1.0,
            '_red': 1.0,
            '_green': 1.0,
            '_blue': 1.0
        })

        super(GraphicNode, self).__init__(parent, **kwargs)
        # State Keys should be set after parent init
        self._stateKeys += ['x', 'y', 'z', 'angle', 'center', 'zscale', 'width', 'height', 'hidden', 'dirty', 'flipv', 'fliph', 'alpha', 'red', 'green', 'blue']

        # Some additional adjustments
        self._z += parent.z if parent.z is not None else 0
    
    def init(self, data):
        """ Initialize the required external data """
        super(GraphicNode, self).init(data)
        self._dirty = [ [0, 0, self.width, self.height], ]
        return self

    # The current full image frame (not the animation atlas, but the consolidated final viewable image)
    @property
    def canvas(self):
        return None
    
    def getDirty(self):
        return self._dirty
       
    def resetDirty(self):
        self._dirty = None
        return True
    
    @property
    def position(self):
        return (self._x, self._y)
        
    @position.setter
    def position(self, xy):
        new_x, new_y = xy
        try:
            x = int(new_x)
            y = int(new_y)
        except:
            return
        
        diffx = new_x - self._x
        diffy = new_y - self._y
        
        if diffx != 0 or diffy != 0:
            for child in self.children.items():
                x,y = child.position
                child.position = (x+diffx, y+diffy)
                
            self._x = new_x
            self._y = new_y
    @property
    def x(self):
        return self._x
    
    @x.setter
    def x(self, new_x):
        try:
            new_x = int(new_x)
        except:
            return
        diff = new_x - self._x
        if diff != 0:
            for child in self.children.items():
                child.x += diff
                
            self._x = new_x
            
    @property
    def y(self):
        return self._y
    
    @y.setter
    def y(self, new_y):
        try:
            new_y = int(new_y)
        except:
            return
        
        diff = new_y - self._y
        if diff != 0:
            for child in self.children.items():
                child.y += diff
                
            self._y = new_y

    @property
    def z(self):
        return self._z if not self._hidden else None
    
    @z.setter
    def z(self, new_z):
        """ Change the Z ordering of the node and its children"""
        new_z = int(new_z) + (self.parent.z if self.parent != None and self.parent.z is not None else 0)
        
        diff = new_z - self._z
        if diff != 0:
            for child in self.children.items():
                child.z += diff
            Gilbert().changeZ(self, new_z)
            self._z = new_z

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, new_angle):
        try:
            new_angle = float(new_angle)
        except:
            return

        diff = new_angle - self._angle
        if diff != 0:
            for child in self.children.items():
                child.angle += diff

            self._angle = new_angle

    @property
    def flipv(self):
        return self._flipv

    @property
    def fliph(self):
        return self._fliph

    @flipv.setter
    def flipv(self, flip):
        for child in self.children.items():
            child.flipv = flip
        self._flipv = flip

    @fliph.setter
    def fliph(self, flip):
        for child in self.children.items():
            child.fliph = flip
        self._fliph = flip

    @property
    def center(self):
        return self._center
        
    @center.setter
    def center(self, new_center):
        """ new_center can be None for a w/2,h/2 center of a tuple/list of two elements """
        if (isinstance(new_center, list) or isinstance(new_center, tuple)) and len(new_center) == 2:
            if isinstance(new_center, list):
                self._center = tuple(new_center)
            else:
                self._center = new_center
        else:
            new_center = None

        for child in self.children.items():
            child.center = None

    @property
    def red(self):
        return self._red

    @red.setter
    def red(self, value):
        for child in self.children.items():
            child.red = value
        self._red = value

    @property
    def green(self):
        return self._green

    @green.setter
    def green(self, value):
        for child in self.children.items():
            child.green = value
        self._green = value

    @property
    def blue(self):
        return self._blue

    @blue.setter
    def blue(self, value):
        for child in self.children.items():
            child.blue = value
        self._blue = value

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, value):
        for child in self.children.items():
            child.alpha = value
        self._alpha = value
            
    def hide(self):
        if not self._hidden:
            for child in self.children.items():
                child.hide()
                
            self._hidden = True
            self.overlord.changeZ(self, None)
        
    def show(self):
        if self._hidden:
            for child in self.children.items():
                child.show()
            self._hidden = False
            self.overlord.changeZ(self, self._z)
    
    def getRect(self):
        """ Get the x,y,w,h rectangle the node occupies in scene coordinates """
        return (self._x, self._y, self.width, self.height)
        
    def getFrameAreas(self):
        
        return [ [0,0,self._x, self._y, self.width, self.height], ]
        
    def hits(self, x, y):
        return False


    def __getstate__(self):
        odict = super(GraphicNode, self).__getstate__()
        odict['_dirty'] = None
        return odict
