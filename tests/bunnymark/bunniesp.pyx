#!./ignifuga-python
# Ignifuga Game Engine "Bunnymark" benchmark clone - Cython Parallel Execution version
# Original version: http://blog.iainlobb.com/2010/11/display-list-vs-blitting-results.html
# See http://philippe.elsass.me/2011/11/nme-ready-for-the-show/ for a HaxeNME version
# This code is licensed under MIT License
# Cython - OpenMP optimized version

from ignifuga.Gilbert import Gilbert, BACKENDS
from ignifuga.Log import Log, debug
from ignifuga.components import *
from ignifuga.Scene import Scene
from ignifuga.Entity import Entity
from ignifuga.backends.sdl.Renderer cimport Renderer, Sprite_p, Sprite as RSprite
from ignifuga.backends.sdl.GameLoop cimport GameLoop
from ignifuga.backends.sdl.SDL cimport Uint8
from cython.parallel cimport parallel, prange
cimport cython

from _random import Random

from libc.stdlib cimport *
from libc.string cimport *
from libcpp.map cimport *
from libcpp.deque cimport *
from libcpp.pair cimport *
from cython.operator cimport dereference as deref, preincrement as inc #dereference and increment operators

# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True


cdef struct _Bunny:
    Sprite_p sprite
    int x, y
    int speedx, speedy
    int w,h
    int cx, cy
    double angle
    Uint8 r,g,b,a

ctypedef _Bunny* _Bunny_p

cdef deque[_Bunny] *bunnies = new deque[_Bunny]()
ctypedef deque[_Bunny].iterator bunnies_iterator

cdef int maxx, maxy

cdef init():
    pass


cdef _addBunny(bunny):
    global bunnies
    cdef _Bunny _bunny
    cdef RSprite rs
    if bunny._rendererSpriteId != None:
        _bunny.x = bunny.x
        _bunny.y = bunny.y
        _bunny.speedx = bunny.speedx
        _bunny.speedy = bunny.speedy
        _bunny.w = bunny.width
        _bunny.h = bunny.height
        _bunny.cx = _bunny.w / 2
        _bunny.cy = _bunny.h / 2
        _bunny.angle = bunny.angle
        r = bunny.red*255.0
        g = bunny.green*255.0
        b = bunny.blue*255.0
        a = bunny.alpha*255.0
        _bunny.r = <Uint8> r
        _bunny.g = <Uint8> g
        _bunny.b = <Uint8> b
        _bunny.a = <Uint8> a
        rs = <RSprite>bunny._rendererSpriteId
        _bunny.sprite = rs.sprite
        bunnies.push_back(_bunny)

@cython.cdivision(True)
cdef void _processBunny(Renderer renderer, _Bunny_p bunny) nogil:
    cdef int gravity = 2
    bunny.speedy += gravity
    bunny.x += bunny.speedx
    bunny.y += bunny.speedy
    bunny.a = 76 + 178 * bunny.y / maxy
    if bunny.x > maxx:
        bunny.x = maxx
        bunny.speedx = -bunny.speedx
    elif bunny.x <= 0:
        bunny.x = 0
        bunny.speedx = -bunny.speedx
    if bunny.y > maxy:
        bunny.y = maxy
        bunny.speedy = -bunny.speedy
    elif bunny.y <= 0:
        bunny.y = 0
        bunny.speedy = 0

    renderer._spriteDst(bunny.sprite, bunny.x, bunny.y, bunny.w, bunny.h)
    #renderer._spriteRot(bunny.sprite, bunny.angle, bunny.cx,bunny.cy, 0)
    renderer._spriteColor(bunny.sprite, bunny.r, bunny.g, bunny.b, bunny.a)

cdef _update(scene):
    global bunnies, maxx, maxy, num_threads, bunny_t, num_threads
    cdef int i, tid, new_bunnies, ft
    cdef bunnies_iterator iter = bunnies.begin()
    cdef Renderer renderer = scene.renderer
    cdef GameLoop gameLoop = scene.gameLoop

    ft = gameLoop.frame_time
    if ft < gameLoop.ticks_second / 30:
        scene.addBunnies+=100


    for i in prange(bunnies.size(), nogil=True):
        _processBunny(renderer, &bunnies.at(i))

class Bunnies(Scene):
    def __init__(self,**data):
        data = {"resolution":{
                    "width":1920,
                    "height":1200
                },
                "keepAspect":True,
                "autoScale": False,
                "autoCenter": True,
                "size":{
                    "width":1920,
                    "height":1200
                },
                "components":[
                     {
                        "id": "fps",
                        "type":"Text",
                        "font": u"images/teenbold.ttf",
                        "htmlColor": u"#ffffff",
                        "text":u"0",
                        "size": 48,
                        "x": 0,
                        "y": 0,
                        "z": 1000
                    }
                ]
        }
        super(Bunnies, self).__init__(**data)


    def sceneInit(self):
        global maxx, maxy
        maxx, maxy = Gilbert().renderer.screenSize
        # Add bunnies
        self.nBunnies = 0
        self.ft = 0
        self.ftc = 0
        self.addBunnies = 500
        init()
        self.size = {'width': maxx, 'height': maxy}
        self.resolution = {'width': maxx, 'height': maxy}
        self.renderer = Gilbert().renderer
        self.gameLoop = Gilbert().gameLoop
        super(Bunnies, self).sceneInit()

        data = {"components":[
                {
                "type":"Sprite",
                "file":u"images/wabbit_alpha.png",
                "x": 0,
                "y": 0
            },
        ]}

        self.bunny = Entity.create(id = 'bunny %d' % self.nBunnies, scene=self, **data)
        self.entities[self.bunny.id] = self.bunny
        Gilbert().startEntity(self.bunny)
        fps = self.getComponent("fps")
        if fps != None:
            fps.text = str(self.nBunnies)
        self.renderer.scrollTo(0,0)

    def update(self, data):
        """ Move bunnies """
        addedBunnies = 0
        if self.addBunnies > 0:
            r = Random()
            for x in range(0, self.addBunnies):
                if self.bunny._components:
                    sprite = self.bunny._components.values()[0]
                    if hasattr(sprite, '_rendererSpriteId') and sprite._rendererSpriteId != None:
                        self.bunny.x = r.random()*self.size['width']
                        self.bunny.y = self.size['height']
                        self.bunny.speedx = int(r.random()*70.0) - 35
                        self.bunny.speedy = int(r.random()*70.0)
                        self.bunny.angle = 90 - r.random() * 90
                        self.bunny.z = 0
                        sprite.speedx = self.bunny.speedx
                        sprite.speedy = self.bunny.speedy
                        _addBunny(sprite)
                        sprite._rendererSpriteId = None
                        sprite.show()
                        addedBunnies +=1

            self.addBunnies -= addedBunnies
            self.nBunnies += addedBunnies
            fps = self.getComponent("fps")
            if fps != None:
                fps.text = str(self.nBunnies)

        _update(self)




def run():
    #try:
        Log(0)
        bunnies = Bunnies()
        Gilbert().init(BACKENDS.sdl, bunnies)
#    except:
#        pass

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-p", "--profile", action="store_true", dest="profile", default=False,help="Do a profile")
    (options, args) = parser.parse_args()

    if options.profile:
        import cProfile, pstats
        profileFileName = 'profile_data.pyprof'
        cProfile.runctx("run()", globals(), locals(), profileFileName)
        pstats.Stats(profileFileName).strip_dirs().sort_stats("time").print_stats()
    else:
        run()