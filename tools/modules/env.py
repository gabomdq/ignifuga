from copy import deepcopy
import os
from os.path import *
from log import error
from util import find_xcode, find_ios_sdk
import multiprocessing

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
    target.builds.FREETYPE = join(tmp_dir, 'freetype')
    target.builds.PNG = join(tmp_dir, 'png')
    target.builds.JPG = join(tmp_dir, 'jpg')
    target.builds.ZLIB = join(tmp_dir, 'zlib')
    target.builds.IGNIFUGA = join(tmp_dir, 'ignifuga')

    target.python_headers = join(target.builds.PYTHON, 'Include')
    target.sdl_headers = join(dist_dir, 'include', 'SDL')

    target.project_root = project_root
    target.project = join(project_root, 'build')

    return target



def prepare_linux64_env():
    """ Set up the environment variables for Linux64 compilation"""
    env = deepcopy(os.environ)
    env['CC'] = 'gcc'
    env['STRIP'] = 'strip'
    env['CFLAGS'] = "" if not 'CFLAGS' in env else env['CFLAGS']
    return env


def prepare_osx_env():
    """ Set up the environment variables for OS X compilation"""
    global XCODE_ROOT, OSX_SDK

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
    env['CFLAGS'] = env['CXXFLAGS'] = '-g -O2 -mmacosx-version-min=10.6 --sysroot=%s' % OSX_SDK
    return env

def prepare_ios_env(sdk=None, target='3.0'):
    """ Set up the environment variables for iOS compilation"""
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
    env['CFLAGS'] = env['CXXFLAGS'] = "-g -O2 -pipe -no-cpp-precomp -isysroot %s -miphoneos-version-min=%s -I%s/usr/include/" % (env['SDKROOT'], target, env['SDKROOT'])
    env['CXXCPP'] = env['CPP'] = env['DEVROOT'] + "/usr/bin/llvm-cpp-4.2"
    env['CXX'] = env['DEVROOT'] + "/usr/bin/llvm-g++-4.2"
    env['CC'] = env['DEVROOT'] + "/usr/bin/llvm-gcc-4.2"
    env['LD'] = env['DEVROOT'] + "/usr/bin/ld"
    env['AR'] = env['DEVROOT'] + "/usr/bin/ar"
    env['AS'] = env['DEVROOT'] + "/usr/bin/ls"
    env['NM'] = env['DEVROOT'] + "/usr/bin/nm"
    env['RANLIB'] = env['DEVROOT'] + "/usr/bin/ranlib"
    env['STRIP'] = env['DEVROOT'] + "/usr/bin/strip"
    env['LDFLAGS'] = "-L%s/usr/lib/ -isysroot %s -miphoneos-version-min=%s" % (env['SDKROOT'], env['SDKROOT'], target)
    return env


def prepare_android_env():
    """ Set up the environment variables for Android compilation"""
    from schafer import ANDROID_NDK, ANDROID_SDK, HOSTPYTHON, HOSTPGEN

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
        error('Can not locate JAVA at %s . Please set the JAVA_HOME environment variable accordingly' % (env['JAVA_HOME'],))
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
    env['MAKE'] = 'make V=0 -k -j%d HOSTPYTHON=%s HOSTPGEN=%s CROSS_COMPILE=arm-eabi- CROSS_COMPILE_TARGET=yes' % (multiprocessing.cpu_count(), HOSTPYTHON, HOSTPGEN)

    return env


def prepare_mingw32_env():
    """ Set up the environment variables for Mingw32 compilation"""
    from schafer import HOSTPYTHON, HOSTPGEN
    env = deepcopy(os.environ)
    #env['PATH'] = "%s/toolchains/arm-linux-androideabi-4.4.3/prebuilt/linux-x86/bin/:%s:%s/tools:/usr/local/bin:/usr/bin:/bin:%s" % (ANDROID_NDK, ANDROID_NDK, ANDROID_SDK, '') #env['PATH'])
    env['ARCH'] = "win32"
    #env['CFLAGS'] ="-I %s" % (join(target.builds.PYTHON, 'PC'),)
    # Force LIBC functions (otherwise you get undefined SDL_sqrt, SDL_cos, etc
    # Force a dummy haptic and mm joystick (otherwise there a bunch of undefined symbols from SDL_haptic.c and SDL_joystick.c).
    # The cross platform configuration of SDL doesnt work fine at this moment and it doesn't define these variables as it should
    #env['CFLAGS'] = "-DHAVE_LIBC=1 -DSDL_HAPTIC_DUMMY=1 -DSDL_JOYSTICK_WINMM=1"
    env['CFLAGS'] = ""
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
    env['MAKE'] = 'make V=0 -k -j%d HOSTPYTHON=%s HOSTPGEN=%s CROSS_COMPILE=mingw32msvc CROSS_COMPILE_TARGET=yes' % (multiprocessing.cpu_count(), HOSTPYTHON, HOSTPGEN)
    return env
