from copy import deepcopy
import os

def prepare_linux64_env():
    """ Set up the environment variables for Linux64 compilation"""
    env = deepcopy(os.environ)
    env['CC'] = 'gcc'
    env['STRIP'] = 'strip'
    env['CFLAGS'] = "" if not 'CFLAGS' in env else env['CFLAGS']
    return env


def prepare_osx_env():
    """ Set up the environment variables for Linux64 compilation"""
    env = deepcopy(os.environ)
    env['CC'] = 'gcc'
    env['STRIP'] = 'strip'
    env['CFLAGS'] = env['CXXFLAGS'] = '-g -O2 -mmacosx-version-min=10.6 -isysroot /Developer/SDKs/MacOSX10.6.sdk'
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
    env['MAKE'] = 'make V=0 -k -j4 HOSTPYTHON=%s HOSTPGEN=%s CROSS_COMPILE=arm-eabi- CROSS_COMPILE_TARGET=yes' % (HOSTPYTHON, HOSTPGEN)

    env['DIST_DIR'] = DIST_DIR
    env['TMP_DIR'] = TMP_DIR
    return env


def prepare_mingw32_env():
    """ Set up the environment variables for Mingw32 compilation"""
    from schafer import HOSTPYTHON, HOSTPGEN
    env = deepcopy(os.environ)
    #env['PATH'] = "%s/toolchains/arm-linux-androideabi-4.4.3/prebuilt/linux-x86/bin/:%s:%s/tools:/usr/local/bin:/usr/bin:/bin:%s" % (ANDROID_NDK, ANDROID_NDK, ANDROID_SDK, '') #env['PATH'])
    env['ARCH'] = "win32"
    #env['CFLAGS'] ="-I %s" % (join(BUILDS['PYTHON'], 'PC'),)
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
    env['MAKE'] = 'make V=0 -k -j4 HOSTPYTHON=%s HOSTPGEN=%s CROSS_COMPILE=mingw32msvc CROSS_COMPILE_TARGET=yes' % (HOSTPYTHON, HOSTPGEN)
    env['DIST_DIR'] = DIST_DIR
    env['TMP_DIR'] = TMP_DIR
    return env
