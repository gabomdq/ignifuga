#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# xcython: profile=True

from libc.stdlib cimport free, malloc
from ignifuga.Log import error

DEF SDL_INIT_EVERYTHING = 0x0000FFFF

cpdef initializeSDL():
    #print "SDL INIT"
    SDL_Init(SDL_INIT_EVERYTHING)
    #print "SDL INITED"
    #SDL_EnableUNICODE(1) -- skip this as its not currently available 2012-01-23
    TTF_Init()

cpdef terminateSDL():
    TTF_Quit()
    SDL_Quit()

cpdef getTicks():
    return SDL_GetTicks()

cpdef delay(Uint32 ms):
    SDL_Delay(ms)

cpdef str readFile(str name):
    cdef bytes contents = bytes()
    cdef bytes filename = <bytes>name
    cdef SDL_RWops *ctx = SDL_RWFromFile(filename, 'r')
    cdef char *buf
    cdef size_t bytesread
    if ctx != NULL:
        buf = <char*>malloc(1025)
        if buf == NULL:
            error("Could not allocate memory for temp buffer to read file!")
            return None

        bytesread = ctx.read(ctx, buf, 1, 1024)
        while bytesread > 0:
            buf[bytesread] = 0
            contents += buf
            bytesread = ctx.read(ctx, buf, 1, 1024)

        ctx.close(ctx)
        free(buf)
        return str(contents)
    return None
