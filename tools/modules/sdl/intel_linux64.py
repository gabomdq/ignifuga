#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Build SDL for Linux 64
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import os, shlex, shutil
from os.path import *
from subprocess import Popen, PIPE
from ..log import log, error
from schafer import SOURCES, SED_CMD
from ..util import prepare_source
import multiprocessing
from shutil import copyfile

def prepare(env, target, options):
    prepare_source('SDL', SOURCES['SDL'], target.builds.SDL)
    prepare_source('SDL_image', SOURCES['SDL_IMAGE'], target.builds.SDL_IMAGE)
    prepare_source('zlib', SOURCES['ZLIB'], target.builds.ZLIB)
    prepare_source('libpng', SOURCES['PNG'], target.builds.PNG)
    prepare_source('libjpeg-turbo', SOURCES['JPGTURBO'], target.builds.JPGTURBO)
    prepare_source('freetype', SOURCES['FREETYPE'], target.builds.FREETYPE)
    shutil.copy(join(SOURCES['FREETYPE'], 'Makefile'), join(target.builds.FREETYPE, 'Makefile') )
    prepare_source('SDL_ttf', SOURCES['SDL_TTF'], target.builds.SDL_TTF)

    if options.oggdecoder == 'VORBIS' and isfile(join(target.builds.OGGDECODER, 'vorbisidec.pc.in')):
        cmd = 'rm -rf %s' % target.builds.OGGDECODER
        Popen(shlex.split(cmd), env=env).communicate()
        cmd = 'rm -rf %s' % target.builds.SDL_MIXER
        Popen(shlex.split(cmd), env=env).communicate()
    elif options.oggdecoder != 'VORBIS' and isfile(join(target.builds.OGGDECODER, 'vorbisenc.pc.in')):
        cmd = 'rm -rf %s' % target.builds.OGGDECODER
        Popen(shlex.split(cmd), env=env).communicate()
        cmd = 'rm -rf %s' % target.builds.SDL_MIXER
        Popen(shlex.split(cmd), env=env).communicate()

    prepare_source('OGG', SOURCES['LIBOGG'], target.builds.LIBOGG)
    prepare_source('VORBIS', SOURCES[options.oggdecoder], target.builds.OGGDECODER)
    prepare_source('SDL_mixer', SOURCES['SDL_MIXER'], target.builds.SDL_MIXER)



def make(env, target, options):
    ncpu = multiprocessing.cpu_count()
    # Build zlib
    if isfile(join(target.dist, 'lib', 'libz.a')):
        os.remove(join(target.dist, 'lib', 'libz.a'))
    if not isfile(join(target.builds.ZLIB, 'Makefile')):
        cmd = './configure --static --prefix="%s"'% (target.dist,)
        Popen(shlex.split(cmd), cwd = target.builds.ZLIB, env=env).communicate()
    cmd = 'make -j%d install' % ncpu
    Popen(shlex.split(cmd), cwd = target.builds.ZLIB, env=env).communicate()
    if isfile(join(target.dist, 'lib', 'libz.a')):
        log('zlib built successfully')
    else:
        error('Problem building zlib')
        exit()

    # Build libpng
    if isfile(join(target.dist, 'lib', 'libpng.a')):
        os.remove(join(target.dist, 'lib', 'libpng.a'))

    if not isfile(join(target.builds.PNG, 'Makefile')):
        cmd = './configure --enable-static --disable-shared --prefix="%s" --with-zlib-prefix="%s"'% (target.dist,target.builds.ZLIB)
        Popen(shlex.split(cmd), cwd = target.builds.PNG, env=env).communicate()

    cmd = 'make -j%d install ' % ncpu
    Popen(shlex.split(cmd), cwd = target.builds.PNG, env=env).communicate()

    if isfile(join(target.dist, 'lib', 'libpng.a')):
        log('libpng built successfully')
    else:
        error('Problem building libpng')
        exit()

    # Build libjpeg-turbo
    if isfile(join(target.dist, 'lib', 'libturbojpeg.a')):
        os.remove(join(target.dist, 'lib', 'libturbojpeg.a'))
    if isfile(join(target.dist, 'lib', 'libjpeg.a')):
        os.remove(join(target.dist, 'lib', 'libjpeg.a'))

    if not isfile(join(target.builds.JPGTURBO, 'Makefile')):
        cmd = './configure --enable-silent-rules LDFLAGS="-static-libgcc" LIBTOOL= --disable-shared --enable-static --prefix="%s"'% (target.dist,)
        Popen(shlex.split(cmd), cwd = target.builds.JPGTURBO, env=env).communicate()

    cmd = 'make -j%d install V=0 ' % ncpu
    Popen(shlex.split(cmd), cwd = target.builds.JPGTURBO, env=env).communicate()

    if isfile(join(target.dist, 'lib', 'libturbojpeg.a')) and isfile(join(target.dist, 'lib', 'libjpeg.a')) :
        log('libjpeg-turbo built successfully')
    else:
        error('Problem building libjpeg-turbo')
        exit()

    # Build SDL
    if isfile(join(target.dist, 'lib', 'libSDL2.a')):
        os.remove(join(target.dist, 'lib', 'libSDL2.a'))

    if not isfile(join(target.builds.SDL, 'Makefile')):
        cmd = './configure --enable-silent-rules LDFLAGS="-static-libgcc" --disable-shared --enable-static --prefix="%s"'% (target.dist,)
        Popen(shlex.split(cmd), cwd = target.builds.SDL, env=env).communicate()
    cmd = 'make -j%d V=0' % ncpu
    Popen(shlex.split(cmd), cwd = target.builds.SDL, env=env).communicate()
    cmd = 'make V=0 install'
    Popen(shlex.split(cmd), cwd = target.builds.SDL, env=env).communicate()

    if isfile(join(target.dist, 'lib', 'libSDL2.a')):
        log('SDL built successfully')
    else:
        error('Problem building SDL')
        exit()

    # Build SDL_Image
    if isfile(join(target.dist, 'lib', 'libSDL2_image.a')):
        os.remove(join(target.dist, 'lib', 'libSDL2_image.a'))

    if not isfile(join(target.builds.SDL_IMAGE, 'Makefile')):
        cmd = join(target.dist, 'bin', 'libpng-config' ) + ' --static --cflags'
        pngcf = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
        cmd = join(target.dist, 'bin', 'libpng-config' ) + ' --static --ldflags'
        pngld = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
        cmd = './configure --enable-silent-rules CFLAGS="%s" LDFLAGS="-static-libgcc" LIBPNG_CFLAGS="%s" LIBPNG_LIBS="%s -ljpeg" --disable-png-shared --disable-jpg-shared --disable-shared --enable-static --with-sdl-prefix="%s" --prefix="%s"'% (env['CFLAGS'], pngcf, pngld, target.dist, target.dist)
        Popen(shlex.split(cmd), cwd = target.builds.SDL_IMAGE, env=env).communicate()

    cmd = 'make -j%d V=0' % ncpu
    Popen(shlex.split(cmd), cwd = target.builds.SDL_IMAGE, env=env).communicate()
    cmd = 'make V=0 install'
    Popen(shlex.split(cmd), cwd = target.builds.SDL_IMAGE, env=env).communicate()
    if isfile(join(target.dist, 'lib', 'libSDL2_image.a')):
        log('SDL Image built successfully')
    else:
        error('Problem building SDL Image')
        exit()

    # Build freetype
    if isfile(join(target.dist, 'lib', 'libfreetype.a')):
        os.remove(join(target.dist, 'lib', 'libfreetype.a'))

    if not isfile(join(target.builds.FREETYPE, 'config.mk')):
        cmd = './configure --enable-silent-rules LDFLAGS="-static-libgcc" --without-bzip2 --disable-shared --enable-static --with-sysroot=%s --prefix="%s"'% (target.dist,target.dist)
        Popen(shlex.split(cmd), cwd = target.builds.FREETYPE, env=env).communicate()
    cmd = 'make -j%d V=0' % ncpu
    Popen(shlex.split(cmd), cwd = target.builds.FREETYPE, env=env).communicate()
    cmd = 'make V=0 install'
    Popen(shlex.split(cmd), cwd = target.builds.FREETYPE, env=env).communicate()
    if isfile(join(target.dist, 'lib', 'libfreetype.a')):
        log('Freetype built successfully')
    else:
        error('Problem building Freetype')
        exit()

    # Build SDL_ttf
    if isfile(join(target.dist, 'lib', 'libSDL2_ttf.a')):
        os.remove(join(target.dist, 'lib', 'libSDL2_ttf.a'))

    if not isfile(join(target.builds.SDL_TTF, 'configure')):
        cmd = './autogen.sh'
        Popen(shlex.split(cmd), cwd = target.builds.SDL_TTF, env=env).communicate()

    if not isfile(join(target.builds.SDL_TTF, 'Makefile')):
        cmd = './configure --enable-silent-rules LDFLAGS="-static-libgcc" --disable-shared --enable-static --with-sdl-prefix="%s" --with-freetype-prefix="%s" --prefix="%s"'% (target.dist, target.dist, target.dist)
        Popen(shlex.split(cmd), cwd = target.builds.SDL_TTF, env=env).communicate()
        # Disable showfont/glfont to avoid the dependencies they carry
        cmd = 'sed -e "s|.*showfont.*||g" -i "" %s' % (join(target.builds.SDL_TTF, 'Makefile'),)
        Popen(shlex.split(cmd), cwd = target.builds.SDL_TTF, env=env).communicate()
        cmd = 'sed -e "s|.*glfont.*||g" -i "" %s' % (join(target.builds.SDL_TTF, 'Makefile'),)
        Popen(shlex.split(cmd), cwd = target.builds.SDL_TTF, env=env).communicate()
    cmd = 'make -j%d V=0' % ncpu
    Popen(shlex.split(cmd), cwd = target.builds.SDL_TTF, env=env).communicate()
    cmd = 'make V=0 install'
    Popen(shlex.split(cmd), cwd = target.builds.SDL_TTF, env=env).communicate()
    if isfile(join(target.dist, 'lib', 'libSDL2_ttf.a')):
        log('SDL TTF built successfully')
    else:
        error('Problem building SDL TTF')
        exit()

    # Build OGG
    if isfile(join(target.dist, 'lib', 'libogg.a')):
        os.remove(join(target.dist, 'lib', 'libogg.a'))

    if not isfile(join(target.builds.LIBOGG, 'Makefile')):
        cmd = './configure --enable-silent-rules LDFLAGS="-static-libgcc" --disable-shared --enable-static --disable-oggtest --prefix="%s"'% (target.dist)
        Popen(shlex.split(cmd), cwd = target.builds.LIBOGG, env=env).communicate()

    cmd = 'make -j%d install V=0' % ncpu
    Popen(shlex.split(cmd), cwd = target.builds.LIBOGG, env=env).communicate()

    if isfile(join(target.dist, 'lib', 'libogg.a')):
        log('Libogg built successfully')
    else:
        error('Problem building Libogg')
        exit()

    # Build OGG Decoder
    if isfile(join(target.dist, 'lib', 'libvorbis.a')):
        os.remove(join(target.dist, 'lib', 'libvorbis.a'))

    if isfile(join(target.dist, 'lib', 'libvorbisidec.a')):
        os.remove(join(target.dist, 'lib', 'libvorbisidec.a'))

    if not isfile(join(target.builds.OGGDECODER, 'configure')):
        cmd = './autogen.sh'
        Popen(shlex.split(cmd), cwd = target.builds.OGGDECODER, env=env).communicate()
        if isfile(join(target.builds.OGGDECODER, 'Makefile')):
            os.remove(join(target.builds.OGGDECODER, 'Makefile'))

    if not isfile(join(target.builds.OGGDECODER, 'Makefile')):
        cmd = './configure --enable-silent-rules LDFLAGS="-static-libgcc" --disable-shared --enable-static --disable-oggtest --prefix="%s"'% (target.dist)
        Popen(shlex.split(cmd), cwd = target.builds.OGGDECODER, env=env).communicate()

    cmd = 'make -j%d install V=0' % ncpu
    Popen(shlex.split(cmd), cwd = target.builds.OGGDECODER, env=env).communicate()

    if options.oggdecoder == 'VORBIS':
        sdl_mixer_ogg = '--enable-music-ogg --disable-music-ogg-tremor'
        # Libvorbis
        if isfile(join(target.dist, 'lib', 'libvorbis.a')):
            log('Libvorbis built successfully')
        else:
            error('Problem building Libvorbis')
            exit(1)
    else:
        sdl_mixer_ogg = '--enable-music-ogg-tremor'
        # Tremor
        if isfile(join(target.dist, 'lib', 'libvorbisidec.a')):
            log('Tremor built successfully')
        else:
            error('Problem building Tremor')
            exit(1)

    # Build SDL_mixer

    if not isfile(join(target.builds.SDL_MIXER, 'Makefile')):
        cmd = './configure --enable-silent-rules LDFLAGS="-static-libgcc %s" CFLAGS="%s" --disable-shared --enable-static --with-sdl-prefix="%s" --prefix="%s" --exec-prefix="%s" %s'% (env['CFLAGS'], env['LDFLAGS'], target.dist, target.dist, target.dist, sdl_mixer_ogg)
        Popen(shlex.split(cmd), cwd = target.builds.SDL_MIXER, env=env).communicate()

    cmd = 'make -j%d install V=0' % ncpu
    Popen(shlex.split(cmd), cwd = target.builds.SDL_MIXER, env=env).communicate()

    if isfile(join(target.dist, 'lib', 'libSDL2_mixer.a')):
        log('SDL Mixer built successfully')
    else:
        error('Problem building SDL Mixer')
        exit(1)

    return True