#!/usr/bin/env python

#Copyright (c) 2010,2011, Gabriel Jacobo
#All rights reserved.

#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions are met:

    #* Redistributions of source code must retain the above copyright
      #notice, this list of conditions and the following disclaimer.
    #* Redistributions in binary form must reproduce the above copyright
      #notice, this list of conditions and the following disclaimer in the
      #documentation and/or other materials provided with the distribution.
    #* Altered source versions must be plainly marked as such, and must not be
      #misrepresented as being the original software.
    #* Neither the name of Gabriel Jacobo, MDQ Incorporeo, Ignifuga Game Engine
      #nor the names of its contributors may be used to endorse or promote
      #products derived from this software without specific prior written permission.
    #* You must NOT, under ANY CIRCUMSTANCES, remove, modify or alter in any way
      #the duration, code functionality and graphic or audio material related to
      #the "splash screen", which should always be the first screen shown by the
      #derived work and which should ALWAYS state the Ignifuga Game Engine name,
      #original author's URL and company logo.

#THIS LICENSE AGREEMENT WILL AUTOMATICALLY TERMINATE UPON A MATERIAL BREACH OF ITS
#TERMS AND CONDITIONS

#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL GABRIEL JACOBO NOR MDQ INCORPOREO NOR THE CONTRIBUTORS
#BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Schafer: The Ignifuga Builder utility
# Author: Gabriel Jacobo <gabriel@mdqinc.com>
# Requires: RSync, Cython, GNU Tools, MINGW32, Android SDK, etc

import os, sys, shutil, shlex, fnmatch, imp, marshal, platform, tempfile, re
from subprocess import Popen, PIPE
from os.path import *
from optparse import OptionParser
from copy import deepcopy

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

class loglevel:
    DEBUG = 5
    INFO = 10
    WARNING = 20
    ERROR = 30


AVAILABLE_PLATFORMS = ['linux64', 'mingw32', 'android']
CYTHON_GIT = 'https://github.com/cython/cython.git'
ANDROID_NDK_URL = 'http://dl.google.com/android/ndk/android-ndk-r7-linux-x86.tar.bz2'
ANDROID_SDK_URL = 'http://dl.google.com/android/android-sdk_r15-linux.tgz'

ROOT_DIR = abspath(join(dirname(sys.argv[0]), '..'))
HOST_DIST_DIR = join(ROOT_DIR, 'host')
HOSTPYTHON = join(HOST_DIST_DIR, 'bin', 'python')
HOSTPGEN = join(HOST_DIST_DIR, 'bin', 'pgen')
TMP_DIR = join (ROOT_DIR, 'tmp')
DIST_DIR = join (ROOT_DIR, 'dist')
PYTHON_SRC = join(ROOT_DIR, 'external', 'Python')
SDL_SRC = join(ROOT_DIR, 'external', 'SDL')
SDL_IMAGE_SRC = join(ROOT_DIR, 'external', 'SDL_image')
SDL_TTF_SRC = join(ROOT_DIR, 'external', 'SDL_ttf')
FREETYPE_SRC = join(ROOT_DIR, 'external', 'freetype')
PNG_SRC = join(ROOT_DIR, 'external', 'png')
JPG_SRC = join(ROOT_DIR, 'external', 'jpeg')
ZLIB_SRC = join(ROOT_DIR, 'external', 'zlib')
GREENLET_SRC = join(ROOT_DIR, 'external', 'greenlet')
BITARRAY_SRC = join(ROOT_DIR, 'external', 'bitarray', 'bitarray')
ANDROID_NDK =  os.environ['ANDROID_NDK'] if 'ANDROID_NDK' in os.environ else '/opt/android-ndk'
ANDROID_SDK =  os.environ['ANDROID_SDK'] if 'ANDROID_SDK' in os.environ else '/opt/android-sdk'
PATCHES_DIR = join(ROOT_DIR, 'tools', 'patches')
IGNIFUGA_SRC = ROOT_DIR

PROJECT_ROOT = ""
PROJECT_BUILD = ""


PLATFORM_FILE = ""
PYTHON_BUILD = ""
PYTHON_HEADERS = ""
SDL_BUILD = ""
SDL_IMAGE_BUILD = ""
SDL_TTF_BUILD = ""
FREETYPE_BUILD = ""
SDL_HEADERS = ""
PNG_BUILD = ""
JPG_BUILD = ""
ZLIB_BUILD = ""
IGNIFUGA_BUILD = ""


def info(msg):
    log(msg, loglevel.INFO)
def warn(msg):
    log(msg, loglevel.WARNING)
def error(msg):
    log(msg, loglevel.ERROR)

def log(msg, level = loglevel.DEBUG):
    if level < 10:
        # Debug
        print bcolors.OKBLUE + "* " + msg + bcolors.ENDC
    elif level < 20:
        # Info
        print bcolors.OKGREEN + "* " + msg + bcolors.ENDC
    elif level < 30:
        # Warning
        print bcolors.WARNING + "* " + msg + bcolors.ENDC
    elif level < 50:
        # Error
        print bcolors.FAIL + "* " + msg + bcolors.ENDC

def setup_variables(dist_dir = join (ROOT_DIR, 'dist'), tmp_dir = join (ROOT_DIR, 'tmp')):
    """ Set up some global variables """
    global DIST_DIR, TMP_DIR, HOST_DIST_DIR, HOSTPYTHON, HOSTPGEN, PLATFORM_FILE, PYTHON_BUILD
    global PYTHON_HEADERS, SDL_BUILD, SDL_IMAGE_BUILD, SDL_TTF_BUILD, FREETYPE_BUILD, SDL_HEADERS, PNG_BUILD, JPG_BUILD, ZLIB_BUILD, IGNIFUGA_BUILD
    DIST_DIR = dist_dir
    TMP_DIR = tmp_dir
    PLATFORM_FILE = join(TMP_DIR, 'platform')
    PYTHON_BUILD = join(TMP_DIR, 'python')
    PYTHON_HEADERS = join(PYTHON_BUILD, 'Include')
    SDL_BUILD = join(TMP_DIR, 'sdl')
    SDL_IMAGE_BUILD = join(TMP_DIR, 'sdl_image')
    SDL_TTF_BUILD = join(TMP_DIR, 'sdl_ttf')
    FREETYPE_BUILD = join(TMP_DIR, 'freetype')
    SDL_HEADERS = join(DIST_DIR, 'include', 'SDL')
    PNG_BUILD = join(TMP_DIR, 'png')
    JPG_BUILD = join(TMP_DIR, 'jpg')
    ZLIB_BUILD = join(TMP_DIR, 'zlib')
    IGNIFUGA_BUILD = join(TMP_DIR, 'ignifuga')

    if not isdir(TMP_DIR):
        os.makedirs(TMP_DIR)
    
def find_cython():
    cmd = 'which cython'
    output = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0]
    cython = output.split('\n')[0]
    if isfile(cython):
        # Get the version
        cmd = '%s -V' % cython
        output = Popen(shlex.split(cmd), stderr=PIPE, stdout=PIPE).communicate()
        version = output[0].split('\n')[0] if output[0] != '' else output[1].split('\n')[0]
        v = re.search("(\d+)\.(\d+)\.(.*)", version)
        # We are looking for 0.15.1+ or higher
        if v.groups(0) > 0:
            return cython
        if v.groups(0) == 0:
            if v.groups(1) > 15:
                return cython
            if v.groups(1) == 15:
                if v.groups(2).startswith('1+') or v.groups(2) >= 2:
                    return cython
        error ('Cython version %s is incompatible')
    return None

def find_rsync():
    cmd = 'which rsync'
    output = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0]
    rsync = output.split('\n')[0]
    if isfile(rsync):
        return rsync
    return None

def find_git():
    cmd = 'which git'
    output = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0]
    git = output.split('\n')[0]
    if isfile(git):
        return git
    return None

def check_gnutools():
    tools = ['make', 'gcc', 'strip']

    for tool in tools:
        cmd = 'which ' + tool
        output = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0]
        tool_path = output.split('\n')[0]
        if not isfile(tool_path):
            error('Could not find ' + tool)
            exit()

    return True

def check_mingw32tools():
    tools = ['i586-mingw32msvc-gcc', 'i586-mingw32msvc-g++', 'i586-mingw32msvc-ar', 'i586-mingw32msvc-ranlib', 'i586-mingw32msvc-strip', 'i586-mingw32msvc-ld', 'i586-mingw32msvc-as',
            'i586-mingw32msvc-nm', 'i586-mingw32msvc-dlltool', 'i586-mingw32msvc-objdump', 'i586-mingw32msvc-windres']

    for tool in tools:
        cmd = 'which ' + tool
        output = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0]
        tool_path = output.split('\n')[0]
        if not isfile(tool_path):
            error('Could not find ' + tool)
            exit()

    return True

def install_host_tools():
    """ Install all the required host tools.
    Platforms supported:
    * Ubuntu 64 Natty 11.04
    * Ubuntu 64 Oneiric 11.10
    """
    log ('Installing development packages')
    cmd = 'sudo apt-get -y install rsync python-dev mingw32 mingw32-binutils mingw32-runtime make gcc-4.5 automake autoconf openjdk-6-jdk ia32-libs gcc-multilib'
    Popen(shlex.split(cmd)).communicate()
    
    cython = find_cython()
    if cython == None:
        git = find_git()
        if git == None:
            # Try to install GIT
            log('Trying to install GIT')
            cmd = 'sudo apt-get -y install git'
            Popen(shlex.split(cmd)).communicate()
            git = find_git()
            if git == None:
                error('Could not install GIT. Try installing it manually')
                exit()
        log ('GIT is available')
    
        log ('Trying to install Cython')
        tmp_cython = tempfile.mkdtemp()
        cmd = 'chmod 777 %s' % tmp_cython
        Popen(shlex.split(cmd)).communicate()
        cmd = 'git clone %s %s' % (CYTHON_GIT, tmp_cython)
        Popen(shlex.split(cmd)).communicate()
        cmd = 'sudo python setup.py install'
        Popen(shlex.split(cmd), cwd=tmp_cython).communicate()
        cmd = 'sudo rm -rf %s' % tmp_cython
        Popen(shlex.split(cmd)).communicate()
        cython = find_cython()
        if cython == None:
            error('Could not install Cython (0.15.1+ or higher). Try installing it manually')
            exit()

    # Android SDK and NDK
    if ANDROID_NDK == None or not isdir(ANDROID_NDK) or not isfile(join(ANDROID_NDK, 'ndk-build')) or not isdir(join(ANDROID_NDK,"toolchains/arm-linux-androideabi-4.4.3/prebuilt/linux-x86/bin")):
        log('Installing Android NDK')
        cmd = 'wget %s' % ANDROID_NDK_URL
        Popen(shlex.split(cmd), cwd=tempfile.gettempdir()).communicate()
        cmd = 'tar -jxvf %s' % ANDROID_NDK_URL.split('/')[-1]
        Popen(shlex.split(cmd), cwd=tempfile.gettempdir()).communicate()
        cmd = 'sudo mv android-ndk-r7 %s' % ANDROID_NDK
        Popen(shlex.split(cmd), cwd=tempfile.gettempdir()).communicate()
        log('Adding ANDROID_NDK variable %s to .bashrc' % ANDROID_NDK)
        f = open(join(os.environ['HOME'],'.bashrc'), 'a')
        f.write('export ANDROID_NDK="%s"\n' % ANDROID_NDK)
        f.close()
        
    if ANDROID_SDK == None or not isdir(ANDROID_SDK) or  not isfile(join(ANDROID_SDK, 'tools', 'android')):
        log('Installing Android SDK')
        cmd = 'wget %s' % ANDROID_SDK_URL
        Popen(shlex.split(cmd), cwd=tempfile.gettempdir()).communicate()
        cmd = 'tar -zxvf %s' % ANDROID_SDK_URL.split('/')[-1]
        Popen(shlex.split(cmd), cwd=tempfile.gettempdir()).communicate()
        cmd = 'sudo mv android-sdk-linux %s' % ANDROID_SDK
        Popen(shlex.split(cmd), cwd=tempfile.gettempdir()).communicate()
        log('Adding ANDROID_SDK variable %s to .bashrc' % ANDROID_SDK)
        f = open(join(os.environ['HOME'],'.bashrc'), 'a')
        f.write('export ANDROID_SDK="%s"\n' % ANDROID_SDK)
        f.close()
    
    
def clean_modules(platforms, modules, everything=False):
    log('Cleaning Build Directories')
    if isinstance(platforms, str):
        platforms = [platforms,]

    for platform in platforms:
        setup_variables(join (ROOT_DIR, 'dist', platform), join (ROOT_DIR, 'tmp', platform))
        if not everything:
            if isdir(TMP_DIR):
                if 'ignifuga' in modules:
                    if isdir(IGNIFUGA_BUILD):
                        shutil.rmtree(IGNIFUGA_BUILD)
                    if isdir(PYTHON_BUILD):
                        shutil.rmtree(PYTHON_BUILD)
                if 'sdl' in modules and isdir(SDL_BUILD):
                    shutil.rmtree(SDL_BUILD)
        else:
            if isdir(TMP_DIR):
                shutil.rmtree(TMP_DIR)
            if isdir(DIST_DIR):
                shutil.rmtree(DIST_DIR)

def locate(pattern, root=os.curdir):
    '''Locate all files matching supplied filename pattern in and below
    supplied root directory.'''
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files, pattern):
            yield os.path.join(path, filename)

def save_platform(platform):
    f = open(PLATFORM_FILE, 'w')
    f.write(platform)
    f.close()

def read_platform():
    if not isfile(PLATFORM_FILE):
        return None
    f = open (PLATFORM_FILE, 'r')
    platform = f.read()
    f.close()
    return platform

def check_host_tools():
    """ Check if the required host tools are present """
    setup_variables(join (ROOT_DIR, 'dist'), join (ROOT_DIR, 'tmp'))

    # Check the host distro
    arch, exe = platform.architecture()
    system = platform.system()
    distro_name, distro_version, distro_id = platform.linux_distribution()
    supported_platform = False
    if system == 'Linux':
        if arch == '64bit':
            if distro_name == 'Ubuntu':
                if distro_id in ['natty', 'oneiric']:
                    supported_platform = True

    if not supported_platform:
        error('Warning: Unsupported host platform/architecture. Proceed with caution. No really, this thing may blow up any minute now')
    
    if find_cython() == None:
        error("Can not find Cython, run with -D to install dependencies automatically")
        exit()

    if find_rsync() == None:
        error("Can not find Rsync, run with -D to install dependencies automatically")
        exit()

    if not check_gnutools():
        error("Can not find compilation tools (Make, GCC), run with -D to install dependencies automatically")
        exit()

    if not isfile(HOSTPYTHON) or not isfile(HOSTPGEN):
        info('Building Python for the host')
        python_build = join(ROOT_DIR, 'tmp', 'python_host')
        prepare_python('linux64', None, python_build)
        # First let's make the host version of Python, statically linked
        cmd = './configure LDFLAGS="-Wl,--no-export-dynamic -static -static-libgcc -lz" LDLAST="-static-libgcc -lz" CPPFLAGS="-static -fPIC" LINKFORSHARED=" " DYNLOADFILE="dynload_stub.o" --disable-shared --prefix="%s"'% (HOST_DIST_DIR,)
        Popen(shlex.split(cmd), cwd = python_build, env=os.environ).communicate()
        cmd = 'make install -k -j4'
        Popen(shlex.split(cmd), cwd = python_build, env=os.environ).communicate()
        shutil.copy(join(python_build, 'Parser', 'pgen'), HOSTPGEN)


def check_ignifuga_libraries(platform):
    if platform == 'linux64' or platform == 'mingw32':
        if isfile(join(DIST_DIR, 'lib', 'libpython2.7.a')):
            return True
    elif platform == 'android':
        if isfile(join(DIST_DIR, 'jni', 'python', 'libpython2.7.so')) and \
        isfile(join(DIST_DIR, 'jni', 'SDL', 'libSDL2.so')) and \
        isfile(join(DIST_DIR, 'jni', 'SDL_image', 'libSDL_image.so')) and \
        isfile(join(DIST_DIR, 'jni', 'SDL_ttf', 'libSDL_ttf.so')):
            return True

    return False
    
def prepare_source(name, src, dst):
    if not isdir(src):
        error ("Can not find %s source code" % (name,) )
        exit()

    retval = False
    if not isdir(dst):
        retval = True

    cmd = 'rsync -aqut --exclude .svn --exclude .hg --exclude Makefile %s/ %s' % (src, dst)
    Popen(shlex.split(cmd), cwd = src).communicate()
    
    return retval

# ===============================================================================================================
# PYTHON BUILDING - Requires Ignifuga building!
# ===============================================================================================================

def prepare_python(platform, ignifuga_src, python_build):
    if prepare_source('Python', PYTHON_SRC, python_build):
        # Now copy the Setup.dist files
        python_setup = join(ROOT_DIR, 'external', 'Setup.'+platform)
        if not isfile(python_setup):
            error("Can not find Python Setup file for platform")
            exit()
        setupfile = join(python_build, 'Modules', 'Setup')
        shutil.copy(python_setup, setupfile)

        # Patch import.c
        cmd = 'patch -p0 -i %s %s' % (join(PATCHES_DIR, 'import.c.diff'), join(python_build, 'Python', 'import.c'))
        Popen(shlex.split(cmd)).communicate()
        
        # Append the Ignifuga sources
        if ignifuga_src != None:
            if platform in ['linux64', 'mingw32']:
                # Get some required flags
                cmd = join(DIST_DIR, 'bin', 'sdl-config' ) + ' --cflags'
                sdlflags = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
                cmd = join(DIST_DIR, 'bin', 'sdl-config' ) + ' --static-libs'
                sdlflags = sdlflags + ' ' + Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
                cmd = join(DIST_DIR, 'bin', 'freetype-config' ) + ' --cflags'
                freetypeflags = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
                cmd = join(DIST_DIR, 'bin', 'freetype-config' ) + ' --libs'
                freetypeflags = freetypeflags + ' ' + Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]

            if platform == 'linux64':
                ignifuga_module = "\nignifuga %s -I%s -lSDL_ttf -lSDL_image -lSDL %s %s\n" % (' '.join(ignifuga_src),IGNIFUGA_BUILD, sdlflags, freetypeflags)

            elif platform== 'android':
                # Hardcoded for now
                sdlflags = '-I%s -I%s -I%s -lSDL_ttf -lSDL_image -lSDL -ldl -lGLESv1_CM -lGLESv2 -llog' % (join(SDL_BUILD, 'jni', 'SDL', 'include'), join(SDL_BUILD, 'jni', 'SDL_image'), join(SDL_BUILD, 'jni', 'SDL_ttf'))

                # Patch some problems with cross compilation
                cmd = 'patch -p0 -i %s -d %s' % (join(PATCHES_DIR, 'python.android.diff'), python_build)
                Popen(shlex.split(cmd)).communicate()
                ignifuga_module = "\nignifuga %s -I%s -L%s %s\n" % (' '.join(ignifuga_src), IGNIFUGA_BUILD, join(SDL_BUILD, 'libs', 'armeabi'), sdlflags)

            elif platform == 'mingw32':
                # Remove some perjudicial flags
                sdlflags = sdlflags.replace('-mwindows', '').replace('-Dmain=SDL_main', '')
                # Patch some problems with cross compilation
                cmd = 'patch -p0 -i %s -d %s' % (join(PATCHES_DIR, 'python.mingw32.diff'), python_build)
                Popen(shlex.split(cmd)).communicate()
                cmd = 'sed -i "s|Windows.h|windows.h|g" %s' % (join(PYTHON_BUILD, 'Modules', 'signalmodule.c'),)
                Popen(shlex.split(cmd), cwd = PYTHON_BUILD ).communicate()

                # Copy some additional files in the right place
                shutil.copy(join(PYTHON_BUILD, 'PC', 'import_nt.c'), join(PYTHON_BUILD, 'Python', 'import_nt.c'))
                shutil.copy(join(PYTHON_BUILD, 'PC', 'dl_nt.c'), join(PYTHON_BUILD, 'Python', 'dl_nt.c'))
                shutil.copy(join(PYTHON_BUILD, 'PC', 'getpathp.c'), join(PYTHON_BUILD, 'Python', 'getpathp.c'))
                shutil.copy(join(PYTHON_BUILD, 'PC', 'errmap.h'), join(PYTHON_BUILD, 'Objects', 'errmap.h'))

                ignifuga_module = "\nignifuga %s -I%s -I%s -lSDL_ttf -lSDL_image %s %s -lpng12 -ljpeg -lz\n" % (' '.join(ignifuga_src), IGNIFUGA_BUILD, join(PYTHON_BUILD, 'Include'), sdlflags, freetypeflags)

            
            f = open(setupfile, 'at')
            f.write(ignifuga_module)
            f.close()

        # Append the greenlet module
        shutil.copy(join(GREENLET_SRC, 'greenlet.c'), join(python_build, 'Modules'))
        shutil.copy(join(GREENLET_SRC, 'greenlet.h'), join(python_build, 'Modules'))
        shutil.copy(join(GREENLET_SRC, 'slp_platformselect.h'), join(python_build, 'Modules'))
        shutil.copytree(join(GREENLET_SRC, 'platform'), join(python_build, 'Modules', 'platform'))

        # Append the bitarray module
        shutil.copy(join(BITARRAY_SRC, '_bitarray.c'), join(python_build, 'Modules'))



def make_python(platform, ignifuga_src, env=os.environ):
    # Modules required by Python itself
    freeze_modules = ['site','os','posixpath','stat','genericpath','warnings','linecache','types','UserDict','_abcoll','abc','_weakrefset','copy_reg','traceback','sysconfig','re','sre_compile','sre_parse','sre_constants','codecs', 'encodings','encodings.aliases','encodings.utf_8']
    # Modules required by Ignifuga in addition to the above
    freeze_modules += ['base64', 'struct', 'json', 'json.decoder', 'json.encoder', 'json.scanner', 'json.tool', 'encodings.hex_codec', 'platform', 'string', 'pickle', 'StringIO', 'copy', 'weakref']
        
    if platform == 'linux64':
        if not isfile(join(PYTHON_BUILD, 'pyconfig.h')) or not isfile(join(PYTHON_BUILD, 'Makefile')):
            # Linux is built in almost static mode (minus libdl/pthread which make OpenGL fail if compiled statically)
            cmd = join(DIST_DIR, 'bin', 'sdl-config' ) + ' --static-libs'
            sdlldflags = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0].replace('-lpthread', '').replace('-ldl', '') # Removing pthread and dl to make them dynamically bound (req'd for Linux)
            cmd = join(DIST_DIR, 'bin', 'sdl-config' ) + ' --cflags'
            sdlcflags = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
            # Fully static config, doesnt load OpenGL from SDL under Linux for some reason
            #cmd = './configure LDFLAGS="-Wl,--no-export-dynamic -static-libgcc -static -Wl,-Bstatic %s" CPPFLAGS="-static -fPIC %s" LINKFORSHARED=" " DYNLOADFILE="dynload_stub.o" --disable-shared --prefix="%s"'% (sdlldflags,sdlcflags,DIST_DIR,)
            # Mostly static, minus pthread and dl - Linux
            cmd = './configure LDFLAGS="-Wl,--no-export-dynamic -Wl,-Bstatic" CPPFLAGS="-static -fPIC %s" LINKFORSHARED=" " LDLAST="-static-libgcc -Wl,-Bstatic %s -Wl,-Bdynamic -lpthread -ldl" DYNLOADFILE="dynload_stub.o" --disable-shared --prefix="%s"'% (sdlcflags,sdlldflags,DIST_DIR,)
            Popen(shlex.split(cmd), cwd = PYTHON_BUILD).communicate()
            # Patch the Makefile to optimize the static libraries inclusion... - Linux
            cmd = 'sed -i "s|^LIBS=.*|LIBS=-static-libgcc  -Wl,-Bstatic -lutil -lz -Wl,-Bdynamic -lpthread -ldl |g" %s' % (join(PYTHON_BUILD, 'Makefile'))
            Popen(shlex.split(cmd), cwd = PYTHON_BUILD).communicate()
        make_python_freeze(freeze_modules)
        if isfile(join(DIST_DIR, 'lib', 'libpython2.7.a')):
            os.remove(join(DIST_DIR, 'lib', 'libpython2.7.a'))

        # Remove setup.py as its of no use here and it tries to compile a lot of extensions that don't work in static mode
        if isfile(join(PYTHON_BUILD,'setup.py')):
            os.unlink(join(PYTHON_BUILD,'setup.py'))
            
        cmd = 'make install -k -j4'
        # Rebuild Python including the frozen modules!
        Popen(shlex.split(cmd), cwd = PYTHON_BUILD, env=env).communicate()

        # Check success
        if isfile(join(DIST_DIR, 'lib', 'libpython2.7.a')):
            log('Python built successfully')
        else:
            error('Error building python')
        
    elif platform == 'android':
        make_python_freeze(freeze_modules)
        # Android is built in shared mode
        if not isfile(join(PYTHON_BUILD, 'pyconfig.h')) or not isfile(join(PYTHON_BUILD, 'Makefile')):
            cmd = './configure LDFLAGS="-Wl,--allow-shlib-undefined" CFLAGS="-mandroid -fomit-frame-pointer --sysroot %s/platforms/android-5/arch-arm" HOSTPYTHON=%s HOSTPGEN=%s --host=arm-eabi --build=i686-pc-linux-gnu --enable-shared --prefix="%s"'% (ANDROID_NDK, HOSTPYTHON, HOSTPGEN, DIST_DIR,)
            Popen(shlex.split(cmd), cwd = PYTHON_BUILD, env=env).communicate()
            cmd = 'sed -i "s|^INSTSONAME=\(.*.so\).*|INSTSONAME=\\1|g" %s' % (join(PYTHON_BUILD, 'Makefile'))
            Popen(shlex.split(cmd), cwd = PYTHON_BUILD).communicate()
        cmd = 'make -k -j4 HOSTPYTHON=%s HOSTPGEN=%s CROSS_COMPILE=arm-eabi- CROSS_COMPILE_TARGET=yes' % (HOSTPYTHON, HOSTPGEN)
        Popen(shlex.split(cmd), cwd = PYTHON_BUILD, env=env).communicate()

        # Copy some files to the skeleton directory
        try:
            if isdir(join(DIST_DIR, 'jni', 'python', 'Include')):
                shutil.rmtree(join(DIST_DIR, 'jni', 'python', 'Include'))
            shutil.copytree(join(PYTHON_BUILD, 'Include'), join(DIST_DIR, 'jni', 'python', 'Include'))
            shutil.copy(join(PYTHON_BUILD, 'pyconfig.h'), join(DIST_DIR, 'jni', 'python', 'pyconfig.h'))
            shutil.copy(join(PYTHON_BUILD, 'libpython2.7.so'), join(DIST_DIR, 'jni', 'python', 'libpython2.7.so'))
            log('Python built successfully')
        except:
            error('Error while building Python for target')
            exit()

    elif platform == 'mingw32':
        if not isfile(join(PYTHON_BUILD, 'pyconfig.h')) or not isfile(join(PYTHON_BUILD, 'Makefile')):
            # Linux is built in almost static mode (minus libdl/pthread which make OpenGL fail if compiled statically)
            cmd = join(DIST_DIR, 'bin', 'sdl-config' ) + ' --static-libs'
            sdlldflags = Popen(shlex.split(cmd), stdout=PIPE, env=env).communicate()[0].split('\n')[0].replace('-lpthread', '').replace('-ldl', '') # Removing pthread and dl to make them dynamically bound (req'd for Linux)
            cmd = join(DIST_DIR, 'bin', 'sdl-config' ) + ' --cflags'
            sdlcflags = Popen(shlex.split(cmd), stdout=PIPE, env=env).communicate()[0].split('\n')[0]
            extralibs = "-lstdc++ -lgcc -lodbc32 -lwsock32 -lwinspool -lwinmm -lshell32 -lcomctl32 -lctl3d32 -lodbc32 -ladvapi32 -lopengl32 -lglu32 -lole32 -loleaut32 -luuid"
            cmd = './configure LDFLAGS="-Wl,--no-export-dynamic -static-libgcc -static %s %s" CFLAGS="-DMS_WIN32 -DMS_WINDOWS -DHAVE_USABLE_WCHAR_T" CPPFLAGS="-static %s" LINKFORSHARED=" " LIBOBJS="import_nt.o dl_nt.o getpathp.o" THREADOBJ="Python/thread.o" DYNLOADFILE="dynload_win.o" --disable-shared HOSTPYTHON=%s HOSTPGEN=%s --host=i586-mingw32msvc --build=i686-pc-linux-gnu  --prefix="%s"'% (sdlldflags, extralibs, sdlcflags, HOSTPYTHON, HOSTPGEN, DIST_DIR,)
            # Mostly static, minus pthread and dl - Linux
            #cmd = './configure LDFLAGS="-Wl,--no-export-dynamic -Wl,-Bstatic" CPPFLAGS="-static -fPIC %s" LINKFORSHARED=" " LDLAST="-static-libgcc -Wl,-Bstatic %s -Wl,-Bdynamic -lpthread -ldl" DYNLOADFILE="dynload_stub.o" --disable-shared --prefix="%s"'% (sdlcflags,sdlldflags,DIST_DIR,)
            Popen(shlex.split(cmd), cwd = PYTHON_BUILD, env=env).communicate()

            cmd = 'sed -i "s|\${LIBOBJDIR}fileblocks\$U\.o||g" %s' % (join(PYTHON_BUILD, 'Makefile'))
            Popen(shlex.split(cmd), cwd = PYTHON_BUILD).communicate()
            # Enable NT Threads
            cmd = 'sed -i "s|.*NT_THREADS.*|#define NT_THREADS|g" %s' % (join(PYTHON_BUILD, 'pyconfig.h'))
            Popen(shlex.split(cmd), cwd = PYTHON_BUILD).communicate()

            # Disable PTY stuff that gets activated because of errors in the configure script
            cmd = 'sed -i "s|.*HAVE_OPENPTY.*|#undef HAVE_OPENPTY|g" %s' % (join(PYTHON_BUILD, 'pyconfig.h'))
            Popen(shlex.split(cmd), cwd = PYTHON_BUILD).communicate()
            cmd = 'sed -i "s|.*HAVE__GETPTY.*|#undef HAVE__GETPTY|g" %s' % (join(PYTHON_BUILD, 'pyconfig.h'))
            Popen(shlex.split(cmd), cwd = PYTHON_BUILD).communicate()
            cmd = 'sed -i "s|.*HAVE_DEV_PTMX.*|#undef HAVE_DEV_PTMX|g" %s' % (join(PYTHON_BUILD, 'pyconfig.h'))
            Popen(shlex.split(cmd), cwd = PYTHON_BUILD).communicate()

        freeze_modules += ['ntpath', 'locale', 'functools']
        make_python_freeze(freeze_modules)
        if isfile(join(DIST_DIR, 'lib', 'libpython2.7.a')):
            os.remove(join(DIST_DIR, 'lib', 'libpython2.7.a'))

        cmd = 'make install -k -j4 HOSTPYTHON=%s HOSTPGEN=%s CROSS_COMPILE=mingw32msvc CROSS_COMPILE_TARGET=yes'  % (HOSTPYTHON, HOSTPGEN)
        Popen(shlex.split(cmd), cwd = PYTHON_BUILD, env=env).communicate()

        # Check success
        if isfile(join(DIST_DIR, 'lib', 'libpython2.7.a')):
            log('Python built successfully')
        else:
            error('Error building python')


def make_python_freeze(modules):
    """Get a list of python native modules, return them frozen"""
    frozen_h = '//Ignifuga auto generated file, contains the following modules: %s\n#include "Python.h"\n\n' % (','.join(modules))
    mod_sizes = {}
    # Locate the Python library
    locations = os.listdir(join(HOST_DIST_DIR, 'lib'))
    python_version = None
    for l in locations:
        if l.startswith('python') and isdir(join(HOST_DIST_DIR, 'lib', l)):
            python_version = l

    if python_version == None:
        error('Could not find Python library')
        exit()

    # Copy module source to a temp location
    modtemp = join(TMP_DIR, 'freezer')
    if isdir(modtemp):
        shutil.rmtree(modtemp)

    os.makedirs(modtemp)
    for mod in modules:
        f = join(HOST_DIST_DIR, 'lib', python_version, mod.replace('.', os.sep))
        if isdir(f):
            # It's a package!
            f = join(HOST_DIST_DIR, 'lib', python_version, mod.replace('.', os.sep), '__init__') + '.py'
            newf = join(modtemp, mod.replace('.', os.sep), '__init__')+'.py'
        else:
            f = f + '.py'
            newf = join(modtemp, mod.replace('.', os.sep)) + '.py'

        if isfile(f):
            if not isdir(dirname(newf)):
                os.makedirs(dirname(newf))
            shutil.copy(f, newf)

            # Patch some modules
            if mod == 'site':
                # Patch USER_BASE, etc
                cmd = 'patch -p0 -i %s %s' % (join(PATCHES_DIR, 'site.py.diff'), basename(newf))
                Popen(shlex.split(cmd), cwd=dirname(newf)).communicate()
            elif mod == 'platform':
                # Patch USER_BASE, etc
                cmd = 'patch -p0 -i %s %s' % (join(PATCHES_DIR, 'platform.py.diff'), basename(newf))
                Popen(shlex.split(cmd), cwd=dirname(newf)).communicate()
            
    f = open(join(modtemp, 'ignifuga_compile.py'), 'w')
    f.write("""
import compileall
compileall.compile_dir("%s")
""" % (modtemp,))
    f.close()

    cmd = '%s %s' % (join(HOST_DIST_DIR, 'bin', 'python'), join(modtemp, 'ignifuga_compile.py'))
    Popen(shlex.split(cmd), cwd = modtemp).communicate()
            
    for mod in modules:
        is_package = False
        f = join(modtemp, mod.replace('.', os.sep))
        if isdir(f):
            # It's a package!
            f = join(modtemp, mod.replace('.', os.sep), '__init__') + '.pyc'
            is_package=True
        else:
            f = f + '.pyc'
            
        if isfile(f):
            log("Freezing...%s" % f)
            fp = open(f, 'rb')
            if fp.read(4) == imp.get_magic():
                fp.read(4)
                code = marshal.dumps(marshal.load(fp))
                mod_sizes[mod] = len(code) if not is_package else -len(code)    # A package is signaled by a negative size

                frozen_h+='unsigned char M_ignifuga_frozen_%s[] = {' % mod.replace('.', '_')
                for i in range(0, len(code), 16):
                    frozen_h+='\n\t'
                    for c in code[i:i+16]:
                        frozen_h+='%d,' % ord(c)
                frozen_h+='\n};\n'
            fp.close()

        else:
            error("Could not Freeze...%s" % f)
            exit()

    frozen_h +='static struct _frozen _PyImport_FrozenModules[] = {\n'
    for mod in modules:
        if mod in mod_sizes:
            frozen_h+='\t{"%s",M_ignifuga_frozen_%s, %d},\n' % (mod, mod.replace('.', '_'), mod_sizes[mod])
    frozen_h +='\t{0, 0, 0} /* sentinel */\n};\n'

    frozen_h +='\nstruct _frozen *PyImport_FrozenModules = _PyImport_FrozenModules;\n'

    f = open(join(PYTHON_BUILD, 'Python', 'frozen.c'), 'w')
    f.write(frozen_h)
    f.close()

# ===============================================================================================================
# Ignifuga BUILDING
# ===============================================================================================================

def prepare_ignifuga(platform):
    # Copy all .py, .pyx and .pxd files
    cmd = 'rsync -aqPm --exclude .svn --exclude host --exclude tmp --exclude dist --exclude external --exclude tools --include "*/" --include "*.py" --include "*.pyx" --include "*.pxd" --include "*.h" --exclude "*" %s/ %s' % (IGNIFUGA_SRC, IGNIFUGA_BUILD)
    Popen(shlex.split(cmd), cwd = IGNIFUGA_SRC).communicate()

def make_glue(package, glue_h, glue_c):
    glue = """
#include "Python.h"
static PyMethodDef nomethods[] = {  {NULL, NULL}};
%s

PyMODINIT_FUNC
init%s(){
    PyObject* module;
    PyObject* __path__;

    // Add a __path__ attribute so Python knows that this is a package
    PyObject* package_%s = PyImport_AddModule("%s");
    Py_InitModule("%s", nomethods);
    __path__ = PyList_New(1);
    PyList_SetItem(__path__, 0, PyString_FromString("%s"));
    PyModule_AddObject(package_%s, "__path__", __path__);
%s

    }

    """ % (glue_h, package, package, package, package, package, package, glue_c)

    return glue

def make_ignifuga():
    return cythonize(IGNIFUGA_BUILD, 'ignifuga')
    
def cythonize(build_dir, package_name, skip=[]):
    files = []
    cfiles = []
    updatedfiles = []
    
    for f in locate('*.py', build_dir):
        files.append(f)
    for f in locate('*.pyx', build_dir):
        files.append(f)

    # Cythonize the source files
    for f in files:
        if f[len(build_dir):] not in skip and f[len(build_dir)+1:] not in skip:
            mf = getctime(f)
            cf = splitext(f)[0] + '.c'
            if not isfile(cf) or getctime(cf) < mf:
                ccf = join(build_dir, 'cython_src', cf.replace(os.sep, '+')[len(build_dir)+1:])
                if not isfile(ccf) or getctime(ccf) < mf:
                    log('Cythonizing %s' % basename(f))
                    cmd = 'cython "%s"' % f
                    Popen(shlex.split(cmd), cwd = build_dir).communicate()
                    updatedfiles.append(cf)
            else:
                log('Skipping Cython for %s' % basename(f))

            cfiles.append(cf)
            
    # Flatten the directory structure, replace / by + signs
    files = cfiles[:]
    cfiles = []
    cython_src = join(build_dir, 'cython_src')
    if not isdir(cython_src):
        os.makedirs(cython_src)
        
    for f in files:
        d = f[len(build_dir)+1:].replace(os.sep, '+')
        cfile = join(cython_src, d)
        if isfile(f):
            shutil.move(f, cfile)
        cfiles.append(cfile)
        if f in updatedfiles:
            updatedfiles.remove(f)
            updatedfiles.append(cfile)

    # Walk the files, arrange the package in the proper hierachy
    glue_h = ""
    glue_c = ""
    modules = {}
    packages = [package_name,]
    for f in cfiles:
        filename = basename(f)
        package = filename.replace('+', '.').replace('.c', '')
        
        # The last part of the package is the current module
        module = package.split('.')[-1]
        # Remove the module from the package
        package = '.'.join(package.split('.')[:-1])

        module_location = modules
        for sp in package.split('.'):
            if sp != '':
                if not sp in module_location:
                    module_location[sp] = {}
                module_location = module_location[sp]
            
        module_location[module] = f
        subpackage = package.split('.')
        if len(subpackage)>0:
            subpackage = subpackage[-1]
        else:
            subpackage = ''
        
        if package != '':
            package = package_name+'.'+package
        else:
            package = package_name
        
        if package not in packages:
                packages.append(package)

        #print "Cfile: %s, Package: %s, Subpackage: %s, Module: %s" % (f, package,subpackage,module)

        # Patch the correct paths and package name in the updated cython generated files
        if f in updatedfiles:
            log('Patching %s' % (basename(f),))
            if module != '__init__':
                cmd = """sed -i 's|Py_InitModule4(__Pyx_NAMESTR("\(.*\)")|Py_InitModule4(__Pyx_NAMESTR("%s.\\1")|g' %s""" % (package,f)
            else:
                cmd = """sed -i 's|Py_InitModule4(__Pyx_NAMESTR("\(.*\)")|Py_InitModule4(__Pyx_NAMESTR("%s")|g' %s""" % (package,f)
            Popen(shlex.split(cmd), cwd = cython_src).communicate()
            if module != '__init__':
                cmd = """sed -i 's|init%s|init%s_%s|g' %s""" % (module,package.replace('.', '_'),module,f)
            else:
                cmd = """sed -i 's|init%s|init%s|g' %s""" % (subpackage,package.replace('.', '_'),f)
            Popen(shlex.split(cmd), cwd = cython_src).communicate()
            cmd = """sed -i 's|__pyx_import_star_type_names|__pyx_import_star_type_names_%s%s|g' %s""" % (package.replace('.', '_'),module, f)
            Popen(shlex.split(cmd), cwd = cython_src).communicate()

        if module != '__init__':
            glue_h += "extern void init%s_%s();\n" % (package.replace('.', '_'),module)
            glue_c += '    PyImport_AppendInittab("%s.%s", init%s_%s);\n' % (package, module, package.replace('.', '_'),module)
        else:
            glue_h += "extern void init%s();\n" % (package.replace('.', '_'))
            glue_c += '    PyImport_AppendInittab("%s", init%s);\n' % (package, package.replace('.', '_'))

    # Make package xxx_glue.c with no frozen modules
    glue = make_glue(package_name, glue_h, glue_c)
    f = open(join(build_dir, 'cython_src', package_name+'_glue.c'), 'w')
    f.write(glue)
    f.close()
    cfiles.append(join(build_dir, 'cython_src', package_name+'_glue.c'))
    
    return cfiles, glue_h, glue_c
    
# ===============================================================================================================
# SDL BUILDING
# ===============================================================================================================
def prepare_sdl(platform):
    if platform == 'linux64':
        prepare_source('SDL', SDL_SRC, SDL_BUILD)
        prepare_source('SDL_image', SDL_IMAGE_SRC, SDL_IMAGE_BUILD)
        prepare_source('zlib', ZLIB_SRC, ZLIB_BUILD)
        prepare_source('libpng', PNG_SRC, PNG_BUILD)
        prepare_source('libjpeg', JPG_SRC, JPG_BUILD)
        prepare_source('freetype', FREETYPE_SRC, FREETYPE_BUILD)
        shutil.copy(join(FREETYPE_SRC, 'Makefile'), join(FREETYPE_BUILD, 'Makefile') )
        prepare_source('SDL_ttf', SDL_TTF_SRC, SDL_TTF_BUILD)
    elif platform == 'android':
        patch_target = not isdir(SDL_BUILD) # Keep count if we are starting from scratch to avoid rebuilding excessively too many files
        
        prepare_source('SDL Android Skeleton', join(SDL_SRC, 'android-project'), SDL_BUILD)
        if patch_target:
            cmd = """sed -i 's|^target=.*|target=android-7|g' %s""" % (join(SDL_BUILD, 'default.properties'),)
            Popen(shlex.split(cmd), cwd = SDL_BUILD).communicate()
            if isdir(join(SDL_BUILD, 'jni', 'src')):
                shutil.rmtree(join(SDL_BUILD, 'jni', 'src'))
            

        # Copy SDL and SDL_image to the android project structure
        prepare_source('SDL', SDL_SRC, join(SDL_BUILD, 'jni', 'SDL'))
        if patch_target:
            shutil.copy(join(SDL_BUILD, 'jni', 'SDL', 'include', 'SDL_config_android.h'), join(SDL_BUILD, 'jni', 'SDL', 'include', 'SDL_config.h'))
        prepare_source('libpng', PNG_SRC, join(SDL_BUILD, 'jni', 'png'))
        prepare_source('libjpeg', JPG_SRC, join(SDL_BUILD, 'jni', 'jpeg'))
        prepare_source('SDL_image', SDL_IMAGE_SRC, join(SDL_BUILD, 'jni', 'SDL_image'))
        if not isfile(join(SDL_BUILD, 'jni', 'SDL_image', 'Android.mk')):
            shutil.copy(join(ROOT_DIR, 'external', 'Android.mk.SDL_image'), join(SDL_BUILD, 'jni', 'SDL_image', 'Android.mk'))

        prepare_source('SDL_ttf', SDL_TTF_SRC, join(SDL_BUILD, 'jni', 'SDL_ttf'))
        prepare_source('freetype', FREETYPE_SRC, FREETYPE_BUILD)
        shutil.copy(join(FREETYPE_SRC, 'Makefile'), join(FREETYPE_BUILD, 'Makefile') )
        
        if not isdir(join(SDL_BUILD, 'jni', 'freetype')):
            os.makedirs(join(SDL_BUILD, 'jni', 'freetype'))
            shutil.copy(join(ROOT_DIR, 'external', 'Android.mk.freetype'), join(SDL_BUILD, 'jni', 'freetype', 'Android.mk'))

    elif platform == 'mingw32':
        prepare_source('SDL', SDL_SRC, SDL_BUILD)
        prepare_source('SDL_image', SDL_IMAGE_SRC, SDL_IMAGE_BUILD)
        prepare_source('zlib', ZLIB_SRC, ZLIB_BUILD)
        prepare_source('libpng', PNG_SRC, PNG_BUILD)
        prepare_source('libjpeg', JPG_SRC, JPG_BUILD)
        prepare_source('freetype', FREETYPE_SRC, FREETYPE_BUILD)
        shutil.copy(join(FREETYPE_SRC, 'Makefile'), join(FREETYPE_BUILD, 'Makefile') )
        prepare_source('SDL_ttf', SDL_TTF_SRC, SDL_TTF_BUILD)

        shutil.copy(join(ROOT_DIR, 'external', 'Makefile.in.zlib'), join(ZLIB_BUILD, 'Makefile.in'))
        shutil.copy(join(ROOT_DIR, 'external', 'Makefile.libpng.mingw32'), join(PNG_BUILD, 'Makefile'))


def make_sdl(platform, env=None):
    if platform == 'linux64':
        # Build zlib
        if isfile(join(DIST_DIR, 'lib', 'libz.a')):
            os.remove(join(DIST_DIR, 'lib', 'libz.a'))
        if not isfile(join(ZLIB_BUILD, 'Makefile')):
            cmd = './configure --static --prefix="%s"'% (DIST_DIR,)
            Popen(shlex.split(cmd), cwd = ZLIB_BUILD, env=env).communicate()
        cmd = 'make'
        Popen(shlex.split(cmd), cwd = ZLIB_BUILD, env=env).communicate()
        cmd = 'make install'
        Popen(shlex.split(cmd), cwd = ZLIB_BUILD, env=env).communicate()
        if isfile(join(DIST_DIR, 'lib', 'libz.a')):
            log('zlib built successfully')
        else:
            error('Problem building zlib')
            exit()

        # Build libpng
        cmd = 'make prefix="%s"' % (DIST_DIR,)
        Popen(shlex.split(cmd), cwd = PNG_BUILD, env=env).communicate()
        cmd = 'make install prefix="%s"' % (DIST_DIR,)
        Popen(shlex.split(cmd), cwd = PNG_BUILD, env=env).communicate()

        # Build libjpeg
        if isfile(join(DIST_DIR, 'lib', 'libjpeg.a')):
            os.remove(join(DIST_DIR, 'lib', 'libjpeg.a'))
            
        if not isfile(join(JPG_BUILD, 'Makefile')):
            cmd = './configure LDFLAGS="-static-libgcc" LIBTOOL= --disable-shared --enable-static --prefix="%s"'% (DIST_DIR,)
            Popen(shlex.split(cmd), cwd = JPG_BUILD, env=env).communicate()
            # Fixes for the Makefile
            cmd = 'sed -i "s|\./libtool||g" %s' % (join(JPG_BUILD, 'Makefile'))
            Popen(shlex.split(cmd), cwd = JPG_BUILD, env=env).communicate()
            cmd = 'sed -i "s|^O = lo|O = o|g" %s' % (join(JPG_BUILD, 'Makefile'))
            Popen(shlex.split(cmd), cwd = JPG_BUILD, env=env).communicate()
            cmd = 'sed -i "s|^A = la|A = a|g" %s' % (join(JPG_BUILD, 'Makefile'))
            Popen(shlex.split(cmd), cwd = JPG_BUILD, env=env).communicate()

        cmd = 'make'
        Popen(shlex.split(cmd), cwd = JPG_BUILD, env=env).communicate()
        cmd = 'make install-lib'
        Popen(shlex.split(cmd), cwd = JPG_BUILD, env=env).communicate()
        cmd = 'make install-headers'
        Popen(shlex.split(cmd), cwd = JPG_BUILD, env=env).communicate()

        if isfile(join(DIST_DIR, 'lib', 'libjpeg.a')):
            log('libjpeg built successfully')
        else:
            error('Problem building libjpeg')
            exit()
        

        # Build SDL
        if isfile(join(DIST_DIR, 'lib', 'libSDL2.a')):
            os.remove(join(DIST_DIR, 'lib', 'libSDL2.a'))
            
        if not isfile(join(SDL_BUILD, 'Makefile')):
            cmd = './configure LDFLAGS="-static-libgcc" --disable-shared --enable-static --prefix="%s"'% (DIST_DIR,)
            Popen(shlex.split(cmd), cwd = SDL_BUILD, env=env).communicate()
        cmd = 'make '
        Popen(shlex.split(cmd), cwd = SDL_BUILD, env=env).communicate()
        cmd = 'make install'
        Popen(shlex.split(cmd), cwd = SDL_BUILD, env=env).communicate()

        if isfile(join(DIST_DIR, 'lib', 'libSDL2.a')):
            log('SDL built successfully')
        else:
            error('Problem building SDL')
            exit()

        # Build SDL_Image
        if isfile(join(DIST_DIR, 'lib', 'libSDL_image.a')):
            os.remove(join(DIST_DIR, 'lib', 'libSDL_image.a'))
            
        if not isfile(join(SDL_IMAGE_BUILD, 'Makefile')):
            cmd = './configure LDFLAGS="-static-libgcc" --disable-shared --enable-static --with-sdl-prefix="%s" --prefix="%s"'% (DIST_DIR, DIST_DIR)
            Popen(shlex.split(cmd), cwd = SDL_IMAGE_BUILD, env=env).communicate()
        cmd = 'make'
        Popen(shlex.split(cmd), cwd = SDL_IMAGE_BUILD, env=env).communicate()
        cmd = 'make install'
        Popen(shlex.split(cmd), cwd = SDL_IMAGE_BUILD, env=env).communicate()
        if isfile(join(DIST_DIR, 'lib', 'libSDL_image.a')):
            log('SDL Image built successfully')
        else:
            error('Problem building SDL Image')
            exit()

        # Build freetype
        if isfile(join(DIST_DIR, 'lib', 'libfreetype.a')):
            os.remove(join(DIST_DIR, 'lib', 'libfreetype.a'))
            
        if not isfile(join(FREETYPE_BUILD, 'config.mk')):
            cmd = './configure LDFLAGS="-static-libgcc" --without-bzip2 --disable-shared --enable-static --with-sysroot=%s --prefix="%s"'% (DIST_DIR,DIST_DIR)
            Popen(shlex.split(cmd), cwd = FREETYPE_BUILD, env=env).communicate()
        cmd = 'make'
        Popen(shlex.split(cmd), cwd = FREETYPE_BUILD, env=env).communicate()
        cmd = 'make install'
        Popen(shlex.split(cmd), cwd = FREETYPE_BUILD, env=env).communicate()
        if isfile(join(DIST_DIR, 'lib', 'libfreetype.a')):
            log('Freetype built successfully')
        else:
            error('Problem building Freetype')
            exit()

        # Build SDL_ttf
        if isfile(join(DIST_DIR, 'lib', 'libSDL_ttf.a')):
            os.remove(join(DIST_DIR, 'lib', 'libSDL_ttf.a'))
            
        if not isfile(join(SDL_TTF_BUILD, 'configure')):
            cmd = './autogen.sh'
            Popen(shlex.split(cmd), cwd = SDL_TTF_BUILD, env=env).communicate()
            
        if not isfile(join(SDL_TTF_BUILD, 'Makefile')):
            cmd = './configure LDFLAGS="-static-libgcc" --disable-shared --enable-static --with-sdl-prefix="%s" --with-freetype-prefix="%s" --prefix="%s"'% (DIST_DIR, DIST_DIR, DIST_DIR)
            Popen(shlex.split(cmd), cwd = SDL_TTF_BUILD, env=env).communicate()
        cmd = 'make'
        Popen(shlex.split(cmd), cwd = SDL_TTF_BUILD, env=env).communicate()
        cmd = 'make install'
        Popen(shlex.split(cmd), cwd = SDL_TTF_BUILD, env=env).communicate()
        if isfile(join(DIST_DIR, 'lib', 'libSDL_ttf.a')):
            log('SDL TTF built successfully')
        else:
            error('Problem building SDL TTF')
            exit()
        
    elif platform == 'android':
        # Build freetype
        if not isfile(join(FREETYPE_BUILD, 'config.mk')):
            env['CFLAGS'] = env['CFLAGS'] + ' -std=gnu99'
            cmd = './configure LDFLAGS="-static-libgcc" --without-bzip2 --host=arm-eabi --build=i686-pc-linux-gnu --disable-shared --enable-static --with-sysroot=%s/platforms/android-5/arch-arm --prefix="%s"'% (ANDROID_NDK,DIST_DIR)
            Popen(shlex.split(cmd), cwd = FREETYPE_BUILD, env=env).communicate()
        cmd = 'make'
        Popen(shlex.split(cmd), cwd = FREETYPE_BUILD, env=env).communicate()
        if isfile(join(FREETYPE_BUILD, 'objs', '.libs', 'libfreetype.a')):
            cmd = 'rsync -aqut --exclude .svn --exclude .hg %s/ %s' % (join(FREETYPE_BUILD, 'include'), join(SDL_BUILD, 'jni', 'freetype', 'include'))
            Popen(shlex.split(cmd)).communicate()
            shutil.copy(join(FREETYPE_BUILD, 'objs', '.libs', 'libfreetype.a'), join(SDL_BUILD, 'jni', 'freetype', 'libfreetype.a'))
        else:
            error('Error compiling freetype')
            exit()
        
        
        cmd = 'ndk-build'
        Popen(shlex.split(cmd), cwd = SDL_BUILD, env=env).communicate()
        # Copy some files to the skeleton directory
        if isdir(join(DIST_DIR, 'jni', 'SDL', 'include')):
            shutil.rmtree(join(DIST_DIR, 'jni', 'SDL', 'include'))
        if isdir(join(DIST_DIR, 'jni', 'SDL', 'src')):
            shutil.rmtree(join(DIST_DIR, 'jni', 'SDL', 'src'))

        try:
            shutil.copytree(join(SDL_BUILD, 'jni', 'SDL', 'include'), join(DIST_DIR, 'jni', 'SDL', 'include'))
            shutil.copytree(join(SDL_BUILD, 'jni', 'SDL', 'src'), join(DIST_DIR, 'jni', 'SDL', 'src'))
            shutil.copy(join(SDL_BUILD, 'libs', 'armeabi', 'libSDL2.so'), join(DIST_DIR, 'jni', 'SDL', 'libSDL2.so'))
            shutil.copy(join(SDL_BUILD, 'libs', 'armeabi', 'libSDL_image.so'), join(DIST_DIR, 'jni', 'SDL_image', 'libSDL_image.so'))
            shutil.copy(join(SDL_BUILD, 'libs', 'armeabi', 'libSDL_ttf.so'), join(DIST_DIR, 'jni', 'SDL_ttf', 'libSDL_ttf.so'))
            shutil.copy(join(SDL_BUILD, 'jni', 'SDL_image', 'SDL_image.h'), join(DIST_DIR, 'jni', 'SDL_image', 'SDL_image.h'))
            shutil.copy(join(SDL_BUILD, 'jni', 'SDL_ttf', 'SDL_ttf.h'), join(DIST_DIR, 'jni', 'SDL_ttf', 'SDL_ttf.h'))
            log('SDL built successfully')
        except:
            error('Error while building SDL for target')
            exit()
    elif platform == 'mingw32':
        # Build zlib
        if isfile(join(DIST_DIR, 'lib', 'libz.a')):
            os.remove(join(DIST_DIR, 'lib', 'libz.a'))
        if not isfile(join(ZLIB_BUILD, 'Makefile')):
            cmd = './configure --static --prefix="%s"'% (DIST_DIR,)
            Popen(shlex.split(cmd), cwd = ZLIB_BUILD, env=env).communicate()
        cmd = 'make'
        Popen(shlex.split(cmd), cwd = ZLIB_BUILD, env=env).communicate()
        cmd = 'make install'
        Popen(shlex.split(cmd), cwd = ZLIB_BUILD, env=env).communicate()
        if isfile(join(DIST_DIR, 'lib', 'libz.a')):
            log('zlib built successfully')
        else:
            error('Problem building zlib')
            exit()
        
        # Build libpng
        if isfile(join(DIST_DIR, 'lib', 'libpng.a')):
            os.remove(join(DIST_DIR, 'lib', 'libpng.a'))
        cmd = 'make prefix="%s"' % (DIST_DIR,)
        Popen(shlex.split(cmd), cwd = PNG_BUILD, env=env).communicate()
        cmd = 'make install prefix="%s"' % (DIST_DIR,)
        Popen(shlex.split(cmd), cwd = PNG_BUILD, env=env).communicate()
        if isfile(join(DIST_DIR, 'lib', 'libpng.a')):
            log('libpng built successfully')
        else:
            error('Problem building libpng')
            exit()

        # Build libjpeg
        if isfile(join(DIST_DIR, 'lib', 'libjpeg.a')):
            os.remove(join(DIST_DIR, 'lib', 'libjpeg.a'))

        if not isfile(join(JPG_BUILD, 'Makefile')):
            cmd = './configure LDFLAGS="-static-libgcc" LIBTOOL= --host=i586-mingw32msvc --disable-shared --enable-static --prefix="%s"'% (DIST_DIR,)
            Popen(shlex.split(cmd), cwd = JPG_BUILD, env=env).communicate()
            # Fixes for the Makefile
            cmd = 'sed -i "s|\./libtool||g" %s' % (join(JPG_BUILD, 'Makefile'))
            Popen(shlex.split(cmd), cwd = JPG_BUILD, env=env).communicate()
            cmd = 'sed -i "s|^O = lo|O = o|g" %s' % (join(JPG_BUILD, 'Makefile'))
            Popen(shlex.split(cmd), cwd = JPG_BUILD, env=env).communicate()
            cmd = 'sed -i "s|^A = la|A = a|g" %s' % (join(JPG_BUILD, 'Makefile'))
            Popen(shlex.split(cmd), cwd = JPG_BUILD, env=env).communicate()
        
        cmd = 'make'
        Popen(shlex.split(cmd), cwd = JPG_BUILD, env=env).communicate()
        cmd = 'make install-lib'
        Popen(shlex.split(cmd), cwd = JPG_BUILD, env=env).communicate()
        cmd = 'make install-headers'
        Popen(shlex.split(cmd), cwd = JPG_BUILD, env=env).communicate()
        if isfile(join(DIST_DIR, 'lib', 'libjpeg.a')):
            log('libjpeg built successfully')
        else:
            error('Problem building libjpeg')
            exit()

        if isfile(join(DIST_DIR, 'lib', 'libSDL2.a')):
            os.remove(join(DIST_DIR, 'lib', 'libSDL2.a'))
        if not isfile(join(SDL_BUILD, 'Makefile')):
            cmd = './configure LDFLAGS="-static-libgcc" --disable-stdio-redirect --host=i586-mingw32msvc --disable-shared --enable-static --prefix="%s"'% (DIST_DIR,)
            Popen(shlex.split(cmd), cwd = SDL_BUILD, env=env).communicate()

            # HACK FIX for SDL problem, this can be removed once SDL fixes this error
            cmd = 'sed -i "s|#define SDL_AUDIO_DRIVER_XAUDIO2.*||g" %s' % (join(SDL_BUILD, 'include', 'SDL_config_windows.h'),)
            Popen(shlex.split(cmd), cwd = SDL_BUILD, env=env).communicate()
            cmd = 'sed -i "s|#define SDL_AUDIO_DRIVER_DSOUND.*||g" %s' % (join(SDL_BUILD, 'include', 'SDL_config_windows.h'),)
            Popen(shlex.split(cmd), cwd = SDL_BUILD, env=env).communicate()



        cmd = 'make'
        Popen(shlex.split(cmd), cwd = SDL_BUILD, env=env).communicate()
        cmd = 'make install'
        Popen(shlex.split(cmd), cwd = SDL_BUILD, env=env).communicate()
        if isfile(join(DIST_DIR, 'lib', 'libSDL2.a')):
            log('SDL built successfully')
        else:
            error('Problem building SDL')
            exit()

        if isfile(join(DIST_DIR, 'lib', 'libSDL_image.a')):
            os.remove(join(DIST_DIR, 'lib', 'libSDL_image.a'))
        if not isfile(join(SDL_IMAGE_BUILD, 'Makefile')):
            cmd = './configure LIBPNG_CFLAGS="-L%s -lpng12 -lz -lm -I%s" LDFLAGS="-static-libgcc" --host=i586-mingw32msvc --disable-shared --enable-static --with-sdl-prefix="%s" --prefix="%s"'% (join(DIST_DIR, 'lib'), join(DIST_DIR, 'include'), DIST_DIR, DIST_DIR)
            Popen(shlex.split(cmd), cwd = SDL_IMAGE_BUILD, env=env).communicate()
        cmd = 'make'
        Popen(shlex.split(cmd), cwd = SDL_IMAGE_BUILD, env=env).communicate()
        cmd = 'make install'
        Popen(shlex.split(cmd), cwd = SDL_IMAGE_BUILD, env=env).communicate()
        if isfile(join(DIST_DIR, 'lib', 'libSDL_image.a')):
            log('SDL Image built successfully')
        else:
            error('Problem building SDL Image')
            exit()

         # Build freetype
        if isfile(join(DIST_DIR, 'lib', 'libfreetype.a')):
            os.remove(join(DIST_DIR, 'lib', 'libfreetype.a'))
        if not isfile(join(FREETYPE_BUILD, 'config.mk')):
            env['CFLAGS'] = env['CFLAGS'] + ' -std=gnu99'
            cmd = './configure LDFLAGS="-static-libgcc" --without-bzip2  --build=i686-pc-linux-gnu --host=i586-mingw32msvc --disable-shared --enable-static --prefix="%s"'% (DIST_DIR,)
            Popen(shlex.split(cmd), cwd = FREETYPE_BUILD, env=env).communicate()
        cmd = 'make'
        Popen(shlex.split(cmd), cwd = FREETYPE_BUILD, env=env).communicate()
        cmd = 'make install'
        Popen(shlex.split(cmd), cwd = FREETYPE_BUILD, env=env).communicate()
        if isfile(join(DIST_DIR, 'lib', 'libfreetype.a')):
            log('Freetype built successfully')
        else:
            error('Problem building Freetype')
            exit()

        # Build SDL_ttf
        if isfile(join(DIST_DIR, 'lib', 'libSDL_ttf.a')):
            os.remove(join(DIST_DIR, 'lib', 'libSDL_ttf.a'))
        if not isfile(join(SDL_TTF_BUILD, 'configure')):
            cmd = './autogen.sh'
            Popen(shlex.split(cmd), cwd = SDL_TTF_BUILD, env=env).communicate()

        if not isfile(join(SDL_TTF_BUILD, 'Makefile')):
            cmd = './configure LDFLAGS="-static-libgcc" --disable-shared --enable-static --disable-sdltest --host=i586-mingw32msvc --with-sdl-prefix="%s" --with-freetype-prefix="%s" --prefix="%s"'% (DIST_DIR, DIST_DIR, DIST_DIR)
            Popen(shlex.split(cmd), cwd = SDL_TTF_BUILD, env=env).communicate()
        cmd = 'make'
        Popen(shlex.split(cmd), cwd = SDL_TTF_BUILD, env=env).communicate()
        cmd = 'make install-libSDL_ttfincludeHEADERS'
        Popen(shlex.split(cmd), cwd = SDL_TTF_BUILD, env=env).communicate()
        cmd = 'make install-libLTLIBRARIES'
        Popen(shlex.split(cmd), cwd = SDL_TTF_BUILD, env=env).communicate()
        if isfile(join(DIST_DIR, 'lib', 'libSDL_ttf.a')):
            log('SDL TTF built successfully')
        else:
            error('Problem building SDL TTF')
            exit()

# ===============================================================================================================
# USER PROJECT BUILDS
# ===============================================================================================================
def prepare_project(src, dst):
    # Copy all .py, .pyx and .pxd files
    cmd = 'rsync -aqPm --exclude .svn --exclude .hg --exclude build --include "*/" --include "*.py" --include "*.pyx" --include "*.pxd" --exclude "*" %s/ %s' % (src, dst)
    Popen(shlex.split(cmd), cwd = src).communicate()
        
# ===============================================================================================================
# PLATFORM BUILDS
# ===============================================================================================================
def spawn_shell(platform):
    cmd = 'bash'
    env = os.environ
    if platform == 'android':
        env = prepare_android_env()
    elif platform == 'mingw32':
        env = prepare_mingw32_env()

    info('Entering %s shell environment' % (platform,))

    Popen(shlex.split(cmd), cwd = DIST_DIR, env=env).communicate()
    info('Exited from %s shell environment' % (platform,))
    
def build_generic(options, platform, env=None):
    if platform in ['linux64', 'mingw32']:
        # Android has its own skeleton set up
        cmd = 'mkdir -p "%s"' % DIST_DIR
        Popen(shlex.split(cmd), env=env).communicate()
        cmd = 'mkdir -p "%s"' % join(DIST_DIR,'include')
        Popen(shlex.split(cmd), env=env).communicate()
        cmd = 'mkdir -p "%s"' % join(DIST_DIR,'bin')
        Popen(shlex.split(cmd), env=env).communicate()
        cmd = 'mkdir -p "%s"' % join(DIST_DIR,'lib')
        Popen(shlex.split(cmd), env=env).communicate()

    if not isdir(TMP_DIR):
        os.makedirs(TMP_DIR)
            
    # Compile SDL statically
    if 'sdl' in options.modules:
        info('Building SDL')
        prepare_sdl(platform)
        make_sdl(platform, env)

    # Compile Ignifuga then Python statically
    if 'ignifuga' in options.modules:
        info('Building Ignifuga')
        prepare_ignifuga(platform)
        ignifuga_src, glue_h, glue_c = make_ignifuga()
        info('Building Python')
        prepare_python(platform, ignifuga_src, PYTHON_BUILD)
        make_python(platform, ignifuga_src, env)

def build_project_generic(options, platform, env=None):
    package = options.project.split('.')[-1]
    if package == 'ignifuga':
        error('Name your project something else than ignifuga please')
        exit()

    if package +'.py' == basename(options.main).lower():
        error('Your main file can not have the same name as the project. If your project is com.mdqinc.test your main file can not be named test.py')
        exit()

    platform_build = join(PROJECT_BUILD, platform)
    main_file = join(platform_build, options.main)
    cython_src = join(PROJECT_BUILD, platform, 'cython_src')
    info('Building %s for %s  (package: %s)' % (options.project, platform, package))
    if not isdir(PROJECT_BUILD):
        os.makedirs(PROJECT_BUILD)

    # Prepare and cythonize project sources
    prepare_project(PROJECT_ROOT, platform_build)
    cfiles, glue_h, glue_c = cythonize(platform_build, package, [options.main,])

    # Cythonize main file
    main_file_ct = getctime(main_file)
    main_file_c = join(cython_src, splitext(options.main)[0] + '.c')
    cfiles.append(main_file_c)

    if not isfile(main_file_c) or getctime(main_file_c) < main_file_ct:
        log('Cythonizing main file %s' % main_file)
        cmd = 'cython --embed %s' % main_file
        mfc = join(platform_build, splitext(main_file)[0] + '.c')
        Popen(shlex.split(cmd), cwd = platform_build).communicate()
        if not isfile(mfc):
            error ('Could not cythonize main file')
            exit()
        cmd = "sed -i '1i#include \"SDL.h\"' %s" % mfc
        Popen(shlex.split(cmd), cwd = platform_build).communicate()
        shutil.move(mfc, main_file_c)

    # Build the executable
    sources = ''
    for cf in cfiles:
        sources += cf + ' '

    if platform in ['linux64', 'mingw32']:
        # Get some required flags
        cmd = join(DIST_DIR, 'bin', 'sdl-config' ) + ' --cflags'
        sdlflags = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
        cmd = join(DIST_DIR, 'bin', 'freetype-config' ) + ' --cflags'
        freetypeflags = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
        if platform == 'linux64':
            cmd = '%s -static-libgcc -Wl,--no-export-dynamic -Wl,-Bstatic -fPIC %s -I%s -I%s -L%s -lpython2.7 -lutil -lSDL_ttf -lSDL_image -lSDL -lfreetype -lm -lz %s %s -Wl,-Bdynamic -lpthread -ldl -o %s' % (env['CC'], sources,join(DIST_DIR, 'include'), join(DIST_DIR, 'include', 'python2.7'), join(DIST_DIR, 'lib'), sdlflags, freetypeflags, options.project)
            Popen(shlex.split(cmd), cwd = cython_src, env=env).communicate()
        elif platform == 'mingw32':
            extralibs = "-lstdc++ -lgcc -lodbc32 -lwsock32 -lwinspool -lwinmm -lshell32 -lcomctl32 -lctl3d32 -lodbc32 -ladvapi32 -lopengl32 -lglu32 -lole32 -loleaut32 -luuid -lgdi32 -limm32 -lversion"
            cmd = '%s -Wl,--no-export-dynamic -static-libgcc -static -DMS_WIN32 -DMS_WINDOWS -DHAVE_USABLE_WCHAR_T %s -I%s -I%s -L%s -lpython2.7 -mwindows -lmingw32 -lSDL_ttf -lSDL_image -lSDLmain -lSDL -lpng -ljpeg -lfreetype -lz %s %s %s -o %s' % (env['CC'], sources, join(DIST_DIR, 'include'), join(DIST_DIR, 'include', 'python2.7'), join(DIST_DIR, 'lib'), sdlflags, freetypeflags, extralibs, options.project)
            print cmd
            Popen(shlex.split(cmd), cwd = cython_src, env=env).communicate()

        if not isfile(join(cython_src, options.project)):
            error('Error during compilation of project')
            exit()
        cmd = '%s %s' % (env['STRIP'], join(cython_src, options.project))
        Popen(shlex.split(cmd), cwd = cython_src, env=env).communicate()
        if platform == 'linux64':
            shutil.move(join(cython_src, options.project), join(PROJECT_BUILD, '..', options.project))
        elif platform == 'mingw32':
            shutil.move(join(cython_src, options.project), join(PROJECT_BUILD, '..', options.project+'.exe'))

    elif platform == 'android':
        # Copy/update the skeleton
        android_project = join(platform_build, 'android_project')
        jni_src = join(android_project, 'jni', 'src')
        local_cfiles = []
        for cfile in cfiles:
            local_cfiles.append(basename(cfile))

        cmd = 'rsync -aqPm --exclude .svn --exclude .hg %s/ %s' % (DIST_DIR, android_project)
        Popen(shlex.split(cmd), cwd = DIST_DIR).communicate()


        if options.wallpaper:
            # Wallpapers use a slightly different manifest
            if isfile(join(android_project, 'AndroidManifest.wallpaper.xml')):
                shutil.move(join(android_project, 'AndroidManifest.wallpaper.xml'), join(android_project, 'AndroidManifest.xml'))

        # Modify the glue code to suit the project
        cmd = "sed -i 's|\[\[PROJECT_NAME\]\]|%s|g' %s" % (options.project.replace('.', '_'), join(jni_src, 'jni_glue.cpp'))
        Popen(shlex.split(cmd), cwd = jni_src).communicate()
        cmd = "sed -i 's|\[\[PROJECT_NAME\]\]|%s|g' %s" % (options.project, join(android_project, 'AndroidManifest.xml'))
        Popen(shlex.split(cmd), cwd = jni_src).communicate()
        cmd = "sed -i 's|\[\[PROJECT_NAME\]\]|%s|g' %s" % (options.project, join(android_project, 'src', 'SDLActivity.java'))
        Popen(shlex.split(cmd), cwd = jni_src).communicate()
        cmd = "sed -i 's|\[\[PROJECT_NAME\]\]|%s|g' %s" % (options.project, join(android_project, 'src', 'SDLActivity.wallpaper.java'))
        Popen(shlex.split(cmd), cwd = jni_src).communicate()
        cmd = "sed -i 's|\[\[PROJECT_NAME\]\]|%s|g' %s" % (options.project, join(android_project, 'build.xml'))
        Popen(shlex.split(cmd), cwd = jni_src).communicate()
        cmd = "sed -i 's|\[\[SDK_LOCATION\]\]|%s|g' %s" % (ANDROID_SDK, join(android_project, 'local.properties'))
        Popen(shlex.split(cmd), cwd = jni_src).communicate()
        cmd = "sed -i 's|\[\[LOCAL_SRC_FILES\]\]|%s|g' %s" % (' '.join(local_cfiles), join(jni_src, 'Android.mk'))
        Popen(shlex.split(cmd), cwd = jni_src).communicate()

        # Make the correct structure inside src
        sdlActivityDir = join(android_project, 'src', options.project.replace('.', os.sep))
        if not isdir(sdlActivityDir):
            os.makedirs(sdlActivityDir)
        if options.wallpaper:
            # Wallpapers use a slightly different activity
            shutil.move(join(android_project, 'src', 'SDLActivity.wallpaper.java'), join(sdlActivityDir, 'SDLActivity.java'))
            os.unlink(join(android_project, 'src', 'SDLActivity.java'))
        else:
            shutil.move(join(android_project, 'src', 'SDLActivity.java'), join(sdlActivityDir, 'SDLActivity.java'))
            os.unlink(join(android_project, 'src', 'SDLActivity.wallpaper.java'))

        # Copy cythonized sources
        cmd = 'rsync -aqPm --exclude .svn --exclude .hg %s/ %s' % (cython_src, jni_src)
        Popen(shlex.split(cmd), cwd = cython_src).communicate()

        # Copy assets
        for asset in options.assets:
            cmd = 'rsync -aqPm --exclude .svn --exclude .hg %s %s' % (asset, join(android_project, 'assets'))
            Popen(shlex.split(cmd)).communicate()

        # Build it
        cmd = 'ndk-build'
        Popen(shlex.split(cmd), cwd = join(platform_build, 'android_project'), env=env).communicate()
        cmd = 'ant debug'
        Popen(shlex.split(cmd), cwd = join(platform_build, 'android_project'), env=env).communicate()

        apk = join(android_project, 'bin', options.project+'-debug.apk')
        if not isfile(apk):
            error ('Error during compilation of the project')
            exit()

        shutil.move(apk, join(PROJECT_BUILD, '..', options.project+'.apk'))


    info('Project built successfully')

        
# ===============================================================================================================
# LINUX 64
# ===============================================================================================================
def prepare_linux64_env():
    """ Set up the environment variables for Linux64 compilation"""
    env = deepcopy(os.environ)
    env['CC'] = 'gcc'
    env['STRIP'] = 'strip'
    return env

def build_linux64 (options):
    platform = 'linux64'
    setup_variables(join(ROOT_DIR, 'dist', platform), join(ROOT_DIR, 'tmp', platform))

    if options.main and check_ignifuga_libraries(platform):
        return
    info('Building Ignifuga For Linux 64 bits')
    if not isdir(DIST_DIR):
        os.makedirs(DIST_DIR)
    build_generic(options, platform)

def build_project_linux64(options):
    platform = 'linux64'
    env = prepare_linux64_env()
    build_project_generic(options, platform, env)


# ===============================================================================================================
# ANDROID
# ===============================================================================================================
def prepare_android_env():
    """ Set up the environment variables for Android compilation"""

    # Check that the NDK and SDK exist
    if ANDROID_NDK == None:
        error('No Android NDK location provided (use command line parameters or environment variable ANDROID_NDK)')
        exit()
    if ANDROID_SDK == None:
        error('No Android SDK location provided (use command line parameters or environment variable ANDROID_SDK)')
        exit()
        
    if not isdir(ANDROID_NDK) or not isfile(join(ANDROID_NDK, 'ndk-build')) or not isdir(join(ANDROID_NDK,"toolchains/arm-linux-androideabi-4.4.3/prebuilt/linux-x86/bin")):
        error('Can not locate Valid Android NDK at %s, install or update it' % (ANDROID_NDK,))
        exit()
    if ANDROID_SDK == None or not isdir(ANDROID_SDK) or  not isfile(join(ANDROID_SDK, 'tools', 'android')):
        error('Can not locate Android SDK at %s' % ANDROID_SDK)
        exit()
    env = deepcopy(os.environ)
    if 'JAVA_HOME' not in os.environ:
        env['JAVA_HOME'] = "/usr/lib/jvm/java-6-openjdk"

    if not isdir(env['JAVA_HOME']) or  not isfile(join(env['JAVA_HOME'], 'bin', 'java')):
        error('Can not locate JAVA at %s' % (env['JAVA_HOME'],))
        exit()
    
    env['PATH'] = "%s/toolchains/arm-linux-androideabi-4.4.3/prebuilt/linux-x86/bin/:%s:%s/tools:/usr/local/bin:/usr/bin:/bin:%s" % (ANDROID_NDK, ANDROID_NDK, ANDROID_SDK, '') #env['PATH'])
    env['ARCH'] = "armeabi"
    env['SDK'] = ANDROID_SDK
    
    #env['ARCH'] = "armeabi-v7a"
    env['CFLAGS'] ="-DANDROID -mandroid -fomit-frame-pointer --sysroot %s/platforms/android-5/arch-arm" % (ANDROID_NDK)
    if env['ARCH'] == "armeabi-v7a":
       env['CFLAGS']+=" -march=armv7-a -mfloat-abi=softfp -mfpu=vfp -mthumb"
    env['CXXFLAGS'] = env['CFLAGS']
    env['CC'] = 'arm-linux-androideabi-gcc %s' % (env['CFLAGS'],)
    env['CXX'] = 'arm-linux-androideabi-g++ %s' % (env['CXXFLAGS'],)
    env['AR'] = "arm-linux-androideabi-ar"
    env['RANLIB'] = "arm-linux-androideabi-ranlib"
    env['STRIP'] = "arm-linux-androideabi-strip --strip-unneeded"
    env['MAKE'] = 'make -k -j4 HOSTPYTHON=%s HOSTPGEN=%s CROSS_COMPILE=arm-eabi- CROSS_COMPILE_TARGET=yes' % (HOSTPYTHON, HOSTPGEN)

    env['DIST_DIR'] = DIST_DIR
    env['TMP_DIR'] = TMP_DIR
    return env

def prepare_android_skeleton():
    """ Copy a skeleton of the final project to the dist directory """
    if not isdir(DIST_DIR):
        shutil.copytree(join(ROOT_DIR, 'tools', 'android_skeleton'), DIST_DIR)
        cmd = 'find %s -name ".svn" -type d -exec rm -rf {} \;' % (DIST_DIR,)
        Popen(shlex.split(cmd), cwd = DIST_DIR).communicate()
    
def build_android (options):
    platform = 'android'
    setup_variables(join(ROOT_DIR, 'dist', platform), join(ROOT_DIR, 'tmp', platform))
    if options.main != None and check_ignifuga_libraries(platform):
        return
    info('Building Ignifuga For Android')
    env = prepare_android_env()
    prepare_android_skeleton()
    build_generic(options, platform, env)

def build_project_android(options):
    platform = 'android'
    env = prepare_android_env()
    build_project_generic(options, platform, env)

# ===============================================================================================================
# Windows - Mingw32
# ===============================================================================================================

def prepare_mingw32_env():
    """ Set up the environment variables for Mingw32 compilation"""
    env = deepcopy(os.environ)
    #env['PATH'] = "%s/toolchains/arm-linux-androideabi-4.4.3/prebuilt/linux-x86/bin/:%s:%s/tools:/usr/local/bin:/usr/bin:/bin:%s" % (ANDROID_NDK, ANDROID_NDK, ANDROID_SDK, '') #env['PATH'])
    env['ARCH'] = "win32"
    #env['CFLAGS'] ="-I %s" % (join(PYTHON_BUILD, 'PC'),)
    # Force LIBC functions (otherwise you get undefined SDL_sqrt, SDL_cos, etc
    # Force a dummy haptic and mm joystick (otherwise there a bunch of undefined symbols from SDL_haptic.c and SDL_joystick.c).
    # The cross platform configuration of SDL doesnt work fine at this moment and it doesn't define these variables as it should
    env['CFLAGS'] = "-DHAVE_LIBC=1 -DSDL_HAPTIC_DUMMY=1 -DSDL_JOYSTICK_WINMM=1"
    env['CXXFLAGS'] = env['CFLAGS']
    env['CC'] = 'i586-mingw32msvc-gcc %s' % (env['CFLAGS'],)
    env['CXX'] = 'i586-mingw32msvc-g++ %s' % (env['CXXFLAGS'],)
    env['AR'] = "i586-mingw32msvc-ar"
    env['RANLIB'] = "i586-mingw32msvc-ranlib"
    env['STRIP'] = "i586-mingw32msvc-strip --strip-unneeded"
    env['LD'] = "i586-mingw32msvc-ld"
    env['AS'] = "i586-mingw32msvc-as"
    env['NM'] = "i586-mingw32msvc-nm"
    env['DLLTOOL'] = "i586-mingw32msvc-dlltool"
    env['OBJDUMP'] = "i586-mingw32msvc-objdump"
    env['RESCOMP'] = "i586-mingw32msvc-windres"
    env['MAKE'] = 'make -k -j4 HOSTPYTHON=%s HOSTPGEN=%s CROSS_COMPILE=mingw32msvc CROSS_COMPILE_TARGET=yes' % (HOSTPYTHON, HOSTPGEN)
    env['DIST_DIR'] = DIST_DIR
    env['TMP_DIR'] = TMP_DIR
    return env

def build_mingw32 (options):
    platform = 'mingw32'
    setup_variables(join(ROOT_DIR, 'dist', platform), join(ROOT_DIR, 'tmp', platform))
    check_mingw32tools()
    if options.main and check_ignifuga_libraries(platform):
        return
    info('Building Ignifuga For Windows 32 bits')
    if not isdir(DIST_DIR):
        os.makedirs(DIST_DIR)
    env = prepare_mingw32_env()
    build_generic(options, platform, env)

def build_project_mingw32(options):
    platform = 'mingw32'
    env = prepare_mingw32_env()
    build_project_generic(options, platform, env)

# ===============================================================================================================
# MAIN
# ===============================================================================================================
    
if __name__ == '__main__':
    info('Schafer - The Ignifuga Builder Utility')
    usage = "schafer.py -p platform [options]"
    parser = OptionParser(usage=usage, version="Ignifuga Build Utility 1.0")
    parser.add_option("-P", "--platform", dest="platform", default=None,
                  help="Platform (iphone, android, linux, windows, osx, all)")
    parser.add_option("-M", "--module", dest="module", default="all",
                  help="Ignifuga module to build (all, ignifuga, sdl) Default: all")
    parser.add_option("-c", "--clean",
                  action="store_true", dest="clean", default=False,
                  help="Clean temporary files before building")
    parser.add_option("-C", "--forceclean",
                  action="store_true", dest="forceclean", default=False,
                  help="Clean everything before building")
    parser.add_option("-s", "--shell",
                  action="store_true", dest="shell", default=False,
                  help="Create a shell with environment variables set up")
    parser.add_option("--androidndk",
                  dest="androidndk", default=None,
                  help="Location of the Android NDK (otherwise looks in env variable ANDROID_NDK)")
    parser.add_option("--androidsdk",
                  dest="androidsdk", default=None,
                  help="Location of the Android SDK (otherwise looks in env variable ANDROID_SDK)")
    parser.add_option("-m", "--main", dest="main", default=None,
                  help="Main Python File (required to compile a project)")
    parser.add_option("-p", "--project", dest="project", default="com.mdqinc.test",
                  help="Project Name (default: com.mdqinc.ignifuga)")
    parser.add_option("-a", "--asset", dest="assets", default=[], action="append",
                  help="Asset location")
    parser.add_option("-D", "--dependencies", dest="dependencies", default=False, action="store_true",
                  help="Install required dependencies and exit")
    parser.add_option("-w", "--wallpaper",
        action="store_true", dest="wallpaper", default=False,
        help="Build a Live Wallpaper (only valid for Android)")
    (options, args) = parser.parse_args()


    if options.dependencies:
        install_host_tools()
        exit()

    options.platform = str(options.platform).lower()

    #if options.platform not in ('iphone','android', 'linux64', 'linux32', 'mingw32', 'mingw64', 'osx', 'all'):
    if options.platform not in AVAILABLE_PLATFORMS and options.platform != 'all':
        error('Invalid target platform')
        parser.print_help()
        exit()

    if options.platform == 'all':
        platforms = AVAILABLE_PLATFORMS
    else:
        platforms = [options.platform,]

    if options.androidndk != None:
        ANDROID_NDK = options.androidndk
    if options.androidsdk != None:
        ANDROID_SDK = options.androidsdk

    if options.shell and options.platform != 'all':
        spawn_shell(options.platform)
        exit()

    if options.module == 'all' or options.main != None:
        options.modules = [ 'sdl', 'ignifuga']
        del options.module
    else:
        options.modules = [options.module,]

    
    if options.clean or options.forceclean:
        clean_modules(platforms, options.modules, options.forceclean)

    check_host_tools()
    for platform in platforms:
        locals()["build_"+platform](options)

    info ('Ignifuga engine files are ready.')

    if options.main == None:
        exit()

    if not isfile(options.main):
        error('Can not find main project file')
        exit()
            
    info('Compiling project: ' + options.project )

    
    PROJECT_ROOT = abspath(dirname(options.main))
    PROJECT_BUILD = join(PROJECT_ROOT, 'build')
    for platform in platforms:
        locals()["build_project_"+platform](options)