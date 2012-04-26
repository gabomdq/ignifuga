#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Build SDL for Android
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import os, shlex, shutil
from os.path import *
from subprocess import Popen, PIPE
from schafer import log, error, prepare_source, SED_CMD, ROOT_DIR

def prepare(DIST_DIR, SOURCES, BUILDS):
    patch_target = not isdir(BUILDS['SDL']) # Keep count if we are starting from scratch to avoid rebuilding excessively too many files
    prepare_source('SDL Android Skeleton', join(SOURCES['SDL'], 'android-project'), BUILDS['SDL'])
    if patch_target:
        cmd = SED_CMD + """'s|^target=.*|target=android-7|g' %s""" % (join(BUILDS['SDL'], 'default.properties'),)
        Popen(shlex.split(cmd), cwd = BUILDS['SDL']).communicate()
        if isdir(join(BUILDS['SDL'], 'jni', 'src')):
            shutil.rmtree(join(BUILDS['SDL'], 'jni', 'src'))


    # Copy SDL and SDL_image to the android project structure
    prepare_source('SDL', SOURCES['SDL'], join(BUILDS['SDL'], 'jni', 'SDL'))
    if patch_target:
        shutil.copy(join(BUILDS['SDL'], 'jni', 'SDL', 'include', 'SDL_config_android.h'), join(BUILDS['SDL'], 'jni', 'SDL', 'include', 'SDL_config.h'))
    prepare_source('libpng', SOURCES['PNG'], join(BUILDS['SDL'], 'jni', 'png'))
    prepare_source('libjpeg', SOURCES['JPG'], join(BUILDS['SDL'], 'jni', 'jpeg'))
    prepare_source('SDL_image', SOURCES['SDL_IMAGE'], join(BUILDS['SDL'], 'jni', 'SDL_image'))
    if not isfile(join(BUILDS['SDL'], 'jni', 'SDL_image', 'Android.mk')):
        shutil.copy(join(ROOT_DIR, 'external', 'Android.mk.SDL_image'), join(BUILDS['SDL'], 'jni', 'SDL_image', 'Android.mk'))

    prepare_source('SDL_ttf', SOURCES['SDL_TTF'], join(BUILDS['SDL'], 'jni', 'SDL_ttf'))
    prepare_source('freetype', SOURCES['FREETYPE'], BUILDS['FREETYPE'])
    shutil.copy(join(SOURCES['FREETYPE'], 'Makefile'), join(BUILDS['FREETYPE'], 'Makefile') )

    if not isdir(join(BUILDS['SDL'], 'jni', 'freetype')):
        os.makedirs(join(BUILDS['SDL'], 'jni', 'freetype'))
        shutil.copy(join(ROOT_DIR, 'external', 'Android.mk.freetype'), join(BUILDS['SDL'], 'jni', 'freetype', 'Android.mk'))

def make(env, DIST_DIR, BUILDS):
    # Build freetype
    if not isfile(join(BUILDS['FREETYPE'], 'config.mk')):
        env['CFLAGS'] = env['CFLAGS'] + ' -std=gnu99'
        cmd = './configure --enable-silent-rules LDFLAGS="-static-libgcc" --without-bzip2 --host=arm-eabi --build=i686-pc-linux-gnu --disable-shared --enable-static --with-sysroot=%s/platforms/android-5/arch-arm --prefix="%s"'% (ANDROID_NDK,DIST_DIR)
        Popen(shlex.split(cmd), cwd = BUILDS['FREETYPE'], env=env).communicate()
    cmd = 'make V=0'
    Popen(shlex.split(cmd), cwd = BUILDS['FREETYPE'], env=env).communicate()
    if isfile(join(BUILDS['FREETYPE'], 'objs', '.libs', 'libfreetype.a')):
        cmd = 'rsync -aqut --exclude .svn --exclude .hg %s/ %s' % (join(BUILDS['FREETYPE'], 'include'), join(BUILDS['SDL'], 'jni', 'freetype', 'include'))
        Popen(shlex.split(cmd)).communicate()
        shutil.copy(join(BUILDS['FREETYPE'], 'objs', '.libs', 'libfreetype.a'), join(BUILDS['SDL'], 'jni', 'freetype', 'libfreetype.a'))
    else:
        error('Error compiling freetype')
        exit()


    cmd = 'ndk-build'
    Popen(shlex.split(cmd), cwd = BUILDS['SDL'], env=env).communicate()
    # Copy some files to the skeleton directory
    if isdir(join(DIST_DIR, 'jni', 'SDL', 'include')):
        shutil.rmtree(join(DIST_DIR, 'jni', 'SDL', 'include'))
    if isdir(join(DIST_DIR, 'jni', 'SDL', 'src')):
        shutil.rmtree(join(DIST_DIR, 'jni', 'SDL', 'src'))

    try:
        shutil.copytree(join(BUILDS['SDL'], 'jni', 'SDL', 'include'), join(DIST_DIR, 'jni', 'SDL', 'include'))
        shutil.copytree(join(BUILDS['SDL'], 'jni', 'SDL', 'src'), join(DIST_DIR, 'jni', 'SDL', 'src'))
        shutil.copy(join(BUILDS['SDL'], 'libs', 'armeabi', 'libSDL2.so'), join(DIST_DIR, 'jni', 'SDL', 'libSDL2.so'))
        shutil.copy(join(BUILDS['SDL'], 'libs', 'armeabi', 'libSDL2_image.so'), join(DIST_DIR, 'jni', 'SDL_image', 'libSDL2_image.so'))
        shutil.copy(join(BUILDS['SDL'], 'libs', 'armeabi', 'libSDL2_ttf.so'), join(DIST_DIR, 'jni', 'SDL_ttf', 'libSDL2_ttf.so'))
        shutil.copy(join(BUILDS['SDL'], 'jni', 'SDL_image', 'SDL_image.h'), join(DIST_DIR, 'jni', 'SDL_image', 'SDL_image.h'))
        shutil.copy(join(BUILDS['SDL'], 'jni', 'SDL_ttf', 'SDL_ttf.h'), join(DIST_DIR, 'jni', 'SDL_ttf', 'SDL_ttf.h'))
        log('SDL built successfully')
    except:
        error('Error while building SDL for target')
        exit()

    return True