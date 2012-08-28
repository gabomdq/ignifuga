#!/usr/bin/env python
#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

#if ROCKET

# libRocket Cython wrapper
from ignifuga.backends.sdl.Rocket cimport *
from ignifuga.Log import debug, error
from ignifuga.components.Viewable import Viewable
from ignifuga.backends.sdl.Renderer cimport Renderer
from ignifuga.Gilbert import Gilbert

cdef class Rocket:
    cdef init(self, SDL_Renderer *renderer, SDL_Window *window):
        # Initialize Rocket
        self.released = False
        self.renderer = renderer
        self.window = window

        debug('Starting Rocket')
        self.rocketCtx = RocketInit(self.renderer, self.window)
        debug('Rocket started')

        # These two imports are done here to ensure the Rocket <-> Python bindings are prepared to be used
        # They should NOT be imported elsewhere before than here, after the Rocket core initialization is done
        import _rocketcore
        import _rocketcontrols

    def __dealloc__(self):
        self.free()

    cdef free(self):
        if not self.released:
            RocketFree(self.rocketCtx)
            self.released = True

    cdef update(self):
        self.rocketCtx.Update()

    cdef render(self):
        self.rocketCtx.Render()

    cdef void loadFont(self, bytes fontname):
        LoadFontFace(String(<char*>fontname))

    cdef ElementDocument * loadDocument(self, bytes url):
        cdef ElementDocument *doc = self.rocketCtx.LoadDocument( String(<char*>url) )
        return doc

    cdef unloadDocument(self, ElementDocument *doc):
        self.rocketCtx.UnloadDocument(doc)

    cdef void resize(self, int width, int height):
        self.rocketCtx.SetDimensions(Vector2i(width, height))

    cdef getDocumentContext(self, ElementDocument *doc):
        cdef PyObject *nms = GetDocumentNamespace(doc)
        dnms = <object> nms
        Py_XDECREF(nms)
        return dnms

    cdef PushSDLEvent(self, SDL_Event *event):
        InjectRocket(self.rocketCtx, event[0])

cdef class _RocketComponent:
    """ A Rocket document wrapper"""
    def __init__(self):
        self.doc = NULL
        cdef Renderer renderer = <Renderer>Gilbert().renderer
        self.rocket = renderer.rocket

    cpdef loadDocument(self, filename):
        cdef bytes bFilename = bytes(filename)
        # TODO: Load this through the DataManager and use Rocket's LoadDocumentFromMemory
        self.doc = self.rocket.loadDocument(bFilename)

    cpdef loadFont(self, filename):
        cdef bytes bFilename = bytes(filename)
        self.rocket.loadFont(bFilename)

    cpdef unloadDocument(self):
        if self.doc != NULL:
            self.doc.Close()
            self.doc = NULL

    cpdef getContext(self):
        if self.doc != NULL:
            ctx = self.rocket.getDocumentContext(self.doc)
            return ctx
        return None

    cpdef show(self):
        if self.doc != NULL and not self.doc.IsVisible():
            self.doc.Show(FOCUS)

    cpdef hide(self):
        if self.doc != NULL and self.doc.IsVisible():
            self.doc.Hide()




class RocketComponent(Viewable, _RocketComponent):
    """ A viewable component based on a Rocket document wrapper"""
    PROPERTIES = Viewable.PROPERTIES + []
    def __init__(self, id=None, entity=None, active=True, frequency=15.0,  **data):
        # Default values
        self._loadDefaults({
            'file': None,
            'docCtx': None,
            'fonts': []
        })

        super(RocketComponent, self).__init__(id, entity, active, frequency, **data)
        _RocketComponent.__init__(self)

    def init(self, **data):
        """ Initialize the required external data """
        self.renderer = Gilbert().renderer
        for font in self.fonts:
            self.loadFont(font)

        self.unloadDocument()
        self.loadDocument(self.file)
        Gilbert().dataManager.addListener(self.file, self)
        self.docCtx = self.getContext()
        self.docCtx['parent'] = self
        self.docCtx['gilbert'] = Gilbert()
        self.show()
        super(RocketComponent, self).init(**data)

    def free(self, **kwargs):
        self.hide()
        del self.docCtx['gilbert']
        del self.docCtx['parent']
        self.docCtx = None
        self.unloadDocument()
        Gilbert().dataManager.removeListener(self.file, self)
        super(RocketComponent, self).free(**kwargs)

    def reload(self, url):
        self.unloadDocument()
        self.file = url
        self.loadDocument(self.file)
        if self._visible:
            self.show()

    def update(self, now, **data):
        #STOP()
        return

    @Viewable.visible.setter
    def visible(self, value):
        if value != self._visible:
            self._visible = value
            if self._visible:
                self.show()
            else:
                self.hide()

#endif
