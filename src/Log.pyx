#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Ignifuga Game Engine
# Logging utilities
# Created 20101105
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

# xcython: profile=True

from ignifuga.Singleton import Singleton
import sys

cpdef debug (msg):
    Log().debug(msg)
    
cpdef info (msg):
    Log().info(msg)
    
cpdef error (msg):
    Log().error(msg)
    
class Log:
    __metaclass__ = Singleton

    def __init__(self, logLevel = 10):
        self.logLevel = logLevel
        
    def debug (self, msg):
        return self.log(10, msg)
    
    def info (self, msg):
        return self.log(20, msg)
    
    def error (self, msg):
        return self.log(40, msg)

    def log(self, level, msg):
        if level>=self.logLevel:
            native_log(level, msg)
            return True
        return False
    