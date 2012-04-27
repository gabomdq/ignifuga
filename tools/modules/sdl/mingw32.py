#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Build SDL for Win32 using mingw
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import os, shlex, shutil
from os.path import *
from subprocess import Popen, PIPE
from ..log import log, error
from schafer import prepare_source, ROOT_DIR, SOURCES, SED_CMD

def prepare(target):
    prepare_source('SDL', SOURCES['SDL'], target.builds.SDL)
    prepare_source('SDL_image', SOURCES['SDL_IMAGE'], target.builds.SDL_IMAGE)
    prepare_source('zlib', SOURCES['ZLIB'], target.builds.ZLIB)
    prepare_source('libpng', SOURCES['PNG'], target.builds.PNG)
    prepare_source('libjpeg', SOURCES['JPG'], target.builds.JPG)
    prepare_source('freetype', SOURCES['FREETYPE'], target.builds.FREETYPE)
    shutil.copy(join(SOURCES['FREETYPE'], 'Makefile'), join(target.builds.FREETYPE, 'Makefile') )
    prepare_source('SDL_ttf', SOURCES['SDL_TTF'], target.builds.SDL_TTF)

    shutil.copy(join(ROOT_DIR, 'external', 'Makefile.in.zlib'), join(target.builds.ZLIB, 'Makefile.in'))
    shutil.copy(join(ROOT_DIR, 'external', 'Makefile.libpng.mingw32'), join(target.builds.PNG, 'Makefile'))

def make(env, target):
    # Build zlib
    if isfile(join(target.dist, 'lib', 'libz.a')):
        os.remove(join(target.dist, 'lib', 'libz.a'))
    if not isfile(join(target.builds.ZLIB, 'Makefile')):
        cmd = './configure --static --prefix="%s"'% (target.dist,)
        Popen(shlex.split(cmd), cwd = target.builds.ZLIB, env=env).communicate()
    cmd = 'make V=0'
    Popen(shlex.split(cmd), cwd = target.builds.ZLIB, env=env).communicate()
    cmd = 'make V=0 install'
    Popen(shlex.split(cmd), cwd = target.builds.ZLIB, env=env).communicate()
    if isfile(join(target.dist, 'lib', 'libz.a')):
        log('zlib built successfully')
    else:
        error('Problem building zlib')
        exit()

    # Build libpng
    if isfile(join(target.dist, 'lib', 'libpng.a')):
        os.remove(join(target.dist, 'lib', 'libpng.a'))
    cmd = 'make V=0 prefix="%s"' % (target.dist,)
    Popen(shlex.split(cmd), cwd = target.builds.PNG, env=env).communicate()
    cmd = 'make V=0 install prefix="%s"' % (target.dist,)
    Popen(shlex.split(cmd), cwd = target.builds.PNG, env=env).communicate()
    if isfile(join(target.dist, 'lib', 'libpng.a')):
        log('libpng built successfully')
    else:
        error('Problem building libpng')
        exit()

    # Build libjpeg
    if isfile(join(target.dist, 'lib', 'libjpeg.a')):
        os.remove(join(target.dist, 'lib', 'libjpeg.a'))

    if not isfile(join(target.builds.JPG, 'Makefile')):
        cmd = './configure --enable-silent-rules LDFLAGS="-static-libgcc" LIBTOOL= --host=i586-mingw32msvc --disable-shared --enable-static --prefix="%s"'% (target.dist,)
        Popen(shlex.split(cmd), cwd = target.builds.JPG, env=env).communicate()
        # Fixes for the Makefile
        cmd = SED_CMD + '"s|\./libtool||g" %s' % (join(target.builds.JPG, 'Makefile'))
        Popen(shlex.split(cmd), cwd = target.builds.JPG, env=env).communicate()
        cmd = SED_CMD + '"s|^O = lo|O = o|g" %s' % (join(target.builds.JPG, 'Makefile'))
        Popen(shlex.split(cmd), cwd = target.builds.JPG, env=env).communicate()
        cmd = SED_CMD + '"s|^A = la|A = a|g" %s' % (join(target.builds.JPG, 'Makefile'))
        Popen(shlex.split(cmd), cwd = target.builds.JPG, env=env).communicate()

    cmd = 'make V=0'
    Popen(shlex.split(cmd), cwd = target.builds.JPG, env=env).communicate()
    cmd = 'make V=0 install-lib'
    Popen(shlex.split(cmd), cwd = target.builds.JPG, env=env).communicate()
    cmd = 'make V=0 install-headers'
    Popen(shlex.split(cmd), cwd = target.builds.JPG, env=env).communicate()
    if isfile(join(target.dist, 'lib', 'libjpeg.a')):
        log('libjpeg built successfully')
    else:
        error('Problem building libjpeg')
        exit()

    if isfile(join(target.dist, 'lib', 'libSDL2.a')):
        os.remove(join(target.dist, 'lib', 'libSDL2.a'))
    if not isfile(join(target.builds.SDL, 'Makefile')):
        cmd = './configure --enable-silent-rules LDFLAGS="-static-libgcc" --disable-stdio-redirect --host=i586-mingw32msvc --disable-shared --enable-static --prefix="%s"'% (target.dist,)
        Popen(shlex.split(cmd), cwd = target.builds.SDL, env=env).communicate()

        # HACK FIX for SDL problem, this can be removed once SDL fixes this error
    #            cmd = 'sed -i "s|#define SDL_AUDIO_DRIVER_XAUDIO2.*||g" %s' % (join(target.builds.SDL, 'include', 'SDL_config_windows.h'),)
    #            Popen(shlex.split(cmd), cwd = target.builds.SDL, env=env).communicate()
    #            cmd = 'sed -i "s|#define SDL_AUDIO_DRIVER_DSOUND.*||g" %s' % (join(target.builds.SDL, 'include', 'SDL_config_windows.h'),)
    #            Popen(shlex.split(cmd), cwd = target.builds.SDL, env=env).communicate()



    cmd = 'make V=0'
    Popen(shlex.split(cmd), cwd = target.builds.SDL, env=env).communicate()
    cmd = 'make V=0 install'
    Popen(shlex.split(cmd), cwd = target.builds.SDL, env=env).communicate()
    if isfile(join(target.dist, 'lib', 'libSDL2.a')):
        log('SDL built successfully')
    else:
        error('Problem building SDL')
        exit()

    if isfile(join(target.dist, 'lib', 'libSDL2_image.a')):
        os.remove(join(target.dist, 'lib', 'libSDL2_image.a'))
    if not isfile(join(target.builds.SDL_IMAGE, 'Makefile')):
        cmd = './configure --enable-silent-rules LIBPNG_CFLAGS="-L%s -lpng12 -lz -lm -I%s" LDFLAGS="-static-libgcc" --host=i586-mingw32msvc --disable-shared --enable-static --with-sdl-prefix="%s" --prefix="%s"'% (join(target.dist, 'lib'), join(target.dist, 'include'), target.dist, target.dist)
        Popen(shlex.split(cmd), cwd = target.builds.SDL_IMAGE, env=env).communicate()
    cmd = 'make V=0'
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
        env['CFLAGS'] = env['CFLAGS'] + ' -std=gnu99'
        cmd = './configure --enable-silent-rules LDFLAGS="-static-libgcc" --without-bzip2  --build=i686-pc-linux-gnu --host=i586-mingw32msvc --disable-shared --enable-static --prefix="%s"'% (target.dist,)
        Popen(shlex.split(cmd), cwd = target.builds.FREETYPE, env=env).communicate()
    cmd = 'make V=0'
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
        cmd = './configure --enable-silent-rules LDFLAGS="-static-libgcc" --disable-shared --enable-static --disable-sdltest --host=i586-mingw32msvc --with-sdl-prefix="%s" --with-freetype-prefix="%s" --prefix="%s"'% (target.dist, target.dist, target.dist)
        Popen(shlex.split(cmd), cwd = target.builds.SDL_TTF, env=env).communicate()
    cmd = 'make V=0'
    Popen(shlex.split(cmd), cwd = target.builds.SDL_TTF, env=env).communicate()
    cmd = 'make V=0 install-libSDL2_ttfincludeHEADERS'
    Popen(shlex.split(cmd), cwd = target.builds.SDL_TTF, env=env).communicate()
    cmd = 'make V=0 install-libLTLIBRARIES'
    Popen(shlex.split(cmd), cwd = target.builds.SDL_TTF, env=env).communicate()
    if isfile(join(target.dist, 'lib', 'libSDL2_ttf.a')):
        log('SDL TTF built successfully')
    else:
        error('Problem building SDL TTF')
        exit()

    return True