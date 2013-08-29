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
		self.region.calculateAllVertexBorderDistances()
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
		self.drainageBasins = set()
		# Drainage routes
		self.calculateDrainageRoutes()
		# Basins
		self.createDrainageBasins()

	def assignLandHeights(self):
		# Assign heights to land vertices
		#terrain.assignEqualAltitudes(self.region)
		#terrain.assignHexMapAltitudes(self.region)
		#terrain.assignHexMapAltitudesFromCoast(self.region)
		terrain.assignRegionVertexAltitudesFromCoast(self.region, self.world.noise)
		#terrain.assignNoisyAltitudes(self.region, self.noise)

	def calculateDrainageRoutes(self):
		for nextHex in self.region.hexes.values():
			drainage.findDrainingNeighbour(nextHex)

	def createDrainageBasins(self, volumeThreshold=0):
		# Examine all hexes which border water
		for borderHex in self.region.borderHexes[0].values():
			# Check if borderHex is above threshold
			#print("borderHex quantity drained = %d" % (borderHex.quantityDrained))
			if borderHex.quantityDrained >= volumeThreshold:
				# Consider this a river
				newBasin = drainage.DrainageBasin(borderHex)
				#print("adding a basin")
				self.drainageBasins.add(newBasin)

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
