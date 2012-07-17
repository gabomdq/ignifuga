#!./ignifuga-python

from ignifuga.Gilbert import Gilbert, BACKENDS
from ignifuga.Log import Log
from ignifuga.components import *
from ignifuga.Scene import Scene
from ignifuga.Entity import Entity
from _random import Random

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
        # Add bunnies
        self.gravity = 0.5
        self.lastBunny = None
        self.firstBunny = None
        self.nBunnies = 0
        self.ft = 0
        self.ftc = 0
        super(Bunnies, self).sceneInit()
        self.addBunnies()

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
        for x in range(0,num):
            bunny = Entity.create(id = 'bunny %d' % x, scene=self, **data)
            if self.firstBunny is None:
                self.firstBunny = bunny
            if self.lastBunny is not None:
                self.lastBunny.nextBunny = bunny
            bunny.speedx = (0.01+r.random())*50.0
            bunny.speedy = (0.01+r.random())*50.0
            bunny.angle = 90 - r.random() * 90
            bunny.z = int(r.random()*100)
            bunny.nextBunny = None
            self.lastBunny = bunny
            self.entities[bunny.id] = bunny
            Gilbert().startEntity(bunny)

        self.nBunnies+=num
        print "BUNNIES", self.nBunnies

    def update(self, data):
        """ Move bunnies """
        maxx = self.size['width']
        maxy = self.size['height']
        bunny = self.firstBunny
        ft = Gilbert().gameLoop.frame_time

        self.ft += ft
        self.ftc += 1
        if self.ftc > 10:
            if self.ft < 320:
                self.addBunnies(100)
            elif self.ft > 360:
                counter = 0
                while counter < 50:
                    bunny.unregister()
                    self.nBunnies-=1
                    if bunny.nextBunny:
                        bunny = bunny.nextBunny
                        self.firstBunny = bunny
                    else:
                        break
                    counter +=1

                print "BUNNIES", self.nBunnies

            self.ft = 0
            self.ftc = 0


        while True:
            if bunny._initialized:
                bunny.x += bunny.speedx
                bunny.y += bunny.speedy
                bunny.speedy += self.gravity
                #bunny.alpha = 0.3 + 0.7 * bunny.y / maxy
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
                    bunny.speedy = -bunny.speedy
                bunny.updateRenderer()

            if bunny.nextBunny:
                bunny = bunny.nextBunny
            else:
                break

def run():
    #try:
        Log(0)
        bunnies = Bunnies()
        Gilbert().init(BACKENDS.sdl, bunnies)
#    except:
#        pass

if __name__ == '__main__':
    run()
