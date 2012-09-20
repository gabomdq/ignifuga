#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Build SDL in the most platform agnostic possible way
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import os, shlex, shutil
from os.path import *
from subprocess import Popen, PIPE
from ..log import log, error
from schafer import prepare_source, SED_CMD, SOURCES
import multiprocessing


def prepare_common(env, target, options):
    prepare_source('zlib', SOURCES['ZLIB'], target.builds.ZLIB)
    prepare_source('libpng', SOURCES['PNG'], target.builds.PNG)
    prepare_source('libjpeg-turbo', SOURCES['JPGTURBO'], target.builds.JPGTURBO)
    prepare_source('SDL', SOURCES['SDL'], target.builds.SDL)
    prepare_source('SDL_image', SOURCES['SDL_IMAGE'], target.builds.SDL_IMAGE)
    prepare_source('SDL_ttf', SOURCES['SDL_TTF'], target.builds.SDL_TTF)
    prepare_source('freetype', SOURCES['FREETYPE'], target.builds.FREETYPE)
    shutil.copy(join(SOURCES['FREETYPE'], 'Makefile'), join(target.builds.FREETYPE, 'Makefile') )

    prepare_source('OGG', SOURCES['LIBOGG'], target.builds.LIBOGG)
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

    prepare_source('VORBIS', SOURCES[options.oggdecoder], target.builds.OGGDECODER)
    prepare_source('SDL_mixer', SOURCES['SDL_MIXER'], target.builds.SDL_MIXER)

def make_common(env, target, options, libs=['zlib', 'png', 'jpeg', 'sdl', 'sdl_image', 'freetype', 'sdl_ttf', 'ogg', 'oggdecoder', 'sdl_mixer']):
    ncpu = multiprocessing.cpu_count()
    env['TARGET_DIST'] = target.dist
    env['TARGET_ZLIB'] = target.builds.ZLIB

    if 'zlib' in libs:
        # Build zlib
        if isfile(join(target.dist, 'lib', 'libz.a')):
            os.remove(join(target.dist, 'lib', 'libz.a'))
        if not isfile(join(target.builds.ZLIB, 'Makefile')):
            cmd = './configure --static --prefix="%(TARGET_DIST)s"' % env
            Popen(shlex.split(cmd), cwd = target.builds.ZLIB, env=env).communicate()
        cmd = 'make -j%d install' % ncpu
        Popen(shlex.split(cmd), cwd = target.builds.ZLIB, env=env).communicate()
        if isfile(join(target.dist, 'lib', 'libz.a')):
            log('zlib built successfully')
        else:
            error('Problem building zlib')
            exit()

    if 'png' in libs:
        # Build libpng
        if isfile(join(target.dist, 'lib', 'libpng.a')):
            os.remove(join(target.dist, 'lib', 'libpng.a'))

        if not isfile(join(target.builds.PNG, 'Makefile')):
            cmd = './configure --enable-static --disable-shared --prefix="%(TARGET_DIST)s" --with-zlib-prefix="%(TARGET_ZLIB)s" %(HOST)s' % env
            Popen(shlex.split(cmd), cwd = target.builds.PNG, env=env).communicate()

        cmd = 'make -j%d install ' % ncpu
        Popen(shlex.split(cmd), cwd = target.builds.PNG, env=env).communicate()

        if isfile(join(target.dist, 'lib', 'libpng.a')):
            log('libpng built successfully')
        else:
            error('Problem building libpng')
            exit()

    if 'jpeg' in libs:
        # Build libjpeg-turbo
        if isfile(join(target.dist, 'lib', 'libturbojpeg.a')):
            os.remove(join(target.dist, 'lib', 'libturbojpeg.a'))
        if isfile(join(target.dist, 'lib', 'libjpeg.a')):
            os.remove(join(target.dist, 'lib', 'libjpeg.a'))

        if not isfile(join(target.builds.JPGTURBO, 'Makefile')):
            cmd = './configure --enable-silent-rules %(HOST)s CFLAGS="%(CFLAGS)s" LDFLAGS="-static-libgcc %(LDFLAGS)s" LIBTOOL= --disable-shared --enable-static --prefix="%(TARGET_DIST)s"' % env
            Popen(shlex.split(cmd), cwd = target.builds.JPGTURBO, env=env).communicate()

        cmd = 'make -j%d install V=0 ' % ncpu
        Popen(shlex.split(cmd), cwd = target.builds.JPGTURBO, env=env).communicate()

        if isfile(join(target.dist, 'lib', 'libturbojpeg.a')) and isfile(join(target.dist, 'lib', 'libjpeg.a')) :
            log('libjpeg-turbo built successfully')
        else:
            error('Problem building libjpeg-turbo')
            exit()

    # Build SDL
    if 'sdl' in libs:
        if isfile(join(target.dist, 'lib', 'libSDL2.a')):
            os.remove(join(target.dist, 'lib', 'libSDL2.a'))

        if not isfile(join(target.builds.SDL, 'Makefile')):
            cmd = './configure --enable-silent-rules %(HOST)s CFLAGS="%(CFLAGS)s" LDFLAGS="-static-libgcc %(LDFLAGS)s" --disable-shared --enable-static --prefix="%(TARGET_DIST)s"' % env
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
    if 'sdl_image' in libs:
        if isfile(join(target.dist, 'lib', 'libSDL2_image.a')):
            os.remove(join(target.dist, 'lib', 'libSDL2_image.a'))

        if not isfile(join(target.builds.SDL_IMAGE, 'Makefile')):
            cmd = join(target.dist, 'bin', 'libpng-config' ) + ' --static --cflags'
            env['LIBPNG_CFLAGS'] = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
            cmd = join(target.dist, 'bin', 'libpng-config' ) + ' --static --ldflags'
            env['LIBPNG_LDFLAGS'] = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]

            cmd = './configure --disable-imageio --enable-silent-rules %(HOST)s CFLAGS="%(CFLAGS)s" LDFLAGS="-static-libgcc %(LDFLAGS)s" LIBPNG_CFLAGS="%(LIBPNG_CFLAGS)s" LIBPNG_LIBS="%(LIBPNG_LDFLAGS)s -ljpeg" --disable-png-shared --disable-jpg-shared --disable-shared --enable-static --with-sdl-prefix="%(TARGET_DIST)s" --prefix="%(TARGET_DIST)s"' % env
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
    if 'freetype' in libs:
        if isfile(join(target.dist, 'lib', 'libfreetype.a')):
            os.remove(join(target.dist, 'lib', 'libfreetype.a'))

        if not isfile(join(target.builds.FREETYPE, 'config.mk')):
            cmd = './configure --enable-silent-rules %(HOST)s LDFLAGS="-static-libgcc %(LDFLAGS)s" CFLAGS="%(CFLAGS)s" --without-bzip2 --disable-shared --enable-static %(WITH_SYSROOT)s --prefix="%(TARGET_DIST)s"' % env
            print cmd
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
    if 'sdl_ttf' in libs:
        if isfile(join(target.dist, 'lib', 'libSDL2_ttf.a')):
            os.remove(join(target.dist, 'lib', 'libSDL2_ttf.a'))

        if not isfile(join(target.builds.SDL_TTF, 'configure')):
            cmd = './autogen.sh'
            Popen(shlex.split(cmd), cwd = target.builds.SDL_TTF, env=env).communicate()

        if not isfile(join(target.builds.SDL_TTF, 'Makefile')):
            cmd = './configure --enable-silent-rules %(HOST)s LDFLAGS="-static-libgcc %(LDFLAGS)s" --disable-shared --enable-static --with-sdl-prefix="%(TARGET_DIST)s" --with-freetype-prefix="%(TARGET_DIST)s" --prefix="%(TARGET_DIST)s"' % env
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
    if 'ogg' in libs:
        if isfile(join(target.dist, 'lib', 'libogg.a')):
            os.remove(join(target.dist, 'lib', 'libogg.a'))

        if not isfile(join(target.builds.LIBOGG, 'Makefile')):
            cmd = './configure --enable-silent-rules %(HOST)s LDFLAGS="-static-libgcc %(LDFLAGS)s" --disable-shared --enable-static --disable-oggtest --prefix="%(TARGET_DIST)s"' % env
            Popen(shlex.split(cmd), cwd = target.builds.LIBOGG, env=env).communicate()

        cmd = 'make -j%d install V=0' % ncpu
        Popen(shlex.split(cmd), cwd = target.builds.LIBOGG, env=env).communicate()

        if isfile(join(target.dist, 'lib', 'libogg.a')):
            log('Libogg built successfully')
        else:
            error('Problem building Libogg')
            exit()

    if 'oggdecoder' in libs:
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
            cmd = './configure --enable-silent-rules %(HOST)s LDFLAGS="-static-libgcc %(LDFLAGS)s" --disable-shared --enable-static --disable-oggtest --prefix="%(TARGET_DIST)s"' % env
            Popen(shlex.split(cmd), cwd = target.builds.OGGDECODER, env=env).communicate()

        cmd = 'make -j%d install V=0' % ncpu
        Popen(shlex.split(cmd), cwd = target.builds.OGGDECODER, env=env).communicate()
        if options.oggdecoder != 'VORBIS':
            # Make a couple of symlinks
            tremor_include_dir = join(target.dist, 'include', 'tremor')
            if not isdir(tremor_include_dir):
                os.makedirs(tremor_include_dir)

            if not exists(join(tremor_include_dir, 'ivorbisfile.h')):
                os.symlink(join(target.dist, 'include', 'ivorbisfile.h'), join(tremor_include_dir, 'ivorbisfile.h'))
            if not exists(join(tremor_include_dir, 'ivorbiscodec.h')):
                os.symlink(join(target.dist, 'include', 'ivorbiscodec.h'), join(tremor_include_dir, 'ivorbiscodec.h'))

        if options.oggdecoder == 'VORBIS':
            env['SDL_MIXER_OGG'] = '--enable-music-ogg --disable-music-ogg-tremor --disable-music-ogg-shared'
            # Libvorbis
            if isfile(join(target.dist, 'lib', 'libvorbis.a')):
                log('Libvorbis built successfully')
            else:
                error('Problem building Libvorbis')
                exit(1)
        else:
            env['SDL_MIXER_OGG'] = '--enable-music-ogg-tremor --disable-music-ogg-shared'
            # Tremor
            if isfile(join(target.dist, 'lib', 'libvorbisidec.a')):
                log('Tremor built successfully')
            else:
                error('Problem building Tremor')
                exit(1)

    # Build SDL_mixer
    if 'sdl_mixer' in libs:
        if not isfile(join(target.builds.SDL_MIXER, 'Makefile')):
            #LIBS="-lvorbis -logg -lm"
            cmd = './configure --enable-silent-rules %(HOST)s LDFLAGS="-static-libgcc %(LDFLAGS)s" CFLAGS="%(CFLAGS)s" --disable-shared --enable-static --with-sdl-prefix="%(TARGET_DIST)s" --prefix="%(TARGET_DIST)s" --exec-prefix="%(TARGET_DIST)s" %(SDL_MIXER_OGG)s' % env
            print cmd
            Popen(shlex.split(cmd), cwd = target.builds.SDL_MIXER, env=env).communicate()
        cmd = 'make -j%d install V=0' % ncpu
        Popen(shlex.split(cmd), cwd = target.builds.SDL_MIXER, env=env).communicate()

        if isfile(join(target.dist, 'lib', 'libSDL2_mixer.a')):
            log('SDL Mixer built successfully')
        else:
            error('Problem building SDL Mixer')
            exit(1)

    return True
