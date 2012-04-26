#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Build SDL for Linux 64
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import os, shlex, shutil
from os.path import *
from subprocess import Popen, PIPE
from schafer import log, error, prepare_source

def prepare(DIST_DIR, SOURCES, BUILDS):
    prepare_source('SDL', SOURCES['SDL'], BUILDS['SDL'])
    prepare_source('SDL_image', SOURCES['SDL_IMAGE'], BUILDS['SDL_IMAGE'])
    prepare_source('zlib', SOURCES['ZLIB'], BUILDS['ZLIB'])
    prepare_source('libpng', SOURCES['PNG'], BUILDS['PNG'])
    shutil.copy(join(BUILDS['PNG'], 'scripts', 'makefile.linux'), join(BUILDS['PNG'], 'Makefile'))
    prepare_source('libjpeg', SOURCES['JPG'], BUILDS['JPG'])
    prepare_source('freetype', SOURCES['FREETYPE'], BUILDS['FREETYPE'])
    shutil.copy(join(SOURCES['FREETYPE'], 'Makefile'), join(BUILDS['FREETYPE'], 'Makefile') )
    prepare_source('SDL_ttf', SOURCES['SDL_TTF'], BUILDS['SDL_TTF'])


def make(env, DIST_DIR, BUILDS):
    # Build zlib
    if isfile(join(DIST_DIR, 'lib', 'libz.a')):
        os.remove(join(DIST_DIR, 'lib', 'libz.a'))
    if not isfile(join(BUILDS['ZLIB'], 'Makefile')):
        cmd = './configure --static --prefix="%s"'% (DIST_DIR,)
        Popen(shlex.split(cmd), cwd = BUILDS['ZLIB'], env=env).communicate()
    cmd = 'make'
    Popen(shlex.split(cmd), cwd = BUILDS['ZLIB'], env=env).communicate()
    cmd = 'make install'
    Popen(shlex.split(cmd), cwd = BUILDS['ZLIB'], env=env).communicate()
    if isfile(join(DIST_DIR, 'lib', 'libz.a')):
        log('zlib built successfully')
    else:
        error('Problem building zlib')
        exit()

    # Build libpng
    if isfile(join(DIST_DIR, 'lib', 'libpng.a')):
        os.remove(join(DIST_DIR, 'lib', 'libpng.a'))

    cmd = 'make V=0 prefix="%s"' % (DIST_DIR,)
    Popen(shlex.split(cmd), cwd = BUILDS['PNG'], env=env).communicate()
    cmd = 'make V=0 install prefix="%s"' % (DIST_DIR,)
    Popen(shlex.split(cmd), cwd = BUILDS['PNG'], env=env).communicate()
    # Remove dynamic libraries to avoid confusions with the linker
    cmd = 'find %s -name "*.so*" -delete' % join(DIST_DIR, 'lib')
    Popen(shlex.split(cmd), cwd = join(DIST_DIR, 'lib'), env=env).communicate()

    # Build libjpeg
    if isfile(join(DIST_DIR, 'lib', 'libjpeg.a')):
        os.remove(join(DIST_DIR, 'lib', 'libjpeg.a'))

    if not isfile(join(BUILDS['JPG'], 'Makefile')):
        cmd = './configure --enable-silent-rules LDFLAGS="-static-libgcc" LIBTOOL= --disable-shared --enable-static --prefix="%s"'% (DIST_DIR,)
        Popen(shlex.split(cmd), cwd = BUILDS['JPG'], env=env).communicate()
        # Fixes for the Makefile
        cmd = SED_CMD + '"s|\./libtool||g" %s' % (join(BUILDS['JPG'], 'Makefile'))
        Popen(shlex.split(cmd), cwd = BUILDS['JPG'], env=env).communicate()
        cmd = SED_CMD + '"s|^O = lo|O = o|g" %s' % (join(BUILDS['JPG'], 'Makefile'))
        Popen(shlex.split(cmd), cwd = BUILDS['JPG'], env=env).communicate()
        cmd = SED_CMD + '"s|^A = la|A = a|g" %s' % (join(BUILDS['JPG'], 'Makefile'))
        Popen(shlex.split(cmd), cwd = BUILDS['JPG'], env=env).communicate()

    cmd = 'make V=0 '
    Popen(shlex.split(cmd), cwd = BUILDS['JPG'], env=env).communicate()
    cmd = 'make V=0 install-lib'
    Popen(shlex.split(cmd), cwd = BUILDS['JPG'], env=env).communicate()
    cmd = 'make V=0 install-headers'
    Popen(shlex.split(cmd), cwd = BUILDS['JPG'], env=env).communicate()

    if isfile(join(DIST_DIR, 'lib', 'libjpeg.a')):
        log('libjpeg built successfully')
    else:
        error('Problem building libjpeg')
        exit()

    # Build SDL
    if isfile(join(DIST_DIR, 'lib', 'libSDL2.a')):
        os.remove(join(DIST_DIR, 'lib', 'libSDL2.a'))

    if not isfile(join(BUILDS['SDL'], 'Makefile')):
        cmd = './configure --enable-silent-rules LDFLAGS="-static-libgcc" --disable-shared --enable-static --prefix="%s"'% (DIST_DIR,)
        Popen(shlex.split(cmd), cwd = BUILDS['SDL'], env=env).communicate()
    cmd = 'make V=0'
    Popen(shlex.split(cmd), cwd = BUILDS['SDL'], env=env).communicate()
    cmd = 'make V=0 install'
    Popen(shlex.split(cmd), cwd = BUILDS['SDL'], env=env).communicate()

    if isfile(join(DIST_DIR, 'lib', 'libSDL2.a')):
        log('SDL built successfully')
    else:
        error('Problem building SDL')
        exit()

    # Build SDL_Image
    if isfile(join(DIST_DIR, 'lib', 'libSDL2_image.a')):
        os.remove(join(DIST_DIR, 'lib', 'libSDL2_image.a'))

    if not isfile(join(BUILDS['SDL_IMAGE'], 'Makefile')):
        cmd = join(DIST_DIR, 'bin', 'libpng-config' ) + ' --static --cflags'
        pngcf = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
        cmd = join(DIST_DIR, 'bin', 'libpng-config' ) + ' --static --ldflags'
        pngld = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
        cmd = './configure --enable-silent-rules CFLAGS="%s" LDFLAGS="-static-libgcc" LIBPNG_CFLAGS="%s" LIBPNG_LIBS="%s -ljpeg" --disable-png-shared --disable-jpg-shared --disable-shared --enable-static --with-sdl-prefix="%s" --prefix="%s"'% (env['CFLAGS'], pngcf, pngld, DIST_DIR, DIST_DIR)
        Popen(shlex.split(cmd), cwd = BUILDS['SDL_IMAGE'], env=env).communicate()
    cmd = 'make V=0'
    Popen(shlex.split(cmd), cwd = BUILDS['SDL_IMAGE'], env=env).communicate()
    cmd = 'make V=0 install'
    Popen(shlex.split(cmd), cwd = BUILDS['SDL_IMAGE'], env=env).communicate()
    if isfile(join(DIST_DIR, 'lib', 'libSDL2_image.a')):
        log('SDL Image built successfully')
    else:
        error('Problem building SDL Image')
        exit()

    # Build freetype
    if isfile(join(DIST_DIR, 'lib', 'libfreetype.a')):
        os.remove(join(DIST_DIR, 'lib', 'libfreetype.a'))

    if not isfile(join(BUILDS['FREETYPE'], 'config.mk')):
        cmd = './configure --enable-silent-rules LDFLAGS="-static-libgcc" --without-bzip2 --disable-shared --enable-static --with-sysroot=%s --prefix="%s"'% (DIST_DIR,DIST_DIR)
        Popen(shlex.split(cmd), cwd = BUILDS['FREETYPE'], env=env).communicate()
    cmd = 'make V=0'
    Popen(shlex.split(cmd), cwd = BUILDS['FREETYPE'], env=env).communicate()
    cmd = 'make V=0 install'
    Popen(shlex.split(cmd), cwd = BUILDS['FREETYPE'], env=env).communicate()
    if isfile(join(DIST_DIR, 'lib', 'libfreetype.a')):
        log('Freetype built successfully')
    else:
        error('Problem building Freetype')
        exit()

    # Build SDL_ttf
    if isfile(join(DIST_DIR, 'lib', 'libSDL2_ttf.a')):
        os.remove(join(DIST_DIR, 'lib', 'libSDL2_ttf.a'))

    if not isfile(join(BUILDS['SDL_TTF'], 'configure')):
        cmd = './autogen.sh'
        Popen(shlex.split(cmd), cwd = BUILDS['SDL_TTF'], env=env).communicate()

    if not isfile(join(BUILDS['SDL_TTF'], 'Makefile')):
        cmd = './configure --enable-silent-rules LDFLAGS="-static-libgcc" --disable-shared --enable-static --with-sdl-prefix="%s" --with-freetype-prefix="%s" --prefix="%s"'% (DIST_DIR, DIST_DIR, DIST_DIR)
        Popen(shlex.split(cmd), cwd = BUILDS['SDL_TTF'], env=env).communicate()
    cmd = 'make V=0'
    Popen(shlex.split(cmd), cwd = BUILDS['SDL_TTF'], env=env).communicate()
    cmd = 'make V=0 install'
    Popen(shlex.split(cmd), cwd = BUILDS['SDL_TTF'], env=env).communicate()
    if isfile(join(DIST_DIR, 'lib', 'libSDL2_ttf.a')):
        log('SDL TTF built successfully')
    else:
        error('Problem building SDL TTF')
        exit()

    return True