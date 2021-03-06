#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Misc utility functions
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import os, shlex, shutil, re, platform, fnmatch, sys
from os.path import *
from subprocess import Popen, PIPE
from log import info, log, error
import multiprocessing, tempfile


def find_cython():
    cmd = 'which cython'
    output = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0]
    cython = output.split('\n')[0]
    if isfile(cython):
        # Get the version
        cmd = '%s -V' % cython
        output = Popen(shlex.split(cmd), stderr=PIPE, stdout=PIPE).communicate()
        version = output[0].split('\n')[0] if output[0] != '' else output[1].split('\n')[0]
        v = re.search("(\d+)\.(\d+)(.*)", version)
        # We are looking for 0.17 or higher
        cython_ver = []
        counter = 0
        while True:
            try:
                cython_ver.append(int(v.group(counter+1)))
                counter += 1
            except:
                break
        try:
            if cython_ver[0] > 0:
                return cython
            if cython_ver[0] == 0:
                if cython_ver[1] >= 17:
                    return cython
    #            if v.group(1) == 16:
    #                if v.groups(2).startswith('1+') or v.groups(2) >= 2:
    #                    return cython
        except:
            pass
        error ('Cython version %s is incompatible' % version)
    return None

def check_tool(tool, fatal=True):
    cmd = 'which ' + tool
    output = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0]
    tool_path = output.split('\n')[0]
    if not isfile(tool_path):
        if fatal:
            error("Can not find %s, try running schafer -D to install dependencies automatically" % tool)
            exit()
        else:
            return None

    return tool_path

def check_gnutools():
    tools = ['make', 'gcc', 'strip']
    for tool in tools:
        check_tool(tool)
    return True

def check_intel_mingw32_tools():
    tools = ['i686-w64-mingw32-gcc', 'i686-w64-mingw32-g++', 'i686-w64-mingw32-ar', 'i686-w64-mingw32-ranlib', 'i686-w64-mingw32-strip', 'i686-w64-mingw32-ld', 'i686-w64-mingw32-as',
             'i686-w64-mingw32-nm', 'i686-w64-mingw32-dlltool', 'i686-w64-mingw32-objdump', 'i686-w64-mingw32-windres']

    for tool in tools:
        check_tool(tool)

    return True

def check_intel_mingw64_tools():
    tools = ['x86_64-w64-mingw32-gcc', 'x86_64-w64-mingw32-g++', 'x86_64-w64-mingw32-ar', 'x86_64-w64-mingw32-ranlib', 'x86_64-w64-mingw32-strip', 'x86_64-w64-mingw32-ld', 'x86_64-w64-mingw32-as',
             'x86_64-w64-mingw32-nm', 'x86_64-w64-mingw32-dlltool', 'x86_64-w64-mingw32-objdump', 'x86_64-w64-mingw32-windres']

    for tool in tools:
        check_tool(tool)

    return True

def check_xcode():
    if check_tool('xcodebuild', False) == None:
        error('Can not detect XCode, please install it')
        exit()

    # Check that we have at least one SDK for Desktop, iOS and iOS simulator
    sdk = find_apple_sdk('macosx', 10, 6)
    if sdk is None:
        error("Could not find a valid OS X SDK")
        exit()

    sdk = find_apple_sdk('iphoneos', 5)
    if sdk is None:
        error("Could not find a valid iOS SDK")
        exit()

    sdk = find_apple_sdk('iphonesimulator', 5)
    if sdk is None:
        error("Could not find a valid iOS simulator SDK")
        exit()

    return True

def find_xcode():
    # Figure out where the XCode developer root is
    if check_tool('xcode-select', False) == None:
        error('Can not detect XCode, please install it')
        exit()

    cmd = 'xcode-select --print-path'
    output = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split("\n")
    if isdir(output[0]):
        return output[0]
    else:
        error("Can not find XCode's location")
        exit()

def find_apple_sdk(type='iphoneos', major=5, minor=None):
    type = type.lower()
    if type not in [ 'macosx', 'iphoneos', 'iphonesimulator']:
        error("Invalid Apple SDK type %s" % type)
        exit()

    if check_tool('xcodebuild', False) == None:
        error('Can not detect XCode, please install it')
        exit()

    # Check SDKs
    cmd = 'xcodebuild -showsdks'
    output = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split("\n")
    for line in output:
        if type in line:
            v = re.search(type+"(\d+)\.(.*)", line)
            if v is not None:
                if v.group(1) >= major:
                    if minor is None:
                        return v.group(1)+'.'+v.group(2)
                    elif v.group(2) >= minor:
                        return v.group(1)+'.'+v.group(2)

    return None

def validate_android_api_level(level, ANDROID_SDK):
    try:
        api_level = int(level)
    except:
        error("Invalid Android API Level, please provide an integer >= 10")
        exit()

    if api_level < 10:
        error("Invalid Android Target API Level Selected (it has to be >=10)")
        exit()

    tool = check_tool('android', False)
    if tool is None:
        tool = join(ANDROID_SDK, 'tools', 'android')
        if not isfile(tool):
            error("Could not find the 'android' tool from the Android SDK. Try executing schafer -D to install the SDK")
            exit()
    # Check that the api level exists
    cmd = '%s list targets' % tool
    output = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split("\n")
    api_level_valid = False
    available_targets = []
    for line in output:
        if 'android-%d' % api_level in line:
            api_level_valid = True
            break
        if 'android-' in line:
            available_targets.append(line.split(' ')[-1])

    if not api_level_valid:
        if available_targets:
            error("You don't have the API Level SDK files for the android-%d target (Currently available levels: %s). Please run the %s tool and install it from there" % (api_level, ' '.join(available_targets), tool))
        else:
            error("You don't have any API Level SDK files. Please run the %s tool and install it from there" % (tool,))
        exit()

def check_host_tools():
    """ Check if the required host tools are present """
    from schafer import HOSTPYTHON, HOSTPGEN, ROOT_DIR, HOST_DIST_DIR, prepare_python
    processor, system, arch, distro_name, distro_version, distro_id = get_build_platform()
    supported_platform = False
    if system == 'Linux':
        if processor == 'x86_64':
            if distro_name == 'Ubuntu':
                if distro_id in ['precise', 'quantal']:
                    supported_platform = True
    elif system == 'Darwin':
        if arch == '64bit':
            if distro_name.startswith('10.7') or distro_name.startswith('10.8'):
                supported_platform = True

    if not supported_platform:
        error('Warning: Unsupported host platform/architecture %s %s %s. Proceed with caution. No really, this thing may blow up any minute now' % (system, arch, distro_name))

    if find_cython() == None:
        error("Can not find Cython, run with -D to install dependencies automatically")
        exit()

    if check_tool('rsync', False) == None:
        error("Can not find Rsync, run with -D to install dependencies automatically")
        exit()

    if not check_gnutools():
        error("Can not find compilation tools (Make, GCC), run with -D to install dependencies automatically")
        exit()

    if system == 'Darwin':
        check_xcode()
        nasm = check_version('nasm', (2,7))
        if nasm is None:
            error('We need a NASM version of at least 2.7, try running schafer -D or install a newer version manually, for example using Mac Ports')
            exit()
        autoconf = check_version('autoconf', (2,69))
        if autoconf is None:
            error('We need a autoconf version of at least 2.69, try running schafer -D or install a newer version manually, for example using Mac Ports')
            exit()
        pkgconfig = check_version('pkg-config', (0,27))
        if pkgconfig is None:
            error('We need a pkgconfig version of at least 2.69, try running schafer -D or install a newer version manually, for example using Mac Ports')
            exit()
        automake = check_version('automake', (1,12))
        if automake is None:
            error('We need a automake version of at least 2.69, try running schafer -D or install a newer version manually, for example using Mac Ports')
            exit()
        # Try the Mac Ports path first
        port = check_tool('port')
        port_path = dirname(port)
        libtool = check_version(join(port_path, '..', 'libexec/gnubin/libtool'), (2,4))
        if libtool is None:
            # Check the system path
            libtool = check_version('libtool', (2,4))
        if libtool is None:
            error('We need a Libtool version of at least 2.4, try running bootstrap.py, or install a newer version manually, for example using Mac Ports')
            exit()



    if not isfile(HOSTPYTHON) or not isfile(HOSTPGEN):
        # First let's make the host version of Python, statically linked
        info('Building Python for the host')
        python_build = join(ROOT_DIR, 'tmp', 'python_host')

        # Fake a few command line options
        class _options(object):
            bare = True
            baresrc = None
        options = _options()

        if system == 'Linux':
            if arch == '64bit':
                prepare_python('intel_linux64', None, python_build, options, os.environ)
                cmd = './configure --enable-silent-rules LDFLAGS="-Wl,--no-export-dynamic -static -static-libgcc -lz" LDLAST="-static-libgcc -lz" CPPFLAGS="-static -fPIC" LINKFORSHARED=" " DYNLOADFILE="dynload_stub.o" --disable-shared --prefix="%s"'% (HOST_DIST_DIR,)
                Popen(shlex.split(cmd), cwd = python_build, env=os.environ).communicate()
            else:
                prepare_python('intel_linux32', None, python_build, options, os.environ)
                cmd = './configure --enable-silent-rules LDFLAGS="-Wl,--no-export-dynamic -static -static-libgcc -lz" LDLAST="-static-libgcc -lz" CPPFLAGS="-static -fPIC" LINKFORSHARED=" " DYNLOADFILE="dynload_stub.o" --disable-shared --prefix="%s"'% (HOST_DIST_DIR,)
                Popen(shlex.split(cmd), cwd = python_build, env=os.environ).communicate()
        elif system == 'Darwin':
            prepare_python('osx', None, python_build, options, os.environ)
            cmd = './configure --enable-silent-rules --with-universal-archs=intel --enable-universalsdk LDFLAGS="-static-libgcc -lz" LDLAST="-static-libgcc -lz" LINKFORSHARED=" " DYNLOADFILE="dynload_stub.o" --disable-shared --prefix="%s"'% (HOST_DIST_DIR,)
            Popen(shlex.split(cmd), cwd = python_build, env=os.environ).communicate()
        cmd = 'make V=0 install -k -j%d' % multiprocessing.cpu_count()
        Popen(shlex.split(cmd), cwd = python_build, env=os.environ).communicate()
        # Check that it built successfully
        if not isfile(join(python_build, 'python')) or not isfile(join(python_build, 'Parser', 'pgen')):
            error('Could not build Python for host system')
            exit()
        shutil.copy(join(python_build, 'Parser', 'pgen'), HOSTPGEN)

def locate(pattern, root=os.curdir, skip = []):
    '''Locate all files matching supplied filename pattern in and below
    supplied root directory.'''
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files, pattern):
            yieldit = True
            for s in skip:
                if path.startswith(s):
                    yieldit = False
                    break
            if yieldit:
                yield os.path.join(path, filename)

def get_sdl_flags(target):
    cmd = join(target.dist, 'bin', 'sdl2-config' ) + ' --cflags'
    flags = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
    cmd = join(target.dist, 'bin', 'sdl2-config' ) + ' --static-libs'
    flags = flags + ' ' + Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
    return flags

def get_freetype_flags(target):
    cmd = join(target.dist, 'bin', 'freetype-config' ) + ' --cflags'
    flags = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
    cmd = join(target.dist, 'bin', 'freetype-config' ) + ' --libs'
    flags = flags + ' ' + Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
    return flags

def get_png_flags(target):
    cmd = join(target.dist, 'bin', 'libpng-config' ) + ' --static --cflags'
    flags = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
    cmd = join(target.dist, 'bin', 'libpng-config' ) + ' --static --ldflags'
    flags = flags + ' ' + Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split('\n')[0]
    return flags

def get_build_platform():
    # Check the host distro
    arch, exe = platform.architecture()
    system = platform.system()
    if system == 'Linux':
        distro_name, distro_version, distro_id = platform.linux_distribution()
    elif system == 'Darwin':
        distro_name, distro_version, distro_id = platform.mac_ver()
    return platform.processor(), system, arch, distro_name, distro_version, distro_id

def get_available_platforms():
    """ Determine which build platforms are available depending on which platform we are building """
    processor, system, arch, distro_name, distro_version, distro_id = get_build_platform()
    AVAILABLE_PLATFORMS = []
    if system == 'Linux':
        SED_CMD = 'sed -i '
        if processor == 'x86_64':
            AVAILABLE_PLATFORMS = ['intel_linux64', 'intel_linux32', 'intel_mingw32', 'intel_mingw64',  'arm_android', 'intel_android']
        elif processor in ['i386', 'i486', 'i586', 'i686']:
            AVAILABLE_PLATFORMS = ['intel_linux32', 'intel_mingw32', 'arm_android', 'intel_android']
    elif system == 'Darwin':
        SED_CMD = 'sed -i "" '
        AVAILABLE_PLATFORMS = ['osx', 'ios', 'arm_android', 'intel_android' ]

    return AVAILABLE_PLATFORMS, SED_CMD

def get_platform_aliases():
    """ Prepare a few platform dependent target system aliases """
    processor, system, arch, distro_name, distro_version, distro_id = get_build_platform()
    ALIASES = {}
    ALIASES['android'] = 'arm_android'
    ALIASES['mingw32'] = 'intel_mingw32'
    ALIASES['win32'] = 'intel_mingw32'
    ALIASES['mingw64'] = 'intel_mingw64'
    ALIASES['win64'] = 'intel_mingw64'

    if system == 'Linux':
        if processor == 'x86_64':
            ALIASES['linux'] = 'intel_linux64'
            ALIASES['linux64'] = 'intel_linux64'
            ALIASES['linux32'] = 'intel_linux32'
        elif processor in ['i386', 'i486', 'i586', 'i686']:
            ALIASES['linux'] = 'intel_linux32'
            ALIASES['linux32'] = 'intel_linux32'
    elif system == 'Darwin':
        pass

    return ALIASES

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

def validate_ogg_decoder(platform, oggdecoder=None):
    """ Validate the desired ogg decoder
    Valid oggdecoder values are None, vorbis, tremor, tremorlm
    """
    oggdecoder = oggdecoder.upper() if oggdecoder is not None else None
    if platform in ['intel_linux64', 'intel_linux32']:
        # Tremor does not seem to work on Linux
        return 'VORBIS'
    elif platform in ['intel_mingw32', 'intel_mingw64', 'osx']:
        if oggdecoder in ['VORBIS', 'TREMOR', 'TREMORLM']:
            return oggdecoder
        return 'VORBIS'

    if platform in ['arm_android', 'intel_android', 'ios']:
        if oggdecoder in ['TREMOR', 'TREMORLM']:
            return oggdecoder
        return 'TREMORLM'

def check_version(executable, min=(0,0)):
    # Check the file version available
    if not isfile(executable):
        cmd = 'which ' + executable
        output = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0]
        executable = output.split('\n')[0]
    if isfile(executable):
        # Get the version
        cmd = '%s --version' % executable
        output = Popen(shlex.split(cmd), stderr=PIPE, stdout=PIPE).communicate()
        version = output[0].split('\n')[0] if output[0] != '' else output[1].split('\n')[0]
        v = re.search("(\d+)\.(\d+)(.*)", version)
        if v is None:
            cmd = '%s -v' % executable
            output = Popen(shlex.split(cmd), stderr=PIPE, stdout=PIPE).communicate()
            version = output[0].split('\n')[0] if output[0] != '' else output[1].split('\n')[0]
            v = re.search("(\d+)\.(\d+)(.*)", version)

        installed_ver = []
        counter = 0
        while True:
            try:
                installed_ver.append(int(v.group(counter+1)))
                counter += 1
            except:
                break
        try:
            if installed_ver[0] > min[0]:
                return executable
            if installed_ver[0] == min[0]:
                if installed_ver[1] >= min[1]:
                    return executable
        except:
            pass
    return None
