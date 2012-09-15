#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Build SDL for Win32 using mingw
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from common import *

def prepare(env, target, options):
    prepare_common(env, target, options)

def make(env, target, options):
    make_common(env, target, options)
    return True