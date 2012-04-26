#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Build Project for OS X (i386 and x86_64)
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import os, shlex, shutil
from os.path import *
from subprocess import Popen, PIPE
from schafer import log, error, prepare_source, make_python_freeze
from ..util import get_sdl_flags, get_freetype_flags, get_png_flags

def make(options, env, DIST_DIR, BUILDS, sources, cython_src, cfiles):
    # Get some required flags
    sdlflags = get_sdl_flags(DIST_DIR)
    freetypeflags = get_freetype_flags(DIST_DIR)
    pngflags = get_png_flags(DIST_DIR)

    cmd = '%s -arch i386 -arch x86_64 -static-libgcc -fPIC %s -I%s -I%s -L%s -lobjc -lpython2.7 -lutil -lSDL2_ttf -lSDL2_image %s -ljpeg -lm %s %s -lpthread -ldl -o %s' % (env['CC'], sources,join(DIST_DIR, 'include'), join(DIST_DIR, 'include', 'python2.7'), join(DIST_DIR, 'lib'), pngflags, sdlflags, freetypeflags, options.project)
    Popen(shlex.split(cmd), cwd = cython_src, env=env).communicate()

    if not isfile(join(cython_src, options.project)):
        error('Error during compilation of project')
        exit()
    cmd = '%s %s' % (env['STRIP'], join(cython_src, options.project))
    Popen(shlex.split(cmd), cwd = cython_src, env=env).communicate()
    shutil.move(join(cython_src, options.project), join(BUILDS['PROJECT'], '..', options.project))

    return True
