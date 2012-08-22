#!/usr/bin/env python
#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license


# libRocket Cython wrapper
from libcpp cimport bool
from ignifuga.backends.sdl.SDL cimport *


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
        bool IsModal()
        #virtual void LoadScript(Stream* stream,  String& source_name)
        void UpdateLayout()
        void UpdatePosition()
        void LockLayout(bool lock)

cdef extern from "Rocket/Core/String.h" namespace "Rocket::Core":
    cdef cppclass String:
        String(char* string)

cdef extern from "Rocket/Core/FontDatabase.h" namespace "Rocket::Core::FontDatabase":
    bool LoadFontFace(String& file_name) # static method of Rocket::Core::FontDatabase

cdef extern from "Rocket/Core/Context.h" namespace "Rocket::Core":

    cdef cppclass Context:
        bool Update()
        bool Render()
        ElementDocument* CreateDocument(String& tag)
        ElementDocument* LoadDocument(String& document_path)
        ElementDocument* LoadDocumentFromMemory(String& string)
        void UnloadDocument(ElementDocument* document)
        void UnloadAllDocuments()


cdef extern from "backends/sdl/RocketGlue.hpp":
    Context* initRocket(SDL_Renderer *renderer, SDL_Window *window)
    void stopRocket(Context *mainCtx)

