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
# Graphic component, common base for text and sprite components
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.Gilbert import REQUESTS, Gilbert, Event
from ignifuga.Task import *
from ignifuga.components.Component import Component
import sys

class Viewable(Component):
    """ Basic "viewable" class (though it has not content itself!)
    Properties:
    x, y: Scene coordinates (not screen coordinates!)
    z: z ordering, zero is at the bottom, positive values means higher up stacking.
    """
    TAGS = ['viewable',]
    ENTITY_TAGS = ['viewable',]
    PROPERTIES = ['canvas', 'position', 'x', 'y', 'z', 'angle', 'center', 'zscale', 'width', 'height', 'visible', 'flipv', 'fliph', 'alpha', 'red', 'green', 'blue', 'parallax', 'getRect', 'getRenderArea', 'hits']
    def __init__(self, id=None, entity=None, active=True, frequency=15.0, **data):
        # We have to do this here otherwise the z ordering thingy breaks
        self._entity = entity

        self._loadDefaults({
            '_visible': True,
            '_x': 0,
            '_y': 0,
            '_z': 0,
            '_angle': 0,
            '_center': None,
            'zscale': None,
            '_width': None,      # The width,height set from configuration data
            '_height': None,
            '_width_pre': 0,    # The computed width,height from configuration data, sprite or canvas information
            '_height_pre': 0,
            '_width_src': 0,    # The source material/original (from canvas, sprite) width, height
            '_height_src': 0,
            'flipv' : False,
            'fliph' : False,
            '_alpha': 1.0,
            '_red': 1.0,
            '_green': 1.0,
            '_blue': 1.0,
            '_parallax_x': 0.0,
            '_parallax_y': 0.0,
            '_scrollx': 0,      # Keep track of the renderer scroll for parallax functionality
            '_scrolly': 0,
            'interactive': True
        })

        super(Viewable, self).__init__(id, entity, active, frequency, **data)


    @Component.active.setter
    def active(self, active):
        if active != self._active:
            Component.active.fset(self,active)
            if self.entity != None:
                if self._active:
                    # Enforce exclusivity, disable other Viewable derived components
                    components = self.entity.getComponentsByTag('viewable')
                    for component in components:
                        if component != self:
                            component.active = False
                    Gilbert().refreshEntityZ(self.entity) # If self.visible == False, it will not be really shown
                else:
                    Gilbert().hideEntity(self.entity)

    # The current full image frame (not the animation atlas, but the consolidated final viewable image)
    @property
    def canvas(self):
        return None

    @property
    def position(self):
        return (self.x, self.y)

    @position.setter
    def position(self, xy):
        new_x, new_y = xy
        try:
            x = int(new_x)
            y = int(new_y)
        except:
            return

        self._x = new_x
        self._y = new_y

    @property
    def parallax(self):
        return (self._parallax_x, self._parallax_y)

    @parallax.setter
    def parallax(self, xy):
        self._parallax_x, self._parallax_y = xy

    @property
    def x(self):
        return self._x + self._scrollx * self._parallax_x

    @x.setter
    def x(self, new_x):
        try:
            new_x = int(new_x)
        except:
            return
        self._x = new_x

    @property
    def y(self):
        return self._y + self._scrolly * self._parallax_y

    @y.setter
    def y(self, new_y):
        try:
            new_y = int(new_y)
        except:
            return
        self._y = new_y

    @property
    def z(self):
        return self._z if self._visible and self._active else None

    @z.setter
    def z(self, new_z):
        """ Change the Z ordering of the entity"""
        try:
            new_z = int(new_z)
        except:
            new_z = None

        if new_z != self._z:
            self._z = new_z
            if self.entity != None and self.active: # If active==false, it's probable that the .z property for the entity is not set!
                Gilbert().refreshEntityZ(self.entity)


    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, new_angle):
        try:
            new_angle = float(new_angle)
        except:
            return
        self._angle = new_angle

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
            self._center = None
            
    @property
    def red(self):
        return self._red
    @red.setter
    def red(self, value):
        self._red = value

    @property
    def green(self):
        return self._green
    @green.setter
    def green(self, value):
        self._green = value

    @property
    def blue(self):
        return self._blue
    @blue.setter
    def blue(self, value):
        self._blue = value

    @property
    def alpha(self):
        return self._alpha
    @alpha.setter
    def alpha(self, value):
        self._alpha = value

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, value):
        if value != self._visible:
            self._visible = value
            if self._visible:
                self.overlord.refreshEntityZ(self.entity)
            else:
                self.overlord.hideEntity(self.entity)

    @property
    def width(self):
        return self._width_pre

    @width.setter
    def width(self, value):
        # Set the internal width, the precomputed _width_pre is updated with _updateSize
        self._width = value
        self._updateSize()

    @property
    def height(self):
        return self._height_pre

    @height.setter
    def height(self, value):
        # Set the internal height, the precomputed _height_pre is updated with _updateSize
        self._height = value
        self._updateSize()

    def getRect(self):
        """ Get the x,y,w,h rectangle the node occupies in scene coordinates """
        return (self.x, self.y, self.width, self.height)

    def getRenderArea(self):
        return [0, 0, self.width, self.height, self.x, self.y, self.width, self.height]

    def _updateSize(self):
        self._width_src = self._width_pre = self._width if self._width != None else 0
        self._height_src = self._height_pre = self._height if self._height != None else 0

    def hits(self, x, y):
        return False

    def event(self, event):
        if event.type == Event.TYPE.scroll:
            self._scrollx = event.x
            self._scrolly = event.y

        return super(Viewable, self).event(event)

