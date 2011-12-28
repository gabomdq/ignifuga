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
# Main Renderer
# Backends available: SDL
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.backends.TargetBase cimport TargetBase
from ignifuga.backends.CanvasBase cimport CanvasBase
from cpython cimport bool

cdef class Renderer:
    cdef double frameTimestamp
    cdef double frameLapse
    cdef tuple nativeResolution
    # Scale factor = screen/scene
    cdef double _scale_x, _scale_y
    cdef TargetBase _target
    #cdef list dirtyRects
    # Native scene resolution
    cdef double _native_res_w, _native_res_h
    # Native scene size
    cdef double _native_size_w, _native_size_h
    cdef bool _keep_aspect
    # Scroll displacement in screen coordinates
    cdef int _scroll_x, _scroll_y

    cpdef update(self)
    #cpdef dirty(self, int x, int y, int w, int h)
    cpdef setNativeResolution(self, double w=*, double h=*, bool keep_aspect=*)
    cpdef setSceneSize(self, int w, int h)
    cpdef _calculateScale(self, double scene_w, double scene_h, int screen_w, int screen_h, bool keep_aspect=*)
    cpdef windowResized(self)
    cpdef scrollBy(self, int deltax, int deltay)
    cpdef scrollTo(self, int x, int y)
    cpdef scaleBy(self, int delta)
    cpdef scaleByFactor(self, double factor)
