import math
import random

import graph
import regions
import drawUtils
import terrain

class Land():
	def __init__(self, world, mainRegion, noise):
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

	def assignLandHeights(self):
		# Assign heights to land vertices
		#terrain.assignEqualAltitudes(self.region)
		#terrain.assignHexMapAltitudes(self.region)
		#terrain.assignHexMapAltitudesFromCoast(self.region)
		terrain.assignRegionVertexAltitudesFromCoast(self.region, self.world.noise)
		#terrain.assignNoisyAltitudes(self.region, self.noise)

	def drawLandBorder(self):
		self.region.drawRegionBorder()

#class Island(Land):
	