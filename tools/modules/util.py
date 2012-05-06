#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Misc utility functions
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import os, shlex, shutil, re, platform, fnmatch
from os.path import *
from subprocess import Popen, PIPE
from log import info, log, error

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

def check_mingw32tools():
    tools = ['i586-mingw32msvc-gcc', 'i586-mingw32msvc-g++', 'i586-mingw32msvc-ar', 'i586-mingw32msvc-ranlib', 'i586-mingw32msvc-strip', 'i586-mingw32msvc-ld', 'i586-mingw32msvc-as',
             'i586-mingw32msvc-nm', 'i586-mingw32msvc-dlltool', 'i586-mingw32msvc-objdump', 'i586-mingw32msvc-windres']

    for tool in tools:
        check_tool(tool)

    return True

def check_xcode():
    if check_tool('xcodebuild', False) == None:
        error('Can not detect XCode, please install it')
        exit()

    # Check SDKs
    cmd = 'xcodebuild -showsdks'
    output = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0].split("\n")
    sdks = ['macosx10.6', 'macosx10.7', 'iphoneos5.0', 'iphonesimulator5.0', None]

    for line in output:

        for sdk in sdks:
            if sdk != None and sdk in line:
                break
        if sdk != None:
            sdks.remove(sdk)

    sdks.remove(None)
    if sdks:
        for sdk in sdks:
            error('Could not find XCode SDK: %s' % sdk)
        exit()

    return True

def check_host_tools():
    """ Check if the required host tools are present """
    from schafer import HOSTPYTHON, HOSTPGEN, ROOT_DIR, HOST_DIST_DIR, prepare_python
    system, arch, distro_name, distro_version, distro_id = get_build_platform()
    supported_platform = False
    if system == 'Linux':
        if arch == '64bit':
            if distro_name == 'Ubuntu':
                if distro_id in ['natty', 'oneiric']:
                    supported_platform = True
    elif system == 'Darwin':
        if arch == '64bit':
            if distro_name == '10.7':
                supported_platform = True

    if not supported_platform:
        error('Warning: Unsupported host platform/architecture. Proceed with caution. No really, this thing may blow up any minute now')

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


    if not isfile(HOSTPYTHON) or not isfile(HOSTPGEN):
        # First let's make the host version of Python, statically linked
        info('Building Python for the host')
        python_build = join(ROOT_DIR, 'tmp', 'python_host')
        if system == 'Linux' and arch == '64bit':
            prepare_python('linux64', None, python_build, os.environ)
            cmd = './configure --enable-silent-rules LDFLAGS="-Wl,--no-export-dynamic -static -static-libgcc -lz" LDLAST="-static-libgcc -lz" CPPFLAGS="-static -fPIC" LINKFORSHARED=" " DYNLOADFILE="dynload_stub.o" --disable-shared --prefix="%s"'% (HOST_DIST_DIR,)
            Popen(shlex.split(cmd), cwd = python_build, env=os.environ).communicate()
        elif system == 'Darwin' and arch == '64bit':
            prepare_python('osx', None, python_build, os.environ)
            cmd = './configure --enable-silent-rules --with-universal-archs=intel --enable-universalsdk LDFLAGS="-static-libgcc -lz" LDLAST="-static-libgcc -lz" LINKFORSHARED=" " DYNLOADFILE="dynload_stub.o" --disable-shared --prefix="%s"'% (HOST_DIST_DIR,)
            Popen(shlex.split(cmd), cwd = python_build, env=os.environ).communicate()
        cmd = 'make V=0 install -k -j4'
        Popen(shlex.split(cmd), cwd = python_build, env=os.environ).communicate()
        # Check that it built successfully
        if not isfile(join(python_build, 'python')) or not isfile(join(python_build, 'Parser', 'pgen')):
            error('Could not build Python for host system')
            exit()
        shutil.copy(join(python_build, 'Parser', 'pgen'), HOSTPGEN)

def install_mac_ports():
    if check_tool('port', False) == None:
        # Install Mac Ports
        log('Installing Mac Ports (macports.org)')
        portsdmg = join(tempfile.gettempdir(), 'MacPorts.dmg')
        cmd = 'curl -o %s https://distfiles.macports.org/MacPorts/MacPorts-2.0.3-10.7-Lion.dmg' % portsdmg
        Popen(shlex.split(cmd)).communicate()

        if isfile(portsdmg):
            cmd = 'hdiutil attach %s' % portsdmg
            Popen(shlex.split(cmd)).communicate()
            if exists('/Volumes/MacPorts-2.0.3/MacPorts-2.0.3.pkg'):
                cmd = 'sudo installer -pkg /Volumes/MacPorts-2.0.3/MacPorts-2.0.3.pkg -target "/"'
                Popen(shlex.split(cmd)).communicate()
                cmd = 'hdiutil detach /Volumes/MacPorts-2.0.3'
                Popen(shlex.split(cmd)).communicate()
                if check_tool('port', False) == None:
                    error('Could not install Mac Ports, please install manually and try again')
                    exit()
            else:
                cmd = 'hdiutil detach /Volumes/MacPorts-2.0.3'
                Popen(shlex.split(cmd)).communicate()
                error('Could not mount Mac Ports dmg')
                exit()
        else:
            error('Could not download Mac Ports dmg. Please install manually and try again')
            exit()
    else:
        log('Mac Ports is available')

def install_host_tools():
    """ Install all the required host tools.
    Platforms supported:
    * Ubuntu 64 Natty 11.04
    * Ubuntu 64 Oneiric 11.10
    * OS X Lion 64
    """
    system, arch, distro_name, distro_version, distro_id = get_build_platform()

    log ('Installing development packages')
    if system == 'Linux':
        cmd = 'sudo apt-get -y install rsync python-dev mingw32 mingw32-binutils mingw32-runtime make gcc-4.5 automake autoconf openjdk-6-jdk ia32-libs gcc-multilib'
        Popen(shlex.split(cmd)).communicate()
    elif system == 'Darwin':
        check_xcode()
        install_mac_ports()
        cmd = 'sudo port install rsync'
        Popen(shlex.split(cmd)).communicate()

    cython = find_cython()
    if cython == None:
        git = check_tool('git', False)
        if git == None:
            # Try to install GIT
            log('Trying to install GIT')
            if system == 'Linux':
                cmd = 'sudo apt-get -y install git'
                Popen(shlex.split(cmd)).communicate()
            else:
                cmd = 'sudo port install git-core'
                Popen(shlex.split(cmd)).communicate()
            git = check_tool('git', False)
            if git == None:
                error('Could not install GIT. Try installing it manually')
                exit()
        log ('GIT is available')

        log ('Installing Cython')
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
    else:
        log('Cython is available')

    # Android SDK and NDK
    if ANDROID_NDK == None or not isdir(ANDROID_NDK) or not isfile(join(ANDROID_NDK, 'ndk-build')) or\
       not isdir(join(ANDROID_NDK,"toolchains/arm-linux-androideabi-4.4.3/prebuilt/linux-x86/bin")) if system=='Linux' else\
    not isdir(join(ANDROID_NDK,"toolchains/arm-linux-androideabi-4.4.3/prebuilt/darwin-x86/bin")) if system == 'Darwin' else False:
        log('Installing Android NDK to %s' % ANDROID_NDK)
        if system == 'Linux':
            cmd = 'wget %s' % ANDROID_NDK_URL[system]
        elif system == 'Darwin':
            cmd = 'curl -O %s' % ANDROID_NDK_URL[system]
        else:
            error ('Can not install dependencies for this system')
            exit()


        ndkfile = ANDROID_NDK_URL[system].split('/')[-1]
        Popen(shlex.split(cmd), cwd=tempfile.gettempdir()).communicate()
        cmd = 'tar -jxvf %s' % ndkfile
        Popen(shlex.split(cmd), cwd=tempfile.gettempdir()).communicate()
        cmd = 'sudo mv %s %s' % ('-'.join(ndkfile.split('-')[0:3]), ANDROID_NDK)
        Popen(shlex.split(cmd), cwd=tempfile.gettempdir()).communicate()
        log('Adding ANDROID_NDK variable %s to .bashrc' % ANDROID_NDK)
        f = open(join(os.environ['HOME'],'.bashrc'), 'a')
        f.write('export ANDROID_NDK="%s"\n' % ANDROID_NDK)
        f.close()
    else:
        log('Android NDK is available at %s' % ANDROID_NDK)

    if ANDROID_SDK == None or not isdir(ANDROID_SDK) or  not isfile(join(ANDROID_SDK, 'tools', 'android')):
        log('Installing Android SDK to %s' % ANDROID_SDK)
        if system == 'Linux':
            cmd = 'wget %s' % ANDROID_SDK_URL[system]
        elif system == 'Darwin':
            cmd = 'curl -O %s' % ANDROID_SDK_URL[system]
        else:
            error ('Can not install dependencies for this system')
            exit()
        Popen(shlex.split(cmd), cwd=tempfile.gettempdir()).communicate()
        cmd = 'tar -zxvf %s' % ANDROID_SDK_URL[system].split('/')[-1]
        Popen(shlex.split(cmd), cwd=tempfile.gettempdir()).communicate()
        if system == 'Linux':
            cmd = 'sudo mv android-sdk-linux %s' % ANDROID_SDK
        elif system == 'Darwin':
            cmd = 'sudo mv android-sdk-macosx %s' % ANDROID_SDK
        Popen(shlex.split(cmd), cwd=tempfile.gettempdir()).communicate()
        log('Adding ANDROID_SDK variable %s to .bashrc' % ANDROID_SDK)
        f = open(join(os.environ['HOME'],'.bashrc'), 'a')
        f.write('export ANDROID_SDK="%s"\n' % ANDROID_SDK)
        f.close()
    else:
        log('Android SDK is available at %s' % ANDROID_SDK)

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
        AVAILABLE_PLATFORMS = ['osx', 'android', 'ios']

    return AVAILABLE_PLATFORMS, SED_CMD

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