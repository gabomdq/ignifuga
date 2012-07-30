#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

cdef extern from "native_log.h":
    cdef int native_log(int level, char *str)
    cdef int __android_log_print(int prio, char *tag, char *fmt, ...)
    