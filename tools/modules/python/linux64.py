#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Build Python for Linux 64
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import os, shlex, shutil
from os.path import *
from subprocess import Popen, PIPE
from schafer import log, error, prepare_source, make_python_freeze

def make(env, DIST_DIR, BUILDS, freeze_modules, frozen_file):
    if not isfile(join(BUILDS['PYTHON'], 'pyconfig.h')) or not isfile(join(BUILDS['PYTHON'], 'Makefile')):
        # Linux is built in almost static mode (minus libdl/pthread which make OpenGL fail if compiled statically)
        cmd = join(DIST_DIR, 'bin', 'sdl2-config' ) + ' --static-libs'
        sdlldflags = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0].replace('-lpthread', '').replace('-ldl', '') # Removing pthread and dl to make them dynamically bound (req'd for Linux)
        cmd = join(DIST_DIR, 'bin', 'sdl2-config' ) + ' --cflags'
        sdlcflags = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
        # Fully static config, doesnt load OpenGL from SDL under Linux for some reason
        #cmd = './configure --enable-silent-rules LDFLAGS="-Wl,--no-export-dynamic -static-libgcc -static -Wl,-Bstatic %s" CPPFLAGS="-static -fPIC %s" LINKFORSHARED=" " DYNLOADFILE="dynload_stub.o" --disable-shared --prefix="%s"'% (sdlldflags,sdlcflags,DIST_DIR,)
        # Mostly static, minus pthread and dl - Linux
        cmd = './configure --enable-silent-rules LDFLAGS="-Wl,--no-export-dynamic -Wl,-Bstatic" CPPFLAGS="-static -fPIC %s" LINKFORSHARED=" " LDLAST="-static-libgcc -Wl,-Bstatic %s -Wl,-Bdynamic -lpthread -ldl" DYNLOADFILE="dynload_stub.o" --disable-shared --prefix="%s"'% (sdlcflags,sdlldflags,DIST_DIR,)
        Popen(shlex.split(cmd), cwd = BUILDS['PYTHON']).communicate()
        # Patch the Makefile to optimize the static libraries inclusion... - Linux
        cmd = SED_CMD + '"s|^LIBS=.*|LIBS=-static-libgcc  -Wl,-Bstatic -lutil -lz -Wl,-Bdynamic -lpthread -ldl |g" %s' % (join(BUILDS['PYTHON'], 'Makefile'))
        Popen(shlex.split(cmd), cwd = BUILDS['PYTHON']).communicate()
    make_python_freeze(freeze_modules, frozen_file)
    if isfile(join(DIST_DIR, 'lib', 'libpython2.7.a')):
        os.remove(join(DIST_DIR, 'lib', 'libpython2.7.a'))

    # Remove setup.py as its of no use here and it tries to compile a lot of extensions that don't work in static mode
    if isfile(join(BUILDS['PYTHON'],'setup.py')):
        os.unlink(join(BUILDS['PYTHON'],'setup.py'))

    cmd = 'make V=0 install -k -j4'
    # Rebuild Python including the frozen modules!
    Popen(shlex.split(cmd), cwd = BUILDS['PYTHON'], env=env).communicate()

    # Check success
    if isfile(join(DIST_DIR, 'lib', 'libpython2.7.a')):
        log('Python built successfully')
    else:
        error('Error building python')

    return True