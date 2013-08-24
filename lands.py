import math
import random

import graph
import regions
import drawUtils
import terrain

class Land():
	def __init__(self, mainRegion, noise):
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
		#terrain.assignEqualAltitudes(landHexes)
		#terrain.assignHexMapAltitudes(landHexes)
		#terrain.assignHexMapAltitudesFromCoast(islandRegion)
		terrain.assignRegionVertexAltitudesFromCoast(self.region, self.noise)

	def drawLand(self):
		self.region.drawRegionBorder()

#class Island(Land):
	