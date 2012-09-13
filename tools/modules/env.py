from copy import deepcopy
import os
from os.path import *
from log import error
from util import find_xcode, find_ios_sdk
import multiprocessing
from pypreprocessor import preprocessor

XCODE_ROOT = None
BEST_IOS_SDK = None
OSX_SDK = None

class Target(object):
    pass

class Builds(object):
    pass


def get_target(platform, project_root = '.', dist=None, tmp=None):
    """ Set up some target system variables """
    from schafer import ROOT_DIR
    target = Target()
    target.platform = platform
    dist_dir = join (ROOT_DIR, 'dist', platform) if dist == None else dist
    tmp_dir = join (ROOT_DIR, 'tmp', platform) if tmp == None else tmp
    target.dist = dist_dir
    target.tmp = tmp_dir
    target.builds = Builds()
    target.builds.PYTHON = join(tmp_dir, 'python')
    target.builds.SDL = join(tmp_dir, 'sdl')
    target.builds.SDL_IMAGE = join(tmp_dir, 'sdl_image')
    target.builds.SDL_TTF = join(tmp_dir, 'sdl_ttf')
    target.builds.SDL_MIXER = join(tmp_dir, 'sdl_mixer')
    target.builds.FREETYPE = join(tmp_dir, 'freetype')
    target.builds.PNG = join(tmp_dir, 'png')
    #target.builds.JPG = join(tmp_dir, 'jpg')
    target.builds.JPGTURBO = join(tmp_dir, 'jpgturbo')
    target.builds.ZLIB = join(tmp_dir, 'zlib')
    target.builds.IGNIFUGA = join(tmp_dir, 'ignifuga')
    target.builds.GC = join(tmp_dir, 'gc')
    target.builds.OGG = join(tmp_dir, 'ogg')

    target.python_headers = join(target.builds.PYTHON, 'Include')
    target.sdl_headers = join(dist_dir, 'include', 'SDL')

    target.project_root = project_root
    target.project = join(project_root, 'build')

    return target



def prepare_intel_linux64_env(target, pp=None, openmp=False):
    """ Set up the environment variables for x86_64 Linux64 native compilation from a x86_64 Linux system"""
    if pp is None:
        pp = preprocessor()

    pp.defines.append('__LINUX__')
    pp.defines.append('__LINUX64__')
    pp.defines.append('LITTLE_ENDIAN')
    pp.undefines.append('BIG_ENDIAN')

    env = deepcopy(os.environ)
    env['CC'] = 'gcc'
    env['STRIP'] = 'strip'
    env['CFLAGS'] = ("" if not 'CFLAGS' in env else env['CFLAGS']) + ' -m64 -I%s/include' % target.dist
    env['CPPFLAGS'] = ("" if not 'CPPFLAGS' in env else env['CPPFLAGS']) + ' -m64 -I%s/include' % target.dist
    env['LDFLAGS'] = ("" if not 'LDFLAGS' in env else env['LDFLAGS']) + ' -m64 -L%s/lib' % target.dist
    if openmp:
        env['CFLAGS'] += "-fopenmp"
        env['CPPFLAGS'] += "-fopenmp"
        env['LDFLAGS'] += '-lgomp'
    return env, pp


def prepare_intel_linux32_env(target, pp=None, openmp=False):
    """ Set up the environment variables for i386 Linux32 compilation from i386 or cross compilation from a x86_64 Linux system"""
    if pp is None:
        pp = preprocessor()

    pp.defines.append('__LINUX__')
    pp.defines.append('__LINUX32__')
    pp.defines.append('LITTLE_ENDIAN')
    pp.undefines.append('BIG_ENDIAN')

    env = deepcopy(os.environ)
    env['CC'] = 'gcc'
    env['STRIP'] = 'strip'
    env['CFLAGS'] = ("" if not 'CFLAGS' in env else env['CFLAGS']) + ' -m64 -I%s/include' % target.dist
    env['CPPFLAGS'] = ("" if not 'CPPFLAGS' in env else env['CPPFLAGS']) + ' -m64 -I%s/include' % target.dist
    env['LDFLAGS'] = ("" if not 'LDFLAGS' in env else env['LDFLAGS']) + ' -m64 -L%s/lib' % target.dist
    if openmp:
        env['CFLAGS'] += "-fopenmp"
        env['CPPFLAGS'] += "-fopenmp"
        env['LDFLAGS'] += '-lgomp'
    return env, pp



def prepare_osx_env(target, pp=None, openmp=False):
    """ Set up the environment variables for OS X native compilation from a OS X environment, fat builds for i386 and x86_64"""
    global XCODE_ROOT, OSX_SDK

    if pp is None:
        pp = preprocessor()

    pp.defines.append('__OSX__')
    pp.defines.append('LITTLE_ENDIAN')
    pp.undefines.append('BIG_ENDIAN')

    if XCODE_ROOT is None:
        XCODE_ROOT = find_xcode()

    if OSX_SDK is None:
        OSX_SDK = '%s/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.6.sdk' % XCODE_ROOT
        if not isdir(OSX_SDK):
            error('Could not locate OS X SDK at %s' % OSX_SDK)
            exit()

    env = deepcopy(os.environ)
    env['CC'] = 'gcc'
    env['STRIP'] = 'strip'
    env['CFLAGS'] = env['CXXFLAGS'] = '-g -O2 -mmacosx-version-min=10.6 --sysroot=%s -I%s/include' % (OSX_SDK, target.dist)
    env['LDFLAGS'] = ("" if not 'LDFLAGS' in env else env['LDFLAGS']) + '-L%s/lib' % target.dist
    return env, pp

def prepare_ios_env(target, pp=None, openmp=False, sdk=None, ostarget='3.0'):
    """ Set up the environment variables for iOS cross compilation from a OS X environment, fat builds for armv6 and armv7"""
    if pp is None:
        pp = preprocessor()

    pp.defines.append('__IOS__')
    pp.defines.append('LITTLE_ENDIAN')
    pp.undefines.append('BIG_ENDIAN')

    env = deepcopy(os.environ)
    global XCODE_ROOT, BEST_IOS_SDK

    if XCODE_ROOT is None:
        XCODE_ROOT = find_xcode()

    if BEST_IOS_SDK is None:
        BEST_IOS_SDK = find_ios_sdk()

    if sdk is None:
        sdk = BEST_IOS_SDK

    env['DEVROOT'] = join(XCODE_ROOT, 'Platforms/iPhoneOS.platform/Developer')
    env['SDKROOT'] = env['DEVROOT'] + '/SDKs/iPhoneOS%s.sdk' % sdk
    env['CFLAGS'] = env['CXXFLAGS'] = "-g -O2 -pipe -no-cpp-precomp -isysroot %s -miphoneos-version-min=%s -I%s/usr/include/ -I%s/include" % (env['SDKROOT'], ostarget, env['SDKROOT'], target.dist)
    env['CXXCPP'] = env['CPP'] = env['DEVROOT'] + "/usr/bin/llvm-cpp-4.2"
    env['CXX'] = env['DEVROOT'] + "/usr/bin/llvm-g++-4.2"
    env['CC'] = env['DEVROOT'] + "/usr/bin/llvm-gcc-4.2"
    env['LD'] = env['DEVROOT'] + "/usr/bin/ld"
    env['AR'] = env['DEVROOT'] + "/usr/bin/ar"
    env['AS'] = env['DEVROOT'] + "/usr/bin/ls"
    env['NM'] = env['DEVROOT'] + "/usr/bin/nm"
    env['RANLIB'] = env['DEVROOT'] + "/usr/bin/ranlib"
    env['STRIP'] = env['DEVROOT'] + "/usr/bin/strip"
    env['LDFLAGS'] = "-L%s/usr/lib/ -isysroot %s -miphoneos-version-min=%s -L%s/lib" % (env['SDKROOT'], env['SDKROOT'], ostarget, target.dist)
    return env, pp

ANDROID_VALID_GCC = ['4.4.3', '4.6']
def prepare_android_env(target, pp=None, openmp=False, api_level=10, gcc='4.4.3'):
    """ Default to an ARM build """
    return prepare_arm_android_env(pp, openmp, api_level, gcc)

def prepare_arm_android_env(target, pp=None, openmp=False, api_level=10, gcc='4.4.3'):
    """ Set up the environment variables for ARM Android cross compilation from a OS X or Linux environment"""
    from schafer import ANDROID_NDK, ANDROID_SDK, HOSTPYTHON, HOSTPGEN
    if pp is None:
        pp = preprocessor()
    pp.defines.append('__ANDROID__')
    pp.defines.append('LITTLE_ENDIAN')
    pp.undefines.append('BIG_ENDIAN')

    try:
        api_level = int(api_level)
    except:
        error("Invalid Android API Level, please provide an integer >= 10")
        exit()

    if api_level < 10:
        error("Invalid Android Target API Level Selected (it has to be >=10)")
        exit()

    apitarget = 'android-%d' % api_level

    env = deepcopy(os.environ)

    # Check that the NDK and SDK exist
    if ANDROID_NDK == None:
        error('No Android NDK location provided (use command line parameters or environment variable ANDROID_NDK)')
        exit()
    if ANDROID_SDK == None:
        error('No Android SDK location provided (use command line parameters or environment variable ANDROID_SDK)')
        exit()

    if not isdir(ANDROID_NDK) or not isfile(join(ANDROID_NDK, 'ndk-build')) or not isdir(join(ANDROID_NDK,"toolchains/arm-linux-androideabi-%s/prebuilt/linux-x86/bin" % gcc)):
        error('Can not locate Valid Android NDK at %s, install or update it' % (ANDROID_NDK,))
        exit()
    if ANDROID_SDK == None or not isdir(ANDROID_SDK) or  not isfile(join(ANDROID_SDK, 'tools', 'android')):
        error('Can not locate Android SDK at %s' % ANDROID_SDK)
        exit()

    # Check GCC version selected
    # NDK rev >= 8b has GCC 4.4.3 and 4.6
    if gcc not in ANDROID_VALID_GCC:
        error("Invalid GCC version. Please select one of: %s", ANDROID_VALID_GCC)

    if not isdir(join(ANDROID_NDK, 'toolchains', 'arm-linux-androideabi-'+gcc)):
        error("Your Android NDK does not have a GCC version %s" % gcc)
        exit()
    env['GCC_VERSION'] = gcc

    if 'JAVA_HOME' not in os.environ:
        env['JAVA_HOME'] = "/usr/lib/jvm/java-6-openjdk"

    if not isdir(env['JAVA_HOME']) or  not isfile(join(env['JAVA_HOME'], 'bin', 'java')):
        error('Can not locate JAVA at %s . Please set the JAVA_HOME environment variable accordingly' % (env['JAVA_HOME'],))
        exit()

    env['PATH'] = "%s/toolchains/arm-linux-androideabi-%s/prebuilt/linux-x86/bin/:%s:%s/tools:/usr/local/bin:/usr/bin:/bin:%s" % (ANDROID_NDK, gcc, ANDROID_NDK, ANDROID_SDK, '') #env['PATH'])
    env['ARCH'] = "armeabi"
    env['SDK'] = ANDROID_SDK
    env['NDK'] = ANDROID_NDK
    env['STL'] = 'gnu'
    env['TARGET'] = apitarget


    #env['ARCH'] = "armeabi-v7a"
    if api_level > 13:
        env['SYSROOT'] = "%s/platforms/android-14/arch-arm" % ANDROID_NDK
    elif api_level > 9:
        env['SYSROOT'] = "%s/platforms/android-9/arch-arm" % ANDROID_NDK
    else:
        error("INVALID API LEVEL")
        exit()

    if not isdir(env['SYSROOT']):
        error("Could not find platform files at %s" % env['SYSROOT'])
        exit()

    env['CFLAGS'] ="-DANDROID -mandroid -fomit-frame-pointer --sysroot %s -I%s/include" % (env['SYSROOT'], target.dist)

    if env['ARCH'] == "armeabi-v7a":
        env['CFLAGS']+=" -march=armv7-a -mfloat-abi=softfp -mfpu=vfp -mthumb"
    env['CXXFLAGS'] = env['CFLAGS']
    env['CC'] = 'arm-linux-androideabi-gcc %s' % (env['CFLAGS'],)
    env['CXX'] = 'arm-linux-androideabi-g++ %s' % (env['CXXFLAGS'],)
    env['AR'] = "arm-linux-androideabi-ar"
    env['RANLIB'] = "arm-linux-androideabi-ranlib"
    env['STRIP'] = "arm-linux-androideabi-strip --strip-unneeded"
    env['MAKE'] = 'make V=0 -k -j%d HOSTPYTHON=%s HOSTPGEN=%s CROSS_COMPILE=arm-eabi- CROSS_COMPILE_TARGET=yes' % (multiprocessing.cpu_count(), HOSTPYTHON, HOSTPGEN)

    # Debugging
#    env['NDK_DEBUG'] = "1"
#    # "-g" for debug info
#    env['CFLAGS'] += " -g -gstabs+"
#    env['CPPFLAGS'] = " -g -gstabs+"

    return env, pp


def prepare_intel_mingw32_env(target, pp=None, openmp=False):
    """ Set up the environment variables for i386 Mingw32 cross compilation from OS X or Linux"""
    from schafer import HOSTPYTHON, HOSTPGEN
    if pp is None:
        pp = preprocessor()

    pp.defines.append('__MINGW__')
    pp.defines.append('__MINGW32__')
    pp.defines.append('LITTLE_ENDIAN')
    pp.undefines.append('BIG_ENDIAN')


    env = deepcopy(os.environ)
    env['ARCH'] = "win32"
    # Force LIBC functions (otherwise you get undefined SDL_sqrt, SDL_cos, etc
    # Force a dummy haptic and mm joystick (otherwise there a bunch of undefined symbols from SDL_haptic.c and SDL_joystick.c).
    # The cross platform configuration of SDL doesnt work fine at this moment and it doesn't define these variables as it should
    #env['CFLAGS'] = "-DHAVE_LIBC=1 -DSDL_HAPTIC_DUMMY=1 -DSDL_JOYSTICK_WINMM=1"
    env['CFLAGS'] = ("" if not 'CFLAGS' in env else env['CFLAGS']) + '-I%s/include' % target.dist
    env['LDFLAGS'] = ("" if not 'LDFLAGS' in env else env['LDFLAGS']) + '-L%s/lib' % target.dist
    env['CXXFLAGS'] = env['CFLAGS']
    env['CC'] = 'i686-w64-mingw32-gcc %s' % (env['CFLAGS'],)
    env['CXX'] = 'i686-w64-mingw32-g++ %s' % (env['CXXFLAGS'],)
    env['AR'] = "i686-w64-mingw32-ar"
    env['RANLIB'] = "i686-w64-mingw32-ranlib"
    env['STRIP'] = "i686-w64-mingw32-strip --strip-unneeded"
    env['LD'] = "i686-w64-mingw32-ld"
    env['AS'] = "i686-w64-mingw32-as"
    env['NM'] = "i686-w64-mingw32-nm"
    env['DLLTOOL'] = "i686-w64-mingw32-dlltool"
    env['OBJDUMP'] = "i686-w64-mingw32-objdump"
    env['RESCOMP'] = "i686-w64-mingw32-windres"
    env['MAKE'] = 'make V=0 -k -j%d HOSTPYTHON=%s HOSTPGEN=%s CROSS_COMPILE=mingw32msvc CROSS_COMPILE_TARGET=yes' % (multiprocessing.cpu_count(), HOSTPYTHON, HOSTPGEN)
    return env, pp


def prepare_intel_mingw64_env(target, pp=None, openmp=False):
    """ Set up the environment variables for x86_64 Mingw64 cross compilation from OS X x86_64 or Linux x86_64"""
    from schafer import HOSTPYTHON, HOSTPGEN
    if pp is None:
        pp = preprocessor()

    pp.defines.append('__MINGW__')
    pp.defines.append('__MINGW64__')
    pp.defines.append('LITTLE_ENDIAN')
    pp.undefines.append('BIG_ENDIAN')


    env = deepcopy(os.environ)
    env['ARCH'] = "win64"
    # Force LIBC functions (otherwise you get undefined SDL_sqrt, SDL_cos, etc
    # Force a dummy haptic and mm joystick (otherwise there a bunch of undefined symbols from SDL_haptic.c and SDL_joystick.c).
    # The cross platform configuration of SDL doesnt work fine at this moment and it doesn't define these variables as it should
    #env['CFLAGS'] = "-DHAVE_LIBC=1 -DSDL_HAPTIC_DUMMY=1 -DSDL_JOYSTICK_WINMM=1"
    env['CFLAGS'] = ("" if not 'CFLAGS' in env else env['CFLAGS']) + '-I%s/include' % target.dist
    env['LDFLAGS'] = ("" if not 'LDFLAGS' in env else env['LDFLAGS']) + '-L%s/lib' % target.dist
    env['CXXFLAGS'] = env['CFLAGS']
    env['CC'] = 'x86_64-w64-mingw32-gcc %s' % (env['CFLAGS'],)
    env['CXX'] = 'x86_64-w64-mingw32-g++ %s' % (env['CXXFLAGS'],)
    env['AR'] = "x86_64-w64-mingw32-ar"
    env['RANLIB'] = "x86_64-w64-mingw32-ranlib"
    env['STRIP'] = "x86_64-w64-mingw32-strip --strip-unneeded"
    env['LD'] = "x86_64-w64-mingw32-ld"
    env['AS'] = "x86_64-w64-mingw32-as"
    env['NM'] = "x86_64-w64-mingw32-nm"
    env['DLLTOOL'] = "x86_64-w64-mingw32-dlltool"
    env['OBJDUMP'] = "x86_64-w64-mingw32-objdump"
    env['RESCOMP'] = "x86_64-w64-mingw32-windres"
    env['MAKE'] = 'make V=0 -k -j%d HOSTPYTHON=%s HOSTPGEN=%s CROSS_COMPILE=mingw64msvc CROSS_COMPILE_TARGET=yes' % (multiprocessing.cpu_count(), HOSTPYTHON, HOSTPGEN)
    return env, pp
