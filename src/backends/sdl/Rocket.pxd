#!/usr/bin/env python
#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


# libRocket Cython wrapper

from ignifuga.backends.sdl.SDL cimport *
from cpython cimport *


cdef extern from "Rocket/Core/ElementDocument.h" namespace "Rocket::Core::ElementDocument":
    ctypedef enum FocusFlags:
        NONE = 0
        FOCUS = (1 << 1)
        MODAL = (1 << 2)

cdef extern from "Rocket/Core/ElementDocument.h" namespace "Rocket::Core":
    cdef cppclass ElementDocument:

        Context* GetContext()
        void SetTitle(String& title)
        String& GetTitle() 
        String& GetSourceURL() 
        #void SetStyleSheet(StyleSheet* style_sheet)
        #virtual StyleSheet* GetStyleSheet() 
        void PullToFront()
        void PushToBack()
        void Show(int focus_flags)
        void Hide()
        void Close()
        #Element* CreateElement( String& name)
        #ElementText* CreateTextNode( String& text)
        bint IsModal()
        #virtual void LoadScript(Stream* stream,  String& source_name)
        void UpdateLayout()
        void UpdatePosition()
        void LockLayout(bint lock)
        Context* GetContext()
        bint IsVisible()

cdef extern from "Rocket/Core/String.h" namespace "Rocket::Core":
    cdef cppclass String:
        String(char* string)

cdef extern from "Rocket/Core/String.h" namespace "Rocket::Core":
    cdef cppclass Vector2i:
        Vector2i(int x, int y)

cdef extern from "Rocket/Core/FontDatabase.h" namespace "Rocket::Core::FontDatabase":
    bint LoadFontFace(String& file_name) # static method of Rocket::Core::FontDatabase

cdef extern from "Rocket/Core/Context.h" namespace "Rocket::Core":
    cdef cppclass Context:
        bint Update()
        bint Render()
        ElementDocument* CreateDocument(String& tag)
        ElementDocument* LoadDocument(String& document_path)
        ElementDocument* LoadDocumentFromMemory(String& string)
        void UnloadDocument(ElementDocument* document)
        void UnloadAllDocuments()
        void SetDimensions(Vector2i& dimensions)

cdef extern from "backends/sdl/RocketGlue.hpp":
    Context* RocketInit(SDL_Renderer *renderer, SDL_Window *window)
    void RocketFree(Context *mainCtx)
    PyObject* GetDocumentNamespace(ElementDocument* document)
    void InjectRocket( Context* context, SDL_Event& event )

cdef class Rocket:
    cdef bint released
    cdef Context *rocketCtx
    cdef SDL_Renderer *renderer
    cdef SDL_Window *window

    cdef init(self, SDL_Renderer *renderer, SDL_Window *window)
    cdef free(self)
    cdef update(self)
    cdef render(self)

    cdef void loadFont(self, bytes fontname)
    cdef ElementDocument * loadDocument(self, bytes url)
    cdef unloadDocument(self, ElementDocument *doc)
    cdef void resize(self, int width, int height)
    cdef getDocumentContext(self, ElementDocument *doc)
    cdef PushSDLEvent(self, SDL_Event *event)

cdef class _RocketComponent:
    cdef ElementDocument *doc
    cdef Rocket rocket

    cpdef _loadDocument(self, filename)
    cpdef _unloadDocument(self)
    cpdef loadFont(self, filename)
    cpdef getContext(self)
    cpdef show(self)
    cpdef hide(self)