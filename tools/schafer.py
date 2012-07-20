#!/usr/bin/env python
#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer: The Ignifuga Builder utility
# Author: Gabriel Jacobo <gabriel@mdqinc.com>
# Requires: RSync, Cython, GNU Tools, MINGW32, Android SDK, etc

import os, sys, shutil, shlex, imp, marshal
from subprocess import Popen, PIPE
from os.path import *
from optparse import OptionParser

########################################################################################################################
# Host system variables, *fixed* values and locations constant during all the execution
########################################################################################################################
ROOT_DIR = abspath(join(dirname(sys.argv[0]), '..'))

from modules.log import log, error, info
from modules.env import *
from modules.util import *

AVAILABLE_PLATFORMS, SED_CMD = get_available_platforms()

ANDROID_NDK =  os.environ['ANDROID_NDK'] if 'ANDROID_NDK' in os.environ else '/opt/android-ndk'
ANDROID_SDK =  os.environ['ANDROID_SDK'] if 'ANDROID_SDK' in os.environ else '/opt/android-sdk'

HOST_DIST_DIR = join(ROOT_DIR, 'host')
HOSTPYTHON = join(HOST_DIST_DIR, 'bin', 'python')
HOSTPGEN = join(HOST_DIST_DIR, 'bin', 'pgen')
PATCHES_DIR = join(ROOT_DIR, 'tools', 'patches')

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

########################################################################################################################


def clean_modules(platforms, modules, everything=False):
    log('Cleaning Build Directories')
    if isinstance(platforms, str):
        platforms = [platforms,]

    for platform in platforms:
        target = get_target(platform)
        if not everything:
            if isdir(target.tmp):
                if 'ignifuga' in modules:
                    if isdir(target.builds.IGNIFUGA):
                        shutil.rmtree(target.builds.IGNIFUGA)
                    if isdir(target.builds.PYTHON):
                        shutil.rmtree(target.builds.PYTHON)
                if 'sdl' in modules and isdir(target.builds.SDL):
                    shutil.rmtree(target.builds.SDL)
        else:
            if isdir(target.tmp):
                shutil.rmtree(target.tmp)
            if isdir(target.dist):
                shutil.rmtree(target.dist)

def check_ignifuga_libraries(platform):
    target = get_target(platform)
    if platform in ['linux64', 'mingw32', 'osx', 'ios']:
        if isfile(join(target.dist, 'lib', 'libpython2.7.a')) and \
           isfile(join(target.dist, 'lib', 'libSDL2.a')) and \
           isfile(join(target.dist, 'lib', 'libSDL2_image.a')) and \
           isfile(join(target.dist, 'lib', 'libSDL2_ttf.a')):
            return True
    elif platform == 'android':
        if isfile(join(target.dist, 'jni', 'python', 'libpython2.7.so')) and \
        isfile(join(target.dist, 'jni', 'SDL', 'libSDL2.so')) and \
        isfile(join(target.dist, 'jni', 'SDL_image', 'libSDL2_image.so')) and \
        isfile(join(target.dist, 'jni', 'SDL_ttf', 'libSDL2_ttf.so')):
            return True
    return False

# ===============================================================================================================
# PYTHON BUILDING - Requires Ignifuga building!
# ===============================================================================================================

def prepare_python(platform, ignifuga_src, python_build, env):
    target = get_target(platform)
    if not isdir(target.tmp):
        os.makedirs(target.tmp)

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
            mod = __import__('modules.python.'+platform, fromlist=['prepare'])
            ignifuga_module = mod.prepare(env, target, ignifuga_src, python_build)

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
    freeze_modules = ['site','os','posixpath','stat','genericpath','warnings','linecache','types','UserDict','_abcoll','abc','_weakrefset','copy_reg','traceback','sysconfig','re','sre_compile','sre_parse','sre_constants','codecs', 'encodings','encodings.aliases','encodings.utf_8', 'encodings.ascii']
    # Modules required by Ignifuga in addition to the above
    freeze_modules += ['base64', 'struct', 'json', 'json.decoder', 'json.encoder', 'json.scanner', 'json.tool', 'encodings.hex_codec', 'platform', 'string', 'pickle', 'StringIO', 'copy', 'weakref', 'optparse', 'textwrap']
    # For profiling
    freeze_modules += ['cProfile', 'runpy', 'pkgutil', 'pstats', 'functools']

    target = get_target(platform)
    mod = __import__('modules.python.'+platform, fromlist=['make'])
    mod.make(env, target, freeze_modules, join(target.builds.PYTHON, 'Python', 'frozen.c'))


def make_python_freeze(platform, modules, frozen_file):
    """Get a list of python native modules, return them frozen"""
    target = get_target(platform)
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
    modtemp = join(target.tmp, 'freezer')
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
                # Add Android platform detection
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
    target = get_target(platform)
    cmd = 'rsync -aqPm --exclude .svn --exclude host --exclude tmp --exclude dist --exclude external --exclude tools --exclude tests --include "*/" --include "*.py" --include "*.pyx" --include "*.pxd" --include "*.h" --include "*.c" --include "*.cpp" --exclude "*" %s/ %s' % (SOURCES['IGNIFUGA'], target.builds.IGNIFUGA)
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

def make_ignifuga(build_dir):
    return cythonize(build_dir, 'ignifuga')
    
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
            cf = splitext(f)[0] + '.cpp'
            if not isfile(cf) or getctime(cf) < mf:
                ccf = join(build_dir, 'cython_src', cf.replace(os.sep, '+')[len(build_dir)+1:])
                if not isfile(ccf) or getctime(ccf) < mf:
                    log('Cythonizing %s' % basename(f))
                    cmd = 'cython --cplus --include-dir "%s/.." "%s"' % (ROOT_DIR, f)
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
        package = filename.replace('+', '.').replace('.cpp', '')
        
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

    for f in locate('*.cpp', build_dir, [cython_src, join(build_dir, 'android_project')]):
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
def prepare_sdl(platform, env=None):
    target = get_target(platform)
    mod = __import__('modules.sdl.'+platform, fromlist=['prepare'])
    mod.prepare(env, target)

def make_sdl(platform, env=None):
    target = get_target(platform)
    mod = __import__('modules.sdl.'+platform, fromlist=['make'])
    mod.make(env, target)

# ===============================================================================================================
# PLATFORM BUILDS
# ===============================================================================================================
def spawn_shell(platform):
    target = get_target(platform)
    cmd = 'bash'
    env = os.environ
    if platform == 'android':
        env = prepare_android_env()
    elif platform == 'mingw32':
        env = prepare_mingw32_env()

    info('Entering %s shell environment' % (platform,))

    Popen(shlex.split(cmd), cwd = target.dist, env=env).communicate()
    info('Exited from %s shell environment' % (platform,))
    
def build_generic(options, platform, env=None):
    target = get_target(platform)

    if platform in ['linux64', 'mingw32', 'osx']:
        # Android/iOS has its own skeleton set up
        cmd = 'mkdir -p "%s"' % target.dist
        Popen(shlex.split(cmd), env=env).communicate()
        cmd = 'mkdir -p "%s"' % join(target.dist,'include')
        Popen(shlex.split(cmd), env=env).communicate()
        cmd = 'mkdir -p "%s"' % join(target.dist,'bin')
        Popen(shlex.split(cmd), env=env).communicate()
        cmd = 'mkdir -p "%s"' % join(target.dist,'lib')
        Popen(shlex.split(cmd), env=env).communicate()

    if not isdir(target.tmp):
        os.makedirs(target.tmp)
            
    # Compile SDL statically
    if 'sdl' in options.modules:
        info('Building SDL')
        prepare_sdl(platform, env)
        make_sdl(platform, env)

    # Compile Ignifuga then Python statically
    if 'ignifuga' in options.modules:
        info('Building Ignifuga')
        prepare_ignifuga(platform)
        ignifuga_src, glue_h, glue_c = make_ignifuga(target.builds.IGNIFUGA)
        info('Building Python')
        prepare_python(platform, ignifuga_src, target.builds.PYTHON, env)
        make_python(platform, ignifuga_src, env)

# ===============================================================================================================
# USER PROJECT BUILDS
# ===============================================================================================================
def prepare_project(src, dst):
    # Copy all .py, .pyx and .pxd files
    cmd = 'rsync -aqPm --exclude .svn --exclude .hg --exclude build --include "*/" --include "*.py" --include "*.pyx" --include "*.pxd" --exclude "*" %s/ %s' % (src, dst)
    Popen(shlex.split(cmd), cwd = src).communicate()

def build_project_generic(options, platform, target, env=None):
    package = options.project.split('.')[-1]
    if package == 'ignifuga':
        error('Name your project something else than ignifuga please')
        exit()

    if package +'.py' == basename(options.main).lower():
        error('Your main file can not have the same name as the project. If your project is com.mdqinc.test your main file can not be named test.py')
        exit()

    platform_build = join(target.project, platform)
    main_file = join(platform_build, options.main)
    cython_src = join(target.project, platform, 'cython_src')
    info('Building %s for %s  (package: %s)' % (options.project, platform, package))
    if not isdir(target.project):
        os.makedirs(target.project)

    # Prepare and cythonize project sources
    prepare_project(target.project_root, platform_build)
    cfiles, glue_h, glue_c = cythonize(platform_build, package, [options.main,])

    # Cythonize main file
    main_file_ct = getctime(main_file)
    main_file_c = join(cython_src, splitext(options.main)[0] + '.cpp')
    cfiles.append(main_file_c)

    if not isfile(main_file_c) or getctime(main_file_c) < main_file_ct:
        log('Cythonizing main file %s' % main_file)
        cmd = 'cython --embed --cplus --include-dir "%s/.." "%s"' % (ROOT_DIR, main_file)
        #cmd = 'cython --embed --cplus %s' % ( main_file)
        mfc = join(platform_build, splitext(main_file)[0] + '.cpp')
        Popen(shlex.split(cmd), cwd = platform_build).communicate()
        if not isfile(mfc):
            error ('Could not cythonize main file')
            exit()

        # Insert SDL.h into the cythonized file
        with file(mfc, 'r') as original: mfc_data = original.read()
        mfc_data = mfc_data.replace('PyErr_Print();', 'PyErr_Print();fflush(stdout);fflush(stderr);')
        with file(mfc, 'w') as modified: modified.write("#include \"SDL.h\"\n"+mfc_data)
        shutil.move(mfc, main_file_c)

    # Build the executable
    sources = ''
    for cf in cfiles:
        sources += cf + ' '

    mod = __import__('modules.project.'+platform, fromlist=['make'])
    mod.make(options, env, target, sources, cython_src, cfiles)

    info('Project built successfully')

        
# ===============================================================================================================
# LINUX 64
# ===============================================================================================================
def build_linux64 (options):
    platform = 'linux64'
    target = get_target(platform)

    if options.main and check_ignifuga_libraries(platform):
        return
    info('Building Ignifuga For Linux 64 bits')
    if not isdir(target.dist):
        os.makedirs(target.dist)
    env = prepare_linux64_env(options.openmp)
    build_generic(options, platform, env)

def build_project_linux64(options, project_root):
    platform = 'linux64'
    env = prepare_linux64_env(options.openmp)
    target = get_target(platform, project_root)
    build_project_generic(options, platform, target, env)


# ===============================================================================================================
# OS X
# ===============================================================================================================
def build_osx (options):
    platform = 'osx'
    target = get_target(platform)

    if options.main and check_ignifuga_libraries(platform):
        return
    info('Building Ignifuga For OS X')
    if not isdir(target.dist):
        os.makedirs(target.dist)
    env = prepare_osx_env(options.openmp)
    build_generic(options, platform, env)

def build_project_osx(options, project_root):
    platform = 'osx'
    env = prepare_osx_env(options.openmp)
    target = get_target(platform, project_root)
    build_project_generic(options, platform, target, env)

# ===============================================================================================================
# iOS
# ===============================================================================================================
def prepare_ios_skeleton():
    """ Copy a skeleton of the final project to the dist directory """
    target = get_target ('ios')
    if not isdir(target.dist):
        shutil.copytree(join(ROOT_DIR, 'tools', 'ios_skeleton'), target.dist)
        cmd = 'find %s -name ".svn" -type d -exec rm -rf {} \;' % (target.dist,)
        Popen(shlex.split(cmd), cwd = target.dist).communicate()

def build_ios (options):
    platform = 'ios'
    target = get_target(platform)

    if options.main and check_ignifuga_libraries(platform):
        return
    info('Building Ignifuga For iOS')
    env = prepare_ios_env(options.openmp, options.iossdk, options.iostarget)
    prepare_ios_skeleton()
    build_generic(options, platform, env)

def build_project_ios(options, project_root):
    platform = 'ios'
    env = prepare_ios_env(options.openmp, options.iossdk, options.iostarget)
    target = get_target(platform, project_root)
    build_project_generic(options, platform, target, env)


# ===============================================================================================================
# ANDROID
# ===============================================================================================================
def prepare_android_skeleton():
    """ Copy a skeleton of the final project to the dist directory """
    target = get_target ('android')
    if not isdir(target.dist):
        shutil.copytree(join(ROOT_DIR, 'tools', 'android_skeleton'), target.dist)
        cmd = 'find %s -name ".svn" -type d -exec rm -rf {} \;' % (target.dist,)
        Popen(shlex.split(cmd), cwd = target.dist).communicate()
    
def build_android (options):
    platform = 'android'
    target = get_target(platform)
    if options.main != None and check_ignifuga_libraries(platform):
        return
    info('Building Ignifuga For Android')
    env = prepare_android_env(options.openmp)
    prepare_android_skeleton()
    build_generic(options, platform, env)

def build_project_android(options, project_root):
    platform = 'android'
    env = prepare_android_env(options.openmp)
    target = get_target(platform, project_root)
    build_project_generic(options, platform, target, env)

# ===============================================================================================================
# Windows - Mingw32
# ===============================================================================================================
def build_mingw32 (options):
    platform = 'mingw32'
    target = get_target(platform)
    check_mingw32tools()
    if options.main and check_ignifuga_libraries(platform):
        return
    info('Building Ignifuga For Windows 32 bits')
    if not isdir(target.dist):
        os.makedirs(target.dist)
    env = prepare_mingw32_env(options.openmp)
    build_generic(options, platform, env)

def build_project_mingw32(options, project_root):
    platform = 'mingw32'
    env = prepare_mingw32_env(options.openmp)
    target = get_target(platform, project_root)
    build_project_generic(options, platform, target, env)

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
    parser.add_option("--android-keystore",
        default=None, dest="androidkeystore",
        help="Android keystore location, if provided the package will be signed ")
    parser.add_option("--android-keyalias",
        default="", dest="androidkeyalias",
        help="Android key alias used to sign the package ")
    parser.add_option("--ios-sdk",
        default=None, dest="iossdk",
        help="Version of the iOS SDK to use for compiling, if none provided an automagic search will be performed for the latest SDK available")
    parser.add_option("--ios-target",
        default="3.0", dest="iostarget",
        help="Minimum iOS version that will be required to run the project")
    parser.add_option("--ios-codesign",
        default=None, dest="ioscodesign",
        help="Code Sign Authority For Signing Apps for iOS (required only for project building) ")
    parser.add_option("--openmp",
        action="store_true", dest="openmp", default=False,
        help="Use OPENMP if available for the target")

    (options, args) = parser.parse_args()


    if options.dependencies:
        install_host_tools(ROOT_DIR, ANDROID_NDK, ANDROID_SDK)
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

    for platform in platforms:
        locals()["build_project_"+platform](options, abspath(dirname(options.main)))