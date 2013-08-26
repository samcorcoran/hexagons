import math
import random

import graph
import regions
import drawUtils
import terrain

class GeographicZone():
	def __init__(self, world, mainRegion, noise=False):
		# Store a reference to the world that contains this Land
		self.world = world
		# A dict of hexagons that makes up this region
		self.region = mainRegion
		# Noise information unique to Land
		self.noise = noise
		# Borders
		self.computeBorders()
		# Altitudes
		self.assignLandHeights()
		
	def computeBorders(self):
		self.region.findBorderHexes()
		self.region.calculateAllVertexBorderDistances()

	def drawGeographicZoneBorder(self):
		self.region.drawRegionBorder()

class Land(GeographicZone):
	#def __init__(self):

	def assignLandHeights(self):
		# Assign heights to land vertices
		#terrain.assignEqualAltitudes(self.region)
		#terrain.assignHexMapAltitudes(self.region)
		#terrain.assignHexMapAltitudesFromCoast(self.region)
		terrain.assignRegionVertexAltitudesFromCoast(self.region, self.world.noise)
		#terrain.assignNoisyAltitudes(self.region, self.noise)

# class Water(GeographicZone):
# 	def __init__(self):