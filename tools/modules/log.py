#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Schafer Module: Log utility functions
# Author: Gabriel Jacobo <gabriel@mdqinc.com>


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