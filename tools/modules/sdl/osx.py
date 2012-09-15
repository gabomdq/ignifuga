#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Build SDL for OS X (i386 and x86_64)
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import shlex
from os.path import *
from subprocess import Popen, PIPE
from ..log import log, error
from copy import deepcopy
from common import *
from schafer import SED_CMD

def setup(env_base, target_base, arch):
    env = deepcopy(env_base)
    target = deepcopy(target_base)
    env['CFLAGS'] = env['CFLAGS'].replace(join(target.dist, 'include'), join(target.dist+'_'+arch, 'include')) + ' -arch ' + arch
    env['CXXFLAGS'] = env['CXXFLAGS'].replace(join(target.dist, 'include'), join(target.dist+'_'+arch, 'include')) + ' -arch ' + arch
    env['LDFLAGS'] = env['LDFLAGS'].replace(join(target.dist, 'lib'), join(target.dist+'_'+arch, 'lib')) + ' -arch ' + arch
    env['HOST'] = '--host '+arch+'-apple-darwin'
    target.dist +='_'+arch
    target.builds.SDL += '_'+arch
    target.builds.SDL_IMAGE += '_'+arch
    target.builds.SDL_TTF += '_'+arch
    target.builds.SDL_MIXER += '_'+arch
    target.builds.FREETYPE += '_'+arch
    target.builds.PNG += '_'+arch
    target.builds.JPGTURBO += '_'+arch
    target.builds.ZLIB += '_'+arch
    target.builds.IGNIFUGA += '_'+arch
    target.builds.GC += '_'+arch
    target.builds.LIBOGG += '_'+arch
    target.builds.OGGDECODER += '_'+arch

    return env, target


def prepare(env, target, options):
    env_base = deepcopy(env)
    target_base = deepcopy(target)
    for arch in ['i386', 'x86_64']:
        env, target = setup(env_base, target_base, arch)
        prepare_common(env, target, options)

def make(env, target, options):
    # Build all libraries in universal mode (i386 and x86_64)
    env_base = deepcopy(env)
    target_base = deepcopy(target)
    for arch in ['i386', 'x86_64']:
        env, target = setup(env_base, target_base, arch)
        env['PKG_CONFIG_PATH'] = join(target.dist, 'lib', 'pkgconfig')
        make_common(env, target, options)

    # Lipo libraries architectures together
    target = target_base
    cmd = 'mkdir -p ' + join(target.dist, 'lib')
    Popen(shlex.split(cmd), env=env).communicate()

    for lib in ['SDL2', 'SDL2main', 'SDL2_image', 'SDL2_ttf', 'SDL2_mixer', 'turbojpeg', 'png12', 'jpeg', 'freetype', 'z']:
        libfile = 'lib'+lib+'.a'

        cmd = 'lipo -create %s %s -output %s' % (join(target.dist+'_i386', 'lib', libfile), join(target.dist+'_x86_64', 'lib', libfile), join(target.dist, 'lib', libfile))
        Popen(shlex.split(cmd), env=env).communicate()
        cmd = 'ranlib %s' % join(target.dist, 'lib', libfile)
        Popen(shlex.split(cmd), env=env).communicate()

        if isfile(join(target.dist, 'lib', libfile)):
            log(lib + ' lipoed successfully')
        else:
            error('Problem lipoing ' + lib)
            exit()

    for path in ['bin', 'include']:
        cmd = 'rsync -aqut --exclude .svn --exclude .hg --exclude Makefile %s/ %s' % (join(target.dist+'_x86_64', path), join(target.dist, path))
        Popen(shlex.split(cmd), env=env).communicate()

    for cfg in ['freetype-config', 'libpng12-config', 'sdl2-config']:
        cmd = SED_CMD + 's|_x86_64||g ' +  join(target.dist, 'bin', cfg)
        Popen(shlex.split(cmd), env=env).communicate()
    return True