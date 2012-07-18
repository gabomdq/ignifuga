#!./ignifuga-python
# Ignifuga Game Engine "Bunnymark" benchmark clone - Cython version
# Original version: http://blog.iainlobb.com/2010/11/display-list-vs-blitting-results.html
# See http://philippe.elsass.me/2011/11/nme-ready-for-the-show/ for a HaxeNME version
# This code is licensed under MIT License

from ignifuga.Gilbert import Gilbert, BACKENDS
from ignifuga.Log import Log, debug
from ignifuga.components import *
from ignifuga.Scene import Scene
from ignifuga.Entity import Entity
from ignifuga.backends.sdl.Renderer cimport Renderer, Sprite_p, Sprite as RSprite
from ignifuga.backends.sdl.GameLoop cimport GameLoop
from ignifuga.backends.sdl.SDL cimport Uint8

from _random import Random

from libc.stdlib cimport *
from libc.string cimport *
from libcpp.map cimport *
from libcpp.deque cimport *
from libcpp.pair cimport *
from cython.operator cimport dereference as deref, preincrement as inc #dereference and increment operators

# cython: boundscheck=False
# cython: wraparound=False

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

cdef _update(scene):
    global bunnies, maxx, maxy
    cdef int gravity = 2, ft
    cdef bunnies_iterator iter = bunnies.begin()
    cdef _Bunny_p bunny
    cdef Renderer renderer = scene.renderer
    cdef GameLoop gameLoop = scene.gameLoop


    ft = gameLoop.frame_time
    if ft < 10:
        scene.addBunnies(1500)
    elif ft < 33:
        scene.addBunnies(500)

    while iter != bunnies.end():
        bunny = &deref(iter)
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
        renderer._spriteRot(bunny.sprite, bunny.angle, bunny.cx,bunny.cy, 0)
        renderer._spriteColor(bunny.sprite, bunny.r, bunny.g, bunny.b, bunny.a)
        inc(iter)


class Bunnies(Scene):
    def __init__(self,**data):
        data = {"resolution":{
                    "width":1920,
                    "height":1200
                },
                "keepAspect":True,
                "autoCenter": True,
                "size":{
                    "width":1920,
                    "height":1200
                }
        }
        super(Bunnies, self).__init__(**data)


    def sceneInit(self):
        global maxx, maxy
        # Add bunnies
        self.nBunnies = 0
        self.ft = 0
        self.ftc = 0
        self.bunnies = []
        super(Bunnies, self).sceneInit()
        init()
        self.addBunnies()
        maxx = self.size['width']
        maxy = self.size['height']
        self.renderer = Gilbert().renderer
        self.gameLoop = Gilbert().gameLoop

    def addBunnies(self, num=500):
        data = {"components":[
                {
                "type":"Sprite",
                "file":u"images/wabbit_alpha.png",
                "x": 0,
                "y": 0
            },
        ]}
        r = Random()
        debug(" ADDING %d BUNNIES" % num)
        for x in range(0,num):
            sprite_id = 'bunny_sprite %d' % self.nBunnies
            data['components'][0]['id'] = sprite_id
            bunny = Entity.create(id = 'bunny %d' % self.nBunnies, scene=self, **data)
            bunny.x = r.random()*self.size['width']
            bunny.y = self.size['height']
            bunny.speedx = int(r.random()*70.0) - 35
            bunny.speedy = int(r.random()*70.0)
            bunny.angle = 90 - r.random() * 90
            bunny.z = int(r.random()*100)
            self.entities[bunny.id] = bunny
            self.bunnies.append(bunny)
            Gilbert().startEntity(bunny)
            self.nBunnies+=1
        debug(" ADDED BUNNIES. TOTAL: %d" % self.nBunnies)

    def update(self, data):
        """ Move bunnies """
        for bunny in self.bunnies:
            if bunny._components:
                sprite = bunny._components.values()[0]
                if hasattr(sprite, '_rendererSpriteId') and sprite._rendererSpriteId != None:
                    sprite.speedx = bunny.speedx
                    sprite.speedy = bunny.speedy
                    _addBunny(sprite)
                    self.bunnies.remove(bunny)

        _update(self)




def run():
    #try:
        Log(0)
        bunnies = Bunnies()
        Gilbert().init(BACKENDS.sdl, bunnies)
#    except:
#        pass

if __name__ == '__main__':
    run()
