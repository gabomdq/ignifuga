#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Build Project for OS X (i386 and x86_64)
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import os, shlex, shutil
from os.path import *
from subprocess import Popen, PIPE
from ..log import log, error
from schafer import prepare_source, make_python_freeze
from ..util import get_sdl_flags, get_freetype_flags, get_png_flags

def make(options, env, target, sources, cython_src, cfiles):
    # Get some required flags
    sdlflags = get_sdl_flags(target)
    freetypeflags = get_freetype_flags(target)
    pngflags = get_png_flags(target)

    cmd = '%s -arch i386 -arch x86_64 -static-libgcc -static-libstdc++ -fPIC %s -I%s -I%s -L%s -lobjc -lpython2.7 -lutil -lSDL2_ttf -lSDL2_image %s -ljpeg -lm -lstdc++ %s %s -lpthread -ldl -o %s' % (env['CC'], sources,join(target.dist, 'include'), join(target.dist, 'include', 'python2.7'), join(target.dist, 'lib'), pngflags, sdlflags, freetypeflags, options.project)
    Popen(shlex.split(cmd), cwd = cython_src, env=env).communicate()

    if not isfile(join(cython_src, options.project)):
        error('Error during compilation of project')
        exit()
    cmd = '%s %s' % (env['STRIP'], join(cython_src, options.project))
    Popen(shlex.split(cmd), cwd = cython_src, env=env).communicate()
    shutil.move(join(cython_src, options.project), join(target.project, '..', options.project))

    return True
