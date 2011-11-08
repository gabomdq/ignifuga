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
# Background node
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.SpriteNode import SpriteNode
from ignifuga.Gilbert import REQUESTS
from ignifuga.Task import *

class Background(SpriteNode):
    def __init__(self, parent, **kwargs):
        # Default values
        self.loadDefaults({
            '_scroll': True
        })

        super(Background, self).__init__(parent, **kwargs)

    def init(self, data):
        """ Initialize the required external data """
        super(Background, self).init(data)
        return self
        
    def hits(self, x, y):
        # Dont receive events on a background
        return False
        