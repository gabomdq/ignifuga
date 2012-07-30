#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


# Ignifuga Game Engine
# SDL Font wrapper
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.backends.FontBase cimport FontBase
from ignifuga.Log import *
from SDL cimport *

cdef class Font(FontBase):
    cdef object __weakref__
    cdef TTF_Font *ttf_font
    cdef char *buffer
    cdef unsigned int buffersize