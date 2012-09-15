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

def prepare(env, target, options):

    # SDL and friends needs some special handling as they only build using ndk-build
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
    prepare_source('SDL_image', SOURCES['SDL_IMAGE'], join(target.builds.SDL, 'jni', 'SDL_image'))
    prepare_source('SDL_ttf', SOURCES['SDL_TTF'], join(target.builds.SDL, 'jni', 'SDL_ttf'))
    prepare_source('freetype', SOURCES['FREETYPE'], target.builds.FREETYPE)
    shutil.copy(join(SOURCES['FREETYPE'], 'Makefile'), join(target.builds.FREETYPE, 'Makefile') )

    # Update projects files - required in case SDL project files become outdated.
    if isfile(join(target.builds.SDL, 'build.xml')):
        os.unlink(join(target.builds.SDL, 'build.xml'))
    cmd = 'android update project -t %s -p %s' % (env['TARGET'], target.builds.SDL)
    Popen(shlex.split(cmd)).communicate()

    ####################################################
    # The following libs build ok using ./configure;make
    ####################################################
    prepare_source('zlib', SOURCES['ZLIB'], target.builds.ZLIB)
    prepare_source('libpng', SOURCES['PNG'], target.builds.PNG)
    prepare_source('libjpeg-turbo', SOURCES['JPGTURBO'], target.builds.JPGTURBO)

    if options.oggdecoder == 'VORBIS' and isfile(join(target.builds.OGGDECODER, 'vorbisidec.pc.in')):
        cmd = 'rm -rf %s' % target.builds.OGGDECODER
        Popen(shlex.split(cmd), env=env).communicate()
        cmd = 'rm -rf %s' % join(target.builds.SDL, 'jni', 'SDL_mixer')
        Popen(shlex.split(cmd), env=env).communicate()
    elif options.oggdecoder != 'VORBIS' and isfile(join(target.builds.OGGDECODER, 'vorbisenc.pc.in')):
        cmd = 'rm -rf %s' % target.builds.OGGDECODER
        Popen(shlex.split(cmd), env=env).communicate()
        cmd = 'rm -rf %s' % join(target.builds.SDL, 'jni', 'SDL_mixer')
        Popen(shlex.split(cmd), env=env).communicate()

    prepare_source('OGG', SOURCES['LIBOGG'], target.builds.LIBOGG)
    prepare_source('VORBIS', SOURCES[options.oggdecoder], target.builds.OGGDECODER)
    prepare_source('SDL_mixer', SOURCES['SDL_MIXER'], join(target.builds.SDL, 'jni', 'SDL_mixer'))



def make(env, target, options):
    ncpu = multiprocessing.cpu_count()
    jni_dir = join(target.builds.SDL, 'jni')
    # Build zlib
    if isfile(join(jni_dir, 'zlib', 'libz.a')):
        os.remove(join(jni_dir, 'zlib', 'libz.a'))
    if not isfile(join(target.builds.ZLIB, 'Makefile')):
        cmd = './configure --static --prefix="%s" --includedir="%s" --libdir="%s"'% (jni_dir,join(jni_dir, 'zlib'), join(jni_dir, 'zlib'))
        Popen(shlex.split(cmd), cwd = target.builds.ZLIB, env=env).communicate()
    cmd = 'make -j%d install' % ncpu
    Popen(shlex.split(cmd), cwd = target.builds.ZLIB, env=env).communicate()
    if isfile(join(jni_dir, 'zlib', 'libz.a')):
        log('zlib built successfully')
    else:
        error('Problem building zlib')
        exit()

    # Build libpng
    if isfile(join(jni_dir, 'png', 'libpng.a')):
        os.remove(join(jni_dir, 'png', 'libpng.a'))

    if not isfile(join(target.builds.PNG, 'Makefile')):
        cmd = './configure --enable-static --disable-shared --prefix="%s" --host=arm-eabi --build=i686-pc-linux-gnu --with-zlib-prefix="%s" --includedir="%s" --libdir="%s"'% (jni_dir,target.builds.ZLIB, join(jni_dir, 'png'), join(jni_dir, 'png'))
        Popen(shlex.split(cmd), cwd = target.builds.PNG, env=env).communicate()

    cmd = 'make -j%d install ' % ncpu
    Popen(shlex.split(cmd), cwd = target.builds.PNG, env=env).communicate()

    if isfile(join(jni_dir, 'png', 'libpng.a')):
        log('libpng built successfully')
    else:
        error('Problem building libpng')
        exit()

    # Build libjpeg-turbo
    if isfile(join(jni_dir, 'jpeg', 'libturbojpeg.a')):
        os.remove(join(jni_dir, 'jpeg', 'libturbojpeg.a'))
    if isfile(join(jni_dir, 'jpeg', 'libjpeg.a')):
        os.remove(join(jni_dir, 'jpeg', 'libjpeg.a'))

    if not isfile(join(target.builds.JPGTURBO, 'Makefile')):
        cmd = './configure --enable-silent-rules LDFLAGS="-static-libgcc" LIBTOOL= --host=arm-eabi --build=i686-pc-linux-gnu --disable-shared --enable-static --prefix="%s" --includedir="%s" --libdir="%s"'% (jni_dir,join(jni_dir, 'jpeg'), join(jni_dir, 'jpeg'))
        Popen(shlex.split(cmd), cwd = target.builds.JPGTURBO, env=env).communicate()

    cmd = 'make -j%d install V=0 ' % ncpu
    Popen(shlex.split(cmd), cwd = target.builds.JPGTURBO, env=env).communicate()

    if isfile(join(jni_dir, 'jpeg', 'libturbojpeg.a')) and isfile(join(jni_dir, 'jpeg', 'libjpeg.a')) :
        log('libjpeg-turbo built successfully')
    else:
        error('Problem building libjpeg-turbo')
        exit()

    # Build freetype
    if not isfile(join(target.builds.FREETYPE, 'config.mk')):
        cflags = env['CFLAGS'] + ' -std=gnu99'
        cmd = './configure --enable-silent-rules LDFLAGS="-static-libgcc" CFLAGS="%s" --without-bzip2 --host=arm-eabi --build=i686-pc-linux-gnu --disable-shared --enable-static --with-sysroot=%s/platforms/%s/arch-arm --prefix="%s" --includedir="%s" --libdir="%s"'% (cflags, ANDROID_NDK, env['TARGET'], jni_dir,join(jni_dir, 'freetype'), join(jni_dir, 'freetype'))
        Popen(shlex.split(cmd), cwd = target.builds.FREETYPE, env=env).communicate()
    cmd = 'make -j%d V=0 install' % ncpu
    Popen(shlex.split(cmd), cwd = target.builds.FREETYPE, env=env).communicate()

    if isfile(join(jni_dir, 'freetype', 'libfreetype.a')):
        log('Freetype built successfully')
    else:
        error('Error compiling Freetype')
        exit()

    # Build OGG
    if isfile(join(jni_dir, 'tremor', 'libogg.a')):
        os.remove(join(jni_dir, 'tremor', 'libogg.a'))

    if not isfile(join(target.builds.LIBOGG, 'Makefile')):
        cmd = './configure --enable-silent-rules LDFLAGS="-static-libgcc" --host=arm-eabi --build=i686-pc-linux-gnu --disable-shared --enable-static --disable-oggtest --prefix="%s" --includedir="%s" --libdir="%s"'% (jni_dir,join(jni_dir, 'ogg'), join(jni_dir, 'ogg'))
        Popen(shlex.split(cmd), cwd = target.builds.LIBOGG, env=env).communicate()

    cmd = 'make -j%d install V=0' % ncpu
    Popen(shlex.split(cmd), cwd = target.builds.LIBOGG, env=env).communicate()

    if isfile(join(jni_dir, 'tremor', 'libogg.a')):
        os.remove(join(jni_dir, 'tremor', 'libogg.a'))

    # Build OGG Decoder
    if isfile(join(jni_dir, 'tremor', 'libvorbis.a')):
        os.remove(join(jni_dir, 'tremor', 'libvorbis.a'))

    if isfile(join(jni_dir, 'tremor', 'libvorbisidec.a')):
        os.remove(join(jni_dir, 'tremor', 'libvorbisidec.a'))

    if not isfile(join(target.builds.OGGDECODER, 'configure')):
        cmd = './autogen.sh'
        Popen(shlex.split(cmd), cwd = target.builds.OGGDECODER, env=env).communicate()
        if isfile(join(target.builds.OGGDECODER, 'Makefile')):
            os.remove(join(target.builds.OGGDECODER, 'Makefile'))

    if not isfile(join(target.builds.OGGDECODER, 'Makefile')):
        cmd = './configure --enable-silent-rules LDFLAGS="-static-libgcc" --host=arm-eabi --build=i686-pc-linux-gnu --disable-shared --enable-static --disable-oggtest --prefix="%s" --includedir="%s" --libdir="%s"' % (jni_dir,join(jni_dir, 'tremor'), join(jni_dir, 'tremor'))
        Popen(shlex.split(cmd), cwd = target.builds.OGGDECODER, env=env).communicate()

    cmd = 'make -j%d install V=0' % ncpu
    Popen(shlex.split(cmd), cwd = target.builds.OGGDECODER, env=env).communicate()

    if options.oggdecoder == 'VORBIS':
        sdl_mixer_ogg = '--enable-music-ogg --disable-music-ogg-tremor'
        # Libvorbis
        if isfile(join(jni_dir, 'tremor', 'libvorbis.a')):
            log('Libvorbis built successfully')
        else:
            error('Problem building Libvorbis')
            exit(1)
    else:
        sdl_mixer_ogg = '--enable-music-ogg-tremor'
        # Tremor
        if isfile(join(jni_dir, 'tremor', 'libvorbisidec.a')):
            log('Tremor built successfully')
        else:
            error('Problem building Tremor')
            exit(1)


    # SDL, SDL_image, SDL_ttf and SDL_mixer are built using Android.mk files and ndk-build

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
        shutil.copy(join(target.builds.SDL, 'libs', 'armeabi', 'libSDL2_mixer.so'), join(target.dist, 'jni', 'SDL_mixer', 'libSDL2_mixer.so'))
        shutil.copy(join(target.builds.SDL, 'jni', 'SDL_image', 'SDL_image.h'), join(target.dist, 'jni', 'SDL_image', 'SDL_image.h'))
        shutil.copy(join(target.builds.SDL, 'jni', 'SDL_ttf', 'SDL_ttf.h'), join(target.dist, 'jni', 'SDL_ttf', 'SDL_ttf.h'))
        shutil.copy(join(target.builds.SDL, 'jni', 'SDL_mixer', 'SDL_mixer.h'), join(target.dist, 'jni', 'SDL_mixer', 'SDL_mixer.h'))
        log('SDL built successfully')
    except:
        error('Error while building SDL for target')
        exit()

    return True