#!/usr/bin/env python
#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


# SimpleFileWatcher Cython wrapper
from libcpp.string cimport string
from libcpp cimport bool

cdef extern from "FileWatcher/FileWatcher.h" namespace "FW::Actions":
    ctypedef enum Action:
        Add = 1
        Delete = 2
        Modified = 4

cdef extern from "FileWatcher/FileWatcher.h" namespace "FW":
    ctypedef string String
    ctypedef unsigned long WatchID

    cdef cppclass FileWatcherImpl
    cdef cppclass FileWatchListener

    cdef cppclass Exception: #: public std::runtime_error
        Exception(String& message) except +

    cdef cppclass FileNotFoundException: # : public Exception
        FileNotFoundException() except +
        FileNotFoundException(String& filename) except +

    cdef cppclass FileWatcher:
        FileWatcher() except +
        WatchID addWatch(String& directory, FileWatchListener* watcher)
        WatchID addWatch(String& directory, FileWatchListener* watcher, bool recursive)
        void removeWatch(String& directory)
        void removeWatch(WatchID watchid)
        void update()

    cdef cppclass FileWatchListener:
        FileWatchListener() except +
        void handleFileAction(WatchID watchid, String& dir, String& filename, Action action)

    cdef cppclass FileWatchListenerIgnifuga(FileWatchListener):
        pass
#        FileWatchListener() except +
#        void handleFileAction(WatchID watchid, String& dir, String& filename, Action action)
