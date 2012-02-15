#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


'''Wrapper for SDL_image.h

Generated with:
./ctypesgen/ctypesgen.py -L/usr/local/lib -lSDL_image /usr/local/include/SDL/SDL_image.h -o SDL_Image.py

Do not modify this file.
'''

__docformat__ =  'restructuredtext'

# Begin preamble

import ctypes, os, sys
from ctypes import *

_int_types = (c_int16, c_int32)
if hasattr(ctypes, 'c_int64'):
    # Some builds of ctypes apparently do not have c_int64
    # defined; it's a pretty good bet that these builds do not
    # have 64-bit pointers.
    _int_types += (c_int64,)
for t in _int_types:
    if sizeof(t) == sizeof(c_size_t):
        c_ptrdiff_t = t
del t
del _int_types

class c_void(Structure):
    # c_void_p is a buggy return type, converting to int, so
    # POINTER(None) == c_void_p is actually written as
    # POINTER(c_void), so it can be treated as a real pointer.
    _fields_ = [('dummy', c_int)]

def POINTER(obj):
    p = ctypes.POINTER(obj)

    # Convert None to a real NULL pointer to work around bugs
    # in how ctypes handles None on 64-bit platforms
    if not isinstance(p.from_param, classmethod):
        def from_param(cls, x):
            if x is None:
                return cls()
            else:
                return x
        p.from_param = classmethod(from_param)

    return p

class UserString:
    def __init__(self, seq):
        if isinstance(seq, basestring):
            self.data = seq
        elif isinstance(seq, UserString):
            self.data = seq.data[:]
        else:
            self.data = str(seq)
    def __str__(self): return str(self.data)
    def __repr__(self): return repr(self.data)
    def __int__(self): return int(self.data)
    def __long__(self): return long(self.data)
    def __float__(self): return float(self.data)
    def __complex__(self): return complex(self.data)
    def __hash__(self): return hash(self.data)

    def __cmp__(self, string):
        if isinstance(string, UserString):
            return cmp(self.data, string.data)
        else:
            return cmp(self.data, string)
    def __contains__(self, char):
        return char in self.data

    def __len__(self): return len(self.data)
    def __getitem__(self, index): return self.__class__(self.data[index])
    def __getslice__(self, start, end):
        start = max(start, 0); end = max(end, 0)
        return self.__class__(self.data[start:end])

    def __add__(self, other):
        if isinstance(other, UserString):
            return self.__class__(self.data + other.data)
        elif isinstance(other, basestring):
            return self.__class__(self.data + other)
        else:
            return self.__class__(self.data + str(other))
    def __radd__(self, other):
        if isinstance(other, basestring):
            return self.__class__(other + self.data)
        else:
            return self.__class__(str(other) + self.data)
    def __mul__(self, n):
        return self.__class__(self.data*n)
    __rmul__ = __mul__
    def __mod__(self, args):
        return self.__class__(self.data % args)

    # the following methods are defined in alphabetical order:
    def capitalize(self): return self.__class__(self.data.capitalize())
    def center(self, width, *args):
        return self.__class__(self.data.center(width, *args))
    def count(self, sub, start=0, end=sys.maxint):
        return self.data.count(sub, start, end)
    def decode(self, encoding=None, errors=None): # XXX improve this?
        if encoding:
            if errors:
                return self.__class__(self.data.decode(encoding, errors))
            else:
                return self.__class__(self.data.decode(encoding))
        else:
            return self.__class__(self.data.decode())
    def encode(self, encoding=None, errors=None): # XXX improve this?
        if encoding:
            if errors:
                return self.__class__(self.data.encode(encoding, errors))
            else:
                return self.__class__(self.data.encode(encoding))
        else:
            return self.__class__(self.data.encode())
    def endswith(self, suffix, start=0, end=sys.maxint):
        return self.data.endswith(suffix, start, end)
    def expandtabs(self, tabsize=8):
        return self.__class__(self.data.expandtabs(tabsize))
    def find(self, sub, start=0, end=sys.maxint):
        return self.data.find(sub, start, end)
    def index(self, sub, start=0, end=sys.maxint):
        return self.data.index(sub, start, end)
    def isalpha(self): return self.data.isalpha()
    def isalnum(self): return self.data.isalnum()
    def isdecimal(self): return self.data.isdecimal()
    def isdigit(self): return self.data.isdigit()
    def islower(self): return self.data.islower()
    def isnumeric(self): return self.data.isnumeric()
    def isspace(self): return self.data.isspace()
    def istitle(self): return self.data.istitle()
    def isupper(self): return self.data.isupper()
    def join(self, seq): return self.data.join(seq)
    def ljust(self, width, *args):
        return self.__class__(self.data.ljust(width, *args))
    def lower(self): return self.__class__(self.data.lower())
    def lstrip(self, chars=None): return self.__class__(self.data.lstrip(chars))
    def partition(self, sep):
        return self.data.partition(sep)
    def replace(self, old, new, maxsplit=-1):
        return self.__class__(self.data.replace(old, new, maxsplit))
    def rfind(self, sub, start=0, end=sys.maxint):
        return self.data.rfind(sub, start, end)
    def rindex(self, sub, start=0, end=sys.maxint):
        return self.data.rindex(sub, start, end)
    def rjust(self, width, *args):
        return self.__class__(self.data.rjust(width, *args))
    def rpartition(self, sep):
        return self.data.rpartition(sep)
    def rstrip(self, chars=None): return self.__class__(self.data.rstrip(chars))
    def split(self, sep=None, maxsplit=-1):
        return self.data.split(sep, maxsplit)
    def rsplit(self, sep=None, maxsplit=-1):
        return self.data.rsplit(sep, maxsplit)
    def splitlines(self, keepends=0): return self.data.splitlines(keepends)
    def startswith(self, prefix, start=0, end=sys.maxint):
        return self.data.startswith(prefix, start, end)
    def strip(self, chars=None): return self.__class__(self.data.strip(chars))
    def swapcase(self): return self.__class__(self.data.swapcase())
    def title(self): return self.__class__(self.data.title())
    def translate(self, *args):
        return self.__class__(self.data.translate(*args))
    def upper(self): return self.__class__(self.data.upper())
    def zfill(self, width): return self.__class__(self.data.zfill(width))

class MutableString(UserString):
    """mutable string objects

    Python strings are immutable objects.  This has the advantage, that
    strings may be used as dictionary keys.  If this property isn't needed
    and you insist on changing string values in place instead, you may cheat
    and use MutableString.

    But the purpose of this class is an educational one: to prevent
    people from inventing their own mutable string class derived
    from UserString and than forget thereby to remove (override) the
    __hash__ method inherited from UserString.  This would lead to
    errors that would be very hard to track down.

    A faster and better solution is to rewrite your program using lists."""
    def __init__(self, string=""):
        self.data = string
    def __hash__(self):
        raise TypeError("unhashable type (it is mutable)")
    def __setitem__(self, index, sub):
        if index < 0:
            index += len(self.data)
        if index < 0 or index >= len(self.data): raise IndexError
        self.data = self.data[:index] + sub + self.data[index+1:]
    def __delitem__(self, index):
        if index < 0:
            index += len(self.data)
        if index < 0 or index >= len(self.data): raise IndexError
        self.data = self.data[:index] + self.data[index+1:]
    def __setslice__(self, start, end, sub):
        start = max(start, 0); end = max(end, 0)
        if isinstance(sub, UserString):
            self.data = self.data[:start]+sub.data+self.data[end:]
        elif isinstance(sub, basestring):
            self.data = self.data[:start]+sub+self.data[end:]
        else:
            self.data =  self.data[:start]+str(sub)+self.data[end:]
    def __delslice__(self, start, end):
        start = max(start, 0); end = max(end, 0)
        self.data = self.data[:start] + self.data[end:]
    def immutable(self):
        return UserString(self.data)
    def __iadd__(self, other):
        if isinstance(other, UserString):
            self.data += other.data
        elif isinstance(other, basestring):
            self.data += other
        else:
            self.data += str(other)
        return self
    def __imul__(self, n):
        self.data *= n
        return self

class String(MutableString, Union):

    _fields_ = [('raw', POINTER(c_char)),
                ('data', c_char_p)]

    def __init__(self, obj=""):
        if isinstance(obj, (str, unicode, UserString)):
            self.data = str(obj)
        else:
            self.raw = obj

    def __len__(self):
        return self.data and len(self.data) or 0

    def from_param(cls, obj):
        # Convert None or 0
        if obj is None or obj == 0:
            return cls(POINTER(c_char)())

        # Convert from String
        elif isinstance(obj, String):
            return obj

        # Convert from str
        elif isinstance(obj, str):
            return cls(obj)

        # Convert from c_char_p
        elif isinstance(obj, c_char_p):
            return obj

        # Convert from POINTER(c_char)
        elif isinstance(obj, POINTER(c_char)):
            return obj

        # Convert from raw pointer
        elif isinstance(obj, int):
            return cls(cast(obj, POINTER(c_char)))

        # Convert from object
        else:
            return String.from_param(obj._as_parameter_)
    from_param = classmethod(from_param)

def ReturnString(obj, func=None, arguments=None):
    return String.from_param(obj)

# As of ctypes 1.0, ctypes does not support custom error-checking
# functions on callbacks, nor does it support custom datatypes on
# callbacks, so we must ensure that all callbacks return
# primitive datatypes.
#
# Non-primitive return values wrapped with UNCHECKED won't be
# typechecked, and will be converted to c_void_p.
def UNCHECKED(type):
    if (hasattr(type, "_type_") and isinstance(type._type_, str)
        and type._type_ != "P"):
        return type
    else:
        return c_void_p

# ctypes doesn't have direct support for variadic functions, so we have to write
# our own wrapper class
class _variadic_function(object):
    def __init__(self,func,restype,argtypes):
        self.func=func
        self.func.restype=restype
        self.argtypes=argtypes
    def _as_parameter_(self):
        # So we can pass this variadic function as a function pointer
        return self.func
    def __call__(self,*args):
        fixed_args=[]
        i=0
        for argtype in self.argtypes:
            # Typecheck what we can
            fixed_args.append(argtype.from_param(args[i]))
            i+=1
        return self.func(*fixed_args+list(args[i:]))

# End preamble

_libs = {}
_libdirs = ['/usr/local/lib']

# Begin loader

# ----------------------------------------------------------------------------
# Copyright (c) 2008 David James
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

import os.path, re, sys, glob
import ctypes
import ctypes.util

def _environ_path(name):
    if name in os.environ:
        return os.environ[name].split(":")
    else:
        return []

class LibraryLoader(object):
    def __init__(self):
        self.other_dirs=[]

    def load_library(self,libname):
        """Given the name of a library, load it."""
        paths = self.getpaths(libname)

        for path in paths:
            if os.path.exists(path):
                return self.load(path)

        raise ImportError("%s not found." % libname)

    def load(self,path):
        """Given a path to a library, load it."""
        try:
            # Darwin requires dlopen to be called with mode RTLD_GLOBAL instead
            # of the default RTLD_LOCAL.  Without this, you end up with
            # libraries not being loadable, resulting in "Symbol not found"
            # errors
            if sys.platform == 'darwin':
                return ctypes.CDLL(path, ctypes.RTLD_GLOBAL)
            else:
                return ctypes.cdll.LoadLibrary(path)
        except OSError,e:
            raise ImportError(e)

    def getpaths(self,libname):
        """Return a list of paths where the library might be found."""
        if os.path.isabs(libname):
            yield libname

        else:
            for path in self.getplatformpaths(libname):
                yield path

            path = ctypes.util.find_library(libname)
            if path: yield path

    def getplatformpaths(self, libname):
        return []

# Darwin (Mac OS X)

class DarwinLibraryLoader(LibraryLoader):
    name_formats = ["lib%s.dylib", "lib%s.so", "lib%s.bundle", "%s.dylib",
                "%s.so", "%s.bundle", "%s"]

    def getplatformpaths(self,libname):
        if os.path.pathsep in libname:
            names = [libname]
        else:
            names = [format % libname for format in self.name_formats]

        for dir in self.getdirs(libname):
            for name in names:
                yield os.path.join(dir,name)

    def getdirs(self,libname):
        '''Implements the dylib search as specified in Apple documentation:

        http://developer.apple.com/documentation/DeveloperTools/Conceptual/
            DynamicLibraries/Articles/DynamicLibraryUsageGuidelines.html

        Before commencing the standard search, the method first checks
        the bundle's ``Frameworks`` directory if the application is running
        within a bundle (OS X .app).
        '''

        dyld_fallback_library_path = _environ_path("DYLD_FALLBACK_LIBRARY_PATH")
        if not dyld_fallback_library_path:
            dyld_fallback_library_path = [os.path.expanduser('~/lib'),
                                          '/usr/local/lib', '/usr/lib']

        dirs = []

        if '/' in libname:
            dirs.extend(_environ_path("DYLD_LIBRARY_PATH"))
        else:
            dirs.extend(_environ_path("LD_LIBRARY_PATH"))
            dirs.extend(_environ_path("DYLD_LIBRARY_PATH"))

        dirs.extend(self.other_dirs)
        dirs.append(".")

        if hasattr(sys, 'frozen') and sys.frozen == 'macosx_app':
            dirs.append(os.path.join(
                os.environ['RESOURCEPATH'],
                '..',
                'Frameworks'))

        dirs.extend(dyld_fallback_library_path)

        return dirs

# Posix

class PosixLibraryLoader(LibraryLoader):
    _ld_so_cache = None

    def _create_ld_so_cache(self):
        # Recreate search path followed by ld.so.  This is going to be
        # slow to build, and incorrect (ld.so uses ld.so.cache, which may
        # not be up-to-date).  Used only as fallback for distros without
        # /sbin/ldconfig.
        #
        # We assume the DT_RPATH and DT_RUNPATH binary sections are omitted.

        directories = []
        for name in ("LD_LIBRARY_PATH",
                     "SHLIB_PATH", # HPUX
                     "LIBPATH", # OS/2, AIX
                     "LIBRARY_PATH", # BE/OS
                    ):
            if name in os.environ:
                directories.extend(os.environ[name].split(os.pathsep))
        directories.extend(self.other_dirs)
        directories.append(".")

        try: directories.extend([dir.strip() for dir in open('/etc/ld.so.conf')])
        except IOError: pass

        directories.extend(['/lib', '/usr/lib', '/lib64', '/usr/lib64'])

        cache = {}
        lib_re = re.compile(r'lib(.*)\.s[ol]')
        ext_re = re.compile(r'\.s[ol]$')
        for dir in directories:
            try:
                for path in glob.glob("%s/*.s[ol]*" % dir):
                    file = os.path.basename(path)

                    # Index by filename
                    if file not in cache:
                        cache[file] = path

                    # Index by library name
                    match = lib_re.match(file)
                    if match:
                        library = match.group(1)
                        if library not in cache:
                            cache[library] = path
            except OSError:
                pass

        self._ld_so_cache = cache

    def getplatformpaths(self, libname):
        if self._ld_so_cache is None:
            self._create_ld_so_cache()

        result = self._ld_so_cache.get(libname)
        if result: yield result

        path = ctypes.util.find_library(libname)
        if path: yield os.path.join("/lib",path)

# Windows

class _WindowsLibrary(object):
    def __init__(self, path):
        self.cdll = ctypes.cdll.LoadLibrary(path)
        self.windll = ctypes.windll.LoadLibrary(path)

    def __getattr__(self, name):
        try: return getattr(self.cdll,name)
        except AttributeError:
            try: return getattr(self.windll,name)
            except AttributeError:
                raise

class WindowsLibraryLoader(LibraryLoader):
    name_formats = ["%s.dll", "lib%s.dll", "%slib.dll"]

    def load_library(self, libname):
        try:
            result = LibraryLoader.load_library(self, libname)
        except ImportError:
            result = None
            if os.path.sep not in libname:
                for name in self.name_formats:
                    try:
                        result = getattr(ctypes.cdll, name % libname)
                        if result:
                            break
                    except WindowsError:
                        result = None
            if result is None:
                try:
                    result = getattr(ctypes.cdll, libname)
                except WindowsError:
                    result = None
            if result is None:
                raise ImportError("%s not found." % libname)
        return result

    def load(self, path):
        return _WindowsLibrary(path)

    def getplatformpaths(self, libname):
        if os.path.sep not in libname:
            for name in self.name_formats:
                dll_in_current_dir = os.path.abspath(name % libname)
                if os.path.exists(dll_in_current_dir):
                    yield dll_in_current_dir
                path = ctypes.util.find_library(name % libname)
                if path:
                    yield path

# Platform switching

# If your value of sys.platform does not appear in this dict, please contact
# the Ctypesgen maintainers.

loaderclass = {
    "darwin":   DarwinLibraryLoader,
    "cygwin":   WindowsLibraryLoader,
    "win32":    WindowsLibraryLoader
}

loader = loaderclass.get(sys.platform, PosixLibraryLoader)()

def add_library_search_dirs(other_dirs):
    loader.other_dirs = other_dirs

load_library = loader.load_library

del loaderclass

# End loader

add_library_search_dirs(['/usr/local/lib'])

# Begin libraries

_libs["SDL_image"] = load_library("SDL_image")

# 1 libraries
# End libraries

# No modules

__off_t = c_long # /usr/include/bits/types.h: 141

__off64_t = c_long # /usr/include/bits/types.h: 142

# /usr/include/libio.h: 271
class struct__IO_FILE(Structure):
    pass

FILE = struct__IO_FILE # /usr/include/stdio.h: 49

_IO_lock_t = None # /usr/include/libio.h: 180

# /usr/include/libio.h: 186
class struct__IO_marker(Structure):
    pass

struct__IO_marker.__slots__ = [
    '_next',
    '_sbuf',
    '_pos',
]
struct__IO_marker._fields_ = [
    ('_next', POINTER(struct__IO_marker)),
    ('_sbuf', POINTER(struct__IO_FILE)),
    ('_pos', c_int),
]

struct__IO_FILE.__slots__ = [
    '_flags',
    '_IO_read_ptr',
    '_IO_read_end',
    '_IO_read_base',
    '_IO_write_base',
    '_IO_write_ptr',
    '_IO_write_end',
    '_IO_buf_base',
    '_IO_buf_end',
    '_IO_save_base',
    '_IO_backup_base',
    '_IO_save_end',
    '_markers',
    '_chain',
    '_fileno',
    '_flags2',
    '_old_offset',
    '_cur_column',
    '_vtable_offset',
    '_shortbuf',
    '_lock',
    '_offset',
    '__pad1',
    '__pad2',
    '__pad3',
    '__pad4',
    '__pad5',
    '_mode',
    '_unused2',
]
struct__IO_FILE._fields_ = [
    ('_flags', c_int),
    ('_IO_read_ptr', String),
    ('_IO_read_end', String),
    ('_IO_read_base', String),
    ('_IO_write_base', String),
    ('_IO_write_ptr', String),
    ('_IO_write_end', String),
    ('_IO_buf_base', String),
    ('_IO_buf_end', String),
    ('_IO_save_base', String),
    ('_IO_backup_base', String),
    ('_IO_save_end', String),
    ('_markers', POINTER(struct__IO_marker)),
    ('_chain', POINTER(struct__IO_FILE)),
    ('_fileno', c_int),
    ('_flags2', c_int),
    ('_old_offset', __off_t),
    ('_cur_column', c_ushort),
    ('_vtable_offset', c_char),
    ('_shortbuf', c_char * 1),
    ('_lock', POINTER(_IO_lock_t)),
    ('_offset', __off64_t),
    ('__pad1', POINTER(None)),
    ('__pad2', POINTER(None)),
    ('__pad3', POINTER(None)),
    ('__pad4', POINTER(None)),
    ('__pad5', c_size_t),
    ('_mode', c_int),
    ('_unused2', c_char * (((15 * sizeof(c_int)) - (4 * sizeof(POINTER(None)))) - sizeof(c_size_t))),
]

enum_anon_31 = c_int # /usr/local/include/SDL/SDL_stdinc.h: 119

SDL_bool = enum_anon_31 # /usr/local/include/SDL/SDL_stdinc.h: 119

Uint8 = c_uint8 # /usr/local/include/SDL/SDL_stdinc.h: 128

Uint32 = c_uint32 # /usr/local/include/SDL/SDL_stdinc.h: 144

# /usr/local/include/SDL/SDL_error.h: 42
if hasattr(_libs['SDL_image'], 'SDL_SetError'):
    _func = _libs['SDL_image'].SDL_SetError
    _restype = None
    _argtypes = [String]
    SDL_SetError = _variadic_function(_func,_restype,_argtypes)

# /usr/local/include/SDL/SDL_error.h: 43
if hasattr(_libs['SDL_image'], 'SDL_GetError'):
    SDL_GetError = _libs['SDL_image'].SDL_GetError
    SDL_GetError.argtypes = []
    if sizeof(c_int) == sizeof(c_void_p):
        SDL_GetError.restype = ReturnString
    else:
        SDL_GetError.restype = String
        SDL_GetError.errcheck = ReturnString

# /usr/local/include/SDL/SDL_rwops.h: 46
class struct_SDL_RWops(Structure):
    pass

# /usr/local/include/SDL/SDL_rwops.h: 99
class struct_anon_59(Structure):
    pass

struct_anon_59.__slots__ = [
    'autoclose',
    'fp',
]
struct_anon_59._fields_ = [
    ('autoclose', SDL_bool),
    ('fp', POINTER(FILE)),
]

# /usr/local/include/SDL/SDL_rwops.h: 105
class struct_anon_60(Structure):
    pass

struct_anon_60.__slots__ = [
    'base',
    'here',
    'stop',
]
struct_anon_60._fields_ = [
    ('base', POINTER(Uint8)),
    ('here', POINTER(Uint8)),
    ('stop', POINTER(Uint8)),
]

# /usr/local/include/SDL/SDL_rwops.h: 111
class struct_anon_61(Structure):
    pass

struct_anon_61.__slots__ = [
    'data1',
]
struct_anon_61._fields_ = [
    ('data1', POINTER(None)),
]

# /usr/local/include/SDL/SDL_rwops.h: 83
class union_anon_62(Union):
    pass

union_anon_62.__slots__ = [
    'stdio',
    'mem',
    'unknown',
]
union_anon_62._fields_ = [
    ('stdio', struct_anon_59),
    ('mem', struct_anon_60),
    ('unknown', struct_anon_61),
]

struct_SDL_RWops.__slots__ = [
    'seek',
    'read',
    'write',
    'close',
    'type',
    'hidden',
]
struct_SDL_RWops._fields_ = [
    ('seek', CFUNCTYPE(UNCHECKED(c_long), POINTER(struct_SDL_RWops), c_long, c_int)),
    ('read', CFUNCTYPE(UNCHECKED(c_size_t), POINTER(struct_SDL_RWops), POINTER(None), c_size_t, c_size_t)),
    ('write', CFUNCTYPE(UNCHECKED(c_size_t), POINTER(struct_SDL_RWops), POINTER(None), c_size_t, c_size_t)),
    ('close', CFUNCTYPE(UNCHECKED(c_int), POINTER(struct_SDL_RWops))),
    ('type', Uint32),
    ('hidden', union_anon_62),
]

SDL_RWops = struct_SDL_RWops # /usr/local/include/SDL/SDL_rwops.h: 117

# /usr/local/include/SDL/SDL_pixels.h: 252
class struct_SDL_Color(Structure):
    pass

struct_SDL_Color.__slots__ = [
    'r',
    'g',
    'b',
    'unused',
]
struct_SDL_Color._fields_ = [
    ('r', Uint8),
    ('g', Uint8),
    ('b', Uint8),
    ('unused', Uint8),
]

SDL_Color = struct_SDL_Color # /usr/local/include/SDL/SDL_pixels.h: 252

# /usr/local/include/SDL/SDL_pixels.h: 261
class struct_SDL_Palette(Structure):
    pass

struct_SDL_Palette.__slots__ = [
    'ncolors',
    'colors',
    'version',
    'refcount',
]
struct_SDL_Palette._fields_ = [
    ('ncolors', c_int),
    ('colors', POINTER(SDL_Color)),
    ('version', Uint32),
    ('refcount', c_int),
]

SDL_Palette = struct_SDL_Palette # /usr/local/include/SDL/SDL_pixels.h: 261

# /usr/local/include/SDL/SDL_pixels.h: 266
class struct_SDL_PixelFormat(Structure):
    pass

struct_SDL_PixelFormat.__slots__ = [
    'format',
    'palette',
    'BitsPerPixel',
    'BytesPerPixel',
    'padding',
    'Rmask',
    'Gmask',
    'Bmask',
    'Amask',
    'Rloss',
    'Gloss',
    'Bloss',
    'Aloss',
    'Rshift',
    'Gshift',
    'Bshift',
    'Ashift',
    'refcount',
    'next',
]
struct_SDL_PixelFormat._fields_ = [
    ('format', Uint32),
    ('palette', POINTER(SDL_Palette)),
    ('BitsPerPixel', Uint8),
    ('BytesPerPixel', Uint8),
    ('padding', Uint8 * 2),
    ('Rmask', Uint32),
    ('Gmask', Uint32),
    ('Bmask', Uint32),
    ('Amask', Uint32),
    ('Rloss', Uint8),
    ('Gloss', Uint8),
    ('Bloss', Uint8),
    ('Aloss', Uint8),
    ('Rshift', Uint8),
    ('Gshift', Uint8),
    ('Bshift', Uint8),
    ('Ashift', Uint8),
    ('refcount', c_int),
    ('next', POINTER(struct_SDL_PixelFormat)),
]

SDL_PixelFormat = struct_SDL_PixelFormat # /usr/local/include/SDL/SDL_pixels.h: 287

# /usr/local/include/SDL/SDL_rect.h: 69
class struct_SDL_Rect(Structure):
    pass

struct_SDL_Rect.__slots__ = [
    'x',
    'y',
    'w',
    'h',
]
struct_SDL_Rect._fields_ = [
    ('x', c_int),
    ('y', c_int),
    ('w', c_int),
    ('h', c_int),
]

SDL_Rect = struct_SDL_Rect # /usr/local/include/SDL/SDL_rect.h: 69

# /usr/local/include/SDL/SDL_surface.h: 89
class struct_SDL_BlitMap(Structure):
    pass

# /usr/local/include/SDL/SDL_surface.h: 93
class struct_SDL_Surface(Structure):
    pass

struct_SDL_Surface.__slots__ = [
    'flags',
    'format',
    'w',
    'h',
    'pitch',
    'pixels',
    'userdata',
    'locked',
    'lock_data',
    'clip_rect',
    'map',
    'refcount',
]
struct_SDL_Surface._fields_ = [
    ('flags', Uint32),
    ('format', POINTER(SDL_PixelFormat)),
    ('w', c_int),
    ('h', c_int),
    ('pitch', c_int),
    ('pixels', POINTER(None)),
    ('userdata', POINTER(None)),
    ('locked', c_int),
    ('lock_data', POINTER(None)),
    ('clip_rect', SDL_Rect),
    ('map', POINTER(struct_SDL_BlitMap)),
    ('refcount', c_int),
]

SDL_Surface = struct_SDL_Surface # /usr/local/include/SDL/SDL_surface.h: 93

# /usr/local/include/SDL/SDL_version.h: 58
class struct_SDL_version(Structure):
    pass

struct_SDL_version.__slots__ = [
    'major',
    'minor',
    'patch',
]
struct_SDL_version._fields_ = [
    ('major', Uint8),
    ('minor', Uint8),
    ('patch', Uint8),
]

SDL_version = struct_SDL_version # /usr/local/include/SDL/SDL_version.h: 58

# /usr/local/include/SDL/SDL_image.h: 57
if hasattr(_libs['SDL_image'], 'IMG_Linked_Version'):
    IMG_Linked_Version = _libs['SDL_image'].IMG_Linked_Version
    IMG_Linked_Version.argtypes = []
    IMG_Linked_Version.restype = POINTER(SDL_version)

enum_anon_89 = c_int # /usr/local/include/SDL/SDL_image.h: 64

IMG_INIT_JPG = 1 # /usr/local/include/SDL/SDL_image.h: 64

IMG_INIT_PNG = 2 # /usr/local/include/SDL/SDL_image.h: 64

IMG_INIT_TIF = 4 # /usr/local/include/SDL/SDL_image.h: 64

IMG_InitFlags = enum_anon_89 # /usr/local/include/SDL/SDL_image.h: 64

# /usr/local/include/SDL/SDL_image.h: 70
if hasattr(_libs['SDL_image'], 'IMG_Init'):
    IMG_Init = _libs['SDL_image'].IMG_Init
    IMG_Init.argtypes = [c_int]
    IMG_Init.restype = c_int

# /usr/local/include/SDL/SDL_image.h: 73
if hasattr(_libs['SDL_image'], 'IMG_Quit'):
    IMG_Quit = _libs['SDL_image'].IMG_Quit
    IMG_Quit.argtypes = []
    IMG_Quit.restype = None

# /usr/local/include/SDL/SDL_image.h: 83
if hasattr(_libs['SDL_image'], 'IMG_LoadTyped_RW'):
    IMG_LoadTyped_RW = _libs['SDL_image'].IMG_LoadTyped_RW
    IMG_LoadTyped_RW.argtypes = [POINTER(SDL_RWops), c_int, String]
    IMG_LoadTyped_RW.restype = POINTER(SDL_Surface)

# /usr/local/include/SDL/SDL_image.h: 85
if hasattr(_libs['SDL_image'], 'IMG_Load'):
    IMG_Load = _libs['SDL_image'].IMG_Load
    IMG_Load.argtypes = [String]
    IMG_Load.restype = POINTER(SDL_Surface)

# /usr/local/include/SDL/SDL_image.h: 86
if hasattr(_libs['SDL_image'], 'IMG_Load_RW'):
    IMG_Load_RW = _libs['SDL_image'].IMG_Load_RW
    IMG_Load_RW.argtypes = [POINTER(SDL_RWops), c_int]
    IMG_Load_RW.restype = POINTER(SDL_Surface)

# /usr/local/include/SDL/SDL_image.h: 91
if hasattr(_libs['SDL_image'], 'IMG_InvertAlpha'):
    IMG_InvertAlpha = _libs['SDL_image'].IMG_InvertAlpha
    IMG_InvertAlpha.argtypes = [c_int]
    IMG_InvertAlpha.restype = c_int

# /usr/local/include/SDL/SDL_image.h: 94
if hasattr(_libs['SDL_image'], 'IMG_isICO'):
    IMG_isICO = _libs['SDL_image'].IMG_isICO
    IMG_isICO.argtypes = [POINTER(SDL_RWops)]
    IMG_isICO.restype = c_int

# /usr/local/include/SDL/SDL_image.h: 95
if hasattr(_libs['SDL_image'], 'IMG_isCUR'):
    IMG_isCUR = _libs['SDL_image'].IMG_isCUR
    IMG_isCUR.argtypes = [POINTER(SDL_RWops)]
    IMG_isCUR.restype = c_int

# /usr/local/include/SDL/SDL_image.h: 96
if hasattr(_libs['SDL_image'], 'IMG_isBMP'):
    IMG_isBMP = _libs['SDL_image'].IMG_isBMP
    IMG_isBMP.argtypes = [POINTER(SDL_RWops)]
    IMG_isBMP.restype = c_int

# /usr/local/include/SDL/SDL_image.h: 97
if hasattr(_libs['SDL_image'], 'IMG_isGIF'):
    IMG_isGIF = _libs['SDL_image'].IMG_isGIF
    IMG_isGIF.argtypes = [POINTER(SDL_RWops)]
    IMG_isGIF.restype = c_int

# /usr/local/include/SDL/SDL_image.h: 98
if hasattr(_libs['SDL_image'], 'IMG_isJPG'):
    IMG_isJPG = _libs['SDL_image'].IMG_isJPG
    IMG_isJPG.argtypes = [POINTER(SDL_RWops)]
    IMG_isJPG.restype = c_int

# /usr/local/include/SDL/SDL_image.h: 99
if hasattr(_libs['SDL_image'], 'IMG_isLBM'):
    IMG_isLBM = _libs['SDL_image'].IMG_isLBM
    IMG_isLBM.argtypes = [POINTER(SDL_RWops)]
    IMG_isLBM.restype = c_int

# /usr/local/include/SDL/SDL_image.h: 100
if hasattr(_libs['SDL_image'], 'IMG_isPCX'):
    IMG_isPCX = _libs['SDL_image'].IMG_isPCX
    IMG_isPCX.argtypes = [POINTER(SDL_RWops)]
    IMG_isPCX.restype = c_int

# /usr/local/include/SDL/SDL_image.h: 101
if hasattr(_libs['SDL_image'], 'IMG_isPNG'):
    IMG_isPNG = _libs['SDL_image'].IMG_isPNG
    IMG_isPNG.argtypes = [POINTER(SDL_RWops)]
    IMG_isPNG.restype = c_int

# /usr/local/include/SDL/SDL_image.h: 102
if hasattr(_libs['SDL_image'], 'IMG_isPNM'):
    IMG_isPNM = _libs['SDL_image'].IMG_isPNM
    IMG_isPNM.argtypes = [POINTER(SDL_RWops)]
    IMG_isPNM.restype = c_int

# /usr/local/include/SDL/SDL_image.h: 103
if hasattr(_libs['SDL_image'], 'IMG_isTIF'):
    IMG_isTIF = _libs['SDL_image'].IMG_isTIF
    IMG_isTIF.argtypes = [POINTER(SDL_RWops)]
    IMG_isTIF.restype = c_int

# /usr/local/include/SDL/SDL_image.h: 104
if hasattr(_libs['SDL_image'], 'IMG_isXCF'):
    IMG_isXCF = _libs['SDL_image'].IMG_isXCF
    IMG_isXCF.argtypes = [POINTER(SDL_RWops)]
    IMG_isXCF.restype = c_int

# /usr/local/include/SDL/SDL_image.h: 105
if hasattr(_libs['SDL_image'], 'IMG_isXPM'):
    IMG_isXPM = _libs['SDL_image'].IMG_isXPM
    IMG_isXPM.argtypes = [POINTER(SDL_RWops)]
    IMG_isXPM.restype = c_int

# /usr/local/include/SDL/SDL_image.h: 106
if hasattr(_libs['SDL_image'], 'IMG_isXV'):
    IMG_isXV = _libs['SDL_image'].IMG_isXV
    IMG_isXV.argtypes = [POINTER(SDL_RWops)]
    IMG_isXV.restype = c_int

# /usr/local/include/SDL/SDL_image.h: 109
if hasattr(_libs['SDL_image'], 'IMG_LoadICO_RW'):
    IMG_LoadICO_RW = _libs['SDL_image'].IMG_LoadICO_RW
    IMG_LoadICO_RW.argtypes = [POINTER(SDL_RWops)]
    IMG_LoadICO_RW.restype = POINTER(SDL_Surface)

# /usr/local/include/SDL/SDL_image.h: 110
if hasattr(_libs['SDL_image'], 'IMG_LoadCUR_RW'):
    IMG_LoadCUR_RW = _libs['SDL_image'].IMG_LoadCUR_RW
    IMG_LoadCUR_RW.argtypes = [POINTER(SDL_RWops)]
    IMG_LoadCUR_RW.restype = POINTER(SDL_Surface)

# /usr/local/include/SDL/SDL_image.h: 111
if hasattr(_libs['SDL_image'], 'IMG_LoadBMP_RW'):
    IMG_LoadBMP_RW = _libs['SDL_image'].IMG_LoadBMP_RW
    IMG_LoadBMP_RW.argtypes = [POINTER(SDL_RWops)]
    IMG_LoadBMP_RW.restype = POINTER(SDL_Surface)

# /usr/local/include/SDL/SDL_image.h: 112
if hasattr(_libs['SDL_image'], 'IMG_LoadGIF_RW'):
    IMG_LoadGIF_RW = _libs['SDL_image'].IMG_LoadGIF_RW
    IMG_LoadGIF_RW.argtypes = [POINTER(SDL_RWops)]
    IMG_LoadGIF_RW.restype = POINTER(SDL_Surface)

# /usr/local/include/SDL/SDL_image.h: 113
if hasattr(_libs['SDL_image'], 'IMG_LoadJPG_RW'):
    IMG_LoadJPG_RW = _libs['SDL_image'].IMG_LoadJPG_RW
    IMG_LoadJPG_RW.argtypes = [POINTER(SDL_RWops)]
    IMG_LoadJPG_RW.restype = POINTER(SDL_Surface)

# /usr/local/include/SDL/SDL_image.h: 114
if hasattr(_libs['SDL_image'], 'IMG_LoadLBM_RW'):
    IMG_LoadLBM_RW = _libs['SDL_image'].IMG_LoadLBM_RW
    IMG_LoadLBM_RW.argtypes = [POINTER(SDL_RWops)]
    IMG_LoadLBM_RW.restype = POINTER(SDL_Surface)

# /usr/local/include/SDL/SDL_image.h: 115
if hasattr(_libs['SDL_image'], 'IMG_LoadPCX_RW'):
    IMG_LoadPCX_RW = _libs['SDL_image'].IMG_LoadPCX_RW
    IMG_LoadPCX_RW.argtypes = [POINTER(SDL_RWops)]
    IMG_LoadPCX_RW.restype = POINTER(SDL_Surface)

# /usr/local/include/SDL/SDL_image.h: 116
if hasattr(_libs['SDL_image'], 'IMG_LoadPNG_RW'):
    IMG_LoadPNG_RW = _libs['SDL_image'].IMG_LoadPNG_RW
    IMG_LoadPNG_RW.argtypes = [POINTER(SDL_RWops)]
    IMG_LoadPNG_RW.restype = POINTER(SDL_Surface)

# /usr/local/include/SDL/SDL_image.h: 117
if hasattr(_libs['SDL_image'], 'IMG_LoadPNM_RW'):
    IMG_LoadPNM_RW = _libs['SDL_image'].IMG_LoadPNM_RW
    IMG_LoadPNM_RW.argtypes = [POINTER(SDL_RWops)]
    IMG_LoadPNM_RW.restype = POINTER(SDL_Surface)

# /usr/local/include/SDL/SDL_image.h: 118
if hasattr(_libs['SDL_image'], 'IMG_LoadTGA_RW'):
    IMG_LoadTGA_RW = _libs['SDL_image'].IMG_LoadTGA_RW
    IMG_LoadTGA_RW.argtypes = [POINTER(SDL_RWops)]
    IMG_LoadTGA_RW.restype = POINTER(SDL_Surface)

# /usr/local/include/SDL/SDL_image.h: 119
if hasattr(_libs['SDL_image'], 'IMG_LoadTIF_RW'):
    IMG_LoadTIF_RW = _libs['SDL_image'].IMG_LoadTIF_RW
    IMG_LoadTIF_RW.argtypes = [POINTER(SDL_RWops)]
    IMG_LoadTIF_RW.restype = POINTER(SDL_Surface)

# /usr/local/include/SDL/SDL_image.h: 120
if hasattr(_libs['SDL_image'], 'IMG_LoadXCF_RW'):
    IMG_LoadXCF_RW = _libs['SDL_image'].IMG_LoadXCF_RW
    IMG_LoadXCF_RW.argtypes = [POINTER(SDL_RWops)]
    IMG_LoadXCF_RW.restype = POINTER(SDL_Surface)

# /usr/local/include/SDL/SDL_image.h: 121
if hasattr(_libs['SDL_image'], 'IMG_LoadXPM_RW'):
    IMG_LoadXPM_RW = _libs['SDL_image'].IMG_LoadXPM_RW
    IMG_LoadXPM_RW.argtypes = [POINTER(SDL_RWops)]
    IMG_LoadXPM_RW.restype = POINTER(SDL_Surface)

# /usr/local/include/SDL/SDL_image.h: 122
if hasattr(_libs['SDL_image'], 'IMG_LoadXV_RW'):
    IMG_LoadXV_RW = _libs['SDL_image'].IMG_LoadXV_RW
    IMG_LoadXV_RW.argtypes = [POINTER(SDL_RWops)]
    IMG_LoadXV_RW.restype = POINTER(SDL_Surface)

# /usr/local/include/SDL/SDL_image.h: 124
if hasattr(_libs['SDL_image'], 'IMG_ReadXPMFromArray'):
    IMG_ReadXPMFromArray = _libs['SDL_image'].IMG_ReadXPMFromArray
    IMG_ReadXPMFromArray.argtypes = [POINTER(POINTER(c_char))]
    IMG_ReadXPMFromArray.restype = POINTER(SDL_Surface)

# /usr/local/include/SDL/SDL_image.h: 39
try:
    SDL_IMAGE_MAJOR_VERSION = 1
except:
    pass

# /usr/local/include/SDL/SDL_image.h: 40
try:
    SDL_IMAGE_MINOR_VERSION = 2
except:
    pass

# /usr/local/include/SDL/SDL_image.h: 41
try:
    SDL_IMAGE_PATCHLEVEL = 10
except:
    pass

# /usr/local/include/SDL/SDL_image.h: 127
try:
    IMG_SetError = SDL_SetError
except:
    pass

# /usr/local/include/SDL/SDL_image.h: 128
try:
    IMG_GetError = SDL_GetError
except:
    pass

# No inserted files

