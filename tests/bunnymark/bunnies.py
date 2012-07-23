#!./ignifuga-python
# Ignifuga Game Engine "Bunnymark" benchmark clone - Pure Python version
# Original version: http://blog.iainlobb.com/2010/11/display-list-vs-blitting-results.html
# See http://philippe.elsass.me/2011/11/nme-ready-for-the-show/ for a HaxeNME version
# This code is licensed under MIT License
# Pure Python version

from ignifuga.Gilbert import Gilbert, BACKENDS
from ignifuga.Log import Log, debug
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
        # Add bunnies
        self.gravity = 2
        self.lastBunny = None
        self.firstBunny = None
        self.nBunnies = 0
        self.ft = 0
        self.ftc = 0
        super(Bunnies, self).sceneInit()
        maxx, maxy = Gilbert().renderer.screenSize
        self.size = {'width': maxx, 'height': maxy}
        self.resolution = {'width': maxx, 'height': maxy}
        Gilbert().renderer.scrollTo(0,0)
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
            bunny.x = r.random()*self.size['width']
            bunny.y = self.size['height']
            bunny.speedx = int(r.random()*70.0) - 35
            bunny.speedy = int(r.random()*70.0)
            bunny.angle = 90 - r.random() * 90
            bunny.z = int(r.random()*100)
            bunny.nextBunny = None
            self.lastBunny = bunny
            self.entities[bunny.id] = bunny
            Gilbert().startEntity(bunny)

        self.nBunnies+=num
        fps = self.getComponent("fps")
        if fps != None:
            fps.text = str(self.nBunnies)
        #debug( "BUNNIES %d" % self.nBunnies)

    def update(self, data):
        """ Move bunnies """
        maxx = self.size['width']
        maxy = self.size['height']
        bunny = self.firstBunny
        ft = Gilbert().gameLoop.frame_time

        if ft < Gilbert().gameLoop.ticks_second / 100:
            scene.addBunnies(1500)
        elif ft < Gilbert().gameLoop.ticks_second / 30:
            scene.addBunnies(500)


        while True:
            if bunny._initialized:
                bunny.speedy += self.gravity
                bunny.x += bunny.speedx
                bunny.y += bunny.speedy
                bunny.alpha = 0.3 + 0.7 * bunny.y / maxy
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
                bunny.updateRenderer()

            if bunny.nextBunny:
                bunny = bunny.nextBunny
            else:
                break

def run():
    try:
        Log(0)
        bunnies = Bunnies()
        Gilbert().init(BACKENDS.sdl, bunnies)
    except:
        pass

if __name__ == '__main__':
    from optparse import OptionParser
    parser = Gilbert().parser
    (options, args) = parser.parse_args()

    if options.profile:
        import cProfile, pstats
        profileFileName = 'profile_data.pyprof'
        cProfile.runctx("run()", globals(), locals(), profileFileName)
        pstats.Stats(profileFileName).strip_dirs().sort_stats("time").print_stats()
    else:
        run()