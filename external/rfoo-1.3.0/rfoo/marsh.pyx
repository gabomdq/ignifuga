"""
    marsh.pyx

    Safe marshal. 

    Provide safe marshaling of data ontop of the built in marshal module 
    by forbidding code objects.

    Does not support long objects since verifying them requires a rocket
    scientist.

    Copyright (c) 2010 Nir Aides <nir@winpdb.org> and individual contributors.
    All rights reserved.

    Redistribution and use in source and binary forms, with or without modification,
    are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice, 
    this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright 
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.

    3. Neither the name of Nir Aides nor the names of other contributors may 
    be used to endorse or promote products derived from this software without
    specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
    ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
    ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
    (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
    LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
    ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


import marshal as _marshal


cdef char NONE = 'N'
cdef char TRUE = 'T'
cdef char FALSE = 'F'
cdef char INT32 = 'i'
cdef char INT64 = 'I'
cdef char LONG = 'l'
cdef char FLOAT = 'f'
cdef char BINARY_FLOAT = 'g'
cdef char STRINGREF = 'R'
cdef char UNICODE = 'u'
cdef char STRING = 's'
cdef char INTERNED = 't'
cdef char LIST = '['
cdef char TUPLE = '('
cdef char SET = '<'
cdef char FROZEN_SET = '>'
cdef char DICT = '{'
cdef char DICT_CLOSE = '0'
cdef char PAD = '_'


cdef int verify_string(char *s_, unsigned int length):
    """Verify marshaled data contains supported data types only."""

    cdef unsigned char *s = <unsigned char*> s_
    cdef unsigned char *eof = s + length
    cdef unsigned int nstrings = 0
    cdef unsigned int i
    cdef unsigned int v
    cdef unsigned int m

    while s < eof:
        if s[0] == INT32:
            s += 5
            continue

        if s[0] in (INT64, BINARY_FLOAT):
            s += 9
            continue

        if s[0] == LONG:
            if s + 5 > eof:
                return 0

            m = 1
            v = 0
            for i in range(1, 5):
                v += m * s[i]
                m *= 256

            s += 5 + v * 2
            continue

        if s[0] in (NONE, TRUE, FALSE):
            s += 1
            continue

        if s[0] == FLOAT:
            if s + 2 > eof:
                return 0

            s += 2 + s[1]
            continue

        if s[0] in (UNICODE, STRING, INTERNED):
            if s + 5 > eof:
                return 0

            if s[0] == INTERNED:
                nstrings += 1

            m = 1
            v = 0
            for i in range(1, 5):
                v += m * s[i]
                m *= 256

            s += 5 + v
            continue

        if s[0] == STRINGREF:
            if s + 5 > eof:
                return 0

            m = 1
            v = 0
            for i in range(1, 5):
                v += m * s[i]
                m *= 256

            # String reference to non-existing string.
            if v >= nstrings:
                return 0

            s += 5
            continue

        if s[0] in (LIST, TUPLE, SET, FROZEN_SET):
            s += 5
            continue

        if s[0] in (DICT, DICT_CLOSE):
            s += 1
            continue

        if s[0] == PAD:
            s += 1
            while s < eof and s[0] == PAD:
                s += 1
            return s == eof

        return 0

    if s > eof:
        return 0

    return 1
 

def loads(s):
    if verify_string(s, len(s)) == 0:
        raise ValueError('bad marshal data')

    return _marshal.loads(s)


def dumps(expr):
    s = _marshal.dumps(expr, 1)
    if verify_string(s, len(s)) == 0:
        raise ValueError('unsupported marshal data')

    return s


