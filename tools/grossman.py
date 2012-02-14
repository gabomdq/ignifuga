#!/usr/bin/env python
#Copyright (c) 2010,2011, Gabriel Jacobo
#All rights reserved.

#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions are met:

    #* Redistributions of source code must retain the above copyright
      #notice, this list of conditions and the following disclaimer.
    #* Redistributions in binary form must reproduce the above copyright
      #notice, this list of conditions and the following disclaimer in the
      #documentation and/or other materials provided with the distribution.
    #* Altered source versions must be plainly marked as such, and must not be
      #misrepresented as being the original software.
    #* Neither the name of Gabriel Jacobo, MDQ Incorporeo, Ignifuga Game Engine
      #nor the names of its contributors may be used to endorse or promote
      #products derived from this software without specific prior written permission.
    #* You must NOT, under ANY CIRCUMSTANCES, remove, modify or alter in any way
      #the duration, code functionality and graphic or audio material related to
      #the "splash screen", which should always be the first screen shown by the
      #derived work and which should ALWAYS state the Ignifuga Game Engine name,
      #original author's URL and company logo.

#THIS LICENSE AGREEMENT WILL AUTOMATICALLY TERMINATE UPON A MATERIAL BREACH OF ITS
#TERMS AND CONDITIONS

#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL GABRIEL JACOBO NOR MDQ INCORPOREO NOR THE CONTRIBUTORS
#BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Grossman - The Ignifuga Game Engine Sprite conversion utility
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

# For the sprite format see Sprite.py



import Image, ImageColor, ImageChops, ImageDraw
from PIL import PngImagePlugin
import os, fnmatch, json, math
from optparse import OptionParser
import numpy as np
import scipy as sp
import scipy.ndimage.morphology
import bitarray, base64, zlib

class NoFilesFound(Exception):
    pass

class InvalidHeightWidth(Exception):
    pass

class Grossman:
    def __init__(self, files, output, width=None, height=None, compress=None, verbose=True, singleMode=False):
        self.files = []
        self.output = output
        self.compress = compress
        self.width = width
        self.height = height
        self.verbose = verbose
        self.fitfactor = 2.5
        self.fitmethod = 'slow'
        self.drawBoxes = False
        self.savediff = False
        self.groupFactor = 5
        self.keyframes = 0
        
        nf = len(files)
        if nf == 0:
            # No files, error
            raise NoFilesFound()
        elif nf > 1:
            # Multiple files provided
            self.files = files
            self.singleMode = False
        else:
            # One file name provided, check if it is a regexp
            self.singleMode = singleMode
            self.cwd = os.path.dirname(files[0])
            if self.cwd == '':
                self.cwd = '.'
            regexp = os.path.basename(files[0])
            for file in os.listdir(self.cwd):
                if fnmatch.fnmatch(file, regexp) and os.path.isfile(file):
                    self.files.append(file)
            
            if len(self.files) == 0:
                raise NoFilesFound()
            elif len(self.files) > 1:
                self.singleMode = False
                
        if self.singleMode and (self.width == None or self.height == None):
            raise InvalidHeightWidth()
        
        self.files.sort()
        
    def convert(self, chroma=None):
        """ Process the files into a single sprite """
        images = []
        base = None
        dest = []
        keyframes = [0,]
        lastKeyframe = 0
        hitmaps = []
    
        if self.singleMode:
            imagetmp = Image.open(self.files[0])
            image = imagetmp.convert("RGBA")
            if chroma != None:
                self.processChroma(image, chroma)
            del imagetmp
            
            # Cut up the image, figure out how many rows, columns in the image
            w,h = image.size
            cols = w/self.width
            rows = h/self.height
            
            # Go over the image, cutting from top to bottom, left to right
            for y in range(0, rows):
                for x in range(0, cols):
                    box = (x*self.width, y*self.height, (1+x) * self.width, (1+y) * self.height)
                    i = Image.new("RGBA", (self.width, self.height))
                    i.paste(image.crop(box))
                    images.append(i)
            # Free some memory
            del image
        else:
            # Open all images
            for file in self.files:
                imagetmp = Image.open(file)
                image = imagetmp.convert("RGBA")
                del imagetmp
                if chroma != None:
                    self.processChroma(image, chroma)
                images.append(image)

            # Determine the output width and height
            self.width, self.height = images[0].size

            
        self.report('Creating sprite with dimensions %dx%d px' % (self.width, self.height))
        
        # Create base image
        base = images[0]
        # Enter the first base image into the destination list
        box = (0,0,self.width, self.height)
        dest.append( ({
            'image': base.copy(),
            'box': box
        },))
        
        self.report('Creating hitmap for image')
        hitmaps.append(self.createHitmap(base))
        
        basearea = float(self.width*self.height)
        totalarea = basearea
        
        # Start processing the rest of the images
        if len(images) > 1:
            imcount = 1
            for image in images[1:]:
                if not self.singleMode:
                    self.report('Processing %s' % (self.files[imcount]))
                    
                self.report('Creating hitmap for image')
                hitmaps.append(self.createHitmap(image))
                
                if self.compress != None:
                    if self.keyframes > 0 and lastKeyframe+self.keyframes == imcount:
                        # This is a keyframe. Enter the image in full with no compression)
                        lastKeyframe = imcount
                        keyframes.append(imcount)
                        
                        base = image
                        box = (0,0,self.width, self.height)
                        dest.append( ({
                            'image': base.copy(),
                            'box': box
                        },))
                    else:
                        # Do compression, compare new image against the base
                        diff = ImageChops.difference(base, image)
                        #base.save(self.files[imcount]+'.base.png', "PNG")
                        #image.save(self.files[imcount]+'.image.png', "PNG")
                        if self.compress == 'deltap':
                            # In deltap mode we compare against the previous frame always
                            # In deltak mode we compare against the keyframe (which is changed elsewhere)
                            base = image
                            
                        rects = self.findBoxes(diff)
                        
                        # Calculate total area
                        area = 0
                        for r in rects:
                            area += (r[2]*r[3])
                        totalarea += area
                        
                        self.report('Found %d changed regions, area changed is %d px, (%.01f%% of total)' % (len(rects), area, area*100.0/basearea) )
                        frame = []
                        for r in rects:
                            cr = (r[0], r[1], r[0]+r[2], r[1]+r[3])
                            i = image.crop(cr)
                            frame.append({
                                'image': i,
                                'box': r
                            })
                        dest.append(frame)
                        
                        if self.savediff:
                            d = ImageDraw.Draw(diff)
                            for region in frame:
                                r = region['box']
                                d.rectangle( [r[0], r[1], r[0]+r[2], r[1]+r[3] ], outline='#FF0000')
                                
                            diff.convert('RGB').save(self.files[imcount]+'.diff.png', "PNG")
                            del d
                            
                        del diff
                else:
                    dest.append( ({
                        'image': image,
                        'box': box
                    },))
                    
                imcount+=1
        self.report('Sprite has %d frames' % (len(dest),))
        

        # Consolidate all dest images into a single image
        target = None
        if self.compress != None:
            cr = float(totalarea) / (float(basearea)*len(images))
            self.report('Idealized compression rate: %.01f%%' % (cr * 100.0))
            
            factor = self.fitfactor
            complete = True
            
            while True:
                
                tw = int(math.sqrt(totalarea)*factor*cr)
                #th = int(self.height*factor*cr)
                th =tw
                target = Image.new("RGBA", (tw, th))
                
                if self.fitmethod == 'fast':
                    rects = (0,0, tw, th)
                else:
                    rects = [(0,0, tw, th),]
                
                frames = list()
                for frame in dest:
                    #print frame
                    boxes = list()
                    for part in frame:
                        image = part['image']
                        box = part['box']
                        # Find a place in the image where we can paste this piece of image
                        if self.fitmethod == 'fast':
                            rects, r, a = self.walkRectBinary(rects, box[2], box[3])
                        else:
                            rects, r, a = self.walkRectSlow(rects, box[2], box[3])
                            
                        if r == None:
                            # Do something here!
                            del target
                            factor += 0.5
                            self.report('Retrying fit with a factor: %f' % (factor))
                            complete = False
                            break
                        
                        target.paste(image, (r[0], r[1]))
                        if self.drawBoxes:
                            d = ImageDraw.Draw(target)
                            d.rectangle( [r[0], r[1], r[0]+r[2], r[1]+r[3] ], outline='#0000FF')
                            del d

                        # Format is src_x, src_y, dst_x, dst_y, w, h
                        # src is the big consolidated target image we are building
                        # dst is the sprite rendered
                        # w,h are the same for src,dst so we store it once
                        
                        boxes.append( (r[0], r[1], box[0], box[1], box[2], box[3]))
                    #print boxes
                    frames.append(boxes)
                    if not complete:
                        break
                if complete:
                    break
                complete = True
            
            if self.drawBoxes:
                d = ImageDraw.Draw(target)
                for r in rects:
                    if r[2] >0 and r[3] > 0:
                        d.rectangle( [r[0], r[1], r[0]+r[2], r[1]+r[3] ], outline='#FF0000')
                del d
                
            w,h = target.size
            self.report('Pixel area compressed to: %.01f%%' % (w*h*100.0/(float(basearea)*len(images))))
        else:
            # No compression, no fitting required, and one image per frame
            frames = list()
            tw, th = self.getOptimalSize(self.width, self.height, len(dest))
            print "Saving to an Atlas of %dx%d %d rows %d columns" % (tw,th, tw/self.width, th/self.height)
            target = Image.new("RGBA", (tw, th))
            offset_x, offset_y = 0,0
            for frame in dest:
                boxes = []
                for part in frame:
                    image = part['image']
                    box = part['box']
                    target.paste(image, (offset_x, offset_y))
                    boxes.append( (offset_x, offset_y, box[0], box[1], box[2], box[3]))
                    offset_x+=box[2]
                    if offset_x >= tw:
                        offset_x = 0
                        offset_y += box[3]
                frames.append(boxes)


        jsondata = { 'type': self.compress if self.compress != None else 'atlas', 'frames': frames, 'hitmap': hitmaps, 'keyframes': keyframes }
        #json.dump(jsondata, fp, indent=2)

        #target.convert('RGB').save(self.output+'.rgb.png', "PNG")
#        fp = open(self.output + '.sprite', 'w')
#        fp.close()

        # Add the sprite data as a zTXT chunk
        meta = PngImagePlugin.PngInfo()
        meta.add_text("SPRITE", json.dumps(jsondata), 1)
        target.save(self.output, "PNG", pnginfo=meta)
    
    def createHitmap (self, im):
        r,g,b,a = im.split()
        # Traverse the alpha map
        alpha = a.getdata()
        hitmap = bitarray.bitarray(len(alpha))
        
        for k in range(0, len(alpha)):
            if alpha[k] == 0:
                hitmap[k] = 0
            else:
                hitmap[k] = 1
                
                
        #return base64.b64encode(zlib.compress(hitmap.tostring()))
        return base64.b64encode(hitmap.tostring())
        
    def getOptimalSize(self, iw, ih, num):
        """ Get the optimal texture size for a num of iw x ih sprites"""
        pow2 = [16,32,64,128,256,512,1024,2048]
        # Iterate over all the combinations, find the smallest area that fits
        tw = th = 2048
        tc = tw/iw
        tr = th/ih
        area = tw*th
        targetarea = iw*ih
        
        for w in pow2:
            for h in pow2:
                newarea = w*h
                if newarea > targetarea:
                    cols = math.ceil(w/iw)
                    rows = math.ceil(h/ih)
                    if cols*rows >=num and newarea < area:
                        area = newarea
                        tw=w
                        th=h
                        tc = cols
                        tr = rows
        tc = math.ceil(tc)
        return int(tc*iw), int(math.ceil(num/tc)*ih)
        
    def walkRectBinary(self, rects, width, height):
        """ Walk a binary rect until we find a rect of the appropriate size to hold w x h """
        if len(rects) == 4:
            # rects is a rect in format (x,y,w,h)
            if width <= rects[2] and height <= rects[3]:
                # Split up the rects, the first one is the one requested
                r = (rects[0], rects[1], width, height)
                # Horizontal square
                rf1 = (rects[0]+width, rects[1], rects[2]-width , height)
                # Vertical free square
                rf2 = (rects[0], rects[1]+height, rects[2], rects[3]-height)
                return [rf1,rf2],r, rects[2]*rects[3]
            else:
                return rects, None, 0
        elif len(rects) == 2:
            # rects holds two rects
            rs1, r1, a1 = self.walkRectBinary(rects[0], width, height)
            if r1 != None:
                return [rs1, rects[1]], r1,a1
            
            rs2, r2, a2 = self.walkRectBinary(rects[1], width, height)
            if r2 != None:
                rects[1] = rs2
                return [rects[0], rs2], r2, a2
        return rects, None, 0
    
    def walkRectSlow(self, rects, width, height):
        """ Find a suitable rect to place widthxheight, alternative method (slower, more space efficient)
            rects are [(x,y,w,h), (x,y,w,h)]
        """
        #print 'free rects ', len(rects)
        best_rect = None
        best_area = None
        
        # Find the best fitting, smallest rectangle
        for r in rects:
            if width <= r[2] and height <= r[3]:
                area = r[2]*r[3]
                if best_area == None or best_area > area:
                    best_rect = r
                    best_area = area
        
        if best_rect != None:
            # Split the rectangle
            dest_rect = (best_rect[0], best_rect[1], width, height)
            # Horizontal square
            rf1 = (best_rect[0]+width, best_rect[1], best_rect[2]-width , best_rect[3])
            # Vertical free square
            rf2 = (best_rect[0], best_rect[1]+height, best_rect[2], best_rect[3]-height)
            
            rects.remove(best_rect)
            if rf1[2] > 0 and rf1[3] > 0:
                rects.append(rf1)
            if rf2[2] > 0 and rf2[3] > 0:
                rects.append(rf2)
            
            # Now go over all the existing rects and see that our new rectangle doesnt interfere, if it does, split
            tmprects = rects[:]
            for r in tmprects:
                left = max((r[0], dest_rect[0]))
                top = max((r[1], dest_rect[1]))
                right = min((r[0]+r[2], dest_rect[0]+dest_rect[2]))
                bottom = min((r[1]+r[3], dest_rect[1]+dest_rect[3]))
                if left < right and top < bottom:
                    # The rectangles interfere, split r in 4
                    rf1 = (r[0], r[1], left-r[0], r[3])
                    rf2 = (right, r[1], r[0]+r[2]-right, r[3])
                    rf3 = (r[0], r[1], r[2], top-r[1])
                    rf4 = (r[0], bottom, r[2], r[1]+r[3]-bottom)
                    
                    rects.remove(r)
                    if rf1[2] > 0 and rf1[3] > 0:
                        rects.append(rf1)
                    if rf2[2] > 0 and rf2[3] > 0:
                        rects.append(rf2)
                    if rf3[2] > 0 and rf3[3] > 0:
                        rects.append(rf3)
                    if rf4[2] > 0 and rf4[3] > 0:
                        rects.append(rf4)
                        

            # Try to merge free rectangles
            outrects = []
            while len(rects) > 0:
                ra = rects.pop()
                skip = False
                tmprects = rects[:]
                for rb in tmprects:
                    # See if ra is fully inside rb
                    if ra[0] >= rb[0] and ra[1] >= rb[1] and ra[0]+ra[2] <= rb[0]+rb[2] and ra[1]+ra[3] <= rb[1]+rb[3]:
                        # Skip this sucker
                        skip = True
                        break
                    # See if they are contiguous
                    elif ra[0] == rb[0] and ra[2] == rb[2]:
                        # Combine them
                        t = min(ra[1], rb[1])
                        h = max(ra[1]+ra[3],rb[1]+rb[3]) - t
                        if height <= ra[3] + rb[3]:
                            ra = (ra[0],t, ra[2], h )
                            rects.remove(rb)
                    elif ra[1] == rb[1] and ra[3] == rb[3]:
                        l = min(ra[0], rb[0])
                        w = max(ra[0]+ra[2],rb[0]+rb[2]) - l
                        if w <= ra[2] + rb[2]:
                            ra = (l,ra[1], w, ra[3] )
                            rects.remove(rb)
                if not skip:
                    outrects.append(ra)

            # do a final check on overlapping, as it seems we might under corner cases overlap dest_rects and free areas (probably due to rf3)
            rects = []
            #print 'pre', len(outrects)
            while len(outrects) > 0:
                r = outrects.pop(0)
                left = max((r[0], dest_rect[0]))
                top = max((r[1], dest_rect[1]))
                right = min((r[0]+r[2], dest_rect[0]+dest_rect[2]))
                bottom = min((r[1]+r[3], dest_rect[1]+dest_rect[3]))
                #print left,top,right, bottom
                if left >= right or top >= bottom:
                    # Free are doesnt overlap dest_area, keep it
                    rects.append(r)
                    
            #print 'post', rects
            #rects=outrects
            return rects, dest_rect, best_area
            
        return rects, None, 0

        
    def processChroma(self, image, chroma):
        """ Change the color chroma in an image for alpha:1 """
        datas = image.getdata()
        newData = list()
        for item in datas:
            if item == chroma:
                newData.append((chroma[0], chroma[1], chroma[2], 0))
            else:
                newData.append(item)
        image.putdata(newData)
        
    def findBoxes(self, image):
        """ Fin non zero regions in an image """
        datas = image.getdata()
        diff = []
        w,h = image.size
        i = iter(datas)
        # Convert the image to a true/false array where one means pixels exist
        for y in range (h):
            line = []
            for x in range (w):
                item = i.next()
                if item == (0,0,0,0):
                    line.append(0)
                else:
                    line.append(1)
            diff.append(line)

        # Crudely find square zones in the data
        rects = []
        filled = sp.ndimage.morphology.binary_fill_holes(diff)
        objects, num_objects = sp.ndimage.label(filled)

        for ndx in range(num_objects):
            rects.append((self.width+1,self.height+1,0,0))

        # Separate the rects ndimage found
        for y in range (h):
            for x in range (w):
                ndx = objects[y][x]
                if ndx > 0:
                    ndx-=1
                    x1,y1,x2,y2 = rects[ndx]
                    if x < x1:
                        x1 = x
                    if y < y1:
                        y1 = y
                    if x >= x2:
                        x2 = x+1
                    if y >= y2:
                        y2 = y+1
                    rects[ndx] = (x1,y1,x2,y2)

        # Convert rects to x, y, w, h
        for ndx in range(num_objects):
            x1,y1,x2,y2 = rects[ndx]
            rects[ndx] = (x1,y1, x2-x1, y2-y1)
            
        #print 'found', len(rects)
        return self.clearRects(rects)
    
    def clearRects(self, rects = []):
        """ Take a list of rects (x,y, w, h) and combine it so they don't have overlapping zones """
        out = []
        nrects = len(rects)
        if nrects < 2:
            return rects
        ra = rects.pop()
        while True:
            found = False
            # Add a grouping factor to aglutinate non overlapping but close by rectangles (rect increases by 2xgroupFactor)
            rc = (ra[0]-self.groupFactor, ra[1]-self.groupFactor, ra[2]+self.groupFactor*2, ra[3]+self.groupFactor*2)
            for rb in rects:
                if ra!=rb:
                    # Different rectangles
                    left = max((rc[0], rb[0]))
                    top = max((rc[1], rb[1]))
                    right = min((rc[0]+rc[2], rb[0]+rb[2]))
                    bottom = min((rc[1]+rc[3], rb[1]+rb[3]))
                    if left < right and top < bottom:
                        found = True
                        # There's some intersection, unite them
                        left = min((ra[0], rb[0]))
                        top = min((ra[1], rb[1]))
                        right = max((ra[0]+ra[2], rb[0]+rb[2]))
                        bottom = max((ra[1]+ra[3], rb[1]+rb[3]))
                        # Append this new rectangle and recheck everything from the top
                        rects.remove(rb)
                        rects.append((left, top, right-left, bottom-top))
                        break
                    
            if not found:
                # No intersection found, pass the rectangle out as it came
                out.append(ra)
            
            if len(rects) == 0:
                break
            ra = rects.pop()

        #print out
        #print nrects, len(out)
        #if nrects != len(out):
        #    # We did some cleaning, but clean it again to see if we can further reduce the rect count
        #    
        #    return self.clearRects(out)
        #else:
        #    return out
                
        return out
    
    def report(self, msg):
        if self.verbose:
            print msg
        
if __name__ == '__main__':
    usage = "grossman.py files --output=spritename.png"
    parser = OptionParser(usage=usage, version="Grossman - Sprite conversion utility 1.0")
    parser.add_option("-o", "--output", dest="output",
                  help="Generate sprite with given name", metavar="FILE")
    parser.add_option("--width", dest="width", default=None, type="int",
                  help="Width of sprite (required for single file mode)")
    parser.add_option("--height", dest="height", default=None, type="int",
                  help="Height of sprite (required for single file mode)")
    parser.add_option("-q", "--quiet",
                  action="store_false", dest="verbose", default=True,
                  help="don't print status messages to stdout")
#    parser.add_option("--deltak",
#                  action="store_true", dest="deltak", default=False,
#                  help="Use difference against previous keyframe compression")
    parser.add_option("--deltap",
                  action="store_true", dest="deltap", default=False,
                  help="Use difference against previous frame compression")
    parser.add_option("-k", "--keyframes",
                  action="store_true", dest="keyframes", default=0,
                  help="Number of frames between each keyframe")
    parser.add_option("-d", "--boxes",
                  action="store_true", dest="boxes", default=False,
                  help="Draw boxes around the sprites")
    parser.add_option("--chroma", dest="chroma", default=None,
                      help="Chroma Key Color (accepts html codes, rgb or hsl functions)")
    parser.add_option("--fitmethod", dest="fitmethod", default='slow',
                      help="Fit method, slow or fast")
    parser.add_option("--fitfactor", dest="fitfactor", default=1.1, type='float',
                      help="Fit factor, default: 1.1")
    parser.add_option("--groupfactor", dest="groupfactor", default=5.0, type='float',
                      help="Grouping factor, default: 5.0")
    parser.add_option("--savediff",
                  action="store_true", dest="savediff", default=False,
                  help="Save the inter frame differences as images")
    parser.add_option("--single",
        action="store_true", dest="singleMode", default=False,
        help="Take all sprites from a single image. Requires --width and --height")
    
    (options, args) = parser.parse_args()

    if len(args) < 1 or options.output is None:
        parser.print_help()
        exit()
    
    if options.deltap:
        compress = 'deltap'
    elif options.deltak:
        compress = 'deltak'
    else:
        compress = None
    
    
    try:    
        t = Grossman(args, options.output, options.width, options.height, compress, options.verbose, options.singleMode)
    except NoFilesFound:
        print "ERROR: No input files found\n"
        parser.print_help()
        exit()
    except InvalidHeightWidth:
        print "ERROR: With a single input file, you have to provide both width and height of destination sprite"
        parser.print_help()
        exit()
        
    chroma = None
    if options.chroma != None:
        chroma = ImageColor.getrgb(options.chroma)
        chroma = chroma + (255,)

    t.fitmethod = options.fitmethod
    t.fitfactor = options.fitfactor
    t.drawBoxes = options.boxes
    t.savediff = options.savediff
    t.groupFactor = options.groupfactor
    t.keyframes = options.keyframes
    t.convert(chroma)
    