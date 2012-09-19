#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Build Project for Linux 64
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import os, shlex, shutil
from os.path import *
from subprocess import Popen, PIPE
from ..log import log, error
from schafer import prepare_source, make_python_freeze
from ..util import get_sdl_flags, get_freetype_flags, get_png_flags

def make(options, env, target, sources, cython_src, cfiles):
    # Get some required flags
    if options.bare:
        cmd = '%s %s %s -static-libgcc -static-libstdc++ -Wl,--no-export-dynamic -Wl,-Bstatic -fPIC %s -I%s -I%s -L%s -lpython2.7 -lm -lutil -lz -Wl,-Bdynamic -lpthread -ldl -o %s' % (env['CC'], env['CFLAGS'], env['LDFLAGS'], sources,join(target.dist, 'include'), join(target.dist, 'include', 'python2.7'), join(target.dist, 'lib'), options.project)
    else:
        sdlflags = '-lSDL2_ttf -lSDL2_image ' + get_sdl_flags(target) + ' -lturbojpeg -ljpeg -lgccpp -lstdc++ -lgc -lgomp'
        freetypeflags = get_freetype_flags(target)
        pngflags = get_png_flags(target)

        sdlflags = sdlflags.replace('-lpthread', '').replace('-ldl', '') + env['LDFLAGS'] + ' ' + env['CFLAGS']
        freetypeflags = freetypeflags.replace('-lpthread', '').replace('-ldl', '')
        pngflags = pngflags.replace('-lpthread', '').replace('-ldl', '')
        cmd = '%s %s %s -static-libgcc -static-libstdc++ -Wl,--no-export-dynamic -Wl,-Bstatic -fPIC %s -I%s -I%s -L%s -lpython2.7 -lutil %s -lm %s %s -lz -Wl,-Bdynamic -lpthread -ldl -o %s' % (env['CC'], env['CFLAGS'], env['LDFLAGS'], sources,join(target.dist, 'include'), join(target.dist, 'include', 'python2.7'), join(target.dist, 'lib'), sdlflags, pngflags, freetypeflags, options.project)

    Popen(shlex.split(cmd), cwd = cython_src, env=env).communicate()
    if not isfile(join(cython_src, options.project)):
        error('Error during compilation of project')
        exit()
    cmd = '%s %s' % (env['STRIP'], join(cython_src, options.project))
    Popen(shlex.split(cmd), cwd = cython_src, env=env).communicate()
    shutil.move(join(cython_src, options.project), join(target.project, '..', options.project))

    return True
