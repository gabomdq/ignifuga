#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Build Python for Android
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

# No OPENMP support in the Android NDK so far...

import os, shlex, shutil
from os.path import *
from subprocess import Popen, PIPE
from ..log import log, error
from schafer import prepare_source, make_python_freeze, SED_CMD, HOSTPYTHON, HOSTPGEN, ANDROID_NDK, ANDROID_SDK, PATCHES_DIR
from ..util import get_sdl_flags, get_freetype_flags, get_png_flags
import multiprocessing

def prepare(env, target, ignifuga_src, python_build):
    # Hardcoded for now
    sdlflags = '-I%s -I%s -I%s ' % (join(target.builds.SDL, 'jni', 'SDL', 'include'), join(target.builds.SDL, 'jni', 'SDL_image'), join(target.builds.SDL, 'jni', 'SDL_ttf'))

    # Patch some problems with cross compilation
    cmd = 'patch -p0 -i %s -d %s' % (join(PATCHES_DIR, 'python.android.diff'), python_build)
    Popen(shlex.split(cmd)).communicate()

    # Figure out where the STL headers are
    if env['STL'] == 'gnu':
        ndk_sources_base = join(env['NDK'], 'sources/cxx-stl/gnu-libstdc++')
        if not isdir(join(ndk_sources_base, 'include')):
            ndk_sources_base = join(env['NDK'], 'sources/cxx-stl/gnu-libstdc++/%s' % env['GCC_VERSION'])
            if not isdir(join(ndk_sources_base, 'include')):
                error("Could not find GNU STL headers location")
                exit()
            else:
                log("Using STL headers from GCC %s for Android NDK rev >=8b" % env['GCC_VERSION'])
        else:
            log("Using STL headers from GCC 4.4.3 for Android NDK rev <= 8")

        stlflags = '-I%s -I%s -L%s -lgnustl_static' % (join(ndk_sources_base, 'include'),
                                            join(ndk_sources_base, 'libs/armeabi/include'),
                                            join(ndk_sources_base, 'libs/armeabi'))
    else:
        # Untested! Probably does not work!
        stlflags = '-I%s -lstlport_shared' % (join(env['NDK'], 'sources/cxx-stl/stlport/stlport'), )


    # ldl is required by SDL dynamic library loading
    # llog, lz, lc are required by STL and Ignifuga logging
    ignifuga_module = "\nignifuga %s -I%s -I%s -I%s %s -L%s -L%s %s -lturbojpeg -lSDL2_ttf -lSDL2_image -lSDL2 -ldl -lGLESv1_CM -lGLESv2 -llog -lz -lc -lgcc\n" % (' '.join(ignifuga_src),
                                                                                                                                                           target.builds.IGNIFUGA,
                                                                                                                                                           join(target.builds.FREETYPE, 'include'),
                                                                                                                                                           join(target.builds.JPGTURBO),
                                                                                                                                                           stlflags,
                                                                                                                                                           join(target.builds.SDL, 'libs', 'armeabi'),
                                                                                                                                                           join(target.builds.SDL, 'jni', 'jpeg'),
                                                                                                                                             sdlflags)
    return ignifuga_module


def make(env, target, options, freeze_modules, frozen_file):

    # Android is built in shared mode
    if not isfile(join(target.builds.PYTHON, 'pyconfig.h')) or not isfile(join(target.builds.PYTHON, 'Makefile')):
        # __android_log is used in the interpreter itself (under PySys_WriteStdout and PySys_WriteStderr), so we need to link explicitly to it
        if env['STL'] == 'gnu':
            cmd = './configure --enable-silent-rules CPPFLAGS="-DBOOST_PYTHON_STATIC_LIB -DBOOST_PYTHON_SOURCE -fexceptions -frtti" CFLAGS="-DBOOST_PYTHON_STATIC_LIB -DBOOST_PYTHON_SOURCE -mandroid -fomit-frame-pointer --sysroot %s" HOSTPYTHON=%s HOSTPGEN=%s --host=arm-eabi --build=i686-pc-linux-gnu --enable-shared --prefix="%s"'% (env['SYSROOT'], HOSTPYTHON, HOSTPGEN, target.dist,)
        else:
            cmd = './configure --enable-silent-rules CFLAGS="-DBOOST_PYTHON_STATIC_LIB -DBOOST_PYTHON_SOURCE -mandroid -fomit-frame-pointer --sysroot %s" HOSTPYTHON=%s HOSTPGEN=%s --host=arm-eabi --build=i686-pc-linux-gnu --enable-shared --prefix="%s"'% (env['SYSROOT'], HOSTPYTHON, HOSTPGEN, target.dist,)
        Popen(shlex.split(cmd), cwd = target.builds.PYTHON, env=env).communicate()
        cmd = SED_CMD + '"s|^INSTSONAME=\(.*.so\).*|INSTSONAME=\\1|g" %s' % (join(target.builds.PYTHON, 'Makefile'))
        Popen(shlex.split(cmd), cwd = target.builds.PYTHON).communicate()

    make_python_freeze(options.platform, freeze_modules, frozen_file)
    if isfile(join(target.builds.PYTHON, 'libpython2.7.so')):
        os.remove(join(target.builds.PYTHON, 'libpython2.7.so'))

    # Remove setup.py as its of no use here and it tries to compile a lot of extensions that don't work in static mode
    if isfile(join(target.builds.PYTHON,'setup.py')):
        os.unlink(join(target.builds.PYTHON,'setup.py'))

    cmd = 'make V=0 -k -j%d HOSTPYTHON=%s HOSTPGEN=%s CROSS_COMPILE=arm-eabi- CROSS_COMPILE_TARGET=yes' % (multiprocessing.cpu_count(), HOSTPYTHON, HOSTPGEN)
    Popen(shlex.split(cmd), cwd = target.builds.PYTHON, env=env).communicate()

    # Copy some files to the skeleton directory
    try:
        if isdir(join(target.dist, 'jni', 'python', 'Include')):
            shutil.rmtree(join(target.dist, 'jni', 'python', 'Include'))
        shutil.copytree(join(target.builds.PYTHON, 'Include'), join(target.dist, 'jni', 'python', 'Include'))
        shutil.copy(join(target.builds.PYTHON, 'pyconfig.h'), join(target.dist, 'jni', 'python', 'pyconfig.h'))
        shutil.copy(join(target.builds.PYTHON, 'libpython2.7.so'), join(target.dist, 'jni', 'python', 'libpython2.7.so'))
        os.makedirs(join(target.dist, 'jni', 'python', 'Include', 'Modules'))
        shutil.copy(join(target.builds.PYTHON, 'Modules/greenlet.h'), join(target.dist, 'jni', 'python', 'Include', 'Modules', 'greenlet.h'))
        log('Python built successfully')
    except:
        error('Error while building Python for target')
        exit()

    return True