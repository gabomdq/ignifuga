#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Build Python for Linux 64
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import os, shlex, shutil
from os.path import *
from subprocess import Popen, PIPE
from ..log import log, error
from schafer import prepare_source, make_python_freeze, SED_CMD, SOURCES
from ..util import get_sdl_flags, get_freetype_flags, get_png_flags
import multiprocessing

def prepare(env, target, ignifuga_src, python_build):
    # Get some required flags
    sdlflags = get_sdl_flags(target)
    freetypeflags = get_freetype_flags(target)
    ignifuga_module = "\nignifuga %s -I%s -lturbojpeg -lSDL2_ttf -lSDL2_image -lSDL2 -lpng12 -ljpeg %s %s\n" % (' '.join(ignifuga_src),target.builds.IGNIFUGA, sdlflags, freetypeflags)

    # For Linux we build our own libgc, because currently Ubuntu is marking libgc-dev:amd64 and libgc-dev:i386 as conflicting,
    # so we can't build a 32 bits version from a 64 bits system using the system provided library.
    cmd = 'rsync -aqPm --exclude .svn --exclude .hg %s/ %s' % (SOURCES['GC'], target.builds.GC)
    Popen(shlex.split(cmd), cwd = target.dist).communicate()
    return ignifuga_module

def make(env, target, options, freeze_modules, frozen_file):
    # Build LIBGC
    if not isfile(join(target.builds.GC, 'Makefile')):
        cmd = './configure LDFLAGS="%s" CPPFLAGS="%s" CFLAGS="%s" --enable-static --disable-shared --enable-cplusplus --prefix="%s"' % (env['LDFLAGS'], env['CPPFLAGS'], env['CFLAGS'], target.dist)
        Popen(shlex.split(cmd), cwd = target.builds.GC).communicate()

    if isfile(join(target.dist, 'lib', 'libgc.a')):
        os.remove(join(target.dist, 'lib', 'libgc.a'))
    if isfile(join(target.dist, 'lib', 'libgccpp.a')):
        os.remove(join(target.dist, 'lib', 'libgccpp.a'))

    cmd = 'make V=0 install -k -j%d' % multiprocessing.cpu_count()
    Popen(shlex.split(cmd), cwd = target.builds.GC, env=env).communicate()

    # Check success
    if isfile(join(target.dist, 'lib', 'libgc.a')) and isfile(join(target.dist, 'lib', 'libgccpp.a')):
        log('GC built successfully')
    else:
        error('Error building GC')
        exit()

    if not isfile(join(target.builds.PYTHON, 'pyconfig.h')) or not isfile(join(target.builds.PYTHON, 'Makefile')):
        # Linux is built in almost static mode (minus libdl/pthread which make OpenGL fail if compiled statically)
        cmd = join(target.dist, 'bin', 'sdl2-config' ) + ' --static-libs'
        sdlldflags = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0].replace('-lpthread', '').replace('-ldl', '') # Removing pthread and dl to make them dynamically bound (req'd for Linux)
        cmd = join(target.dist, 'bin', 'sdl2-config' ) + ' --cflags'
        sdlcflags = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0] + env['CFLAGS']
        # Fully static config, doesnt load OpenGL from SDL under Linux for some reason
        #cmd = './configure --enable-silent-rules LDFLAGS="-Wl,--no-export-dynamic -static-libgcc -static -Wl,-Bstatic %s" CPPFLAGS="-static -fPIC %s" LINKFORSHARED=" " DYNLOADFILE="dynload_stub.o" --disable-shared --prefix="%s"'% (sdlldflags,sdlcflags,target.dist,)
        # Mostly static, minus pthread and dl - Linux
        # http://wiki.python.org/moin/DebuggingWithGdb -> -g -fno-inline -fno-strict-aliasing
        cmd = './configure --enable-silent-rules LDFLAGS="%s -L%s -Wl,--no-export-dynamic -Wl,-Bstatic" CPPFLAGS="-DBOOST_PYTHON_STATIC_LIB -DBOOST_PYTHON_SOURCE %s -static -fPIC" CFLAGS="-DBOOST_PYTHON_STATIC_LIB -DBOOST_PYTHON_SOURCE %s" LINKFORSHARED=" " LDLAST="-static-libgcc -static-libstdc++ -Wl,-Bstatic %s -lgccpp -lstdc++ -lgc -Wl,-Bdynamic -lpthread -ldl" DYNLOADFILE="dynload_stub.o" --disable-shared --prefix="%s"'%\
              (env['LDFLAGS'], join(target.dist, 'lib'), env['CPPFLAGS'], sdlcflags,sdlldflags,target.dist,)
        if options.valgrind:
            cmd += ' --with-valgrind'
        Popen(shlex.split(cmd), cwd = target.builds.PYTHON).communicate()
        # Patch the Makefile to optimize the static libraries inclusion... - Linux
        cmd = SED_CMD + '"s|^LIBS=.*|LIBS=-static-libgcc -static-libstdc++ -Wl,-Bstatic -lutil -lz -lgccpp -lstdc++ -lgc -Wl,-Bdynamic %s -lpthread -ldl |g" %s' % (env['LDFLAGS'], join(target.builds.PYTHON, 'Makefile'))
        Popen(shlex.split(cmd), cwd = target.builds.PYTHON).communicate()
    make_python_freeze(options.platform, freeze_modules, frozen_file)
    if isfile(join(target.dist, 'lib', 'libpython2.7.a')):
        os.remove(join(target.dist, 'lib', 'libpython2.7.a'))

    # Remove setup.py as its of no use here and it tries to compile a lot of extensions that don't work in static mode
    if isfile(join(target.builds.PYTHON,'setup.py')):
        os.unlink(join(target.builds.PYTHON,'setup.py'))

    cmd = 'make V=0 install -k -j%d' % multiprocessing.cpu_count()
    # Rebuild Python including the frozen modules!
    Popen(shlex.split(cmd), cwd = target.builds.PYTHON, env=env).communicate()

    if not isdir (join(target.dist, 'include', 'Modules')):
        os.makedirs(join(target.dist, 'include', 'Modules'))
    shutil.copy(join(target.builds.PYTHON, 'Modules/greenlet.h'), join(target.dist, 'include', 'Modules', 'greenlet.h'))

    # Check success
    if isfile(join(target.dist, 'lib', 'libpython2.7.a')):
        log('Python built successfully')
    else:
        error('Error building python')

    return True