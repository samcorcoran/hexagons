import math
import random
import time

import graph
import regions
import drawUtils
import terrain
import drainage

class GeographicZone():
    def __init__(self, world, mainRegion, noise=False):
        # Store a reference to the world that contains this Land
        self.world = world
        # A dict of hexagons that makes up this region
        self.region = mainRegion
        # Noise information unique to Land
        self.noise = noise
        
    def computeBorders(self):
        t0 = time.clock()
        self.region.findBorderHexes()
        t1 = time.clock()
        print("     - LAND BORDERS finding border hexes: ", t1-t0)
        print("     - Total border hexes: %d" % (len(self.region.borderHexes)))
        t0 = time.clock()
        self.region.calculateAllClosestBorderVertex()
        t1 = time.clock()
        print("     - LAND BORDERS closest border vertex calculation: ", t1-t0)
        t0 = time.clock()
        self.region.findOrderedBorderVertices()
        t1 = time.clock()
        print("     - LAND BORDERS order border vertex finding: ", t1-t0)

    def drawGeographicZoneBorders(self):
        self.region.drawRegionBorders()

    def drawGeographicZoneBorderHexes(self):
        self.region.drawBorderHexes()

    def receiveBordersFromLands(self, geoZones):
        for geoZone in geoZones:
            self.region.adoptBordersFromRegion(geoZone.region)

class Land(GeographicZone):
    def __init__(self, world, mainRegion, noise=False):
        print("TIME - LAND:")
        # Initialise base class
        t0 = time.clock()
        GeographicZone.__init__(self, world, mainRegion, noise=False)
        t1 = time.clock()
        print("     - LAND geographic zone initialisation: ", t1-t0)
        self.id = next(landIdGen)
        # Borders
        t0 = time.clock()
        self.computeBorders()
        t1 = time.clock()
        print("     - LAND border computation: ", t1-t0)
        # Altitudes
        t0 = time.clock()
        self.assignLandHeights()
        t1 = time.clock()
        print("     - LAND height assignment: ", t1-t0)
        # Rivers
        self.sinks = set()
        self.outflows = set()
        self.drainageBasins = set()
        self.rivers = set()
        # Drainage routes
        t0 = time.clock()
        self.calculateDrainageRoutes()
        t1 = time.clock()
        print("     - LAND drainage route calculation: ", t1-t0)
        # Basins
        t0 = time.clock()
        self.createDrainageBasins()
        t1 = time.clock()
        print("     - LAND drainage basin calculation: ", t1-t0)
        # Rivers objects
        t0 = time.clock()
        self.createRivers()
        t1 = time.clock()
        print("     - LAND river creation: ", t1-t0)

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

    def createRivers(self, minRiverSize=0, percentageOfRivers=0.2):
        # A low-bar can be applied to river length acceptance
        riverCandidates = []
        for nextHex in self.outflows:
            river = drainage.River(nextHex)
            if len(river.routeHexes) > minRiverSize:
                riverCandidates.append(river)
        # Percentage acceptance takes given percentage of longest rivers, and any others that share a length with those accepted
        #   this is so rivers of equal length aren't arbitrarily accepted/discarded
        riverCandidates.sort(key = lambda x: len(x.routeHexes))
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

    def drawRivers(self, riverPoints, useSimpleRoutes=True, minDrainedAbove=0, minTotalDrainedAtMouth=False):
        for nextRiver in self.rivers:
            nextRiver.getRiverPoints(riverPoints, useSimpleRoutes, minDrainedAbove, minTotalDrainedAtMouth)
            nextRiver.drawRiver(useSimpleRoutes, minDrainedAbove, minTotalDrainedAtMouth)

    def drawDrainageBasins(self):
        #print("Drawing basins for region %d" % (self.id))
        for basin in self.drainageBasins:
            #print("drawing basin")
            basin.drawDrainageBasin()

# Initialise a generator for 
landIdGen = graph.idGenerator()

class Water(GeographicZone):
    def __init__(self, world, mainRegion, noise=False):
        # Initialise base class
        super(Water, self).__init__(world, mainRegion, noise=False)
