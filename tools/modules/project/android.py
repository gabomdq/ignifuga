#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Build Project for Android
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

import os, shlex, shutil
from os.path import *
from subprocess import Popen, PIPE
from ..log import log, error
from schafer import prepare_source, make_python_freeze

def make(options, env, target, sources, cython_src, cfiles):
    from schafer import SED_CMD, ANDROID_SDK, ANDROID_NDK

    # Copy/update the skeleton
    platform_build = join(target.project, 'android')
    android_project = join(platform_build, 'android_project')
    jni_src = join(android_project, 'jni', 'src')
    local_cfiles = []
    for cfile in cfiles:
        local_cfiles.append(basename(cfile))

    cmd = 'rsync -aqPm --exclude .svn --exclude .hg %s/ %s' % (target.dist, android_project)
    Popen(shlex.split(cmd), cwd = target.dist).communicate()

    if options.wallpaper:
        # Wallpapers use a slightly different manifest
        if isfile(join(android_project, 'AndroidManifest.wallpaper.xml')):
            shutil.move(join(android_project, 'AndroidManifest.wallpaper.xml'), join(android_project, 'AndroidManifest.xml'))

    # Modify the glue code to suit the project
    cmd = SED_CMD + "'s|\[\[PROJECT_NAME\]\]|%s|g' %s" % (options.project.replace('.', '_'), join(jni_src, 'jni_glue.cpp'))
    Popen(shlex.split(cmd), cwd = jni_src).communicate()
    cmd = SED_CMD + "'s|\[\[PROJECT_NAME\]\]|%s|g' %s" % (options.project, join(android_project, 'AndroidManifest.xml'))
    Popen(shlex.split(cmd), cwd = jni_src).communicate()
    cmd = SED_CMD + "'s|\[\[PROJECT_NAME\]\]|%s|g' %s" % (options.project, join(android_project, 'src', 'SDLActivity.java'))
    Popen(shlex.split(cmd), cwd = jni_src).communicate()
    cmd = SED_CMD + "'s|\[\[PROJECT_NAME\]\]|%s|g' %s" % (options.project, join(android_project, 'src', 'SDLActivity.wallpaper.java'))
    Popen(shlex.split(cmd), cwd = jni_src).communicate()
    cmd = SED_CMD + "'s|\[\[PROJECT_NAME\]\]|%s|g' %s" % (options.project, join(android_project, 'build.xml'))
    Popen(shlex.split(cmd), cwd = jni_src).communicate()
    cmd = SED_CMD + "'s|\[\[SDK_LOCATION\]\]|%s|g' %s" % (ANDROID_SDK, join(android_project, 'local.properties'))
    Popen(shlex.split(cmd), cwd = jni_src).communicate()
    cmd = SED_CMD + "'s|\[\[LOCAL_SRC_FILES\]\]|%s|g' %s" % (' '.join(local_cfiles), join(jni_src, 'Android.mk'))
    Popen(shlex.split(cmd), cwd = jni_src).communicate()

    cmd = SED_CMD + "'s|\[\[TARGET\]\]|%s|g' %s" % (env['TARGET'], join(android_project, 'project.properties'))
    Popen(shlex.split(cmd), cwd = jni_src).communicate()
    cmd = SED_CMD + "'s|\[\[TARGET\]\]|%s|g' %s" % (env['TARGET'], join(android_project, 'jni', 'Application.mk'))
    Popen(shlex.split(cmd), cwd = jni_src).communicate()

    if options.androidkeystore != None:
        # Uncomment
        cmd = SED_CMD + "'s|#key.store=|key.store=|g' %s" % (join(android_project, 'ant.properties'))
        Popen(shlex.split(cmd), cwd = jni_src).communicate()
        cmd = SED_CMD + "'s|#key.alias=|key.alias=|g' %s" % (join(android_project, 'ant.properties'))
        Popen(shlex.split(cmd), cwd = jni_src).communicate()

        # Replace the key store and key alias
        cmd = SED_CMD + "'s|key.store=.*|key.store=%s|g' %s" % (options.androidkeystore, join(android_project, 'ant.properties'))
        Popen(shlex.split(cmd), cwd = jni_src).communicate()
        cmd = SED_CMD + "'s|key.alias=.*|key.alias=%s|g' %s" % (options.androidkeyalias, join(android_project, 'ant.properties'))
        Popen(shlex.split(cmd), cwd = jni_src).communicate()
    else:
        # Comment out the relevant lines
        cmd = SED_CMD + "'s|^key.store=|#key.store=|g' %s" % (join(android_project, 'ant.properties'))
        Popen(shlex.split(cmd), cwd = jni_src).communicate()
        cmd = SED_CMD + "'s|^key.alias=|#key.alias=|g' %s" % (join(android_project, 'ant.properties'))
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

    # Update projects files in case something is outdated vs the Android SDK tools
    if isfile(join(platform_build, 'android_project', 'build.xml')):
        os.unlink(join(platform_build, 'android_project', 'build.xml'))
    cmd = 'android update project -t %s -n %s -p %s' % (env['TARGET'], options.project, join(platform_build, 'android_project'))
    Popen(shlex.split(cmd)).communicate()

    # Build it
    cmd = 'ndk-build'
    Popen(shlex.split(cmd), cwd = join(platform_build, 'android_project'), env=env).communicate()
    if options.androidkeystore != None:
        cmd = 'ant release'
        Popen(shlex.split(cmd), cwd = join(platform_build, 'android_project'), env=env).communicate()
        apk = join(android_project, 'bin', options.project+'-release.apk')
    else:
        cmd = 'ant debug'
        Popen(shlex.split(cmd), cwd = join(platform_build, 'android_project'), env=env).communicate()
        apk = join(android_project, 'bin', options.project+'-debug.apk')


    if not isfile(apk):
        error ('Error during compilation of the project')
        exit()
    shutil.move(apk, join(target.project, '..', options.project+'.apk'))

    return True
