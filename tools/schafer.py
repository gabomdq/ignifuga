#!/usr/bin/env python
#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

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

def get_build_platform():
    # Check the host distro
    arch, exe = platform.architecture()
    system = platform.system()
    if system == 'Linux':
        distro_name, distro_version, distro_id = platform.linux_distribution()
    elif system == 'Darwin':
        distro_name, distro_version, distro_id = platform.mac_ver()
    return system, arch, distro_name, distro_version, distro_id

def get_available_platforms():
    """ Determine which build platforms are available depending on which platform we are building """
    system, arch, distro_name, distro_version, distro_id = get_build_platform()

    if system == 'Linux':
        SED_CMD = 'sed -i '
        if arch == '64bit':
            AVAILABLE_PLATFORMS = ['linux64', 'mingw32', 'android']
        else:
            AVAILABLE_PLATFORMS = ['mingw32', 'android']
    elif system == 'Darwin':
        SED_CMD = 'sed -i "" '
        AVAILABLE_PLATFORMS = ['osx', 'android', 'iosv6', 'iosv7']

    return AVAILABLE_PLATFORMS, SED_CMD

AVAILABLE_PLATFORMS, SED_CMD = get_available_platforms()

CYTHON_GIT = 'https://github.com/cython/cython.git'
ANDROID_NDK_URL = {'Linux': 'http://dl.google.com/android/ndk/android-ndk-r7b-linux-x86.tar.bz2', 'Darwin': 'http://dl.google.com/android/ndk/android-ndk-r7b-darwin-x86.tar.bz2'}
ANDROID_SDK_URL = {'Linux': 'http://dl.google.com/android/android-sdk_r16-linux.tgz', 'Darwin': 'http://dl.google.com/android/android-sdk_r16-macosx.zip' }

ROOT_DIR = abspath(join(dirname(sys.argv[0]), '..'))
HOST_DIST_DIR = join(ROOT_DIR, 'host')
HOSTPYTHON = join(HOST_DIST_DIR, 'bin', 'python')
HOSTPGEN = join(HOST_DIST_DIR, 'bin', 'pgen')
TMP_DIR = join (ROOT_DIR, 'tmp')
DIST_DIR = join (ROOT_DIR, 'dist')

SOURCES = {}
SOURCES['PYTHON'] = join(ROOT_DIR, 'external', 'Python')
SOURCES['SDL'] = join(ROOT_DIR, 'external', 'SDL')
SOURCES['SDL_IMAGE'] = join(ROOT_DIR, 'external', 'SDL_image')
SOURCES['SDL_TTF'] = join(ROOT_DIR, 'external', 'SDL_ttf')
SOURCES['FREETYPE'] = join(ROOT_DIR, 'external', 'freetype')
SOURCES['PNG'] = join(ROOT_DIR, 'external', 'png')
SOURCES['JPG'] = join(ROOT_DIR, 'external', 'jpeg')
SOURCES['ZLIB'] = join(ROOT_DIR, 'external', 'zlib')
SOURCES['GREENLET'] = join(ROOT_DIR, 'external', 'greenlet')
SOURCES['BITARRAY'] = join(ROOT_DIR, 'external', 'bitarray', 'bitarray')
SOURCES['IGNIFUGA'] = ROOT_DIR

ANDROID_NDK =  os.environ['ANDROID_NDK'] if 'ANDROID_NDK' in os.environ else '/opt/android-ndk'
ANDROID_SDK =  os.environ['ANDROID_SDK'] if 'ANDROID_SDK' in os.environ else '/opt/android-sdk'
PATCHES_DIR = join(ROOT_DIR, 'tools', 'patches')

PROJECT_ROOT = ""
BUILDS = {}
BUILDS['PROJECT'] = ""

PLATFORM_FILE = ""
BUILDS['PYTHON'] = ""
PYTHON_HEADERS = ""
BUILDS['SDL'] = ""
BUILDS['SDL_IMAGE'] = ""
BUILDS['SDL_TTF'] = ""
BUILDS['FREETYPE'] = ""
SDL_HEADERS = ""
BUILDS['PNG'] = ""
BUILDS['JPG'] = ""
BUILDS['ZLIB'] = ""
BUILDS['IGNIFUGA'] = ""

from modules.util import *
from modules.env import *

def setup_variables(dist_dir = join (ROOT_DIR, 'dist'), tmp_dir = join (ROOT_DIR, 'tmp')):
    """ Set up some global variables """
    global DIST_DIR, TMP_DIR, HOST_DIST_DIR, HOSTPYTHON, HOSTPGEN, PLATFORM_FILE, BUILDS, PYTHON_HEADERS
    DIST_DIR = dist_dir
    TMP_DIR = tmp_dir
    PLATFORM_FILE = join(TMP_DIR, 'platform')
    BUILDS['PYTHON'] = join(TMP_DIR, 'python')
    PYTHON_HEADERS = join(BUILDS['PYTHON'], 'Include')
    BUILDS['SDL'] = join(TMP_DIR, 'sdl')
    BUILDS['SDL_IMAGE'] = join(TMP_DIR, 'sdl_image')
    BUILDS['SDL_TTF'] = join(TMP_DIR, 'sdl_ttf')
    BUILDS['FREETYPE'] = join(TMP_DIR, 'freetype')
    SDL_HEADERS = join(DIST_DIR, 'include', 'SDL')
    BUILDS['PNG'] = join(TMP_DIR, 'png')
    BUILDS['JPG'] = join(TMP_DIR, 'jpg')
    BUILDS['ZLIB'] = join(TMP_DIR, 'zlib')
    BUILDS['IGNIFUGA'] = join(TMP_DIR, 'ignifuga')

    if not isdir(TMP_DIR):
        os.makedirs(TMP_DIR)

def clean_modules(platforms, modules, everything=False):
    log('Cleaning Build Directories')
    if isinstance(platforms, str):
        platforms = [platforms,]

    for platform in platforms:
        setup_variables(join (ROOT_DIR, 'dist', platform), join (ROOT_DIR, 'tmp', platform))
        if not everything:
            if isdir(TMP_DIR):
                if 'ignifuga' in modules:
                    if isdir(BUILDS['IGNIFUGA']):
                        shutil.rmtree(BUILDS['IGNIFUGA'])
                    if isdir(BUILDS['PYTHON']):
                        shutil.rmtree(BUILDS['PYTHON'])
                if 'sdl' in modules and isdir(BUILDS['SDL']):
                    shutil.rmtree(BUILDS['SDL'])
        else:
            if isdir(TMP_DIR):
                shutil.rmtree(TMP_DIR)
            if isdir(DIST_DIR):
                shutil.rmtree(DIST_DIR)

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

def check_ignifuga_libraries(platform):
    if platform in ['linux64', 'mingw32', 'osx']:
        if isfile(join(DIST_DIR, 'lib', 'libpython2.7.a')):
            return True
    elif platform == 'android':
        if isfile(join(DIST_DIR, 'jni', 'python', 'libpython2.7.so')) and \
        isfile(join(DIST_DIR, 'jni', 'SDL', 'libSDL2.so')) and \
        isfile(join(DIST_DIR, 'jni', 'SDL_image', 'libSDL2_image.so')) and \
        isfile(join(DIST_DIR, 'jni', 'SDL_ttf', 'libSDL2_ttf.so')):
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
    if prepare_source('Python', SOURCES['PYTHON'], python_build):
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
            if platform in ['linux64', 'mingw32', 'osx']:
                # Get some required flags
                cmd = join(DIST_DIR, 'bin', 'sdl2-config' ) + ' --cflags'
                sdlflags = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
                cmd = join(DIST_DIR, 'bin', 'sdl2-config' ) + ' --static-libs'
                sdlflags = sdlflags + ' ' + Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
                cmd = join(DIST_DIR, 'bin', 'freetype-config' ) + ' --cflags'
                freetypeflags = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
                cmd = join(DIST_DIR, 'bin', 'freetype-config' ) + ' --libs'
                freetypeflags = freetypeflags + ' ' + Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]

            if platform == 'linux64' or platform == 'osx':
                ignifuga_module = "\nignifuga %s -I%s -lSDL2_ttf -lSDL2_image -lSDL2 -lpng12 -ljpeg %s %s\n" % (' '.join(ignifuga_src),BUILDS['IGNIFUGA'], sdlflags, freetypeflags)

            elif platform== 'android':
                # Hardcoded for now
                sdlflags = '-I%s -I%s -I%s -lSDL2_ttf -lSDL2_image -lSDL2 -ldl -lGLESv1_CM -lGLESv2 -llog' % (join(BUILDS['SDL'], 'jni', 'SDL', 'include'), join(BUILDS['SDL'], 'jni', 'SDL_image'), join(BUILDS['SDL'], 'jni', 'SDL_ttf'))

                # Patch some problems with cross compilation
                cmd = 'patch -p0 -i %s -d %s' % (join(PATCHES_DIR, 'python.android.diff'), python_build)
                Popen(shlex.split(cmd)).communicate()
                ignifuga_module = "\nignifuga %s -I%s -L%s %s\n" % (' '.join(ignifuga_src), BUILDS['IGNIFUGA'], join(BUILDS['SDL'], 'libs', 'armeabi'), sdlflags)

            elif platform == 'mingw32':
                # Remove some perjudicial flags
                sdlflags = sdlflags.replace('-mwindows', '').replace('-Dmain=SDL_main', '')
                # Patch some problems with cross compilation
                cmd = 'patch -p0 -i %s -d %s' % (join(PATCHES_DIR, 'python.mingw32.diff'), python_build)
                Popen(shlex.split(cmd)).communicate()
                cmd = SED_CMD + '"s|Windows.h|windows.h|g" %s' % (join(BUILDS['PYTHON'], 'Modules', 'signalmodule.c'),)
                Popen(shlex.split(cmd), cwd = BUILDS['PYTHON'] ).communicate()

                # Copy some additional files in the right place
                shutil.copy(join(BUILDS['PYTHON'], 'PC', 'import_nt.c'), join(BUILDS['PYTHON'], 'Python', 'import_nt.c'))
                shutil.copy(join(BUILDS['PYTHON'], 'PC', 'dl_nt.c'), join(BUILDS['PYTHON'], 'Python', 'dl_nt.c'))
                shutil.copy(join(BUILDS['PYTHON'], 'PC', 'getpathp.c'), join(BUILDS['PYTHON'], 'Python', 'getpathp.c'))
                shutil.copy(join(BUILDS['PYTHON'], 'PC', 'errmap.h'), join(BUILDS['PYTHON'], 'Objects', 'errmap.h'))

                ignifuga_module = "\nignifuga %s -I%s -I%s -lSDL2_ttf -lSDL2_image %s %s -lpng12 -ljpeg -lz\n" % (' '.join(ignifuga_src), BUILDS['IGNIFUGA'], join(BUILDS['PYTHON'], 'Include'), sdlflags, freetypeflags)

            
            f = open(setupfile, 'at')
            f.write(ignifuga_module)
            f.close()

        # Append the greenlet module
        shutil.copy(join(SOURCES['GREENLET'], 'greenlet.c'), join(python_build, 'Modules'))
        shutil.copy(join(SOURCES['GREENLET'], 'greenlet.h'), join(python_build, 'Modules'))
        shutil.copy(join(SOURCES['GREENLET'], 'slp_platformselect.h'), join(python_build, 'Modules'))
        shutil.copytree(join(SOURCES['GREENLET'], 'platform'), join(python_build, 'Modules', 'platform'))

        # Append the bitarray module
        shutil.copy(join(SOURCES['BITARRAY'], '_bitarray.c'), join(python_build, 'Modules'))


def make_python(platform, ignifuga_src, env=os.environ):
    # Modules required by Python itself
    freeze_modules = ['site','os','posixpath','stat','genericpath','warnings','linecache','types','UserDict','_abcoll','abc','_weakrefset','copy_reg','traceback','sysconfig','re','sre_compile','sre_parse','sre_constants','codecs', 'encodings','encodings.aliases','encodings.utf_8']
    # Modules required by Ignifuga in addition to the above
    freeze_modules += ['base64', 'struct', 'json', 'json.decoder', 'json.encoder', 'json.scanner', 'json.tool', 'encodings.hex_codec', 'platform', 'string', 'pickle', 'StringIO', 'copy', 'weakref']
    # For profiling
    freeze_modules += ['cProfile', 'runpy', 'pkgutil']

    mod = __import__('modules.python.'+platform, fromlist=['make'])
    mod.make(env, DIST_DIR, BUILDS, freeze_modules, join(BUILDS['PYTHON'], 'Python', 'frozen.c'))


def make_python_freeze(modules, frozen_file):
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

    f = open(frozen_file, 'w')
    f.write(frozen_h)
    f.close()

# ===============================================================================================================
# Ignifuga BUILDING
# ===============================================================================================================

def prepare_ignifuga(platform):
    # Copy all .py, .pyx and .pxd files
    cmd = 'rsync -aqPm --exclude .svn --exclude host --exclude tmp --exclude dist --exclude external --exclude tools --include "*/" --include "*.py" --include "*.pyx" --include "*.pxd" --include "*.h" --include "*.c" --exclude "*" %s/ %s' % (SOURCES['IGNIFUGA'], BUILDS['IGNIFUGA'])
    Popen(shlex.split(cmd), cwd = SOURCES['IGNIFUGA']).communicate()

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
    return cythonize(BUILDS['IGNIFUGA'], 'ignifuga')
    
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
                    p = Popen(shlex.split(cmd), cwd = build_dir)
                    p.communicate()
                    if p.returncode != 0:
                        error("Problem cythonizing file")
                        exit()
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
                cmd = SED_CMD + """'s|Py_InitModule4(__Pyx_NAMESTR("\(.*\)")|Py_InitModule4(__Pyx_NAMESTR("%s.\\1")|g' %s""" % (package,f)
            else:
                cmd = SED_CMD + """'s|Py_InitModule4(__Pyx_NAMESTR("\(.*\)")|Py_InitModule4(__Pyx_NAMESTR("%s")|g' %s""" % (package,f)
            Popen(shlex.split(cmd), cwd = cython_src).communicate()
            if module != '__init__':
                cmd = SED_CMD + """'s|init%s|init%s_%s|g' %s""" % (module,package.replace('.', '_'),module,f)
            else:
                cmd = SED_CMD + """'s|init%s|init%s|g' %s""" % (subpackage,package.replace('.', '_'),f)
            Popen(shlex.split(cmd), cwd = cython_src).communicate()
            cmd = SED_CMD + """'s|__pyx_import_star_type_names|__pyx_import_star_type_names_%s%s|g' %s""" % (package.replace('.', '_'),module, f)
            Popen(shlex.split(cmd), cwd = cython_src).communicate()

        if module != '__init__':
            glue_h += "extern void init%s_%s(void);\n" % (package.replace('.', '_'),module)
            glue_c += '    PyImport_AppendInittab("%s.%s", init%s_%s);\n' % (package, module, package.replace('.', '_'),module)
        else:
            glue_h += "extern void init%s(void);\n" % (package.replace('.', '_'))
            glue_c += '    PyImport_AppendInittab("%s", init%s);\n' % (package, package.replace('.', '_'))

    # Make package xxx_glue.c with no frozen modules
    glue = make_glue(package_name, glue_h, glue_c)
    f = open(join(cython_src, package_name+'_glue.c'), 'w')
    f.write(glue)
    f.close()
    cfiles.append(join(cython_src, package_name+'_glue.c'))

    for f in locate('*.c', build_dir, [cython_src, join(build_dir, 'android_project')]):
        if f not in cfiles:
            d = f[len(build_dir)+1:].replace(os.sep, '+')
            cfile = join(cython_src, d)
            cmd = 'cp -u %s %s' % (f, cfile)
            Popen(shlex.split(cmd), cwd = build_dir).communicate()
            cfiles.append(cfile)
    
    return cfiles, glue_h, glue_c
    
# ===============================================================================================================
# SDL BUILDING
# ===============================================================================================================
def prepare_sdl(platform):
    mod = __import__('modules.sdl.'+platform, fromlist=['prepare'])
    mod.prepare(DIST_DIR, SOURCES, BUILDS)

def make_sdl(platform, env=None):
    mod = __import__('modules.sdl.'+platform, fromlist=['make'])
    mod.make(env, DIST_DIR, BUILDS)


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
    if platform in ['linux64', 'mingw32', 'osx']:
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
        prepare_python(platform, ignifuga_src, BUILDS['PYTHON'])
        make_python(platform, ignifuga_src, env)

def build_project_generic(options, platform, env=None):
    package = options.project.split('.')[-1]
    if package == 'ignifuga':
        error('Name your project something else than ignifuga please')
        exit()

    if package +'.py' == basename(options.main).lower():
        error('Your main file can not have the same name as the project. If your project is com.mdqinc.test your main file can not be named test.py')
        exit()

    platform_build = join(BUILDS['PROJECT'], platform)
    main_file = join(platform_build, options.main)
    cython_src = join(BUILDS['PROJECT'], platform, 'cython_src')
    info('Building %s for %s  (package: %s)' % (options.project, platform, package))
    if not isdir(BUILDS['PROJECT']):
        os.makedirs(BUILDS['PROJECT'])

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

        # Insert SDL.h into the cythonized file
        with file(mfc, 'r') as original: mfc_data = original.read()
        with file(mfc, 'w') as modified: modified.write("#include \"SDL.h\"\n"+mfc_data)
        shutil.move(mfc, main_file_c)

    # Build the executable
    sources = ''
    for cf in cfiles:
        sources += cf + ' '

    mod = __import__('modules.project.'+platform, fromlist=['make'])
    mod.make(options, env, DIST_DIR, BUILDS, sources, cython_src, cfiles)

    info('Project built successfully')

        
# ===============================================================================================================
# LINUX 64
# ===============================================================================================================
def build_linux64 (options):
    platform = 'linux64'
    setup_variables(join(ROOT_DIR, 'dist', platform), join(ROOT_DIR, 'tmp', platform))

    if options.main and check_ignifuga_libraries(platform):
        return
    info('Building Ignifuga For Linux 64 bits')
    if not isdir(DIST_DIR):
        os.makedirs(DIST_DIR)
    env = prepare_linux64_env()
    build_generic(options, platform, env)

def build_project_linux64(options):
    platform = 'linux64'
    env = prepare_linux64_env()
    build_project_generic(options, platform, env)


# ===============================================================================================================
# OS X
# ===============================================================================================================
def build_osx (options):
    platform = 'osx'
    setup_variables(join(ROOT_DIR, 'dist', platform), join(ROOT_DIR, 'tmp', platform))

    if options.main and check_ignifuga_libraries(platform):
        return
    info('Building Ignifuga For OS X')
    if not isdir(DIST_DIR):
        os.makedirs(DIST_DIR)
    env = prepare_osx_env()
    build_generic(options, platform, env)

def build_project_osx(options):
    platform = 'osx'
    env = prepare_osx_env()
    build_project_generic(options, platform, env)


# ===============================================================================================================
# ANDROID
# ===============================================================================================================
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

    if options.platform not in AVAILABLE_PLATFORMS and options.platform != 'all':
        error('Invalid target platform. Valid platforms: %s' % AVAILABLE_PLATFORMS)
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

    # Check the availability of host tools, build host Python if required.
    setup_variables(join (ROOT_DIR, 'dist'), join (ROOT_DIR, 'tmp'))
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
    BUILDS['PROJECT'] = join(PROJECT_ROOT, 'build')
    for platform in platforms:
        locals()["build_project_"+platform](options)