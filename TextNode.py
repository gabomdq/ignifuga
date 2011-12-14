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
# Text node
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from Node import Node
from GraphicNode import GraphicNode
from Sprite import Sprite
from ignifuga.Gilbert import REQUESTS
from ignifuga.Task import *
from Action import Action
import sys
from Gilbert import Canvas, DataManager

class TextNode(GraphicNode):
    """ Sprite Node class, viewable node, potentially animated
    """
    ALIGN_CENTER = 'center'
    ALIGN_LEFT = 'left'
    ALIGN_RIGHT = 'right'
    
    def __init__(self, parent, **kwargs):
        if 'htmlColor' in kwargs:
            self.htmlColor = kwargs['htmlColor']
            del kwargs['htmlColor']

        # Default values
        self.loadDefaults({
            '_text': '',
            '_font': None,
            '_size': 16,
            '_align': TextNode.ALIGN_CENTER,
            '_color': (0,0,0),
            '_canvas': None
        })

        super(TextNode, self).__init__(parent, **kwargs)

    def init(self, data):
        """ Initialize the required external data """
        super(TextNode, self).init(data)
        self._canvas = Canvas()(width=1, height=1)
        self._canvas.mod(self._red, self._green, self._blue, self._alpha)
        
        if self._text != '' and self._font != None:
            self._updateCanvas()

        return self

    @property
    def canvas(self):
        return self._canvas

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
        self.color = (r, g, b)

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
        if value in [TextNode.ALIGN_LEFT, TextNode.ALIGN_CENTER, TextNode.ALIGN_RIGHT]:
            self._align = value

    def _updateCanvas(self):
        if self._canvas != None:
            if self._text == '':
                self._canvas = None
                return
            if self._font != None:
                self._canvas.text(self._text,self._color, self._font, self._size)
                self.width = self._canvas.width
                self.height = self._canvas.height

    @GraphicNode.red.setter
    def red(self, value):
        GraphicNode.red.fset(self,value)
        if self._canvas != None:
            self._canvas.mod(self._red, self._green, self._blue, self._alpha)

    @GraphicNode.green.setter
    def green(self, value):
        GraphicNode.green.fset(self,value)
        if self._canvas != None:
            self._canvas.mod(self._red, self._green, self._blue, self._alpha)

    @GraphicNode.blue.setter
    def blue(self, value):
        GraphicNode.blue.fset(self,value)
        if self._canvas != None:
            self._canvas.mod(self._red, self._green, self._blue, self._alpha)

    @GraphicNode.alpha.setter
    def alpha(self, value):
        GraphicNode.alpha.fset(self,value)
        if self._canvas != None:
            self._canvas.mod(self._red, self._green, self._blue, self._alpha)
        
    def hits(self, x, y):
        # Check if x,y hits the node
        if x>=self._x and x <= self._x+self.width and y >= self._y and y <= self._y + self.height:
            # Check if the point on the sprite is visible
            return True
        return False


    def __getstate__(self):
        odict = super(TextNode, self).__getstate__()
        # Remove non pickable elements
        del odict['_canvas']
        return odict
