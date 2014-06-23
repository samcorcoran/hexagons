import math
import random
import copy
import pyglet
import time
from itertools import chain

import hexagon
import graph
import regions
import drawUtils
import terrain
import lands
import weather
import drainage

class World():
    def __init__(self, worldWidth, worldHeight, hexesInOddRow=10, clipPointsToWorldLimits=True, maskImage=False, createWeather=False):
        self.hexEdge_vertex_list = None
        self.hexCentre_vertex_list = None
        self.hexFills_vertex_list = None
        # World dimensions
        self.worldWidth = worldWidth
        self.worldHeight = worldHeight
        self.hexesInOddRow = hexesInOddRow
        # Structures for holding hexes
        self.landHexes = dict()
        self.waterHexes = dict()
        # Create a hex grid
        self.hexMap = dict()
        t0 = time.clock()
        self.hexGrid = self.createHexGridFromPoints(clipPointsToWorldLimits)
        t1 = time.clock()
        print("TIME - Hex grid creation: ", t1-t0)
        print("     - time per hex: ", (t1-t0)/float(len(self.hexGrid)))
        if clipPointsToWorldLimits:
            t0 = time.clock()
            self.clipGridHexagonsToWorldDimensions()
            t1 = time.clock()
            print("TIME - World limit clipping: ", t1-t0)
        # Add verts to spatial grid
        t0 = time.clock()
        self.spatialGrid = graph.SpatialGrid(0, 0, self.worldWidth, self.worldHeight, int(0.75*hexesInOddRow))
        t1 = time.clock()
        print("TIME - Grid vert creation: ", t1-t0)
        t0 = time.clock()
        self.addVertsToSpatialGrid()
        t1 = time.clock()
        print("TIME - Adding verts to grid: ", t1-t0)
        # Tag hexagons/vertices according to masks
        self.landMask = maskImage
        ## Collect land and water hexagons
        t0 = time.clock()
        self.findLandMarkedHexes()
        t1 = time.clock()
        print("TIME - Land hex finding: ", t1-t0)
        # Create noise for world altitudes
        self.noise = terrain.createNoiseList(self.worldWidth, self.worldHeight, inBytes=False)
        # Create lands - creation process involves finding borders
        t0 = time.clock()
        self.islands = []
        self.createLands()
        t1 = time.clock()
        print("TIME - Land creation: ", t1-t0)
        print("     - time per hex: ", (t1-t0)/float(len(self.hexGrid)))
        print("     - time per land: ", (t1-t0)/float(len(self.islands)))
        # Create oceans/seas and lakes
        t0 = time.clock()
        self.waters = []
        self.createWaters()
        t1 = time.clock()
        print("TIME - Water creation: ", t1-t0)
        # Use land borders to avoid recomputing the same vertex sequences
        t0 = time.clock()
        for water in self.waters:
            water.receiveBordersFromLands(self.islands)
        t1 = time.clock()
        print("TIME - Water border adoption: ", t1-t0)
        # Create weather system
        if createWeather:
            t0 = time.clock()
            self.weatherSystem = weather.WeatherSystem(worldWidth, worldHeight)
            t1 = time.clock()
            print("TIME - Weather system: ", t1-t0)

    # Build a hex grid, hex by hex, using points of neighbouring generated hexagons where possible
    def createHexGridFromPoints(self, clipPointsToWorldLimits=True):
        print("Creating hex grid from points (hexesInOddRow: %d)" % (self.hexesInOddRow))
        # Width of hexagons (w=root3*Radius/2) is calculated from self.worldWidth, which then determines hex radius
        hexWidth = float(self.worldWidth)/float(self.hexesInOddRow)
        hexRadius = (hexWidth) / math.sqrt(3) # Also edge length

        gridRows = []

        # Loop through hexagon locations, using index to determine if some points should be taken from neighbours
        # Loop over hex coordinate locations
        hexCentreY = 0
        totalHexes = 0
        row = 0
        while hexCentreY - hexRadius < self.worldHeight:
            #print("Row number: %d" % (row))
            hexCentreX = 0 
            # Offset each row to allow for tesselation
            if row%2==1:
                hexCentreX += hexWidth / 2
            # Add another row to gridRows
            gridRows.append([])
            # Draw one less hex on odd-numbered rows
            hexesInThisRow = self.hexesInOddRow+1-(row%2)
            for col in range(hexesInThisRow):
                #print("Hex (%d, %d)" % (col, row))
                #print("Creating hex %d, with (col,row): (%d, %d)" % (totalHexes, col, row))
                isBorderHex = row == 0 or col == 0 or row == hexesInThisRow or (hexCentreY+(0.5*hexRadius) >= self.worldHeight)
                neighbours = self.getExistingNeighbours(gridRows, col, row)
                hexPolygon = hexagon.Hexagon((hexCentreX, hexCentreY), hexRadius, hexIndex=(col, row), jitterStrength=0.2, existingNeighbours=neighbours, isBorderHex=isBorderHex)
                #hexPolygon.addHexToNeighbourhood(gridRows, hexesInThisRow)
                totalHexes += 1
                # Add hex to current top row of hex grid
                gridRows[-1].append(hexPolygon)
                self.hexMap[(col, row)] = hexPolygon
                hexCentreX += hexWidth
            #print("Length of nextRow: %d" % (len(nextRow)))
            #gridRows.append(nextRow)
            row += 1
            hexCentreY += hexRadius * 1.5
        print("Created all hexagons.")

        print("Created a hexGrid with %d rows. Odd rows are length %d and even are %d." % (len(gridRows), len(gridRows[0]), len(gridRows[1])))
        return gridRows

    def getExistingNeighbours(self, gridRows, currentX, currentY):
        rowIsOdd = currentY%2 == 1

        seNeighbour = None
        # Identify SE neighbouring hex, if one exists
        # If hex isn't last in row, or row is odd, then it has a SE neighbour, excluding first row hexes
        hasSENeighbour = currentX < self.hexesInOddRow or rowIsOdd
        if currentY == 0:
            hasSENeighbour = False
        # Not last column, unless this row is odd (previous row is therefore longer)
        if hasSENeighbour:
            x = currentX+1 if rowIsOdd else currentX
            y = currentY-1
            #print("SE Neighbour of Hex %s has x,y: (%d, %d)" % ((currentX, currentY), x, y))
            seNeighbour = gridRows[y][x]

        swNeighbour = None
        # Identify SW neighbouring hex, if one exists
        # If hex isn't first in row, or row is odd then has SW neighbour, unless its on the first row
        hasSWNeighbour = currentX > 0 or rowIsOdd
        if currentY == 0:
            hasSWNeighbour = False
        # Not first column, unless this row is even (previous row is therefore longer)
        if hasSWNeighbour:
            x = currentX-1 if not rowIsOdd else currentX
            y = currentY-1
            #print("SW Neighbour of Hex %s has x,y: (%d, %d)" % ((currentX, currentY), x, y))
            swNeighbour = gridRows[y][x]

        wNeighbour = None
        # Identify W neighbouring hex, if one exists
        # Not first column...
        if currentX > 0:
            x = currentX-1
            y = currentY
            #print("W Neighbour of Hex %s has x,y: (%d, %d)" % ((currentX, currentY), x, y))
            wNeighbour = gridRows[y][x]

        return (seNeighbour, swNeighbour, wNeighbour)

    # Examine mask image and tag hexagons as land or water
    def findLandMarkedHexes(self):
        print("Begun finding masked hexes")
        if self.landMask:
            maskImageData = self.landMask.get_image_data()
            data = maskImageData.get_data('I', self.landMask.width)

            hexCount = 0
            for row in self.hexGrid:
                for nextHex in row:
                    #print("Hex " + str(hexCount))
                    if nextHex.compareToMaskImage(data, self.landMask.width):
                        nextHex.fillColor = (1.0,0.0,0.0,1.0)
                        # Indicate that hex must be land
                        nextHex.land = True
                        self.landHexes[nextHex.hexIndex] = nextHex
                    else:
                        # Indicate hex is water
                        nextHex.fillColor = (0.0,0.0,1.0,1.0)
                        nextHex.water = True
                        self.waterHexes[nextHex.hexIndex] = nextHex
                    #print("hexCount: " + str(hexCount))
                    hexCount += 1
            print("Finished finding masked hexes")

    def createLands(self):
        unassignedHexes = copy.copy(self.landHexes)
        while unassignedHexes:
            landRegion = self.createContiguousRegion(unassignedHexes)
            self.islands.append(lands.Land(self, landRegion, self.noise))

    def createWaters(self):
        unassignedHexes = copy.copy(self.waterHexes)
        while unassignedHexes:
            waterRegion = self.createContiguousRegion(unassignedHexes)
            self.waters.append( lands.GeographicZone(self, waterRegion, self.noise) )

    # Using dict of landHexes, floodfilling finds distinct tracts of land from which regions can be created.
    def createContiguousRegion(self, unassignedHexes):
        # Copy map so this dict can have keys removed without losing items from other dict
        # Choose a new land color
        fillColor = (random.randint(0,255), random.randint(0,255), random.randint(0,255), 255)
        # Take a hex from the list of unassigned
        nextHex = unassignedHexes.pop(random.choice(list(unassignedHexes.keys())))

        groupedHexes = []
        # Add it and its like-regioned neighbours to a list
        explorableHexes = [nextHex]
        while explorableHexes:
            unexploredHex = explorableHexes.pop()
            groupedHexes.append(unexploredHex)
            # If there are still hexes left to find, check hex's neighbours
            if unassignedHexes:
                explorableHexes.extend(self.floodFillLandNeighbours(unexploredHex, unassignedHexes))
        island = dict()
        for gHex in groupedHexes:
            island[gHex.hexIndex] = gHex
            # Apply some behaviour to hexes in region
            gHex.fillColor = fillColor
        # Create region with hexes and store as an island
        return regions.Region(island)

    # Check nextHex's neighbours for validity, return list of those which are valid
    def floodFillLandNeighbours(self, nextHex, remainingHexes):
        #print("Hex "  + str(nextHex.hexIndex))
        groupedNeighbours = []
        # Only continue of there are hexes remaining
        #print("Hex has %d neighbours." % (len(nextHex.neighbours)))
        # Determine which neighbours are valid
        for neighbour in nextHex.neighbours.values():
            # If neighbour is tagged as land and exists in remainingHexes
            if neighbour.hexIndex in remainingHexes:
                # Add this neighbour to group
                groupedNeighbours.append(remainingHexes.pop(neighbour.hexIndex))
        #print("Returning grouped neighbours:")
        #print(groupedNeighbours)
        return groupedNeighbours

    # Hexagons which are created with points outside of world limits which must have their OOB points shifted to the perimeter
    def clipGridHexagonsToWorldDimensions(self, printOOBChecks=False):
        #print("Screen-clipping hexagons")
        # Loop over boundary hexes, fixing their off-screen points to the screen boundary
        # Border hexes are not jittered, so points will definitely create an off-screen boundary that needs clipping
        widthInterval = [0, self.worldWidth]
        heightInterval = [0, self.worldHeight]
        # Bottom row
        #print("Clipping bottom row")
        for nextHex in self.hexGrid[0]:
            nextHex.clipPointsToScreen(widthInterval, heightInterval)
        # Top row
        #print("Clipping top row")
        for nextHex in self.hexGrid[-1]:
            nextHex.clipPointsToScreen(widthInterval, heightInterval)
        # Left and right columns
        #print("Clipping left and right column of each row")
        for nextRow in self.hexGrid:
            nextRow[0].clipPointsToScreen(widthInterval, heightInterval)
            nextRow[-1].clipPointsToScreen(widthInterval, heightInterval)
        if printOOBChecks:
            self.checkForOutOfBounds()

    def addVertsToSpatialGrid(self):
        for row in self.hexGrid:
            for nextHex in row:
                for vertex in nextHex.points:
                    self.spatialGrid.addVertex(vertex)
                self.spatialGrid.addVertex(nextHex.centre)


    # Utility function to optionally run after clipping to be informed of any vertices which continue to be out of bounds
    def checkForOutOfBounds(self):
        hexCount = 0
        for row in self.hexGrid:
            for nextHex in row:
                for i in range(len(nextHex.points)):
                    if nextHex.points[i].x < 0 or nextHex.points[i].x > self.worldWidth or nextHex.points[i].y < 0 or nextHex.points[i].y > self.worldHeight:
                        print("Hex %d (%d, %d) is out of bounds." % (hexCount, nextHex.hexIndex[0], nextHex.hexIndex[1]))
                        print("Hex point %d: %s" % (i, str(nextHex.points[i])))
                        return True
                hexCount += 1
        return False

    # Use pyglet GL calls to draw hexagons
    def drawHexGrid(self, drawHexEdges=True, drawHexFills=True, drawHexCentres=False, drawLand=False, drawWater=True):
        if drawLand:
            self.drawLandHexes(drawHexEdges, drawHexFills, drawHexCentres)

    def drawLandHexes(self, drawHexEdges=True, drawHexFills=True, drawHexCentres=False):
        hexEdgeVerts = []
        hexEdgeColours = []
        hexCentreVerts = []
        hexCentreColours = []
        hexTriangleVerts = []
        hexFillColours = []
        if not self.hexCentre_vertex_list or not self.hexEdge_vertex_list or not self.hexFills_vertex_list:
            for land in self.islands:
                for landHex in land.region.hexes.values():
                    # Populate hex edge vert and colour lists
                    if drawHexEdges and not self.hexEdge_vertex_list:
                        landHex.getPerimeterEdgeVerts(hexEdgeVerts, hexEdgeColours)
                    # Populate hex centres vert and colour lists
                    if drawHexCentres and not self.hexCentre_vertex_list:
                        landHex.getCentreCoordinatesVerts(hexCentreVerts, hexCentreColours)
                    # Populate hex triangles vert and colour lists
                    if drawHexFills and not self.hexFills_vertex_list:
                        landHex.getTriangleVerts(hexTriangleVerts, hexFillColours)
            # Format centre point vertex list
            if not self.hexCentre_vertex_list and hexCentreVerts:

                numHexCentreVerts = len(hexCentreVerts)/2
                self.hexCentre_vertex_list = pyglet.graphics.vertex_list(numHexCentreVerts,
                    ('v2f/static', hexCentreVerts),
                    ('c4B/static', hexCentreColours)
                )
            # Format edge point vertex list
            if not self.hexEdge_vertex_list and hexEdgeVerts:
                numHexEdgeVerts = len(hexEdgeVerts)/2
                self.hexEdge_vertex_list = pyglet.graphics.vertex_list(numHexEdgeVerts,
                    ('v2f/static', hexEdgeVerts),
                    ('c4B/static', list(chain.from_iterable(hexEdgeColours)))
                )
            # Format centre point vertex list
            if not self.hexFills_vertex_list and hexTriangleVerts:
                numHexFillsVerts = len(hexTriangleVerts)/2
                self.hexFills_vertex_list = pyglet.graphics.vertex_list(numHexFillsVerts,
                    ('v2f/static', hexTriangleVerts),
                    ('c4B/static', list(chain.from_iterable(hexFillColours)))
                )
        # Draw vertex lists
        if drawHexFills:
            self.hexFills_vertex_list.draw(pyglet.gl.GL_TRIANGLES)
        if drawHexCentres:
            self.hexCentre_vertex_list.draw(pyglet.gl.GL_POINTS)
        if drawHexEdges:
            self.hexEdge_vertex_list.draw(pyglet.gl.GL_LINES)


    # Use pyglet GL calls to draw drainage routes
    def drawDrainageRoutes(self, useSimpleRoutes=True, minHexesDrainedAbove=False):
        for nextHex in self.landHexes.values():
            #nextHex.drawPerimeterDrainageRoutes()
            #nextHex.drawVertexDrainageRoute()
            drainage.drawDrainageRoute(nextHex, useSimpleRoutes=useSimpleRoutes, minHexesDrainedAbove=minHexesDrainedAbove)

    # Use pyglet GL calls to draw drainage routes for each river hex
    def drawRivers(self, useSimpleRoutes=True, minDrainedAbove=0, minTotalDrainedAtMouth=False):
        riverPoints = []
        for nextLand in self.islands:
            nextLand.getRiverPoints(riverPoints, minDrainedAbove, minTotalDrainedAtMouth)
            #nextLand.drawRivers(useSimpleRoutes, minDrainedAbove, minTotalDrainedAtMouth)
        # Do the drawing
        drawUtils.drawRivers(riverPoints)

    # Draw borders of each distinct land region
    def drawIslandBorders(self):
        for island in self.islands:
            island.drawGeographicZoneBorders()

    # Draw borders of each distinct waters region
    def drawWatersBorders(self):
        for water in self.waters:
            water.drawGeographicZoneBorders()

    def drawGeographicZoneBorderHexes(self):
        points = []
        colours = []
        # Accumulate hex vert coordinates
        for island in self.islands:
            island.getGeographicZoneBorderHexTrianglePoints(points, colours)
        # Draw points as a batch
        drawUtils.drawHexagonBatch(points, colours)

