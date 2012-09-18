#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Build Python for iOS
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import os, shlex, shutil
from os.path import *
from subprocess import Popen, PIPE
from ..log import log, error
from schafer import prepare_source, make_python_freeze, SED_CMD, HOSTPYTHON, HOSTPGEN, ANDROID_NDK, ANDROID_SDK, PATCHES_DIR
from ..util import get_sdl_flags, get_freetype_flags, get_png_flags
import multiprocessing

def prepare(env, target, options, ignifuga_src, python_build):
    if options.bare:
        if options.baresrc is None:
            ignifuga_module = ''
        else:
            ignifuga_module = "\n%s %s -I%s %s\n" % (options.modulename, ' '.join(ignifuga_src),target.builds.IGNIFUGA, options.baredependencies if options.baredependencies is not None else '')
    else:
        # Hardcoded for now as SDL doesn't give us the proper dependencies with sdl2-config
        sdlflags = '-I%s -I%s -I%s -lturbojpeg -lSDL2_ttf -lSDL2_image -lSDL2 -lz -lfreetype -lpng12 -lm -liconv -lobjc -Wl,-framework,Foundation -Wl,-framework,UIKit -Wl,-framework,OpenGLES -Wl,-framework,QuartzCore -Wl,-framework,CoreAudio -Wl,-framework,AudioToolbox -Wl,-framework,CoreGraphics' % (join(target.builds.SDL, 'jni', 'SDL', 'include'), join(target.builds.SDL, 'jni', 'SDL_image'), join(target.builds.SDL, 'jni', 'SDL_ttf'))

        # Patch some problems with cross compilation
        cmd = 'patch -p1 -i %s -d %s' % (join(PATCHES_DIR, 'python.ios.diff'), python_build)
        Popen(shlex.split(cmd)).communicate()
        ignifuga_module = "\nignifuga %s -I%s -I%s -I%s -L%s %s -lstdc++\n" % (' '.join(ignifuga_src), target.builds.IGNIFUGA, join(target.dist, 'include'), join(target.dist, 'include', 'freetype2'), join(target.dist, 'libs'), sdlflags)

    return ignifuga_module


def make(env, target, options, freeze_modules, frozen_file):
    make_python_freeze('ios', freeze_modules, frozen_file)
    if not isfile(join(target.builds.PYTHON, 'pyconfig.h')) or not isfile(join(target.builds.PYTHON, 'Makefile')):
        # sdl2-config --static-libs flags are not really useful for iOS, as they are OS X oriented, so we forge them by hand
        if options.bare:
            sdlldflags = sdlcflags = ''
        else:
            sdlldflags = '-L%s/lib -lSDL2' % target.dist
            cmd = join(target.dist, 'bin', 'sdl2-config' ) + ' --cflags'
            sdlcflags = Popen(shlex.split(cmd), stdout=PIPE, env=env).communicate()[0].split('\n')[0]

        cmd = './configure --enable-silent-rules LDLAST="-lz" LINKFORSHARED=" " DYNLOADFILE="dynload_stub.o" LDFLAGS="-arch armv6 -arch armv7 -static-libgcc %s %s" CPPFLAGS="-DBOOST_PYTHON_STATIC_LIB -DBOOST_PYTHON_SOURCE -arch armv6 -arch armv7 %s" CFLAGS="-DBOOST_PYTHON_STATIC_LIB -DBOOST_PYTHON_SOURCE -arch armv6 -arch armv7 %s %s" HOSTPYTHON=%s HOSTPGEN=%s --disable-toolbox-glue --host=arm-apple-darwin --disable-shared --prefix="%s"'% (env['LDFLAGS'], sdlldflags, env['CFLAGS'], env['CFLAGS'], sdlcflags, HOSTPYTHON, HOSTPGEN, target.dist,)
        Popen(shlex.split(cmd), cwd = target.builds.PYTHON, env=env).communicate()
        cmd = SED_CMD + '"s|^INSTSONAME=\(.*.so\).*|INSTSONAME=\\1|g" %s' % (join(target.builds.PYTHON, 'Makefile'))
        Popen(shlex.split(cmd), cwd = target.builds.PYTHON).communicate()

        # Remove the FP register saving from Greenlet as it's not needed and causes compilation problems
        cmd = SED_CMD + '"s|\\(^#define REGS_TO_SAVE.*\\)\\"fp\\",\\(.*\\)|\\1\\2|g" %s' % (join(target.builds.PYTHON, 'Modules/platform/switch_arm32_gcc.h'))
        Popen(shlex.split(cmd), cwd = target.builds.PYTHON).communicate()

    # Remove setup.py as its of no use here and it tries to compile a lot of extensions that don't work in static mode
    if isfile(join(target.builds.PYTHON,'setup.py')):
        os.unlink(join(target.builds.PYTHON,'setup.py'))

    cmd = 'make V=0 install -k -j%d HOSTPYTHON=%s HOSTPGEN=%s CROSS_COMPILE=arm-apple-darwin CROSS_COMPILE_TARGET=yes' % (multiprocessing.cpu_count(), HOSTPYTHON, HOSTPGEN)
    Popen(shlex.split(cmd), cwd = target.builds.PYTHON, env=env).communicate()
    if not isdir (join(target.dist, 'include', 'Modules')):
        os.makedirs(join(target.dist, 'include', 'Modules'))
    shutil.copy(join(target.builds.PYTHON, 'Modules/greenlet.h'), join(target.dist, 'include', 'Modules', 'greenlet.h'))

    # Check success
    if isfile(join(target.dist, 'lib', 'libpython2.7.a')):
        log('Python built successfully')
    else:
        error('Error building python')
    return True
