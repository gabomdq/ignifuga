#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Build SDL for Android
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import os, shlex, shutil
from os.path import *
from subprocess import Popen, PIPE
from ..log import log, error
from schafer import SED_CMD, ROOT_DIR, SOURCES, ANDROID_NDK, ANDROID_SDK
from ..util import prepare_source
import multiprocessing

def prepare(env, target):
    patch_target = not isdir(target.builds.SDL) # Keep count if we are starting from scratch to avoid rebuilding excessively too many files
    prepare_source('SDL Android Skeleton', join(SOURCES['SDL'], 'android-project'), target.builds.SDL)
    if patch_target:
        cmd = SED_CMD + """'s|^target=.*|target=%s|g' %s""" % (env['TARGET'], join(target.builds.SDL, 'default.properties'),)
        Popen(shlex.split(cmd), cwd = target.builds.SDL).communicate()
        # Future proof patching (default.properties is now called project.properties), this may fail harmlessly in current SDL versions
        cmd = SED_CMD + """'s|^target=.*|target=%s|g' %s""" % (env['TARGET'], join(target.builds.SDL, 'project.properties'),)
        Popen(shlex.split(cmd), cwd = target.builds.SDL).communicate()
        if isdir(join(target.builds.SDL, 'jni', 'src')):
            shutil.rmtree(join(target.builds.SDL, 'jni', 'src'))


    # Copy SDL and SDL_image to the android project structure
    prepare_source('SDL', SOURCES['SDL'], join(target.builds.SDL, 'jni', 'SDL'))
    if patch_target:
        shutil.copy(join(target.builds.SDL, 'jni', 'SDL', 'include', 'SDL_config_android.h'), join(target.builds.SDL, 'jni', 'SDL', 'include', 'SDL_config.h'))
    prepare_source('libpng', SOURCES['PNG'], join(target.builds.SDL, 'jni', 'png'))
    prepare_source('libjpeg', SOURCES['JPG'], join(target.builds.SDL, 'jni', 'jpeg'))
    prepare_source('SDL_image', SOURCES['SDL_IMAGE'], join(target.builds.SDL, 'jni', 'SDL_image'))
    if not isfile(join(target.builds.SDL, 'jni', 'SDL_image', 'Android.mk')):
        shutil.copy(join(ROOT_DIR, 'external', 'Android.mk.SDL_image'), join(target.builds.SDL, 'jni', 'SDL_image', 'Android.mk'))

    prepare_source('SDL_ttf', SOURCES['SDL_TTF'], join(target.builds.SDL, 'jni', 'SDL_ttf'))
    prepare_source('freetype', SOURCES['FREETYPE'], target.builds.FREETYPE)
    shutil.copy(join(SOURCES['FREETYPE'], 'Makefile'), join(target.builds.FREETYPE, 'Makefile') )

    if not isdir(join(target.builds.SDL, 'jni', 'freetype')):
        os.makedirs(join(target.builds.SDL, 'jni', 'freetype'))
        shutil.copy(join(ROOT_DIR, 'external', 'Android.mk.freetype'), join(target.builds.SDL, 'jni', 'freetype', 'Android.mk'))

    # Update projects files - required in case SDL project files become outdated.
    if isfile(join(target.builds.SDL, 'build.xml')):
        os.unlink(join(target.builds.SDL, 'build.xml'))
    cmd = 'android update project -t %s -p %s' % (env['TARGET'], target.builds.SDL)
    Popen(shlex.split(cmd)).communicate()


def make(env, target):
    ncpu = multiprocessing.cpu_count()
    # Build freetype
    if not isfile(join(target.builds.FREETYPE, 'config.mk')):
        cflags = env['CFLAGS'] + ' -std=gnu99'
        cmd = './configure --enable-silent-rules LDFLAGS="-static-libgcc" CFLAGS="%s" --without-bzip2 --host=arm-eabi --build=i686-pc-linux-gnu --disable-shared --enable-static --with-sysroot=%s/platforms/%s/arch-arm --prefix="%s"'% (cflags, ANDROID_NDK, env['TARGET'], target.dist)
        Popen(shlex.split(cmd), cwd = target.builds.FREETYPE, env=env).communicate()
    cmd = 'make -j%d V=0' % ncpu
    Popen(shlex.split(cmd), cwd = target.builds.FREETYPE, env=env).communicate()
    if isfile(join(target.builds.FREETYPE, 'objs', '.libs', 'libfreetype.a')):
        cmd = 'rsync -aqut --exclude .svn --exclude .hg %s/ %s' % (join(target.builds.FREETYPE, 'include'), join(target.builds.SDL, 'jni', 'freetype', 'include'))
        Popen(shlex.split(cmd)).communicate()
        shutil.copy(join(target.builds.FREETYPE, 'objs', '.libs', 'libfreetype.a'), join(target.builds.SDL, 'jni', 'freetype', 'libfreetype.a'))
    else:
        error('Error compiling freetype')
        exit()


    cmd = 'ndk-build'
    env['CFLAGS'] = env['CFLAGS'] + ' -DSDL_ANDROID_BLOCK_ON_PAUSE=1'
    Popen(shlex.split(cmd), cwd = target.builds.SDL, env=env).communicate()
    # Copy some files to the skeleton directory
    if isdir(join(target.dist, 'jni', 'SDL', 'include')):
        shutil.rmtree(join(target.dist, 'jni', 'SDL', 'include'))
    if isdir(join(target.dist, 'jni', 'SDL', 'src')):
        shutil.rmtree(join(target.dist, 'jni', 'SDL', 'src'))

    try:
        shutil.copytree(join(target.builds.SDL, 'jni', 'SDL', 'include'), join(target.dist, 'jni', 'SDL', 'include'))
        shutil.copytree(join(target.builds.SDL, 'jni', 'SDL', 'src'), join(target.dist, 'jni', 'SDL', 'src'))
        shutil.copy(join(target.builds.SDL, 'libs', 'armeabi', 'libSDL2.so'), join(target.dist, 'jni', 'SDL', 'libSDL2.so'))
        shutil.copy(join(target.builds.SDL, 'libs', 'armeabi', 'libSDL2_image.so'), join(target.dist, 'jni', 'SDL_image', 'libSDL2_image.so'))
        shutil.copy(join(target.builds.SDL, 'libs', 'armeabi', 'libSDL2_ttf.so'), join(target.dist, 'jni', 'SDL_ttf', 'libSDL2_ttf.so'))
        shutil.copy(join(target.builds.SDL, 'jni', 'SDL_image', 'SDL_image.h'), join(target.dist, 'jni', 'SDL_image', 'SDL_image.h'))
        shutil.copy(join(target.builds.SDL, 'jni', 'SDL_ttf', 'SDL_ttf.h'), join(target.dist, 'jni', 'SDL_ttf', 'SDL_ttf.h'))
        log('SDL built successfully')
    except:
        error('Error while building SDL for target')
        exit()

    return True