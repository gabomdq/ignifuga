#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Build SDL for OS X (i386 and x86_64)
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import os, shlex, shutil
from os.path import *
from subprocess import Popen, PIPE
from ..log import log, error
from schafer import prepare_source, SED_CMD, SOURCES
import multiprocessing

def prepare(env, target, options):
    prepare_source('SDL', SOURCES['SDL'], target.builds.SDL+'_i386')
    prepare_source('SDL', SOURCES['SDL'], target.builds.SDL+'_x86_64')
    prepare_source('SDL_image', SOURCES['SDL_IMAGE'], target.builds.SDL_IMAGE+'_i386')
    prepare_source('SDL_image', SOURCES['SDL_IMAGE'], target.builds.SDL_IMAGE+'_x86_64')
    prepare_source('SDL_ttf', SOURCES['SDL_TTF'], target.builds.SDL_TTF+'_i386')
    prepare_source('SDL_ttf', SOURCES['SDL_TTF'], target.builds.SDL_TTF+'_x86_64')
    prepare_source('zlib', SOURCES['ZLIB'], target.builds.ZLIB)
    prepare_source('libpng', SOURCES['PNG'], target.builds.PNG)
    if not isfile(join(target.builds.PNG, 'Makefile')):
        shutil.copy(join(target.builds.PNG, 'scripts', 'makefile.darwin'), join(target.builds.PNG, 'Makefile'))
        # Force libpng to build universally
        cmd = SED_CMD + '-e "s|CFLAGS=|CFLAGS= %s -arch i386 -arch x86_64 |g" %s' % (env['CFLAGS'] if 'CFLAGS' in env else '', join(target.builds.PNG, 'Makefile'))
        Popen(shlex.split(cmd), cwd = target.builds.PNG).communicate()
        cmd = SED_CMD + '-e "s|LDFLAGS=|LDFLAGS= %s -arch i386 -arch x86_64 |g" %s' % (env['LDFLAGS'] if 'LDFLAGS' in env else '', join(target.builds.PNG, 'Makefile'))
        Popen(shlex.split(cmd), cwd = target.builds.PNG).communicate()
        cmd = SED_CMD + '-e "s|-dynamiclib|-dynamiclib -arch i386 -arch x86_64 |g" %s' % join(target.builds.PNG, 'Makefile')
        Popen(shlex.split(cmd), cwd = target.builds.PNG).communicate()
        cmd = SED_CMD + '-e "s|prefix=.*|prefix=%s|g" %s' % (join(target.builds.PNG, 'Makefile'), target.dist)
        Popen(shlex.split(cmd), cwd = target.builds.PNG).communicate()
    prepare_source('libjpeg', SOURCES['JPG'], target.builds.JPG)
    prepare_source('freetype', SOURCES['FREETYPE'], target.builds.FREETYPE)
    shutil.copy(join(SOURCES['FREETYPE'], 'Makefile'), join(target.builds.FREETYPE, 'Makefile') )
    prepare_source('SDL_ttf', SOURCES['SDL_TTF'], target.builds.SDL_TTF)
    prepare_source('OGG', SOURCES[options.libogg], target.builds.OGG)
    prepare_source('SDL_mixer', SOURCES['SDL_MIXER'], target.builds.SDL_MIXER)

def make(env, target):
    ncpu = multiprocessing.cpu_count()
    universal_cflags = '-arch i386 -arch x86_64'
    # Build all libraries in universal mode (i386 and x86_64)
    # Build zlib
    if isfile(join(target.dist, 'lib', 'libz.a')):
        os.remove(join(target.dist, 'lib', 'libz.a'))
    if not isfile(join(target.builds.ZLIB, 'Makefile')):
        cmd = './configure --static --prefix="%s"'% (target.dist,)
        Popen(shlex.split(cmd), cwd = target.builds.ZLIB, env=env).communicate()
        # Force zlib to build universally
        cmd = SED_CMD + '-e "s|CFLAGS=|CFLAGS=%s %s |g" %s' % (universal_cflags, env['CFLAGS'], (join(target.builds.ZLIB, 'Makefile')))
        Popen(shlex.split(cmd), cwd = target.builds.JPG, env=env).communicate()
    cmd = 'make -j%d V=0' % ncpu
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

    cmd = 'make -j%d V=0 prefix="%s"' % (ncpu, target.dist,)
    Popen(shlex.split(cmd), cwd = target.builds.PNG, env=env).communicate()
    cmd = 'make V=0 install prefix="%s"' % (target.dist,)
    Popen(shlex.split(cmd), cwd = target.builds.PNG, env=env).communicate()
    # Remove dynamic libraries to avoid confusions with the linker
    cmd = 'rm *.dylib'
    Popen(shlex.split(cmd), cwd = join(target.dist, 'lib')).communicate()
    if isfile(join(target.dist, 'lib', 'libpng.a')):
        log('libpng built successfully')
    else:
        error('Problem building libpng')
        exit()

    # Build libjpeg
    if isfile(join(target.dist, 'lib', 'libjpeg.a')):
        os.remove(join(target.dist, 'lib', 'libjpeg.a'))

    if not isfile(join(target.builds.JPG, 'Makefile')):
        cmd = './configure --enable-silent-rules CFLAGS="%s %s" LDFLAGS="-static-libgcc" LIBTOOL= --disable-shared --enable-static --prefix="%s"' % (universal_cflags, env['CFLAGS'], target.dist)
        Popen(shlex.split(cmd), cwd = target.builds.JPG, env=env).communicate()
        # Fixes for the Makefile
        cmd = SED_CMD + '-e "s|\./libtool||g" %s' % (join(target.builds.JPG, 'Makefile'))
        Popen(shlex.split(cmd), cwd = target.builds.JPG, env=env).communicate()
        cmd = SED_CMD + '-e "s|^O = lo|O = o|g" %s' % (join(target.builds.JPG, 'Makefile'))
        Popen(shlex.split(cmd), cwd = target.builds.JPG, env=env).communicate()
        cmd = SED_CMD + '-e "s|^A = la|A = a|g" %s' % (join(target.builds.JPG, 'Makefile'))
        Popen(shlex.split(cmd), cwd = target.builds.JPG, env=env).communicate()

    cmd = 'make -j%d V=0' % ncpu
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

    # Build freetype
    if isfile(join(target.dist, 'lib', 'libfreetype.a')):
        os.remove(join(target.dist, 'lib', 'libfreetype.a'))

    if not isfile(join(target.builds.FREETYPE, 'config.mk')):
        cmd = './configure --enable-silent-rules CFLAGS="%s %s" LDFLAGS="-static-libgcc" --without-bzip2 --disable-shared --enable-static --with-sysroot=%s --prefix="%s"'% (universal_cflags, env['CFLAGS'],target.dist,target.dist)
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

    # Build SDL, SDL Image, SDL TTF
    # SDL can not be built with multiple -arch flags, so we build it twice and then lipo the results
    if isfile(join(target.dist, 'lib', 'libSDL2.a')):
        os.remove(join(target.dist, 'lib', 'libSDL2.a'))
    if isfile(join(target.dist, 'lib', 'libSDL2_i386.a')):
        os.remove(join(target.dist, 'lib', 'libSDL2_i386.a'))
    if isfile(join(target.dist, 'lib', 'libSDL2_x86_64.a')):
        os.remove(join(target.dist, 'lib', 'libSDL2_x86_64.a'))
    if isfile(join(target.dist, 'lib', 'libSDL2_image.a')):
        os.remove(join(target.dist, 'lib', 'libSDL2_image.a'))
    if isfile(join(target.dist, 'lib', 'libSDL2_image_i386.a')):
        os.remove(join(target.dist, 'lib', 'libSDL2_image_i386.a'))
    if isfile(join(target.dist, 'lib', 'libSDL2_image_x86_64.a')):
        os.remove(join(target.dist, 'lib', 'libSDL2_image_x86_64.a'))
    if isfile(join(target.dist, 'lib', 'libSDL2_ttf.a')):
        os.remove(join(target.dist, 'lib', 'libSDL2_ttf.a'))
    if isfile(join(target.dist, 'lib', 'libSDL2_ttf_i386.a')):
        os.remove(join(target.dist, 'lib', 'libSDL2_ttf_i386.a'))
    if isfile(join(target.dist, 'lib', 'libSDL2_ttf_x86_64.a')):
        os.remove(join(target.dist, 'lib', 'libSDL2_ttf_x86_64.a'))

    sdl_build_i386 = target.builds.SDL+'_i386'
    sdl_build_x86_64 = target.builds.SDL+'_x86_64'
    sdl_image_build_i386 = target.builds.SDL_IMAGE+'_i386'
    sdl_image_build_x86_64 = target.builds.SDL_IMAGE+'_x86_64'
    sdl_ttf_build_i386 = target.builds.SDL_TTF+'_i386'
    sdl_ttf_build_x86_64 = target.builds.SDL_TTF+'_x86_64'

    # i386 builds
    if not isfile(join(sdl_build_i386, 'Makefile')):
        cmd = './configure --enable-silent-rules CFLAGS="%s -m32" LDFLAGS="-m32 -static-libgcc" --disable-shared --enable-static --prefix="%s"'% (env['CFLAGS'], target.dist)
        Popen(shlex.split(cmd), cwd = sdl_build_i386, env=env).communicate()
    cmd = 'make V=0 '
    Popen(shlex.split(cmd), cwd = sdl_build_i386, env=env).communicate()
    cmd = 'make V=0 install'
    Popen(shlex.split(cmd), cwd = sdl_build_i386, env=env).communicate()

    if not isfile(join(sdl_image_build_i386, 'Makefile')):
        cmd = join(target.dist, 'bin', 'libpng-config' ) + ' --static --cflags'
        pngcf = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
        cmd = join(target.dist, 'bin', 'libpng-config' ) + ' --static --ldflags'
        pngld = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
        # --disable-imageio is required otherwise the sprite data extracting code for PNGs is never enabled!
        cmd = './configure --disable-imageio --enable-silent-rules CFLAGS="%s -m32" LDFLAGS="-m32 -static-libgcc" LIBPNG_CFLAGS="%s" LIBPNG_LIBS="%s -ljpeg" --disable-png-shared --disable-jpg-shared --disable-shared --enable-static --disable-sdltest --with-sdl-prefix="%s" --prefix="%s"'% (env['CFLAGS'], pngcf, pngld, target.dist, target.dist)
        Popen(shlex.split(cmd), cwd = sdl_image_build_i386, env=env).communicate()
        # There's a bug (http://bugzilla.libsdl.org/show_bug.cgi?id=1429) in showimage compilation that prevents it from working, at least up to 2012-02-23, we just remove it as we don't need it
        cmd = SED_CMD + '-e "s|.*showimage.*||g" %s' % (join(sdl_image_build_i386, 'Makefile'),)
        Popen(shlex.split(cmd), cwd = sdl_image_build_i386, env=env).communicate()
    cmd = 'make -j%d V=0' % ncpu
    Popen(shlex.split(cmd), cwd = sdl_image_build_i386, env=env).communicate()
    cmd = 'make V=0 install'
    Popen(shlex.split(cmd), cwd = sdl_image_build_i386, env=env).communicate()

    if not isfile(join(sdl_ttf_build_i386, 'configure')):
        cmd = './autogen.sh'
        Popen(shlex.split(cmd), cwd = target.builds.SDL_TTF, env=env).communicate()
    if not isfile(join(sdl_ttf_build_i386, 'Makefile')):
        cmd = './configure --enable-silent-rules CFLAGS="%s -m32" LDFLAGS="-m32 -static-libgcc" --disable-shared --enable-static --with-sdl-prefix="%s" --with-freetype-prefix="%s" --prefix="%s"'% (env['CFLAGS'],target.dist, target.dist, target.dist)
        Popen(shlex.split(cmd), cwd = sdl_ttf_build_i386, env=env).communicate()
        # There's a bug in showfont compilation that prevents it from working, at least up to 2012-02-23, we just remove it as we don't need it
        #cmd = 'sed -e "s|.*showfont.*||g" -i "" %s' % (join(sdl_ttf_build_i386, 'Makefile'),)
        #Popen(shlex.split(cmd), cwd = sdl_ttf_build_i386, env=env).communicate()
    cmd = 'make -j%d V=0' % ncpu
    Popen(shlex.split(cmd), cwd = sdl_ttf_build_i386, env=env).communicate()
    cmd = 'make V=0 install'
    Popen(shlex.split(cmd), cwd = sdl_ttf_build_i386, env=env).communicate()

    if isfile(join(target.dist, 'lib', 'libSDL2.a')) and isfile(join(target.dist, 'lib', 'libSDL2main.a')):
        log('SDL i386 built successfully')
    else:
        error('Problem building SDL i386')
        exit()
    if isfile(join(target.dist, 'lib', 'libSDL2_image.a')):
        log('SDL Image i386 built successfully')
    else:
        error('Problem building SDL Image i386')
        exit()
    if isfile(join(target.dist, 'lib', 'libSDL2_ttf.a')):
        log('SDL TTF built successfully')
    else:
        error('Problem building SDL TTF i386')
        exit()

    # Rename libraries with the _i386 suffix
    cmd = 'mv -f "%s" "%s"' % (join(target.dist, 'lib', 'libSDL2.a'), join(target.dist, 'lib', 'libSDL2_i386.a'))
    Popen(shlex.split(cmd), env=env).communicate()
    cmd = 'mv -f "%s" "%s"' % (join(target.dist, 'lib', 'libSDL2main.a'), join(target.dist, 'lib', 'libSDL2main_i386.a'))
    Popen(shlex.split(cmd), env=env).communicate()
    cmd = 'mv -f "%s" "%s"' % (join(target.dist, 'lib', 'libSDL2_image.a'), join(target.dist, 'lib', 'libSDL2_image_i386.a'))
    Popen(shlex.split(cmd), env=env).communicate()
    cmd = 'mv -f "%s" "%s"' % (join(target.dist, 'lib', 'libSDL2_ttf.a'), join(target.dist, 'lib', 'libSDL2_ttf_i386.a'))
    Popen(shlex.split(cmd), env=env).communicate()

    # x86_64 builds
    if not isfile(join(sdl_build_x86_64, 'Makefile')):
        cmd = './configure --enable-silent-rules CFLAGS="%s -m64" LDFLAGS="-m64 -static-libgcc" --disable-shared --enable-static --prefix="%s"'% (env['CFLAGS'], target.dist)
        Popen(shlex.split(cmd), cwd = sdl_build_x86_64, env=env).communicate()

    cmd = 'make -j%d V=0' % ncpu
    Popen(shlex.split(cmd), cwd = sdl_build_x86_64, env=env).communicate()
    cmd = 'make V=0 install'
    Popen(shlex.split(cmd), cwd = sdl_build_x86_64, env=env).communicate()

    if not isfile(join(sdl_image_build_x86_64, 'Makefile')):
        cmd = join(target.dist, 'bin', 'libpng-config' ) + ' --static --cflags'
        pngcf = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
        cmd = join(target.dist, 'bin', 'libpng-config' ) + ' --static --ldflags'
        pngld = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
        # --disable-imageio is required otherwise the sprite data extracting code for PNGs is never enabled!
        cmd = './configure --disable-imageio --enable-silent-rules CFLAGS="%s -m64" LDFLAGS="-m64 -static-libgcc" LIBPNG_CFLAGS="%s" LIBPNG_LIBS="%s -ljpeg" --disable-png-shared --disable-jpg-shared --disable-shared --enable-static --disable-sdltest --with-sdl-prefix="%s" --prefix="%s"'% (env['CFLAGS'], pngcf, pngld, target.dist, target.dist)
        Popen(shlex.split(cmd), cwd = sdl_image_build_x86_64, env=env).communicate()
        # There's a bug (http://bugzilla.libsdl.org/show_bug.cgi?id=1429) in showimage compilation that prevents it from working, at least up to 2012-02-23, we just remove it as we don't need it
        #cmd = 'sed -e "s|.*showimage.*||g" -i "" %s' % (join(sdl_image_build_x86_64, 'Makefile'),)
        #Popen(shlex.split(cmd), cwd = sdl_image_build_i386, env=env).communicate()
    cmd = 'make -j%d V=0' % ncpu
    Popen(shlex.split(cmd), cwd = sdl_image_build_x86_64, env=env).communicate()
    cmd = 'make V=0 install'
    Popen(shlex.split(cmd), cwd = sdl_image_build_x86_64, env=env).communicate()

    if not isfile(join(sdl_ttf_build_x86_64, 'configure')):
        cmd = './autogen.sh'
        Popen(shlex.split(cmd), cwd = target.builds.SDL_TTF, env=env).communicate()
    if not isfile(join(sdl_ttf_build_x86_64, 'Makefile')):
        cmd = './configure --enable-silent-rules CFLAGS="%s -m64" LDFLAGS="-m64 -static-libgcc" --disable-shared --enable-static --with-sdl-prefix="%s" --with-freetype-prefix="%s" --prefix="%s"'% (env['CFLAGS'],target.dist, target.dist, target.dist)
        Popen(shlex.split(cmd), cwd = sdl_ttf_build_x86_64, env=env).communicate()
        # There's a bug in showfont compilation that prevents it from working, at least up to 2012-02-23, we just remove it as we don't need it
        cmd = SED_CMD + '-e "s|.*showfont.*||g" %s' % (join(sdl_ttf_build_x86_64, 'Makefile'),)
        Popen(shlex.split(cmd), cwd = sdl_ttf_build_x86_64, env=env).communicate()
    cmd = 'make -j%d V=0' % ncpu
    Popen(shlex.split(cmd), cwd = sdl_ttf_build_x86_64, env=env).communicate()
    cmd = 'make V=0 install'
    Popen(shlex.split(cmd), cwd = sdl_ttf_build_x86_64, env=env).communicate()

    if isfile(join(target.dist, 'lib', 'libSDL2.a')) and isfile(join(target.dist, 'lib', 'libSDL2main.a')):
        log('SDL x86_64 built successfully')
    else:
        error('Problem building SDL x86_64')
        exit()
    if isfile(join(target.dist, 'lib', 'libSDL2_image.a')):
        log('SDL Image built successfully')
    else:
        error('Problem building SDL Image x86_64')
        exit()
    if isfile(join(target.dist, 'lib', 'libSDL2_ttf.a')):
        log('SDL TTF built successfully')
    else:
        error('Problem building SDL TTF x86_64')
        exit()

    # Rename libraries with the _x86_64 suffix
    cmd = 'mv -f "%s" "%s"' % (join(target.dist, 'lib', 'libSDL2.a'), join(target.dist, 'lib', 'libSDL2_x86_64.a'))
    Popen(shlex.split(cmd), env=env).communicate()
    cmd = 'mv -f "%s" "%s"' % (join(target.dist, 'lib', 'libSDL2main.a'), join(target.dist, 'lib', 'libSDL2main_x86_64.a'))
    Popen(shlex.split(cmd), env=env).communicate()
    cmd = 'mv -f "%s" "%s"' % (join(target.dist, 'lib', 'libSDL2_image.a'), join(target.dist, 'lib', 'libSDL2_image_x86_64.a'))
    Popen(shlex.split(cmd), env=env).communicate()
    cmd = 'mv -f "%s" "%s"' % (join(target.dist, 'lib', 'libSDL2_ttf.a'), join(target.dist, 'lib', 'libSDL2_ttf_x86_64.a'))
    Popen(shlex.split(cmd), env=env).communicate()

    # Lipo SDL library versions together
    cmd = 'lipo -create %s %s -output %s' % (join(target.dist, 'lib', 'libSDL2_i386.a'), join(target.dist, 'lib', 'libSDL2_x86_64.a'), join(target.dist, 'lib', 'libSDL2.a'))
    Popen(shlex.split(cmd), env=env).communicate()
    cmd = 'ranlib %s' % join(target.dist, 'lib', 'libSDL2.a')
    Popen(shlex.split(cmd), env=env).communicate()

    if isfile(join(target.dist, 'lib', 'libSDL2.a')):
        log('SDL built successfully')
    else:
        error('Problem building SDL')
        exit()

    cmd = 'lipo -create %s %s -output %s' % (join(target.dist, 'lib', 'libSDL2main_i386.a'), join(target.dist, 'lib', 'libSDL2main_x86_64.a'), join(target.dist, 'lib', 'libSDL2main.a'))
    Popen(shlex.split(cmd), env=env).communicate()
    cmd = 'ranlib %s' % join(target.dist, 'lib', 'libSDL2main.a')
    Popen(shlex.split(cmd), env=env).communicate()

    if isfile(join(target.dist, 'lib', 'libSDL2main.a')):
        log('SDL built successfully')
    else:
        error('Problem building SDL')
        exit()

    # Lipo SDL Image library versions together
    cmd = 'lipo -create %s %s -output %s' % (join(target.dist, 'lib', 'libSDL2_image_i386.a'), join(target.dist, 'lib', 'libSDL2_image_x86_64.a'), join(target.dist, 'lib', 'libSDL2_image.a'))
    Popen(shlex.split(cmd), env=env).communicate()
    cmd = 'ranlib %s' % join(target.dist, 'lib', 'libSDL2_image.a')
    Popen(shlex.split(cmd), env=env).communicate()

    if isfile(join(target.dist, 'lib', 'libSDL2_image.a')):
        log('SDL Image built successfully')
    else:
        error('Problem building SDL Image')
        exit()

    # Lipo SDL TTF library versions together
    cmd = 'lipo -create %s %s -output %s' % (join(target.dist, 'lib', 'libSDL2_ttf_i386.a'), join(target.dist, 'lib', 'libSDL2_ttf_x86_64.a'), join(target.dist, 'lib', 'libSDL2_ttf.a'))
    Popen(shlex.split(cmd), env=env).communicate()
    cmd = 'ranlib %s' % join(target.dist, 'lib', 'libSDL2_ttf.a')
    Popen(shlex.split(cmd), env=env).communicate()

    if isfile(join(target.dist, 'lib', 'libSDL2_ttf.a')):
        log('SDL TTF built successfully')
    else:
        error('Problem building SDL TTF')
        exit()

    return True