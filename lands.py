import math
import random

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
		self.region.findBorderHexes()
		self.region.calculateAllClosestBorderVertex()
		self.region.findOrderedBorderVertices()

	def drawGeographicZoneBorders(self):
		self.region.drawRegionBorders()

	def drawGeographicZoneBorderHexes(self):
		self.region.drawBorderHexes()

	def receiveBordersFromLands(self, geoZones):
		for geoZone in geoZones:
			self.region.adoptBordersFromRegion(geoZone.region)

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
		minRiverSize = 5
		for nextHex in self.outflows:
			river = drainage.River(nextHex)
			if len(river.routeHexes) > minRiverSize:
				self.rivers.add(river)

	def drawRivers(self, useSimpleRoutes):
		for nextRiver in self.rivers:
			nextRiver.drawRiver(useSimpleRoutes)

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
