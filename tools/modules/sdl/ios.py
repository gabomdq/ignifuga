#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Build SDL for iOS (see prepare_ios_env for available platforms)
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import os, shlex, shutil
from os.path import *
from subprocess import Popen, PIPE
from ..log import log, error
from schafer import prepare_source, SED_CMD, SOURCES
import multiprocessing
from copy import deepcopy
from common import *

def setup(env_base, target_base, arch):
    env = deepcopy(env_base)
    target = deepcopy(target_base)
    env['CFLAGS'] = env['CFLAGS'].replace(join(target.dist, 'include'), join(target.dist+'_'+arch, 'include')) + ' -arch ' + arch
    env['CXXFLAGS'] = env['CXXFLAGS'].replace(join(target.dist, 'include'), join(target.dist+'_'+arch, 'include')) + ' -arch ' + arch
    env['LDFLAGS'] = env['LDFLAGS'].replace(join(target.dist, 'lib'), join(target.dist+'_'+arch, 'lib')) + ' -arch ' + arch
#    env['HOST'] = '--host '+arch+'-apple-darwin'
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
    for arch in env['ARCHS'].split(' '):
        env, target = setup(env_base, target_base, arch)
        prepare_common(env, target, options)

def make(env, target, options):
    # Build all libraries in universal mode (see prepare_ios_env for available platforms)
    env_base = deepcopy(env)
    target_base = deepcopy(target)
    archs = env['ARCHS'].split(' ')

    for arch in archs:
        env, target = setup(env_base, target_base, arch)
        env['TARGET_DIST'] = target.dist
        env['PKG_CONFIG_PATH'] = join(target.dist, 'lib', 'pkgconfig')
        if not isfile(join(target.builds.SDL, 'Makefile')):
            # Disable IPHONE_TOUCH_EFFICIENT_DANGEROUS on SDL
            cmd = SED_CMD + '-e "s|^#define IPHONE_TOUCH_EFFICIENT_DANGEROUS|//#define IPHONE_TOUCH_EFFICIENT_DANGEROUS|g" %s' % join (target.builds.SDL, 'src', 'video', 'uikit', 'SDL_uikitview.h')
            Popen(shlex.split(cmd), env=env).communicate()

            cmd = './configure --enable-silent-rules %(HOST)s CFLAGS="%(CFLAGS)s" LDFLAGS="-static-libgcc %(LDFLAGS)s" --disable-shared --enable-static --prefix="%(TARGET_DIST)s"' % env
            Popen(shlex.split(cmd), cwd = target.builds.SDL, env=env).communicate()
            # Replace the auto generated config file for a hand made one
            shutil.copy(join(target.builds.SDL, 'include', 'SDL_config_iphoneos.h'), join(target.builds.SDL, 'include', 'SDL_config.h'))
            # Get rid of autodetected extra flags that SDL thinks we need but we don't as we are not compiling for OS X!
            cmd = SED_CMD + '-e "s|^EXTRA_CFLAGS.*|EXTRA_CFLAGS=-I./include|g" %s' % (join(target.builds.SDL, 'Makefile'),)
            Popen(shlex.split(cmd), cwd = target.builds.SDL, env=env).communicate()
            cmd = SED_CMD + '-e "s|^EXTRA_LDFLAGS.*|EXTRA_LDFLAGS=-lm|g" %s' % (join(target.builds.SDL, 'Makefile'),)
            Popen(shlex.split(cmd), cwd = target.builds.SDL, env=env).communicate()

        make_common(env, target, options, ['zlib', 'png', 'jpeg', 'sdl', 'sdl_image'])
        cflags = env['CFLAGS']
        #Modify CFLAGS for Freetype
        env['CFLAGS'] = cflags + ' -pipe -mdynamic-no-pic -std=c99 -Wno-trigraphs -fpascal-strings -Wreturn-type -Wunused-variable -fmessage-length=0 -fvisibility=hidden'
        make_common(env, target, options, ['freetype',])
        env['CFLAGS'] = cflags
        make_common(env, target, options, ['sdl_ttf', 'ogg'])
        env['CFLAGS'] = cflags + ' -mno-thumb -mthumb-interwork'
        make_common(env, target, options, ['oggdecoder',])
        env['CFLAGS'] = cflags
        make_common(env, target, options, ['sdl_mixer',])

    # Lipo libraries architectures together
    target = target_base
    cmd = 'mkdir -p ' + join(target.dist, 'lib')
    Popen(shlex.split(cmd), env=env).communicate()

    for lib in ['SDL2', 'SDL2main', 'SDL2_image', 'SDL2_ttf', 'SDL2_mixer', 'turbojpeg', 'png12', 'jpeg', 'freetype', 'z', 'vorbisidec', 'ogg']:
        libfile = 'lib'+lib+'.a'

        cmd = 'lipo -create '
        for arch in archs:
            cmd += join(target.dist+'_' + arch, 'lib', libfile) + ' '
        cmd +=' -output %s' %  join(target.dist, 'lib', libfile)
        Popen(shlex.split(cmd), env=env).communicate()

        cmd = 'ranlib %s' % join(target.dist, 'lib', libfile)
        Popen(shlex.split(cmd), env=env).communicate()

        if isfile(join(target.dist, 'lib', libfile)):
            log(lib + ' lipoed successfully')
        else:
            error('Problem lipoing ' + lib)
            exit()

    for path in ['bin', 'include']:
        cmd = 'rsync -aqut --exclude .svn --exclude .hg --exclude Makefile %s/ %s' % (join(target.dist+'_'+archs[0], path), join(target.dist, path))
        Popen(shlex.split(cmd), env=env).communicate()

    # Hack the architectures on one of the architectures config utilities for use on the lipo'ed versions
    for cfg in ['freetype-config', 'libpng12-config', 'sdl2-config']:
        cmd = SED_CMD + ('s|_%s||g ' % archs[0]) +  join(target.dist, 'bin', cfg)
        Popen(shlex.split(cmd), env=env).communicate()
    return True
