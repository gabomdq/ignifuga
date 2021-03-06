#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


# Ignifuga Game Engine
# Text component
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.backends.sdl.Sprite import Sprite
from ignifuga.Gilbert import Gilbert, Canvas
from ignifuga.Task import *
from ignifuga.Log import *
import sys

class Text(Sprite):
    """ Text component class, viewable
    """
    ALIGN_CENTER = 'center'
    ALIGN_LEFT = 'left'
    ALIGN_RIGHT = 'right'

    def __init__(self, id=None, entity=None, active=True, frequency=15.0, **data):
        if 'htmlColor' in data:
            self.htmlColor = data['htmlColor']
            del data['htmlColor']

        # Default values
        self._loadDefaults({
            '_text': '',
            '_font': None,
            '_size': 16,
            '_align': Text.ALIGN_CENTER,
            '_color': (0,0,0),
            '_canvas': None
        })

        super(Text, self).__init__(id, entity, active, frequency, **data)

    def init(self, **data):
        """ Initialize the required external data """
        self._atlas = self._canvas = Canvas()(width=1, height=1)
        self._canvas.mod(self._red, self._green, self._blue, self._alpha)
        if self._text != '' and self._font != None:
            self._updateCanvas()
        super(Text, self).init(**data)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        # Update the canvas
        self._updateCanvas()

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        if len(value) == 3:
            self._color = value

    @property
    def htmlColor(self):
        return self._htmlColor

    @htmlColor.setter
    def htmlColor(self, colorstring):
        """ convert #RRGGBB to an (R, G, B) tuple """
        colorstring = colorstring.strip()
        if colorstring[0] == '#': colorstring = colorstring[1:]
        if len(colorstring) != 6:
            raise ValueError, "input #%s is not in #RRGGBB format" % colorstring
        r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
        r, g, b = [int(n, 16) for n in (r, g, b)]
        self._color = (r,g,b)

    @property
    def font(self):
        return self._font

    @font.setter
    def font(self, value):
        self._font = value

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = value

    @property
    def align(self):
        return self._align

    @align.setter
    def align(self, value):
        if value in [Text.ALIGN_LEFT, Text.ALIGN_CENTER, Text.ALIGN_RIGHT]:
            self._align = value

    def _updateCanvas(self):
        if self._canvas != None and self._font != None:
            self._canvas.text(self._text,self._color, self._font, self._size)
            self._updateSize()
            if self._rendererSpriteId:
                # The canvas surface changed, remove and add it to the renderer
                self.hide()
                self.show()

    def hits(self, x, y):
        """ x,y are in sprite coords"""
        if self.interactive and x>=0 and x <= self._width_src and y >= 0 and y <= self._height_src:
            # Check if the point on the sprite is visible
            return True
        return False

    def __getstate__(self):
        odict = super(Text, self).__getstate__()
        # Remove non pickable elements
        del odict['_canvas']
        return odict
