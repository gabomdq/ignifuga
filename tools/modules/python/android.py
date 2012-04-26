#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Build Python for Android
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import os, shlex, shutil
from os.path import *
from subprocess import Popen, PIPE
from schafer import log, error, prepare_source, make_python_freeze

def make(env, DIST_DIR, BUILDS, freeze_modules, frozen_file):
    make_python_freeze(freeze_modules, frozen_file)
    # Android is built in shared mode
    if not isfile(join(BUILDS['PYTHON'], 'pyconfig.h')) or not isfile(join(BUILDS['PYTHON'], 'Makefile')):
        cmd = './configure --enable-silent-rules LDFLAGS="-Wl,--allow-shlib-undefined" CFLAGS="-mandroid -fomit-frame-pointer --sysroot %s/platforms/android-5/arch-arm" HOSTPYTHON=%s HOSTPGEN=%s --host=arm-eabi --build=i686-pc-linux-gnu --enable-shared --prefix="%s"'% (ANDROID_NDK, HOSTPYTHON, HOSTPGEN, DIST_DIR,)
        Popen(shlex.split(cmd), cwd = BUILDS['PYTHON'], env=env).communicate()
        cmd = SED_CMD + '"s|^INSTSONAME=\(.*.so\).*|INSTSONAME=\\1|g" %s' % (join(BUILDS['PYTHON'], 'Makefile'))
        Popen(shlex.split(cmd), cwd = BUILDS['PYTHON']).communicate()
    cmd = 'make V=0 -k -j4 HOSTPYTHON=%s HOSTPGEN=%s CROSS_COMPILE=arm-eabi- CROSS_COMPILE_TARGET=yes' % (HOSTPYTHON, HOSTPGEN)
    Popen(shlex.split(cmd), cwd = BUILDS['PYTHON'], env=env).communicate()

    # Copy some files to the skeleton directory
    try:
        if isdir(join(DIST_DIR, 'jni', 'python', 'Include')):
            shutil.rmtree(join(DIST_DIR, 'jni', 'python', 'Include'))
        shutil.copytree(join(BUILDS['PYTHON'], 'Include'), join(DIST_DIR, 'jni', 'python', 'Include'))
        shutil.copy(join(BUILDS['PYTHON'], 'pyconfig.h'), join(DIST_DIR, 'jni', 'python', 'pyconfig.h'))
        shutil.copy(join(BUILDS['PYTHON'], 'libpython2.7.so'), join(DIST_DIR, 'jni', 'python', 'libpython2.7.so'))
        log('Python built successfully')
    except:
        error('Error while building Python for target')
        exit()

    return True