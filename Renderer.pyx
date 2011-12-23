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

# Ignifuga Game Engine
# Main Renderer
# Backends available: SDL
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.Gilbert import BACKENDS, Gilbert
from ignifuga.Log import Log, debug

from ignifuga.Singleton import Singleton
from ignifuga.Rect cimport Rect

from time import time as getTime
import sys

cdef class Renderer:
    def __init__(self, target):
        self.frameTimestamp = 0.0 # seconds since epoch
        self.frameLapse = 0.0 # Time it takes to render a frame
        self.nativeResolution = (None, None)
        self._scale_x = 1.0
        self._scale_y = 1.0
        self._target = None
        self._scroll_x = 0
        self._scroll_y = 0
        
        self.reset()
        self._target = target
        self.dirtyAll()

    #cpdef update(self):
        #""" Update the screen by rendering the nodes that intersect the dirty rectangles """
        #cdef Rect nr, ir, r
        #cdef int z
        
        #if self.frameTimestamp == 0.0:
            #raise Exception ('You have to call preUpdate before calling update')

        #if self._target.isDoubleBuffered:
            ## Double buffered systems force us to draw all the screen in every frame as there's no delta updating possible.
            #self.dirtyAll()

        ## In the following, screen coordinates refers to a set of coordinates that start in 0,0 and go to (screen width-1, screen height-1)
        ## Scene coordinates are the logical node coordinates, which relate to the screen via scale and scroll modifiers.
        ## What we do here is basically put everything in scene coordinates first, see what we have to render, then move those rectangles back to screen coordinates to render them.
        
        ## Let's start building a rectangle that holds the part of the scene we want to show
        ## screen is the rectangle that holds the piece of scene that we will show. We still have to apply scaling to it.
        #screen_w = self.target.width
        #screen_h = self.target.height
        #screen = Rect((self._scroll_x, self._scroll_y, screen_w, screen_h))
        
        #rects = []
        
        ## Apply the overall scale setting if needed.
        #if self._scale_x != 1.0 or self._scale_y != 1.0:
            #doScale = True
            ## Convert screen coordinates to unscaled absolute coordinates
            #screen.scale(1.0/self._scale_x, 1.0/self._scale_y)
        #else:
            #doScale = False
            
        ## At this point, screen contains the rectangle in scene coordinates that we will show, everything that falls inside it gets on the screen.
        ## Now we get all the dirty rectangles reported by the nodes, and we determine which ones intersect with the screen, discarding everything else.
        #if self.dirtyRects != None:
            #for dr in self.dirtyRects:
                ## dr is in scene coordinates
                ## Intersect the rect with the screen rectangle in scene coordinates
                #ir = screen.intersection(Rect(dr))
                #if ir != None:
                    ## There's some intersection, append it to the list of rectangles to be rendered.
                    #rects.append(ir)
        #else:
            ## Set all the screen as dirty
            #rects.append(screen)
        
        #gilbert = Gilbert()
        ## Get a list of the z index of the nodes in the scenes, we will traverse it in increasing order
        #zindexs = gilbert.nodesZ.keys()
        #if len(zindexs) >0:
            #zindexs.sort()

        ## Iterate over the dirty rects that fall on the viewable area and draw them
        #for r in rects:
            ##print "DIRTY RECTANGLE:", r
            ## r is in scene coordinates, already intersected with the scaled & scrolled screen rectangle
            #for z in zindexs:
                #for node in gilbert.nodesZ[z]:
                    ## Intersect the node rectangle with the dirty rectangle
                    ## nr is in scene coordinates
                    #nr = Rect(node.getRect())
                    ##print node.id, 'nr: ', nr, 'r:', r
                    ## ir is the intersection, in scene coordinates
                    #ir = r.intersection(nr)
                    ##print "Intersect r ", r, " with nr ", nr, " results in ", ir
                    #if ir != None:
                        ## There's an intersection, go over the node areas, and see what parts of those fall inside the intersected rect.
                        ## This areas is what we end up rendering.
                        #nx, ny = node.position
                        #for a in node.getFrameAreas():
                            ## a is a frame area, it's format is [sx, sy, dx, dy, w, h]
                            ## sx,sy -> coordinates in the atlas
                            ## dx,dy -> node coordinates where to put this
                            ## w,h -> size of the rectangle to blit
                            #sx,sy,dx,dy,w,h = a
                            
                            
                            ## Create nr, a rectangle with the destination location in scene coordinates  (scene coords = node coords+node position)
                            #nr = Rect((dx+nx, dy+ny, w, h))
                            
                            ##print node.id, ' r:', r, ' nr :', nr, 'Frame Area:', sx,sy,dx,dy,w,h
                            
                            #ir = r.intersection(nr)
                            #if ir != None:
                                ## ir is now the intersection of the frame area (moved to the proper location in the scene) with the dirty rectangle, in scene coordinates
                                #src_r = ir.copy()
                                #dst_r = ir.copy()
                                
                                ## src_r is in scene coordinates, created by intersecting the destination rectangle with the dirty rectangle in scene coordinates
                                ## We need to move it to the proper position on the source canvas
                                ## We adjust it to node coordinates by substracting the node position
                                ## Then, we substract the dx,dy coordinates (as they were used to construct nr and we don't need those)
                                ## Finally we add sx,sy to put the rectangle in the correct position in the canvas
                                ## This operations as completed in one step, and we end up with a source rectangle properly intersected with r, in source canvas coordinates
                                #src_r.move(sx-nx-dx, sy-ny-dy)
                                
                                ## dst_r is in scene coordinates, we will adjust it to screen coordinates
                                ## Now we apply the scale factor
                                #if doScale:
                                    ##Scale the dst_r values
                                    #dst_r.scale(self._scale_x, self._scale_y)

                                ## Apply scrolling
                                #dst_r.move(-self._scroll_x, -self._scroll_y)
                                
                                ## Perform the blitting if the src and dst rectangles have w,h > 0
                                #if src_r.width > 0 and src_r.height >0 and dst_r.width>0 and dst_r.height > 0:
                                    #if node.center == None:
                                        #self.target.blitCanvas(node.canvas, dst_r.left, dst_r.top, dst_r.width, dst_r.height, src_r.left, src_r.top, src_r.width, src_r.height, node.angle, False, 0, 0, (1 if node.fliph else 0) + (2 if node.flipv else 0) )
                                    #else:
                                        #self.target.blitCanvas(node.canvas, dst_r.left, dst_r.top, dst_r.width, dst_r.height, src_r.left, src_r.top, src_r.width, src_r.height, node.angle, True, node.center[0], node.center[1], (1 if node.fliph else 0) + (2 if node.flipv else 0))
                                    ##raw_input("Press Enter to continue...")
        #self._target.flip()
        #self.dirtyNone()
        ## Calculate how long it's been since the pre update until now.
        #self.frameLapse = getTime() - self.frameTimestamp
        #self.frameTimestamp = 0.0


    cpdef update(self):
        """ Renders the whole screen in every frame, ignores dirty rects completely (easier for handling rotations, etc) """
        cdef Rect nr, ir, screen
        cdef int z
        cdef double extra
        cdef CanvasBase canvas

        if self.frameTimestamp == 0.0:
            raise Exception ('You have to call preUpdate before calling update')

        # In the following, screen coordinates refers to a set of coordinates that start in 0,0 and go to (screen width-1, screen height-1)
        # Scene coordinates are the logical node coordinates, which relate to the screen via scale and scroll modifiers.
        # What we do here is basically put everything in scene coordinates first, see what we have to render, then move those rectangles back to screen coordinates to render them.

        # Let's start building a rectangle that holds the part of the scene we want to show
        # screen is the rectangle that holds the piece of scene that we will show. We still have to apply scaling to it.
        screen_w = self.target.width
        screen_h = self.target.height
        screen = Rect((self._scroll_x, self._scroll_y, screen_w, screen_h))

        # Apply the overall scale setting if needed.
        if self._scale_x != 1.0 or self._scale_y != 1.0:
            doScale = True
            # Convert screen coordinates to unscaled absolute coordinates
            screen.scale(1.0/self._scale_x, 1.0/self._scale_y)
        else:
            doScale = False

        gilbert = Gilbert()
        # Get a list of the z index of the nodes in the scenes, we will traverse it in increasing order
        zindexs = gilbert.nodesZ.keys()
        if len(zindexs) >0:
            zindexs.sort()

        for z in zindexs:
            for node in gilbert.nodesZ[z]:
                # Intersect the node rectangle with the dirty rectangle
                # nr is in scene coordinates
                nr = Rect(node.getRect())
                #print node.id, 'nr: ', nr, 'r:', r
                # ir is the intersection, in scene coordinates
                if node.angle != 0:
                    # Expand the node rect with some generous dimensions (to avoid having to calculate exactly how bigger it is)
                    extra = nr.width if nr.width > nr.height else nr.height
                    nr.left -= extra
                    nr.top -= extra
                    nr.height += extra
                    nr.width += extra

                ir = screen.intersection(nr)
                #print "Intersect r ", r, " with nr ", nr, " results in ", ir
                if ir != None:
                    # There's an intersection, go over the node areas, and see what parts of those fall inside the intersected rect.
                    # This areas is what we end up rendering.
                    nx, ny = node.position
                    for a in node.getFrameAreas():
                        # a is a frame area, it's format is [sx, sy, dx, dy, w, h]
                        # sx,sy -> coordinates in the atlas
                        # dx,dy -> node coordinates where to put this
                        # w,h -> size of the rectangle to blit
                        sx,sy,dx,dy,w,h = a

                        # Create nr, a rectangle with the destination location in scene coordinates  (scene coords = node coords+node position)
                        nr = Rect((dx+nx, dy+ny, w, h))

                        #print node.id, ' r:', r, ' nr :', nr, 'Frame Area:', sx,sy,dx,dy,w,h
                        if node.angle == 0 and node.flipv == False and node.fliph == False:
                            ir = screen.intersection(nr)
                        else:
                            ir = nr
                        
                        if ir != None:
                            # ir is now the intersection of the frame area (moved to the proper location in the scene) with the dirty rectangle, in scene coordinates
                            src_r = ir.copy()
                            dst_r = ir.copy()

                            # src_r is in scene coordinates, created by intersecting the destination rectangle with the dirty rectangle in scene coordinates
                            # We need to move it to the proper position on the source canvas
                            # We adjust it to node coordinates by substracting the node position
                            # Then, we substract the dx,dy coordinates (as they were used to construct nr and we don't need those)
                            # Finally we add sx,sy to put the rectangle in the correct position in the canvas
                            # This operations as completed in one step, and we end up with a source rectangle properly intersected with r, in source canvas coordinates
                            src_r.move(sx-nx-dx, sy-ny-dy)

                            # dst_r is in scene coordinates, we will adjust it to screen coordinates
                            # Now we apply the scale factor
                            if doScale:
                                #Scale the dst_r values
                                dst_r.scale(self._scale_x, self._scale_y)

                            # Apply scrolling
                            dst_r.move(-self._scroll_x, -self._scroll_y)

                            # Perform the blitting if the src and dst rectangles have w,h > 0
                            if src_r.width > 0 and src_r.height >0 and dst_r.width>0 and dst_r.height > 0:
                                if node.center == None:
                                    self.target.blitCanvas(node.canvas, dst_r.left, dst_r.top, dst_r.width, dst_r.height, src_r.left, src_r.top, src_r.width, src_r.height, node.angle, False, 0, 0, (1 if node.fliph else 0) + (2 if node.flipv else 0) )
                                else:
                                    self.target.blitCanvas(node.canvas, dst_r.left, dst_r.top, dst_r.width, dst_r.height, src_r.left, src_r.top, src_r.width, src_r.height, node.angle, True, node.center[0], node.center[1], (1 if node.fliph else 0) + (2 if node.flipv else 0))
                                #raw_input("Press Enter to continue...")
        self._target.flip()
        self.dirtyNone()
        # Calculate how long it's been since the pre update until now.
        self.frameLapse = getTime() - self.frameTimestamp
        self.frameTimestamp = 0.0
    
    def preUpdate(self, now):
        """Mark the initiation time of the frame and save it"""
        self.frameTimestamp = now
        
    property target:
        def __get__(self):
            """ Return the rendering target """
            return self._target
        def __set__(self, TargetBase new_target):
            """ Set the rendering target """
            self._target = new_target

    property needsRects:
        def __get__(self):
            """ Answer whether dirty rectangles are needed or discarded (due to double buffering for example) """
            return not self._target.isDoubleBuffered

    property screenSize:
        def __get__(self):
            """ Return the width,height of the screen """
            if self._target != None:
                return self._target.width, self._target.height
            else:
                return 0,0
            
    property sceneSize:
        def __get__(self):
            """ Return the width,height of the scene """
            return self._native_size_w, self._native_size_h
        def __set__(self, value):
            self.setSceneSize(value[0], value[1])

    property scroll:
        def __get__(self):
            """ Return the scrolling of the scene in scene coordinates"""
            return self._scroll_x, self._scroll_y

    property scale:
        def __get__(self):
            """ Return the scaling factor of the scene """
            return self._scale_x, self._scale_y
        
    def reset(self):
        """ Reset the renderer, mark everything as clean """
        self.dirtyNone()
        
    cpdef dirty(self, int x, int y, int w, int h):
        """ Mark the area that starts at x,y with size w,h as dirty """
        if self.dirtyRects != None:
            self.dirtyRects.append((x,y,w,h))
        
    def dirtyAll(self):
        """ Dirty up all the screen """
        self.dirtyRects = None
        
    def dirtyNone(self):
        """ Remove all dirty rectangles """
        self.dirtyRects = []

    def getTimestamp(self):
        """ Return the current frame timestamp in ms """
        return self.frameTimestamp
    
    def checkRate(self, lastTime, rate):
        """ Check if for a given frame rate enough time has elapsed  """
        return self.frameTimestamp - lastTime > 60.0/rate
    
    def checkLapse(self, lastTime, lapse):
        """ Check that a given time lapse has passed """
        return self.frameTimestamp - lastTime > lapse
    
    cpdef setNativeResolution(self, double w=-1.0, double h=-1.0, bool keep_aspect=True):
        """ This function receives the scene native resolution. Based on it, it sets the scaling factor to the screen to fit the scene """
        self._native_res_w = w
        self._native_res_h = h
        self._keep_aspect = keep_aspect
        self._calculateScale(w,h,self.target.width, self.target.height, keep_aspect)

    cpdef setSceneSize(self, int w, int h):
        """ This function receives the scene size. Based on it, it controls the scrolling allowed """
        self._native_size_w = w
        self._native_size_h = h
        
    cpdef _calculateScale(self, double scene_w, double scene_h, int screen_w, int screen_h, bool keep_aspect=True):
        cdef double sx, sy
        if scene_w!=-1.0 and scene_h != -1.0:
            sx = <double>screen_w/scene_w
            sy = <double>screen_h/scene_h
            if keep_aspect:
                # Choose the higher scaling
                if sx > sy:
                    sy = sx
                else:
                    sx = sy
            self._scale_x = sx
            self._scale_y = sy
        else:
            self._scale_x = 1.0
            self._scale_y = 1.0

    cpdef windowResized(self):
        """ Tell the target to update it's size """
        self.target.updateSize()

        # TODO: handle switching of scrolling properly
        self._scroll_x = 0
        self._scroll_y = 0

        # Adjust scaling
        screen_w = self.target.width
        screen_h = self.target.height
        self._calculateScale(self._native_res_w, self._native_res_h, screen_w, screen_h, self._keep_aspect)

    cpdef scrollBy(self, int deltax, int deltay):
        """ Scroll the screen by deltax,deltay. Scrolling is done in screen coordinates,
        but as the parameters are a difference, they can be in scene or screen coordinates.
        """
        screen_w = self.target.width
        screen_h = self.target.height
        cdef int max_w = self._native_size_w*self._scale_x - screen_w
        cdef int max_h = self._native_size_h*self._scale_y - screen_h
        
        cdef int sx = self._scroll_x - deltax
        if sx < 0:
            sx = 0
        elif sx > max_w:
            sx = max_w

        cdef int sy = self._scroll_y - deltay
        if sy < 0:
            sy = 0
        elif sy > max_h:
            sy = max_h

        self._scroll_x = sx
        self._scroll_y = sy
        self.dirtyAll()

    cpdef scrollTo(self, int x, int y):
        #STUB
        pass

    cpdef scaleBy(self, int delta):
        """ delta is a value in pixel area (width*height)"""
        
        cdef double factor = <double>1.0 + <double> delta / <double> (self.target.width*self.target.height)

        self.scaleByFactor(factor)
        
    cpdef scaleByFactor(self, double factor):
        """ Apply a scaling factor"""
        cdef double scale_x = self._scale_x * factor
        cdef double scale_y = self._scale_y * factor

        if self._native_size_w*scale_x < self.target.width:
            scale_x = self.target.width / self._native_size_w

        if self._native_size_h*scale_y < self.target.height:
            scale_y = self.target.height / self._native_size_h

        if self._keep_aspect:
            if scale_x > scale_y:
                scale_y = scale_x
            else:
                scale_x = scale_y

        self._scale_x = scale_x
        self._scale_y = scale_y
        self.dirtyAll()

        # Adjust scrolling if needed
        self.scrollBy(0,0)
