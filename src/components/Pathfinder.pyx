#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# Ignifuga Game Engine
# Pathfinder Component class
# Author: Gabriel Jacobo <gabriel@mdqinc.com>

from ignifuga.components.Component import Component
from cython.operator cimport dereference as deref, preincrement as inc #dereference and increment operators

cdef class _PathfinderComponent:
    cdef bint pointInArea(self, int x, int y, WalkAreaVertexDeque *areas, int numAreas):
        cdef bint oddNodes = False
        cdef int xj, xi, x0, yj, yi, y0, n = 1
        cdef _WalkAreaVertex *v

        cdef WalkAreaVertexIterator it = areas.begin()

        while it != areas.end():
            v = &deref(it)

            if n == 1:
                # This is the first point of the polygon, we need one more point to make a comparison

                # Save this point for later
                xi = x0 = v.x
                yi = y0 = v.y
                inc(it)
                if it == areas.end():
                    break
                v = &deref(it)
                xj = v.x
                yj = v.y
            elif n == v.numVertexs:
                # This is the last point, compare it against the first one
                xj = x0
                yj = y0
                n = 0
            else:
                # Regular point, compare against the previous round point stored in xi,yi
                xj = v.x
                yj = v.y

            if ((yi>=y) != (yj>=y)) and (x < (xj-xi) * (y-yi) / (yj-yi) + xi):
                oddNodes = not oddNodes

            # Keep a reference to the last point to use for comparison in the next round
            xi = xj
            yi = yj
            inc(it)
            n+=1

        return oddNodes

    cdef bint lineInArea(self, int Ax, int Ay, int Bx, int By, WalkAreaVertexDeque *areas, int numAreas):
        cdef int Dx, Cx, x0, Dy, Cy, y0, n = 1
        cdef bint ccw1,ccw2, ccw3, ccw4
        cdef _WalkAreaVertex *v

        cdef WalkAreaVertexIterator it = areas.begin()

        while it != areas.end():
            v = &deref(it)
            if n == 1:
                # This is the first point of the polygon, we need one more point to make a comparison

                # Save this point for later
                Cx = x0 = v.x
                Cy = y0 = v.y
                inc(it)
                if it == areas.end():
                    break
                v = &deref(it)
                Dx = v.x
                Dy = v.y
            elif n == v.numVertexs:
                # This is the last point, compare it against the first one
                Dx = x0
                Dy = y0
                n = 0
            else:
                # Regular point, compare against the previous round point stored in Cx,Cy
                Dx = v.x
                Dy = v.y


            # See http://www.bryceboe.com/2006/10/23/line-segment-intersection-algorithm/ for the rationale behind this
            # Adds previsions for colinearity,
            #ccw = (Cy-Ay)*(Bx-Ax) > (By-Ay)*(Cx-Ax)

            if (By - Ay) * (Cx - Dx)  != (Dy - Cy) * (Ax - Bx):
                # Not colinear
                ccw1 = (Dy-Ay)*(Cx-Ax) >= (Cy-Ay)*(Dx-Ax)
                ccw2 = (Dy-By)*(Cx-Bx) >= (Cy-By)*(Dx-Bx)
                ccw3 = (Cy-Ay)*(Bx-Ax) >= (By-Ay)*(Cx-Ax)
                ccw4 = (Dy-Ay)*(Bx-Ax) >= (By-Ay)*(Dx-Ax)
                if ccw1 != ccw2 and ccw3 != ccw4:
                    # Intersection
                    return False

            # Keep a reference to the last point to use for comparison in the next round
            Cx = Dx
            Cy = Dy
            inc(it)

        return True


    cdef bint shortestPath(self, int sX, int sY, int eX, int eY, WalkAreaVertexDeque *areas, int numAreas, PathfinderNodeDeque *solution):
        cdef PathfinderNodeDeque *nodes = new PathfinderNodeDeque()
        cdef PathfinderNodeIterator bestJ, bestI, i, j, treeCount
        cdef double bestDist, newDist
        cdef _PathfinderNode node, *vi, *vj, swap, *tmp
        cdef WalkAreaVertexIterator areas_it
        cdef _WalkAreaVertex *v,
        cdef int dx, dy
        cdef bint solutionFound = False


        #  Fail if either the startpoint or endpoint is outside the polygon set.
        if not self.pointInArea(sX, sY, areas, numAreas) or not self.pointInArea(eX, eY, areas, numAreas):
            return False

        # If there is a straight-line solution, return with it immediately.
        if self.lineInArea(sX,sY,eX,eY,areas,numAreas):
            solution.resize(0)
            node.x = sX
            node.y = sY
            node.distance = 0.0
            solution.push_back(node)

            node.x = eX
            node.y = eY
            eX -= sX
            eY -= sY
            node.distance = sqrt(<double>(eX*eX+eY*eY))

            solution.push_back(node)
            return True

        #  Build the node list from the vertex
        #  First push the initial node
        node.x = sX
        node.y = sY
        node.prev = NULL
        node.distance = 0.0
        nodes.push_back(node)

        areas_it = areas.begin()

        while areas_it != areas.end():
            v = &deref(areas_it)
            node.x = v.x
            node.y = v.y
            node.prev = NULL
            node.distance = 0.0
            nodes.push_back(node)
            inc(areas_it)

        # Add the end point
        node.x = eX
        node.y = eY
        node.prev = NULL
        node.distance = 0.0
        nodes.push_back(node)

        treeCount = nodes.begin()
        inc(treeCount)

        # Iteratively grow the shortest-path tree until it reaches the endpoint
        # or until it becomes unable to grow, in which case exit with failure.

        bestJ = nodes.begin()
        while not solutionFound:
            bestDist=-1.0;
            i = nodes.begin()
            while i != treeCount and not solutionFound:
                vi = &deref(i)
                j = treeCount
                while j != nodes.end() and not solutionFound:
                    vj = &deref(j)
                    if self.lineInArea(vi.x,vi.y,vj.x,vj.y,areas, numAreas):
                        # Distance is actually the sqrt of the sum of the squared sides, but...close enough ;)
                        dx = (vj.x-vi.x)
                        dy = (vj.y-vj.y)
                        newDist=vi.distance + sqrt(<double>(dx*dx + dy*dy))
                        if bestDist == -1 or newDist<bestDist:
                            bestDist=newDist
                            bestI=i
                            bestJ=j
                            if vj.x == eX and vj.y == eY:
                                solutionFound = True

                    inc(j)
                inc(i)

            if bestDist==-1.0:
                # Let's see if the last node is connected
                if not solutionFound:
                    return False
                else:
                    break

            tmp = &deref(bestJ)
            tmp.prev = &deref(bestI)
            tmp.distance = bestDist

            if not solutionFound:
                swap = tmp[0]
                tmp[0] = deref(treeCount)
                tmp = &deref(treeCount)
                tmp[0] = swap
                inc(treeCount)

        # Build the resulting path by starting from the end and walking through the previous nodes
        node = deref(bestJ)
        solution.resize(0)
        while True:
            solution.push_front(node)
            if node.prev == NULL:
                break
            node = node.prev[0]

        del nodes
        # Success
        return True


    cpdef path(self, int x, int y):
        cdef _Scene scene
        cdef PathfinderNodeDeque *solution = new PathfinderNodeDeque()
        cdef PathfinderNodeIterator it
        cdef _PathfinderNode *n

        if self._entity is not None and self._entity.scene is not None:
            #self._entity.scene is a weakref
            scene = <_Scene>self._entity.scene()

            _path = []

            if self.shortestPath(self._entity.x, self._entity.y, x, y, scene.walkAreas, scene.numWalkAreas, solution):
                it = solution.begin()
                while it != solution.end():
                    n = &deref(it)
                    _path.append((n.x, n.y, n.distance))
                    inc(it)
                return _path
            else:
                return None

    cpdef bint goto(self, int x, int y):
        cdef _Scene scene
        cdef PathfinderNodeDeque *solution = new PathfinderNodeDeque()
        cdef PathfinderNodeIterator it
        cdef _PathfinderNode *n

        if self._entity is not None and self._entity.scene is not None:
            #self._entity.scene is a weakref
            scene = <_Scene>self._entity.scene()

            if self.shortestPath(self._entity.x, self._entity.y, x, y, scene.walkAreas, scene.numWalkAreas, solution):
                it = solution.begin()
                while it != solution.end():
                    n = &deref(it)
                    inc(it)
            else:
                return False



class Pathfinder(Component, _PathfinderComponent):
    """ A viewable component based on a Rocket document wrapper"""
    PROPERTIES = Component.PROPERTIES + ['goto', 'path']
    def __init__(self, id=None, entity=None, active=True, frequency=15.0,  **data):
        # Default values
        self._loadDefaults({
        })

        super(Pathfinder, self).__init__(id, entity, active, frequency, **data)
        _PathfinderComponent.__init__(self)