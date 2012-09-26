#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Build Project for iOS
# Author: Gabriel Jacobo <gabriel@mdqinc.com>
#057ACB5D155DA021001F2261

import os, shlex, shutil, re
from os.path import *
from subprocess import Popen, PIPE
from ..log import log, error
from schafer import prepare_source, make_python_freeze
from mod_pbxproj import *

def make(options, env, target, sources, cython_src, cfiles):
    from schafer import SED_CMD

    if options.ioscodesign is None:
        error("You have to supply a CodeSign Authority with --ios-codesign")
        exit()

    if options.bare:
        error("We don't support bare mode projects for iOS yet")
        exit()

    # Copy/update the skeleton
    platform_build = join(target.project, 'ios')
    ios_project = join(platform_build, 'ios_project')
    project_name = options.project.split('.')[-1]
    # Strip whitespace
    project_name = re.sub(r'\s', '', project_name)

    local_cfiles = []
    for cfile in cfiles:
        local_cfiles.append(basename(cfile))

    if isdir(ios_project):
        cmd = 'rm -rf %s' % ios_project
        Popen(shlex.split(cmd), cwd = target.dist).communicate()

    cmd = 'rsync -auqPm --exclude .svn --exclude .hg %s/ %s' % (target.dist, ios_project)
    Popen(shlex.split(cmd), cwd = target.dist).communicate()
    # Modify the skeleton to suit the project
    cmd = SED_CMD + "'s|\[\[PROJECT_NAME\]\]|%s|g' %s" % (project_name, join(ios_project, 'ios.xcodeproj', 'project.pbxproj'))
    Popen(shlex.split(cmd)).communicate()
    cmd = SED_CMD + "'s|\[\[PROJECT_ARCHS\]\]|%s|g' %s" % (env['ARCHS'], join(ios_project, 'ios.xcodeproj', 'project.pbxproj'))
    Popen(shlex.split(cmd)).communicate()
    cmd = SED_CMD + "'s|\[\[PROJECT_NAME\]\]|%s|g' %s" % (project_name, join(ios_project, 'ios.xcodeproj', 'xcuserdata', 'user.xcuserdatad', 'xcschemes', 'ios.xcscheme'))
    Popen(shlex.split(cmd)).communicate()
    cmd = SED_CMD + "'s|\[\[PROJECT_NAME\]\]|%s|g' %s" % (project_name, join(ios_project, 'ios.xcodeproj', 'xcuserdata', 'user.xcuserdatad', 'xcschemes', 'xcschememanagement.plist'))
    Popen(shlex.split(cmd)).communicate()

    cmd = SED_CMD + "'s|\[\[CODESIGN_DEVELOPER\]\]|%s|g' %s" % (options.ioscodesign, join(ios_project, 'ios.xcodeproj', 'project.pbxproj'))
    Popen(shlex.split(cmd)).communicate()

    cmd = SED_CMD + "'s|\[\[DEPLOY_TARGET\]\]|%s|g' %s" % (env['IPHONEOS_DEPLOYMENT_TARGET'], join(ios_project, 'ios.xcodeproj', 'project.pbxproj'))
    Popen(shlex.split(cmd)).communicate()

    project = XcodeProject.Load(join(ios_project, 'ios.xcodeproj', 'project.pbxproj' ))
    for cf in cfiles:
        project.add_file(cf)

    for asset in options.assets:
        project.add_file(abspath(join(target.project_root, asset)))

    project.add_header_search_paths(join(target.dist, 'include'), False)
    project.add_header_search_paths(join(target.dist, 'include', 'SDL2'), False)
    project.add_header_search_paths(join(target.dist, 'include', 'python2.7'), False)
    project.add_library_search_paths(join(target.dist, 'lib'), False)

    project.save()

    shutil.move(join(ios_project, 'ios.xcodeproj', 'xcuserdata', 'user.xcuserdatad', 'xcschemes', 'ios.xcscheme'),join(ios_project, 'ios.xcodeproj', 'xcuserdata', 'user.xcuserdatad', 'xcschemes', project_name+'.xcscheme'))
    shutil.move(join(ios_project, 'ios.xcodeproj', 'xcuserdata', 'user.xcuserdatad'), join(ios_project, 'ios.xcodeproj', 'xcuserdata', env['USER']+'.xcuserdatad'))
    shutil.move(join(ios_project, 'ios.xcodeproj'), join(ios_project, project_name+'.xcodeproj'))
    shutil.move(join(ios_project, 'ios', 'ios-Info.plist'), join(ios_project, 'ios', project_name+'-Info.plist'))
    shutil.move(join(ios_project, 'ios', 'ios-Prefix.pch'), join(ios_project, 'ios', project_name+'-Prefix.pch'))
    shutil.move(join(ios_project, 'ios'), join(ios_project, project_name))

    app = join(ios_project, 'build/Release-iphoneos', project_name+'.app')
    ipa = join(target.project_root, project_name+'.ipa')

    if isdir(app):
        cmd = 'rm -rf %s' % app
        Popen(shlex.split(cmd)).communicate()

    if isfile(ipa):
        os.unlink(ipa)

    cmd = "/usr/bin/xcodebuild"
    # We do not use env here as it causes problems with xcodebuild!
    Popen(shlex.split(cmd), cwd=ios_project, env=os.environ).communicate()

    if not isdir(app) or not isfile(join(app, 'embedded.mobileprovision')):
        error('error building iOS app')
        return False

    log ('iOS app built, now we will codesign it and build the IPA'
    )
    # Hacky way to make an ad hoc distributable IPA
    cmd = "/usr/bin/xcrun -sdk iphoneos PackageApplication \"%s\" -o \"%s\" --sign \"%s\" --embed \"%s\"" % (app, ipa, options.ioscodesign, join(app, 'embedded.mobileprovision'))
    # Use env here, or codesign may fail for using the wrong codesign_allocate binary
    Popen(shlex.split(cmd), cwd=ios_project, env=env).communicate()

    print cmd
    if isfile(ipa):
        log('iOS app built succesfully')
    else:
        error('error building iOS app')
        return False

    return True
