#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Bootstrap Ignifuga code and dependencies
# Author: Gabriel Jacobo <gabriel@mdqinc.com>


#Platforms supported:
# Ubuntu Precise 12.04 32/64
# Ubuntu Quantal 12.10 32/64
# OS X Lion 64
# OS X Mountain Lion 64


import os, shlex, sys, platform, re
from os.path import *
from copy import deepcopy
from subprocess import Popen, PIPE
import tempfile
from optparse import OptionParser

#ROOT_DIR = abspath(join(dirname(sys.argv[0]), '..'))
ANDROID_NDK_URL = {'Linux': 'http://dl.google.com/android/ndk/android-ndk-r8-linux-x86.tar.bz2',
                   'Darwin': 'http://dl.google.com/android/ndk/android-ndk-r8-darwin-x86.tar.bz2'}
ANDROID_SDK_URL = {'Linux': 'http://dl.google.com/android/android-sdk_r18-linux.tgz',
                   'Darwin': 'http://dl.google.com/android/android-sdk_r18-macosx.zip' }

ANDROID_NDK =  os.environ['ANDROID_NDK'] if 'ANDROID_NDK' in os.environ else join(os.getenv('HOME'), 'android-ndk')
ANDROID_SDK =  os.environ['ANDROID_SDK'] if 'ANDROID_SDK' in os.environ else join(os.getenv('HOME'), 'android-sdk')
MACPORTS_VERSION = "2.1.3"
MACPORTS_URL =  "https://distfiles.macports.org/MacPorts/MacPorts-%s.tar.bz2" % MACPORTS_VERSION

PORT_CMD = 'port '

bash_profile = join(os.getenv('HOME'), '.profile')

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
        print 'Cython version %s is incompatible' % version
    return None

def check_tool(tool, fatal=True):
    cmd = 'which ' + tool
    output = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0]
    tool_path = output.split('\n')[0]
    if not isfile(tool_path):
        if fatal:
            print "Can not find %s, try running schafer -D to install dependencies automatically" % tool
            exit()
        else:
            return None

    return tool_path


def find_apple_sdk(type='iphoneos', major=5, minor=None):
    type = type.lower()
    if type not in [ 'macosx', 'iphoneos', 'iphonesimulator']:
        print "Invalid Apple SDK type %s" % type
        exit()

    if check_tool('xcodebuild', False) == None:
        print 'Can not detect XCode, please install it'
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


def check_xcode():
    if check_tool('xcodebuild', False) == None:
        print 'Can not detect XCode, please install it'
        exit()

    # Check that we have at least one SDK for Desktop, iOS and iOS simulator
    sdk = find_apple_sdk('macosx', 10, 6)
    if sdk is None:
        print "Could not find a valid OS X SDK"
        exit()

    sdk = find_apple_sdk('iphoneos', 5)
    if sdk is None:
        print "Could not find a valid iOS SDK"
        exit()

    sdk = find_apple_sdk('iphonesimulator', 5)
    if sdk is None:
        print "Could not find a valid iOS simulator SDK"
        exit()

    return True


def install_mac_ports(prefix=None):
    if prefix is None:
        prefix = join(os.getenv('HOME'), 'macports')

    if check_tool('port', False) is None:
        # Try with the prefix path
        env = deepcopy(os.environ)
        os.environ['PATH'] = '%(prefix)s/bin:%(prefix)s/bin:%(prev_path)s' % {'prefix': prefix, 'prev_path': env['PATH'] if 'PATH' in env else ''}
        os.environ['MANPATH'] = '%(prefix)s/share/man:%(prev_path)s' % {'prefix': prefix, 'prev_path': env['MANPATH'] if 'MANPATH' in env else ''}
        os.environ['PERL5LIB'] = '%(prefix)s/lib/perl5/5.8.8:%(prefix)s/lib/perl5/vendor_perl/5.8.8:%(prev_path)s' % {'prefix': prefix, 'prev_path': env['PERL5LIB'] if 'PERL5LIB' in env else ''}

        if check_tool('port', False) is None:
            # Restore the environment
            os.environ = deepcopy(env)

            # Install Mac Ports
            print "Mac Ports can not be located (perhaps you need to configure the PATH environment variable)"
            print "It is required to set up Ignifuga's dependencies automatically and to download the source code"
            print "I can download and install it for you, installation will be done as an unprivileged user"
            print "See here for more details: http://trac.macports.org/wiki/InstallingMacPorts#InstallMacPortsfromsourceasanunprivilegednon-rootuser"
            print "Should I proceed? (y/N)"
            choice = raw_input().lower()
            if choice != 'y':
                print 'Can not proceed without Mac Ports, install dependencies manually'
                exit(1)

            print 'Installing Mac Ports %s (macports.org)' % MACPORTS_VERSION
            tmpdir = tempfile.gettempdir()
            ports_source = join(tmpdir, 'MacPorts-'+MACPORTS_VERSION)
            ports_source_file = join(tmpdir, 'MacPorts.tar.bz2')
            cmd = 'curl -o %s %s' % (ports_source_file, MACPORTS_URL)
            Popen(shlex.split(cmd)).communicate()

            if isfile(ports_source_file):
                cmd = 'tar xjvf %s' % ports_source_file
                Popen(shlex.split(cmd), cwd=tmpdir).communicate()
                user = Popen(shlex.split('id -un'), stdout=PIPE).communicate()[0].replace("\n", '')
                group = Popen(shlex.split('id -gn'), stdout=PIPE).communicate()[0].replace("\n", '')

                env = deepcopy(os.environ)
                env['PATH'] = '/usr/bin:/usr/sbin:/bin:/sbin'

                cmd = "./configure --prefix=%(prefix)s --enable-readline --with-install-user=%(user)s --with-install-group=%(group)s --x-includes=/usr/X11R6/include --x-libraries=/usr/X11R6/lib --with-tclpackage=%(prefix)s/share/macports/Tcl" % \
                {
                    'user': user,
                    'group': group,
                    'prefix': prefix
                }
                Popen(shlex.split(cmd), cwd=ports_source, env=env).communicate()
                cmd = 'make'
                Popen(shlex.split(cmd), cwd=ports_source, env=env).communicate()
                cmd = 'make install'
                Popen(shlex.split(cmd), cwd=ports_source, env=env).communicate()

                os.environ['PATH'] = '%(prefix)s/bin:%(prefix)s/bin:%(prev_path)s' % {'prefix': prefix, 'prev_path': env['PATH'] if 'PATH' in env else ''}
                os.environ['MANPATH'] = '%(prefix)s/share/man:%(prev_path)s' % {'prefix': prefix, 'prev_path': env['MANPATH'] if 'MANPATH' in env else ''}
                os.environ['PERL5LIB'] = '%(prefix)s/lib/perl5/5.8.8:%(prefix)s/lib/perl5/vendor_perl/5.8.8:%(prev_path)s' % {'prefix': prefix, 'prev_path': env['PERL5LIB'] if 'PERL5LIB' in env else ''}

                # Check if it all worked
                if check_tool('port', False) is None:
                    print 'There was a problem installing Mac Ports. Please install manually and try again.'
                    exit(1)

                global bash_profile
                with open(bash_profile, "a") as f:
                    f.write("export PATH=%s\n" % os.environ['PATH'])
                    f.write("export MANPATH=%s\n" % os.environ['MANPATH'])
                    f.write("export PERL5LIB=%s\n" % os.environ['PERL5LIB'])
        else:
            print 'Could not download Mac Ports source. Please install manually and try again'
            exit(1)
    else:
        print 'Mac Ports is available'

def get_build_platform():
    # Check the host distro
    arch, exe = platform.architecture()
    system = platform.system()
    if system == 'Linux':
        distro_name, distro_version, distro_id = platform.linux_distribution()
    elif system == 'Darwin':
        distro_name, distro_version, distro_id = platform.mac_ver()
    return platform.processor(), system, arch, distro_name, distro_version, distro_id



########################################################################################################################
# Bootstrap Ignifuga
########################################################################################################################
if __name__ == '__main__':
    processor, system, arch, distro_name, distro_version, distro_id = get_build_platform()
    print 'Bootstrap utility for the Ignifuga Game Engine'
    print 'Host Platform: %s' % system
    usage = "bootstrap.py [-i install_path]"
    parser = OptionParser(usage=usage, version="Ignifuga Bootstrap 1.0")
    parser.add_option("-i",
        dest="path", default=join(os.getenv('HOME'),'ignifuga'),
        help="The installation path, default: ~/ignifuga")

    parser.add_option("--no-android",
                      action="store_true", dest="noandroid", default=False,
                      help="Do not install the Android SDK")

    parser.add_option("--no-rfoo",
                      action="store_true", dest="norfoo", default=False,
                      help="Do not install the RFoo console")

    if system == 'Linux':
        parser.add_option("--no-i386",
            action="store_true", dest="noi386", default=False,
            help="Do not install i386 packages on Ubuntu 64 bits")

    elif system == 'Darwin':
        parser.add_option("-m",
                      dest="macports_prefix", default=None,
                      help="MacPorts installation path: ~/macports")
        parser.add_option("--sudo-ports",
                          action="store_true", dest="sudoport", default=False,
                          help="Install Mac Ports packages using sudo")


    (options, args) = parser.parse_args()


    if system == 'Linux':
        print 'I need to install the following development packages and build dependencies:'
        base_pkgs = 'mercurial git-core rsync python-dev mingw-w64 g++-mingw-w64 mingw-w64-tools make gcc-4.6 automake autoconf openjdk-6-jdk gcc-multilib g++-multilib libx11-dev wget nasm libxext-dev libxinerama-dev mesa-common-dev libusb-1.0-0-dev libasound2-dev libpulse-dev libtool'
        print base_pkgs
        if processor == 'x86_64':
            if options.noi386:
                cmd = 'sudo apt-get -y install ' + base_pkgs
                Popen(shlex.split(cmd)).communicate()
            else:
                if distro_id == 'quantal':
                    # Enable i386 arch and install the required packages
                    cmd = 'sudo dpkg --add-architecture i386'
                    Popen(shlex.split(cmd)).communicate()
                    cmd = 'sudo apt-get update'
                    Popen(shlex.split(cmd)).communicate()
                cmd = 'sudo apt-get -y install ' + base_pkgs + ' ia32-libs libx11-dev:i386 '
                Popen(shlex.split(cmd)).communicate()
        else:
            cmd = 'sudo apt-get -y install ' + base_pkgs
            Popen(shlex.split(cmd)).communicate()
    elif system == 'Darwin':
        if options.sudoport:
            PORT_CMD = 'sudo ' + PORT_CMD
        check_xcode()
        install_mac_ports(options.macports_prefix)
        print 'Updating Mac Ports'
        cmd = PORT_CMD + 'selfupdate'
        Popen(shlex.split(cmd)).communicate()
        print 'Installing build dependencies using Mac Ports'
        cmd = PORT_CMD + 'install mercurial git-core rsync nasm libtool autoconf automake pkgconfig'
        Popen(shlex.split(cmd)).communicate()


    # Crudely determine if the Ignifuga source is present at the install path
    print "Verifying Ignifuga's source code"
    if not isdir(options.path) or not isdir(join(options.path, 'src')) or not isfile(join(options.path, 'src', 'Gilbert.py')):
        print "Source code not found, retrieving it..."
        if isdir(options.path):
            cmd = 'rm -rf %s' % options.path
            Popen(shlex.split(cmd)).communicate()

        cmd = 'hg clone https://bitbucket.org/gabomdq/ignifuga %s' % options.path
        Popen(shlex.split(cmd)).communicate()

        if not isdir(options.path) or not isdir(join(options.path, 'src')) or not isfile(join(options.path, 'src', 'Gilbert.py')):
            print "Could not check out the source code. Exiting."
            exit(1)
    else:
        print "Source code found"



    cython = find_cython()
    if cython == None:
        if system == 'Linux':
            # Install Cython using PIP as the .deb package on Ubuntu 12.04 is too old for our needs
            pip = check_tool('pip', False)
            if pip == None:
                # Try to install GIT
                print 'Trying to install PIP'
                cmd = 'sudo apt-get -y install python-pip'
                Popen(shlex.split(cmd)).communicate()
                pip = check_tool('pip', False)
                if pip == None:
                    print 'Could not install PIP which we need to install Cython. Try installing it manually'
                    exit(1)
            print 'PIP is available'
            print 'Installing Cython using PIP'
            cmd = 'sudo pip install cython'
            Popen(shlex.split(cmd)).communicate()
        elif system == 'Darwin':
            print 'Installing Cython using Mac Ports'
            cmd = PORT_CMD + 'install py27-cython'
            Popen(shlex.split(cmd)).communicate()
            cmd = PORT_CMD + 'select --set cython cython27'
            Popen(shlex.split(cmd)).communicate()

        cython = find_cython()
        if cython == None:
            print 'Could not install Cython (0.17 or higher). An system wide version may be present. Try installing it manually'
            exit(1)
    else:
        print 'Cython is available'

    # Android SDK and NDK
    if not options.noandroid:
        if ANDROID_NDK == None or not isdir(ANDROID_NDK) or not isfile(join(ANDROID_NDK, 'ndk-build')) or\
           not isdir(join(ANDROID_NDK,"toolchains/arm-linux-androideabi-4.4.3")):
            print 'Installing Android NDK to %s' % ANDROID_NDK
            if system == 'Linux':
                cmd = 'wget %s' % ANDROID_NDK_URL[system]
            elif system == 'Darwin':
                cmd = 'curl -O %s' % ANDROID_NDK_URL[system]
            else:
                print 'Can not install dependencies for this system'
                exit()


            ndkfile = ANDROID_NDK_URL[system].split('/')[-1]
            Popen(shlex.split(cmd), cwd=tempfile.gettempdir()).communicate()
            cmd = 'tar -jxvf %s' % ndkfile
            Popen(shlex.split(cmd), cwd=tempfile.gettempdir()).communicate()
            cmd = 'mv %s %s' % (join(tempfile.gettempdir(), '-'.join(ndkfile.split('-')[0:3])), ANDROID_NDK)
            Popen(shlex.split(cmd), cwd=tempfile.gettempdir()).communicate()
            print 'Adding ANDROID_NDK variable %s to bash profile' % ANDROID_NDK
            with open(bash_profile, "a") as f:
                f.write('export ANDROID_NDK="%s"\n' % ANDROID_NDK)
        else:
            print 'Android NDK is available at %s' % ANDROID_NDK

        if ANDROID_SDK == None or not isdir(ANDROID_SDK) or  not isfile(join(ANDROID_SDK, 'tools', 'android')):
            print 'Installing Android SDK to %s' % ANDROID_SDK
            if system == 'Linux':
                cmd = 'wget %s' % ANDROID_SDK_URL[system]
            elif system == 'Darwin':
                cmd = 'curl -O %s' % ANDROID_SDK_URL[system]
            else:
                print 'Can not install dependencies for this system'
                exit()
            Popen(shlex.split(cmd), cwd=tempfile.gettempdir()).communicate()
            cmd = 'tar -zxvf %s' % ANDROID_SDK_URL[system].split('/')[-1]
            Popen(shlex.split(cmd), cwd=tempfile.gettempdir()).communicate()
            if system == 'Linux':
                cmd = 'mv %s %s' % (join(tempfile.gettempdir(), 'android-sdk-linux'), ANDROID_SDK)
            elif system == 'Darwin':
                cmd = 'mv %s %s' % (join(tempfile.gettempdir(), 'android-sdk-macosx'), ANDROID_SDK)
            Popen(shlex.split(cmd), cwd=tempfile.gettempdir()).communicate()
            print 'Adding ANDROID_SDK variable %s to bash profile' % ANDROID_SDK
            with open(bash_profile, "a") as f:
                f.write('export ANDROID_SDK="%s"\n' % ANDROID_SDK)

            # Update the SDK using the android tool
            print 'Updating Android platform tools'
            cmd = join(ANDROID_SDK, 'tools', 'android') + ' update sdk -u --filter platform-tools'
            Popen(shlex.split(cmd)).communicate()
            print 'Installing android-10 SDK and tools'
            cmd = join(ANDROID_SDK, 'tools', 'android') + ' update sdk -u --filter tools'
            Popen(shlex.split(cmd)).communicate()
            cmd = join(ANDROID_SDK, 'tools', 'android') + ' update sdk -u --filter android-10'
            Popen(shlex.split(cmd)).communicate()
            cmd = join(ANDROID_SDK, 'tools', 'android') + ' update adb'
            Popen(shlex.split(cmd)).communicate()
        else:
            print 'Android SDK is available at %s' % ANDROID_SDK

    if not options.norfoo:
        # Rfoo
        install_rfoo = True
        try:
            import rfoo
            install_rfoo = False
        except:
            pass

        if install_rfoo:
            print 'Installing RFOO'
            rfoo_dir = join(options.path, 'external', 'rfoo-1.3.0')
            if system == 'Linux':
                cmd = 'sudo ' + sys.executable + ' setup.py install'
            else:
                cmd = 'python2.7 setup.py install'

            Popen(shlex.split(cmd), cwd=rfoo_dir).communicate()


    # Add the tools path
    if check_tool('schafer', False) is None:
        with open(bash_profile, "a") as f:
            f.write("export PATH=$PATH:%s\n" % join(options.path, 'tools'))

    print "Everything is set up, you can build the engine using the Schafer tool\nFor example:"
    print "export PATH=$PATH:%s" % join(options.path, 'tools')
    if system == 'Linux':
        print 'schafer -P linux64'
    elif system == 'Darwin':
        print 'schafer -P osx'
