#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Build Python for Android
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import os, shlex, shutil
from os.path import *
from subprocess import Popen, PIPE
from ..log import log, error
from schafer import prepare_source, make_python_freeze, SED_CMD

def make(env, target, freeze_modules, frozen_file):
    make_python_freeze('android', freeze_modules, frozen_file)
    # Android is built in shared mode
    if not isfile(join(target.builds.PYTHON, 'pyconfig.h')) or not isfile(join(target.builds.PYTHON, 'Makefile')):
        cmd = './configure --enable-silent-rules LDFLAGS="-Wl,--allow-shlib-undefined" CFLAGS="-mandroid -fomit-frame-pointer --sysroot %s/platforms/android-5/arch-arm" HOSTPYTHON=%s HOSTPGEN=%s --host=arm-eabi --build=i686-pc-linux-gnu --enable-shared --prefix="%s"'% (ANDROID_NDK, HOSTPYTHON, HOSTPGEN, target.dist,)
        Popen(shlex.split(cmd), cwd = target.builds.PYTHON, env=env).communicate()
        cmd = SED_CMD + '"s|^INSTSONAME=\(.*.so\).*|INSTSONAME=\\1|g" %s' % (join(target.builds.PYTHON, 'Makefile'))
        Popen(shlex.split(cmd), cwd = target.builds.PYTHON).communicate()
    cmd = 'make V=0 -k -j4 HOSTPYTHON=%s HOSTPGEN=%s CROSS_COMPILE=arm-eabi- CROSS_COMPILE_TARGET=yes' % (HOSTPYTHON, HOSTPGEN)
    Popen(shlex.split(cmd), cwd = target.builds.PYTHON, env=env).communicate()

    # Copy some files to the skeleton directory
    try:
        if isdir(join(target.dist, 'jni', 'python', 'Include')):
            shutil.rmtree(join(target.dist, 'jni', 'python', 'Include'))
        shutil.copytree(join(target.builds.PYTHON, 'Include'), join(target.dist, 'jni', 'python', 'Include'))
        shutil.copy(join(target.builds.PYTHON, 'pyconfig.h'), join(target.dist, 'jni', 'python', 'pyconfig.h'))
        shutil.copy(join(target.builds.PYTHON, 'libpython2.7.so'), join(target.dist, 'jni', 'python', 'libpython2.7.so'))
        log('Python built successfully')
    except:
        error('Error while building Python for target')
        exit()

    return True