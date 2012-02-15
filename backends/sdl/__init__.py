#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Ignifuga Game Engine
# SDL Backend
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

# Required for embedding
__path__ = ['ignifuga/backends/sdl',]

from SDL import *

def initializeBackend():
   initializeSDL()

def terminateBackend():
    terminateSDL()