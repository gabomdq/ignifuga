#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Build SDL for iOS (armv6 and armv7)
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import os, shlex, shutil
from os.path import *
from subprocess import Popen, PIPE
from ..log import log, error
from schafer import prepare_source, SED_CMD, SOURCES
import multiprocessing
from copy import deepcopy
from common import *

def setup(env_base, target_base, arch):
    env = deepcopy(env_base)
    target = deepcopy(target_base)
    env['CFLAGS'] = env['CFLAGS'].replace(join(target.dist, 'include'), join(target.dist+'_'+arch, 'include')) + ' -arch ' + arch
    env['CXXFLAGS'] = env['CXXFLAGS'].replace(join(target.dist, 'include'), join(target.dist+'_'+arch, 'include')) + ' -arch ' + arch
    env['LDFLAGS'] = env['LDFLAGS'].replace(join(target.dist, 'lib'), join(target.dist+'_'+arch, 'lib')) + ' -arch ' + arch
#    env['HOST'] = '--host '+arch+'-apple-darwin'
    target.dist +='_'+arch
    target.builds.SDL += '_'+arch
    target.builds.SDL_IMAGE += '_'+arch
    target.builds.SDL_TTF += '_'+arch
    target.builds.SDL_MIXER += '_'+arch
    target.builds.FREETYPE += '_'+arch
    target.builds.PNG += '_'+arch
    target.builds.JPGTURBO += '_'+arch
    target.builds.ZLIB += '_'+arch
    target.builds.IGNIFUGA += '_'+arch
    target.builds.GC += '_'+arch
    target.builds.LIBOGG += '_'+arch
    target.builds.OGGDECODER += '_'+arch

    return env, target


def prepare(env, target, options):
    env_base = deepcopy(env)
    target_base = deepcopy(target)
    for arch in ['armv6', 'armv7']:
        env, target = setup(env_base, target_base, arch)
        prepare_common(env, target, options)

def make(env, target, options):
    # Build all libraries in universal mode (armv6, armv7)
    env_base = deepcopy(env)
    target_base = deepcopy(target)
    for arch in ['armv6', 'armv7']:
        env, target = setup(env_base, target_base, arch)
        env['TARGET_DIST'] = target.dist
        env['PKG_CONFIG_PATH'] = join(target.dist, 'lib', 'pkgconfig')
        if not isfile(join(target.builds.SDL, 'Makefile')):
            # Disable IPHONE_TOUCH_EFFICIENT_DANGEROUS on SDL
            cmd = SED_CMD + '-e "s|^#define IPHONE_TOUCH_EFFICIENT_DANGEROUS|//#define IPHONE_TOUCH_EFFICIENT_DANGEROUS|g" %s' % join (target.builds.SDL, 'src', 'video', 'uikit', 'SDL_uikitview.h')
            Popen(shlex.split(cmd), env=env).communicate()

            cmd = './configure --enable-silent-rules %(HOST)s CFLAGS="%(CFLAGS)s" LDFLAGS="-static-libgcc %(LDFLAGS)s" --disable-shared --enable-static --prefix="%(TARGET_DIST)s"' % env
            Popen(shlex.split(cmd), cwd = target.builds.SDL, env=env).communicate()
            # Replace the auto generated config file for a hand made one
            shutil.copy(join(target.builds.SDL, 'include', 'SDL_config_iphoneos.h'), join(target.builds.SDL, 'include', 'SDL_config.h'))
            # Get rid of autodetected extra flags that SDL thinks we need but we don't as we are not compiling for OS X!
            cmd = SED_CMD + '-e "s|^EXTRA_CFLAGS.*|EXTRA_CFLAGS=-I./include|g" %s' % (join(target.builds.SDL, 'Makefile'),)
            Popen(shlex.split(cmd), cwd = target.builds.SDL, env=env).communicate()
            cmd = SED_CMD + '-e "s|^EXTRA_LDFLAGS.*|EXTRA_LDFLAGS=-lm|g" %s' % (join(target.builds.SDL, 'Makefile'),)
            Popen(shlex.split(cmd), cwd = target.builds.SDL, env=env).communicate()

        make_common(env, target, options, ['zlib', 'png', 'jpeg', 'sdl', 'sdl_image'])
        cflags = env['CFLAGS']
        #Modify CFLAGS for Freetype
        env['CFLAGS'] = cflags + ' -pipe -mdynamic-no-pic -std=c99 -Wno-trigraphs -fpascal-strings -Wreturn-type -Wunused-variable -fmessage-length=0 -fvisibility=hidden'
        make_common(env, target, options, ['freetype',])
        env['CFLAGS'] = cflags
        make_common(env, target, options, ['sdl_ttf', 'ogg'])
        env['CFLAGS'] = cflags + ' -mno-thumb -mthumb-interwork'
        make_common(env, target, options, ['oggdecoder',])
        env['CFLAGS'] = cflags
        make_common(env, target, options, ['sdl_mixer',])

    # Lipo libraries architectures together
    target = target_base
    cmd = 'mkdir -p ' + join(target.dist, 'lib')
    Popen(shlex.split(cmd), env=env).communicate()

    for lib in ['SDL2', 'SDL2main', 'SDL2_image', 'SDL2_ttf', 'SDL2_mixer', 'turbojpeg', 'png12', 'jpeg', 'freetype', 'z']:
        libfile = 'lib'+lib+'.a'

        cmd = 'lipo -create %s %s -output %s' % (join(target.dist+'_armv6', 'lib', libfile), join(target.dist+'_armv7', 'lib', libfile), join(target.dist, 'lib', libfile))
        Popen(shlex.split(cmd), env=env).communicate()
        cmd = 'ranlib %s' % join(target.dist, 'lib', libfile)
        Popen(shlex.split(cmd), env=env).communicate()

        if isfile(join(target.dist, 'lib', libfile)):
            log(lib + ' lipoed successfully')
        else:
            error('Problem lipoing ' + lib)
            exit()

    for path in ['bin', 'include']:
        cmd = 'rsync -aqut --exclude .svn --exclude .hg --exclude Makefile %s/ %s' % (join(target.dist+'_armv7', path), join(target.dist, path))
        Popen(shlex.split(cmd), env=env).communicate()

    for cfg in ['freetype-config', 'libpng12-config', 'sdl2-config']:
        cmd = SED_CMD + 's|_armv7||g ' +  join(target.dist, 'bin', cfg)
        Popen(shlex.split(cmd), env=env).communicate()
    return True

#def prepare(env, target, options):
#
#    prepare_source('zlib', SOURCES['ZLIB'], target.builds.ZLIB)
#    prepare_source('libpng', SOURCES['PNG'], target.builds.PNG)
##    if not isfile(join(target.builds.PNG, 'Makefile')):
##        shutil.copy(join(target.builds.PNG, 'scripts', 'makefile.ios'), join(target.builds.PNG, 'Makefile'))
#    prepare_source('libjpeg-turbo', SOURCES['JPGTURBO'], target.builds.JPGTURBO)
#
#
#    for arch_suffix in ['_armv6', '_armv7']:
#        prepare_source('SDL', SOURCES['SDL'], target.builds.SDL+arch_suffix)
#        prepare_source('SDL_image', SOURCES['SDL_IMAGE'], target.builds.SDL_IMAGE+arch_suffix)
#        prepare_source('SDL_ttf', SOURCES['SDL_TTF'], target.builds.SDL_TTF+arch_suffix)
#        prepare_source('freetype', SOURCES['FREETYPE'], target.builds.FREETYPE+arch_suffix)
#        shutil.copy(join(SOURCES['FREETYPE'], 'Makefile'), join(target.builds.FREETYPE+arch_suffix, 'Makefile') )
#
#        prepare_source('OGG', SOURCES['LIBOGG'], target.builds.LIBOGG+arch_suffix)
#        if options.oggdecoder == 'VORBIS' and isfile(join(target.builds.OGGDECODER+arch_suffix, 'vorbisidec.pc.in')):
#            cmd = 'rm -rf %s' % target.builds.OGGDECODER+arch_suffix
#            Popen(shlex.split(cmd), env=env).communicate()
#            cmd = 'rm -rf %s' % target.builds.SDL_MIXER+arch_suffix
#            Popen(shlex.split(cmd), env=env).communicate()
#        elif options.oggdecoder != 'VORBIS' and isfile(join(target.builds.OGGDECODER+arch_suffix, 'vorbisenc.pc.in')):
#            cmd = 'rm -rf %s' % target.builds.OGGDECODER+arch_suffix
#            Popen(shlex.split(cmd), env=env).communicate()
#            cmd = 'rm -rf %s' % target.builds.SDL_MIXER+arch_suffix
#            Popen(shlex.split(cmd), env=env).communicate()
#
#        prepare_source('SDL_mixer', SOURCES['SDL_MIXER'], target.builds.SDL_MIXER+arch_suffix)
#
#
#
#def make(env, target):
#    ncpu = multiprocessing.cpu_count()
#    universal_cflags = '-arch armv6 -arch armv7'
#    # Build all libraries in universal mode (armv6 and armv7)
#    # Build zlib
#    if isfile(join(target.dist, 'lib', 'libz.a')):
#        os.remove(join(target.dist, 'lib', 'libz.a'))
#
#    if not isfile(join(target.builds.ZLIB, 'Makefile')):
#        cmd = './configure --static --prefix="%s"'% (target.dist,)
#        Popen(shlex.split(cmd), cwd = target.builds.ZLIB, env=env).communicate()
#        # Force zlib to build universally
#        cmd = SED_CMD + '-e "s|CFLAGS=|CFLAGS=%s %s |g" %s' % (universal_cflags, env['CFLAGS'], (join(target.builds.ZLIB, 'Makefile')))
#        Popen(shlex.split(cmd), cwd = target.builds.JPG, env=env).communicate()
#    cmd = 'make -j%d V=0' % ncpu
#    Popen(shlex.split(cmd), cwd = target.builds.ZLIB, env=env).communicate()
#    cmd = 'make V=0 install'
#    Popen(shlex.split(cmd), cwd = target.builds.ZLIB, env=env).communicate()
#    if isfile(join(target.dist, 'lib', 'libz.a')):
#        log('zlib built successfully')
#    else:
#        error('Problem building zlib')
#        exit()
#
#    # Build libpng
#    if isfile(join(target.dist, 'lib', 'libpng.a')):
#        os.remove(join(target.dist, 'lib', 'libpng.a'))
#
#    cmd = 'make -j%d V=0 prefix="%s"' % (ncpu, target.dist,)
#    Popen(shlex.split(cmd), cwd = target.builds.PNG, env=env).communicate()
#    cmd = 'make V=0 install PREFIX="%s"' % (target.dist,)
#    Popen(shlex.split(cmd), cwd = target.builds.PNG, env=env).communicate()
#
#    if isfile(join(target.dist, 'lib', 'libpng.a')):
#        log('libpng built successfully')
#    else:
#        error('Problem building libpng')
#        exit()
#
#    # Build libjpeg
#    if isfile(join(target.dist, 'lib', 'libjpeg.a')):
#        os.remove(join(target.dist, 'lib', 'libjpeg.a'))
#
#    if not isfile(join(target.builds.JPG, 'Makefile')):
#        cmd = './configure --host=arm-apple-darwin --enable-silent-rules CFLAGS="%s %s" LDFLAGS="-static-libgcc %s %s" LIBTOOL= --disable-shared --enable-static --prefix="%s"' % (universal_cflags, env['CFLAGS'], universal_cflags, env['LDFLAGS'], target.dist)
#        Popen(shlex.split(cmd), cwd = target.builds.JPG, env=env).communicate()
#        # Fixes for the Makefile
#        cmd = SED_CMD + '-e "s|\./libtool||g" %s' % (join(target.builds.JPG, 'Makefile'))
#        Popen(shlex.split(cmd), cwd = target.builds.JPG, env=env).communicate()
#        cmd = SED_CMD + '-e "s|^O = lo|O = o|g" %s' % (join(target.builds.JPG, 'Makefile'))
#        Popen(shlex.split(cmd), cwd = target.builds.JPG, env=env).communicate()
#        cmd = SED_CMD + '-e "s|^A = la|A = a|g" %s' % (join(target.builds.JPG, 'Makefile'))
#        Popen(shlex.split(cmd), cwd = target.builds.JPG, env=env).communicate()
#
#    cmd = 'make -j%d libjpeg.a V=0' % ncpu
#    Popen(shlex.split(cmd), cwd = target.builds.JPG, env=env).communicate()
#    cmd = 'make V=0 install-lib'
#    Popen(shlex.split(cmd), cwd = target.builds.JPG, env=env).communicate()
#    cmd = 'make V=0 install-headers'
#    Popen(shlex.split(cmd), cwd = target.builds.JPG, env=env).communicate()
#
#    if isfile(join(target.dist, 'lib', 'libjpeg.a')):
#        log('libjpeg built successfully')
#    else:
#        error('Problem building libjpeg')
#        exit()
#
#    # Build SDL, SDL Image, SDL TTF
#    # SDL and Freetype can not be built with multiple -arch flags, so we build it twice and then lipo the results
#    if isfile(join(target.dist, 'lib', 'libSDL2.a')):
#        os.remove(join(target.dist, 'lib', 'libSDL2.a'))
#    if isfile(join(target.dist, 'lib', 'libSDL2_armv6.a')):
#        os.remove(join(target.dist, 'lib', 'libSDL2_armv6.a'))
#    if isfile(join(target.dist, 'lib', 'libSDL2_armv7.a')):
#        os.remove(join(target.dist, 'lib', 'libSDL2_armv7.a'))
#    if isfile(join(target.dist, 'lib', 'libSDL2_image.a')):
#        os.remove(join(target.dist, 'lib', 'libSDL2_image.a'))
#    if isfile(join(target.dist, 'lib', 'libSDL2_image_armv6.a')):
#        os.remove(join(target.dist, 'lib', 'libSDL2_image_armv6.a'))
#    if isfile(join(target.dist, 'lib', 'libSDL2_image_armv7.a')):
#        os.remove(join(target.dist, 'lib', 'libSDL2_image_armv7.a'))
#    if isfile(join(target.dist, 'lib', 'libSDL2_ttf.a')):
#        os.remove(join(target.dist, 'lib', 'libSDL2_ttf.a'))
#    if isfile(join(target.dist, 'lib', 'libSDL2_ttf_armv6.a')):
#        os.remove(join(target.dist, 'lib', 'libSDL2_ttf_armv6.a'))
#    if isfile(join(target.dist, 'lib', 'libSDL2_ttf_armv7.a')):
#        os.remove(join(target.dist, 'lib', 'libSDL2_ttf_armv7.a'))
#
#    freetype_build_armv6 = target.builds.FREETYPE+'_armv6'
#    freetype_build_armv7 = target.builds.FREETYPE+'_armv7'
#    sdl_build_armv6 = target.builds.SDL+'_armv6'
#    sdl_build_armv7 = target.builds.SDL+'_armv7'
#    sdl_image_build_armv6 = target.builds.SDL_IMAGE+'_armv6'
#    sdl_image_build_armv7 = target.builds.SDL_IMAGE+'_armv7'
#    sdl_ttf_build_armv6 = target.builds.SDL_TTF+'_armv6'
#    sdl_ttf_build_armv7 = target.builds.SDL_TTF+'_armv7'
#    pngcf = '-I%s/include/libpng12' % target.dist
#    pngld = '-lpng'
#
#    # armv6 builds
#
#    # Build freetype
#    if isfile(join(target.dist, 'lib', 'libfreetype.a')):
#        os.remove(join(target.dist, 'lib', 'libfreetype.a'))
#
#    if not isfile(join(freetype_build_armv6, 'config.mk')):
#        cflags = env['CFLAGS'] + '-pipe -mdynamic-no-pic -std=c99 -Wno-trigraphs -fpascal-strings -Wreturn-type -Wunused-variable -fmessage-length=0 -fvisibility=hidden'
#        cmd = './configure --host=arm-apple-darwin CFLAGS="-arch armv6 %s" LDFLAGS="-static-libgcc -arch armv6" --without-bzip2 --disable-shared --enable-static --with-sysroot=%s --prefix="%s"'% (cflags,target.dist,target.dist)
#        Popen(shlex.split(cmd), cwd = freetype_build_armv6, env=env).communicate()
#    cmd = 'make -j%d V=0' % ncpu
#    Popen(shlex.split(cmd), cwd = freetype_build_armv6, env=env).communicate()
#    cmd = 'make V=0 install'
#    Popen(shlex.split(cmd), cwd = freetype_build_armv6, env=env).communicate()
#
#    if isfile(join(target.dist, 'lib', 'libfreetype.a')):
#        log('Freetype armv6 built successfully')
#    else:
#        error('Problem building Freetype armv6')
#        exit()
#
#    # Build SDL
#    if not isfile(join(sdl_build_armv6, 'Makefile')):
#        # Disable IPHONE_TOUCH_EFFICIENT_DANGEROUS on SDL
#        cmd = SED_CMD + '-e "s|^#define IPHONE_TOUCH_EFFICIENT_DANGEROUS|//#define IPHONE_TOUCH_EFFICIENT_DANGEROUS|g" %s' % join (sdl_build_armv6, 'src', 'video', 'uikit', 'SDL_uikitview.h')
#        Popen(shlex.split(cmd), env=env).communicate()
#
#        cmd = './configure --host=armv6-apple-darwin --enable-silent-rules CFLAGS="%s -arch armv6" LDFLAGS="-arch armv6 -static-libgcc" --disable-shared --enable-static --prefix="%s"'% (env['CFLAGS'], target.dist)
#        Popen(shlex.split(cmd), cwd = sdl_build_armv6, env=env).communicate()
#        # Replace the auto generated config file for a hand made one
#        shutil.copy(join(sdl_build_armv6, 'include', 'SDL_config_iphoneos.h'), join(sdl_build_armv6, 'include', 'SDL_config.h'))
#        # Get rid of autodetected extra flags that SDL thinks we need but we don't as we are not compiling for OS X!
#        cmd = SED_CMD + '-e "s|^EXTRA_CFLAGS.*|EXTRA_CFLAGS=-I./include|g" %s' % (join(sdl_build_armv6, 'Makefile'),)
#        Popen(shlex.split(cmd), cwd = sdl_build_armv6, env=env).communicate()
#        cmd = SED_CMD + '-e "s|^EXTRA_LDFLAGS.*|EXTRA_LDFLAGS=-lm|g" %s' % (join(sdl_build_armv6, 'Makefile'),)
#        Popen(shlex.split(cmd), cwd = sdl_build_armv6, env=env).communicate()
#
#    cmd = 'make -j%d V=0' % ncpu
#    Popen(shlex.split(cmd), cwd = sdl_build_armv6, env=env).communicate()
#    cmd = 'make V=0 install'
#    Popen(shlex.split(cmd), cwd = sdl_build_armv6, env=env).communicate()
#
#    if isfile(join(target.dist, 'lib', 'libSDL2.a')) and isfile(join(target.dist, 'lib', 'libSDL2main.a')):
#        log('SDL armv6 built successfully')
#    else:
#        error('Problem building SDL armv6')
#        exit()
#
#    if not isfile(join(sdl_image_build_armv6, 'Makefile')):
#        # --disable-imageio is required otherwise the sprite data extracting code for PNGs is never enabled!
#        cmd = './configure --host=arm-apple-darwin --disable-imageio --enable-silent-rules CFLAGS="%s -arch armv6" LDFLAGS="-arch armv6 -static-libgcc" LIBPNG_CFLAGS="%s" LIBPNG_LIBS="%s -ljpeg" --disable-png-shared --disable-jpg-shared --disable-shared --enable-static --disable-sdltest --with-sdl-prefix="%s" --prefix="%s"'% (env['CFLAGS'], pngcf, pngld, target.dist, target.dist)
#        Popen(shlex.split(cmd), cwd = sdl_image_build_armv6, env=env).communicate()
#        # There's a bug (http://bugzilla.libsdl.org/show_bug.cgi?id=1429) in showimage compilation that prevents it from working, at least up to 2012-02-23, we just remove it as we don't need it
#        cmd = SED_CMD + '-e "s|.*showimage.*||g" %s' % (join(sdl_image_build_armv6, 'Makefile'),)
#        Popen(shlex.split(cmd), cwd = sdl_image_build_armv6, env=env).communicate()
#    cmd = 'make -j%d V=0' % ncpu
#    Popen(shlex.split(cmd), cwd = sdl_image_build_armv6, env=env).communicate()
#    cmd = 'make V=0 install'
#    Popen(shlex.split(cmd), cwd = sdl_image_build_armv6, env=env).communicate()
#
#    if isfile(join(target.dist, 'lib', 'libSDL2_image.a')):
#        log('SDL Image armv6 built successfully')
#    else:
#        error('Problem building SDL Image armv6')
#        exit()
#
#    if not isfile(join(sdl_ttf_build_armv6, 'configure')):
#        cmd = './autogen.sh'
#        Popen(shlex.split(cmd), cwd = target.builds.SDL_TTF, env=env).communicate()
#    if not isfile(join(sdl_ttf_build_armv6, 'Makefile')):
#        cmd = './configure --host=arm-apple-darwin --enable-silent-rules CFLAGS="%s -arch armv6" LDFLAGS="-arch armv6 -static-libgcc" --disable-shared --enable-static --with-sdl-prefix="%s" --with-freetype-prefix="%s" --prefix="%s"'% (env['CFLAGS'],target.dist, target.dist, target.dist)
#        Popen(shlex.split(cmd), cwd = sdl_ttf_build_armv6, env=env).communicate()
#        # There's a bug in showfont compilation that prevents it from working, at least up to 2012-02-23, we just remove it as we don't need it
#        cmd = 'sed -e "s|.*showfont.*||g" -i "" %s' % (join(sdl_ttf_build_armv6, 'Makefile'),)
#        Popen(shlex.split(cmd), cwd = sdl_ttf_build_armv6, env=env).communicate()
#    cmd = 'make -j%d V=0' % ncpu
#    Popen(shlex.split(cmd), cwd = sdl_ttf_build_armv6, env=env).communicate()
#    cmd = 'make V=0 install'
#    Popen(shlex.split(cmd), cwd = sdl_ttf_build_armv6, env=env).communicate()
#
#    if isfile(join(target.dist, 'lib', 'libSDL2_ttf.a')):
#        log('SDL TTF built successfully')
#    else:
#        error('Problem building SDL TTF armv6')
#        exit()
#
#    # Rename libraries with the _armv6 suffix
#    cmd = 'mv -f "%s" "%s"' % (join(target.dist, 'lib', 'libfreetype.a'), join(target.dist, 'lib', 'libfreetype_armv6.a'))
#    Popen(shlex.split(cmd), env=env).communicate()
#    cmd = 'mv -f "%s" "%s"' % (join(target.dist, 'lib', 'libSDL2.a'), join(target.dist, 'lib', 'libSDL2_armv6.a'))
#    Popen(shlex.split(cmd), env=env).communicate()
#    cmd = 'mv -f "%s" "%s"' % (join(target.dist, 'lib', 'libSDL2main.a'), join(target.dist, 'lib', 'libSDL2main_armv6.a'))
#    Popen(shlex.split(cmd), env=env).communicate()
#    cmd = 'mv -f "%s" "%s"' % (join(target.dist, 'lib', 'libSDL2_image.a'), join(target.dist, 'lib', 'libSDL2_image_armv6.a'))
#    Popen(shlex.split(cmd), env=env).communicate()
#    cmd = 'mv -f "%s" "%s"' % (join(target.dist, 'lib', 'libSDL2_ttf.a'), join(target.dist, 'lib', 'libSDL2_ttf_armv6.a'))
#    Popen(shlex.split(cmd), env=env).communicate()
#
#    # armv7 builds
#
#    # Build freetype
#    if isfile(join(target.dist, 'lib', 'libfreetype.a')):
#        os.remove(join(target.dist, 'lib', 'libfreetype.a'))
#
#    if not isfile(join(freetype_build_armv7, 'config.mk')):
#        cflags = env['CFLAGS'] + '-pipe -mdynamic-no-pic -std=c99 -Wno-trigraphs -fpascal-strings -Wreturn-type -Wunused-variable -fmessage-length=0 -fvisibility=hidden'
#        cmd = './configure --host=arm-apple-darwin CFLAGS="-arch armv7 %s" LDFLAGS="-static-libgcc -arch armv7" --without-bzip2 --disable-shared --enable-static --with-sysroot=%s --prefix="%s"'% (cflags,target.dist,target.dist)
#        Popen(shlex.split(cmd), cwd = freetype_build_armv7, env=env).communicate()
#
#    cmd = 'make -j%d V=0' % ncpu
#    Popen(shlex.split(cmd), cwd = freetype_build_armv7, env=env).communicate()
#    cmd = 'make V=0 install'
#    Popen(shlex.split(cmd), cwd = freetype_build_armv7, env=env).communicate()
#
#    if isfile(join(target.dist, 'lib', 'libfreetype.a')):
#        log('Freetype armv7 built successfully')
#    else:
#        error('Problem building Freetype armv7')
#        exit()
#
#    # Build SDL
#    if not isfile(join(sdl_build_armv7, 'Makefile')):
#        # Disable IPHONE_TOUCH_EFFICIENT_DANGEROUS on SDL
#        cmd = SED_CMD + '-e "s|^#define IPHONE_TOUCH_EFFICIENT_DANGEROUS|//#define IPHONE_TOUCH_EFFICIENT_DANGEROUS|g" %s' % join (sdl_build_armv7, 'src', 'video', 'uikit', 'SDL_uikitview.h')
#        Popen(shlex.split(cmd), env=env).communicate()
#
#        cmd = './configure --host=armv7-apple-darwin --enable-silent-rules CFLAGS="%s -arch armv7" LDFLAGS="-arch armv7 -static-libgcc" --disable-shared --enable-static --prefix="%s"'% (env['CFLAGS'], target.dist)
#        Popen(shlex.split(cmd), cwd = sdl_build_armv7, env=env).communicate()
#        # Replace the auto generated config file for a hand made one
#        shutil.copy(join(sdl_build_armv7, 'include', 'SDL_config_iphoneos.h'), join(sdl_build_armv7, 'include', 'SDL_config.h'))
#        # Get rid of autodetected extra flags that SDL thinks we need but we don't as we are not compiling for OS X!
#        cmd = SED_CMD + '-e "s|^EXTRA_CFLAGS.*|EXTRA_CFLAGS=-I./include|g" %s' % (join(sdl_build_armv7, 'Makefile'),)
#        Popen(shlex.split(cmd), cwd = sdl_build_armv7, env=env).communicate()
#        cmd = SED_CMD + '-e "s|^EXTRA_LDFLAGS.*|EXTRA_LDFLAGS=-lm|g" %s' % (join(sdl_build_armv7, 'Makefile'),)
#        Popen(shlex.split(cmd), cwd = sdl_build_armv7, env=env).communicate()
#
#
#    cmd = 'make -j%d V=0' % ncpu
#    Popen(shlex.split(cmd), cwd = sdl_build_armv7, env=env).communicate()
#    cmd = 'make V=0 install'
#    Popen(shlex.split(cmd), cwd = sdl_build_armv7, env=env).communicate()
#
#    if isfile(join(target.dist, 'lib', 'libSDL2.a')) and isfile(join(target.dist, 'lib', 'libSDL2main.a')):
#        log('SDL armv7 built successfully')
#    else:
#        error('Problem building SDL armv7')
#        exit()
#
#    if not isfile(join(sdl_image_build_armv7, 'Makefile')):
#        # --disable-imageio is required otherwise the sprite data extracting code for PNGs is never enabled!
#        cmd = './configure --host=arm-apple-darwin --disable-imageio --enable-silent-rules CFLAGS="%s -arch armv7" LDFLAGS="-arch armv7 -static-libgcc" LIBPNG_CFLAGS="%s" LIBPNG_LIBS="%s -ljpeg" --disable-png-shared --disable-jpg-shared --disable-shared --enable-static --disable-sdltest --with-sdl-prefix="%s" --prefix="%s"'% (env['CFLAGS'], pngcf, pngld, target.dist, target.dist)
#        Popen(shlex.split(cmd), cwd = sdl_image_build_armv7, env=env).communicate()
#        # There's a bug (http://bugzilla.libsdl.org/show_bug.cgi?id=1429) in showimage compilation that prevents it from working, at least up to 2012-02-23, we just remove it as we don't need it
#        cmd = SED_CMD + '-e "s|.*showimage.*||g" %s' % (join(sdl_image_build_armv7, 'Makefile'),)
#        Popen(shlex.split(cmd), cwd = sdl_image_build_armv7, env=env).communicate()
#    cmd = 'make -j%d V=0' % ncpu
#    Popen(shlex.split(cmd), cwd = sdl_image_build_armv7, env=env).communicate()
#    cmd = 'make V=0 install'
#    Popen(shlex.split(cmd), cwd = sdl_image_build_armv7, env=env).communicate()
#
#    if isfile(join(target.dist, 'lib', 'libSDL2_image.a')):
#        log('SDL Image built successfully')
#    else:
#        error('Problem building SDL Image armv7')
#        exit()
#
#    if not isfile(join(sdl_ttf_build_armv7, 'configure')):
#        cmd = './autogen.sh'
#        Popen(shlex.split(cmd), cwd = target.builds.SDL_TTF, env=env).communicate()
#    if not isfile(join(sdl_ttf_build_armv7, 'Makefile')):
#        cmd = './configure --host=arm-apple-darwin --enable-silent-rules CFLAGS="%s -arch armv7" LDFLAGS="-arch armv7 -static-libgcc" --disable-shared --enable-static --with-sdl-prefix="%s" --with-freetype-prefix="%s" --prefix="%s"'% (env['CFLAGS'],target.dist, target.dist, target.dist)
#        Popen(shlex.split(cmd), cwd = sdl_ttf_build_armv7, env=env).communicate()
#        # There's a bug in showfont compilation that prevents it from working, at least up to 2012-02-23, we just remove it as we don't need it
#        cmd = SED_CMD + '-e "s|.*showfont.*||g" %s' % (join(sdl_ttf_build_armv7, 'Makefile'),)
#        Popen(shlex.split(cmd), cwd = sdl_ttf_build_armv7, env=env).communicate()
#    cmd = 'make -j%d V=0' % ncpu
#    Popen(shlex.split(cmd), cwd = sdl_ttf_build_armv7, env=env).communicate()
#    cmd = 'make V=0 install'
#    Popen(shlex.split(cmd), cwd = sdl_ttf_build_armv7, env=env).communicate()
#
#    if isfile(join(target.dist, 'lib', 'libSDL2_ttf.a')):
#        log('SDL TTF built successfully')
#    else:
#        error('Problem building SDL TTF armv7')
#        exit()
#
#    # Rename libraries with the _armv7 suffix
#    cmd = 'mv -f "%s" "%s"' % (join(target.dist, 'lib', 'libfreetype.a'), join(target.dist, 'lib', 'libfreetype_armv7.a'))
#    Popen(shlex.split(cmd), env=env).communicate()
#    cmd = 'mv -f "%s" "%s"' % (join(target.dist, 'lib', 'libSDL2.a'), join(target.dist, 'lib', 'libSDL2_armv7.a'))
#    Popen(shlex.split(cmd), env=env).communicate()
#    cmd = 'mv -f "%s" "%s"' % (join(target.dist, 'lib', 'libSDL2main.a'), join(target.dist, 'lib', 'libSDL2main_armv7.a'))
#    Popen(shlex.split(cmd), env=env).communicate()
#    cmd = 'mv -f "%s" "%s"' % (join(target.dist, 'lib', 'libSDL2_image.a'), join(target.dist, 'lib', 'libSDL2_image_armv7.a'))
#    Popen(shlex.split(cmd), env=env).communicate()
#    cmd = 'mv -f "%s" "%s"' % (join(target.dist, 'lib', 'libSDL2_ttf.a'), join(target.dist, 'lib', 'libSDL2_ttf_armv7.a'))
#    Popen(shlex.split(cmd), env=env).communicate()
#
#
#    # Lipo freetype library versions together
#    cmd = 'lipo -create %s %s -output %s' % (join(target.dist, 'lib', 'libfreetype_armv6.a'), join(target.dist, 'lib', 'libfreetype_armv7.a'), join(target.dist, 'lib', 'libfreetype.a'))
#    Popen(shlex.split(cmd), env=env).communicate()
#    cmd = '%s %s' % (env['RANLIB'], join(target.dist, 'lib', 'libfreetype.a'))
#    Popen(shlex.split(cmd), env=env).communicate()
#
#    if isfile(join(target.dist, 'lib', 'libfreetype.a')):
#        log('Freetype built successfully')
#    else:
#        error('Problem building Freetype')
#        exit()
#
#    # Lipo SDL library versions together
#    cmd = 'lipo -create %s %s -output %s' % (join(target.dist, 'lib', 'libSDL2_armv6.a'), join(target.dist, 'lib', 'libSDL2_armv7.a'), join(target.dist, 'lib', 'libSDL2.a'))
#    Popen(shlex.split(cmd), env=env).communicate()
#    cmd = '%s %s' % (env['RANLIB'],join(target.dist, 'lib', 'libSDL2.a'))
#    Popen(shlex.split(cmd), env=env).communicate()
#
#    if isfile(join(target.dist, 'lib', 'libSDL2.a')):
#        log('SDL built successfully')
#    else:
#        error('Problem building SDL')
#        exit()
#
#    cmd = 'lipo -create %s %s -output %s' % (join(target.dist, 'lib', 'libSDL2main_armv6.a'), join(target.dist, 'lib', 'libSDL2main_armv7.a'), join(target.dist, 'lib', 'libSDL2main.a'))
#    Popen(shlex.split(cmd), env=env).communicate()
#    cmd = '%s %s' % (env['RANLIB'], join(target.dist, 'lib', 'libSDL2main.a'))
#    Popen(shlex.split(cmd), env=env).communicate()
#
#    if isfile(join(target.dist, 'lib', 'libSDL2main.a')):
#        log('SDL built successfully')
#    else:
#        error('Problem building SDL')
#        exit()
#
#    # Lipo SDL Image library versions together
#    cmd = 'lipo -create %s %s -output %s' % (join(target.dist, 'lib', 'libSDL2_image_armv6.a'), join(target.dist, 'lib', 'libSDL2_image_armv7.a'), join(target.dist, 'lib', 'libSDL2_image.a'))
#    Popen(shlex.split(cmd), env=env).communicate()
#    cmd = '%s %s' % (env['RANLIB'], join(target.dist, 'lib', 'libSDL2_image.a'))
#    Popen(shlex.split(cmd), env=env).communicate()
#
#    if isfile(join(target.dist, 'lib', 'libSDL2_image.a')):
#        log('SDL Image built successfully')
#    else:
#        error('Problem building SDL Image')
#        exit()
#
#    # Lipo SDL TTF library versions together
#    cmd = 'lipo -create %s %s -output %s' % (join(target.dist, 'lib', 'libSDL2_ttf_armv6.a'), join(target.dist, 'lib', 'libSDL2_ttf_armv7.a'), join(target.dist, 'lib', 'libSDL2_ttf.a'))
#    Popen(shlex.split(cmd), env=env).communicate()
#    cmd = '%s %s' % (env['RANLIB'], join(target.dist, 'lib', 'libSDL2_ttf.a'))
#    Popen(shlex.split(cmd), env=env).communicate()
#
#    if isfile(join(target.dist, 'lib', 'libSDL2_ttf.a')):
#        log('SDL TTF built successfully')
#    else:
#        error('Problem building SDL TTF')
#        exit()
#
#    return True