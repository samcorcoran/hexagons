import math
import random
import time

import graph
import regions
import drawUtils
import terrain
import drainage
import namegen
from itertools import chain
import pyglet
#
# GeographicZones are entities that represent terrain formations. They
# encompass a region (body of hexes) and so have borders, but may also
# have other attributes. Examples of a geographic zone are islands, lakes
# oceans and seas.
#
class GeographicZone():
    def __init__(self, world, mainRegion, noise=False):
        # Store a reference to the world that contains this Land
        self.world = world
        # A dict of hexagons that makes up this region
        self.region = mainRegion
        # Noise information unique to Land
        self.noise = noise
        
    def computeBorders(self):
        self.region.findBorderHexes()
        self.region.calculateAllClosestBorderVertex()
        self.region.findOrderedBorderVertices()

    def drawGeographicZoneBorders(self):
        self.region.drawRegionBorders()

    def getGeographicZoneBorderHexTrianglePoints(self, points, colours):
        self.region.getRegionBorderHexTrianglePoints(points, colours)

    def drawGeographicZoneBorderHexes(self):
        self.region.drawBorderHexes()

    def receiveBordersFromLands(self, geoZones):
        for geoZone in geoZones:
            self.region.adoptBordersFromRegion(geoZone.region)

#
# Land is a particular geographic zone that represents above-sea terrain.
#
class Land(GeographicZone):
    def __init__(self, world, mainRegion, noise=False):
        # Initialise base class
        GeographicZone.__init__(self, world, mainRegion, noise=False)
        self.id = next(landIdGen)
        # Borders
        self.computeBorders()
        # Altitudes
        self.assignLandHeights()
        # Rivers
        self.sinks = set()
        self.outflows = set()
        self.drainageBasins = set()
        self.rivers = set()
        # Drainage routes
        self.calculateDrainageRoutes()
        # Basins
        self.createDrainageBasins()
        # Rivers objects
        self.createRivers()
        # Name land
        self.name = namegen.generateName()
        # Vertex Lists
        self.hex_fill_list = None
        self.hex_edge_list = None
        self.region_border_list = None
        self.river_edge_list = None

    def assignLandHeights(self):
        # Assign heights to land vertices
        #terrain.assignEqualAltitudes(self.region)
        #terrain.assignHexMapAltitudes(self.region)
        terrain.assignRegionVertexAltitudesFromCoast(self.region, self.world.noise)
        #terrain.assignNoisyAltitudes(self.region, self.noise)

    def calculateDrainageRoutes(self):
        for nextHex in self.region.hexes.values():
            drainingNeighbour = drainage.findDrainingNeighbour(nextHex)
            if drainingNeighbour:
                if drainingNeighbour.water:
                    # hexagon nextHex drains to a body of water and so must be an outflow
                    self.outflows.add(nextHex)
            else:
                # hexagon nextHex is a sink for an endorheic drainage basin
                self.sinks.add(nextHex)
        for nextTermination in (self.outflows | self.sinks):
            drainage.findHexesDrainedAbove(nextTermination)


    def createDrainageBasins(self, volumeThreshold=0):
        # Examine all hexes which border water
        for terminationHex in (self.outflows | self.sinks):
            # Check if borderHex is above threshold
            #print("borderHex quantity drained = %d" % (borderHex.quantityDrained))
            if terminationHex.quantityDrained >= volumeThreshold:
                # Consider this a river
                newBasin = drainage.DrainageBasin(terminationHex)
                #print("adding a basin")
                self.drainageBasins.add(newBasin)

    def createRivers(self, minRiverSize=1, percentageOfRivers=1.0):
        # A low-bar can be applied to river length acceptance
        riverCandidates = []
        for nextHex in self.outflows:
            river = drainage.River(nextHex)
            if len(river.routeHexes) > minRiverSize:
                riverCandidates.append(river)
        # Percentage acceptance takes given percentage of longest rivers, and any others that share a length with those accepted
        #   this is so rivers of equal length aren't arbitrarily accepted/discarded
        riverCandidates.sort(key = lambda x: len(x.routeHexes))
        if len(riverCandidates) > 0:
            lastRiverHexLength = len(riverCandidates[0].routeHexes)
            totalCandidates = len(riverCandidates)
            while riverCandidates:
                nextRiver = riverCandidates.pop()
                # Adding rivers stops if another would take the acceptance percentage too high
                percentageTooHigh = (len(self.rivers)+1)/float(totalCandidates) > percentageOfRivers
                # Unless next river is the same length as last, so is included anyway
                shorterThanLastRiver = len(nextRiver.routeHexes) < lastRiverHexLength
                if (percentageTooHigh and shorterThanLastRiver):
                    break
                # Store only legitimate rivers in set
                self.rivers.add(nextRiver)
                lastRiverHexLength = len(nextRiver.routeHexes)
            # What remains in riverCandidates are all failed candidates

    def getRiverPoints(self, riverPoints, minDrainedAbove=0, minTotalDrainedAtMouth=False):
        for nextRiver in self.rivers:
            nextRiver.getRiverPoints(riverPoints, minDrainedAbove, minTotalDrainedAtMouth)

    def drawDrainageBasins(self):
        #print("Drawing basins for region %d" % (self.id))
        for basin in self.drainageBasins:
            #print("drawing basin")
            basin.drawDrainageBasin()

    def doesLandContainHex(self, hex):
        return self.region.doesRegionContainHex(hex)

    # Hex verts aggregated for land
    def buildTerrainVertexLists(self, batch):
        # Hex edges are the lines that form the perimeter of each hexagon
        hexFillVerts = []
        hexFillColours = []
        hexEdgeVerts = []
        hexEdgeColours = []
        hexCentreVerts = []
        hexCentreColours = []
        # Collect lists of vertices
        for hex in self.region.hexes.values():
            # Hex fills
            hex.getTriangleVerts(hexFillVerts, hexFillColours)
            # Hex edges
            hexEdgeVerts.extend(list(chain.from_iterable( [(hex.points[n].x, hex.points[n].y, hex.points[n-1].x, hex.points[n-1].y) for n in range(len(hex.points))])))
            hexEdgeColours.extend([hex.fillColor for n in range(len(hex.points)*2)])
            # Hex centres
            hexCentreVerts.extend([hex.centre.x, hex.centre.y])
            hexCentreColours.extend(hex.fillColor)
        # Construct vertex lists and add to batch
        self.hex_fill_list = batch.add(len(hexFillVerts)/2, pyglet.gl.GL_TRIANGLES, None,
            ('v2f/static', hexFillVerts),
            ('c4B/static', list(chain.from_iterable(hexFillColours)))
        )
        self.hex_edge_list = batch.add(len(hexEdgeVerts)/2, pyglet.gl.GL_LINES, None,
            ('v2f/static', hexEdgeVerts),
            ('c4B/static', list(chain.from_iterable(hexEdgeColours)))
        )
        self.hex_centre_list = batch.add(len(hexCentreVerts)/2, pyglet.gl.GL_POINTS, None,
            ('v2f/static', hexCentreVerts),
            ('c4B/static', hexCentreColours)
        )

        self.hex_edge_list = None

    def populateBorderVList(self):
        self.region_border_list = None

    def populateRiverVList(self):
        self.river_edge_list = None

    def buildBatch(self, batch):
        # Hexagon edges, fills, centres
        self.buildTerrainVertexLists(batch)
        # Region border
        self.region.buildBatch(batch)
        # Rivers
        for river in self.rivers:
            river.buildBatch(batch)

# Initialise a generator for 
landIdGen = graph.idGenerator()

class Water(GeographicZone):
    def __init__(self, world, mainRegion, noise=False):
        # Initialise base class
        super(Water, self).__init__(world, mainRegion, noise=False)
