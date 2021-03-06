import math
import pyglet
import random

class Vertex():
    def __init__(self, coordinates, hexes=[], maxJitter=0 ):
        self.id = next(vertexIdGen)
        self.x = coordinates[0] + random.uniform(-maxJitter, maxJitter)
        self.y = coordinates[1] + random.uniform(-maxJitter, maxJitter)
        self.surroundingHexes = dict()
        self.neighbouringVertices = []
        self.addHexNeighbours(hexes)
        self.altitude = None
        # Closest coastal vertex can be found by hexRegion.closestBorderVertex[ point.id ]
        self.directionToCoast = False
        # Neighbouring vertex which is drained into from this vertex
        self.drainingNeighbour = False
        # Neighbouring vertices which drain into this vertex
        self.drainedNeighbours = []
        self.minBorderDistance = False

    def addHexNeighbours(self, hexes):
        for nextHex in hexes:
            # Only add hex if it isn't already included
            if not nextHex.hexIndex in self.surroundingHexes:
                self.surroundingHexes[len(self.surroundingHexes)] = nextHex

    def addVertexNeighbour(self, newVertex):
        for neighbour in self.neighbouringVertices:
            # Prevent a vertex from being added multiple times
            if neighbour == newVertex:
                return False
        self.neighbouringVertices.append(newVertex)
        # Ensure reciprocal relationship
        newVertex.addVertexNeighbour(self)
        return True

    def isByWater(self):
        for nextHex in self.surroundingHexes.values():
            if nextHex.water:
                return True
        return False

    def distanceFrom(self, v1):
        return math.sqrt((v1.x - self.x)**2 + (v1.y - self.y)**2)

    def getCoords(self):
        return [self.x, self.y]

    def drawVertex(self, color=(1,1,1,1)):
        pyglet.gl.glColor4f(*color)
        pyglet.graphics.draw(1, pyglet.gl.GL_POINTS,
            ('v2f', (self.x, self.y))
        )

def idGenerator():
    i = 0
    while True:
        yield i
        i += 1

# Initialise the generator
vertexIdGen = idGenerator()

class SpatialGrid():
    def __init__(self, minX, minY, maxX, maxY, cellsAlongEdge):
        self.minX = minX
        self.minY = minY
        self.maxX = maxX
        self.maxY = maxY
        self.width = self.maxX - self.minX
        self.height = self.maxY - self.minY
        # Determine grid cell sizes
        # 1 layer is 1 division (cells on edge)
        # 2 layers is 2 divisions
        # 3 layers is 4 divisions
        # 4 layers is 8 divisions
        # 2**(layers-1)=divisions
        self.cellsAlongEdge = cellsAlongEdge#2**(numTreeLayers-1)
        self.cellWidth = self.width / float(self.cellsAlongEdge)
        self.cellHeight = self.height / float(self.cellsAlongEdge)
        # Create grid so QuadNodes can access neighbours
        self.cells = [[list() for a in range(self.cellsAlongEdge)] for b in range(self.cellsAlongEdge)]
        # Create a quad tree for space
        xCentre = self.minX+(self.width/2)
        yCentre = self.minY+(self.height/2)
        #self.rootNode = QuadNode(xCentre, yCentre, self.width, self.height, numTreeLayers, self)

    def addVertex(self, vertex):
        xIndex = self.getNearestXIndex(vertex.x)
        yIndex = self.getNearestYIndex(vertex.y)
        #print("Adding vertex (%f, %f) to index: %d, %d" % (vertex.x, vertex.y, xIndex, yIndex))
        alreadyExists = False
        for nextVertex in self.cells[xIndex][yIndex]:
            if vertex == nextVertex:
                alreadyExists = True
        if not alreadyExists:
            self.cells[xIndex][yIndex].append(vertex)

    def getNearestXIndex(self, x):
        # x below zero defaults xIndex to zero
        xIndex = 0
        if x >= self.maxX:
            xIndex = self.cellsAlongEdge-1
        elif x >= self.cellWidth:
            xIndex = int((x - self.minX) / self.cellWidth)
        return xIndex

    def getNearestYIndex(self, y):
        # y below zero defaults yIndex to zero
        yIndex = 0
        if y >= self.maxY:
            yIndex = self.cellsAlongEdge-1
        elif y >= self.cellHeight:
            yIndex = int((y - self.minY) / self.cellHeight)
        return yIndex

    # Finds closest vertex stored in spatial grid through distance comparisons to nearby vertices
    #  Note: Assumes there will be a vertex within the nine-cell-block
    def findNearestVertex(self, x, y, drawCandidateVertices=False):
        verts = []
        vertCount = 0
        #print("Finding nearest vertex to: %f, %f" % (x, y))
        xIndex = self.getNearestXIndex(x)
        yIndex = self.getNearestYIndex(y)
        #print("Indices: %d, %d" % (xIndex, yIndex))
        # Compare point to vertices held in this
        closestPerimeterVertex = None
        closestCentreVertex = None
        perimeterMinDist = max(self.width+1, self.height+1)**2
        centreMinDist = max(self.width+1, self.height+1)**2
        for xOffset in range(-1,2):
        #for xOffset in range(1):
            for yOffset in range(-1,2):
            #for yOffset in range(1):
                xNeighbour = xIndex + xOffset
                if xNeighbour < 0 or xNeighbour > self.cellsAlongEdge-1:
                    continue
                yNeighbour = yIndex + yOffset
                if yNeighbour < 0 or yNeighbour > self.cellsAlongEdge-1:
                    continue
                #print("Neighbours in index: (%d, %d)" % (xNeighbour, yNeighbour))
                v = 0
                for nextVertex in self.cells[xNeighbour][yNeighbour]:
                    dist = (x-nextVertex.x)**2 + (y-nextVertex.y)**2
                    #print(" vertex: %f, %f (dist %f)" % (nextVertex.x, nextVertex.y, math.sqrt(dist)))
                    if len(nextVertex.surroundingHexes) > 1:
                        #print("Found border vertex")
                        # Replace selected point
                        if dist < perimeterMinDist:
                            closestPerimeterVertex = nextVertex
                            perimeterMinDist = dist
                    elif len(nextVertex.surroundingHexes) == 1:
                        #print("Found hex centre vertex")
                        if dist < centreMinDist:
                            closestCentreVertex = nextVertex
                            centreMinDist = dist
                    else:
                        print("Vertex was neither perimeter nor centre")
                        pass
                    verts.extend([nextVertex.x, nextVertex.y])
                    vertCount += 1
                    v+=1
                    #print("Closest vertex: %f, %f" % (closestPerimeterVertex.x, closestPerimeterVertex.y))
                #print("Num candidates considered for nearest: %d" % v)
        if drawCandidateVertices:
            pyglet.gl.glColor4f(0.0, 1.0, 0.2, 0.2)
            pyglet.graphics.draw(vertCount, pyglet.gl.GL_POINTS,
                ('v2f', verts)
            )
        return closestPerimeterVertex, perimeterMinDist, closestCentreVertex, centreMinDist

    def findNearestHexAndVertex(self, x, y):
        closestVertex = None
        closestHex = None
        closestPerimeterVertex, perimeterMinDist, closestCentreVertex, centreMinDist = self.findNearestVertex(x, y)

        if closestCentreVertex and closestCentreVertex.surroundingHexes:
            closestHex = closestCentreVertex.surroundingHexes.values()[0]

        if perimeterMinDist >= centreMinDist:
            closestVertex = closestCentreVertex
        elif centreMinDist > perimeterMinDist:
            closestVertex = closestPerimeterVertex

        return closestHex, closestVertex

    # Draws faint spatial grid to help indicate which cell different vertices fall into
    def drawGridCells(self):
        pyglet.gl.glColor4f(1.0, 1.0, 1.0, 0.1)
        x = 0.0
        while x < self.maxX:
            pyglet.graphics.draw(2, pyglet.gl.GL_LINES,
                ('v2f', (x, 0.0, x, self.maxY))
            )
            x += self.cellWidth
        y = 0.0
        while y < self.maxY:
            pyglet.graphics.draw(2, pyglet.gl.GL_LINES,
                ('v2f', (0, y, self.maxX, y))
            )
            y += self.cellHeight

    def drawAllPoints(self):
        verts = []
        vertCount = 0
        for xIndex in range(self.cellsAlongEdge):
            for yIndex in range(self.cellsAlongEdge):
                for point in self.cells[xIndex][yIndex]:
                    verts.extend([point.x, point.y])
                    vertCount += 1
        pyglet.gl.glColor4f(1.0, 0.0, 0.2, 0.2)
        pyglet.graphics.draw(vertCount, pyglet.gl.GL_POINTS,
            ('v2f', verts)
        )