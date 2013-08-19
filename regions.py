import pyglet
from pyglet.gl import *
from pyglet import image
import random
import copy
from itertools import chain

import graph
import drawUtils

class Region():
	def __init__(self, hexes):
		self.hexes = copy.copy(hexes)
		self.borderHexes = []
		self.borderDistances = dict()
		self.borderEdges = []

	def findBorderHexes(self, ringDepth=False):
		unassignedHexes = copy.copy(self.hexes)

		ringNumber = 0
		while unassignedHexes.values():
			nextRing = dict()
			# Find members of the group which have neigbours that aren't in the group
			for nextHex in unassignedHexes.values():
				for neighbour in nextHex.neighbours.values():
					# If hex neighbour is not in region it must be a border hex
					if not neighbour.hexIndex in unassignedHexes:
						nextRing[nextHex.hexIndex] = nextHex
			# Remove hexes that have now been assigned
			for borderHex in nextRing.values():
				#print("Hex %s is in ring %d" % (str(borderHex.hexIndex), ringNumber))
				del unassignedHexes[borderHex.hexIndex]
				# Store the hex's distance to the edge of the region
				self.borderDistances[borderHex.hexIndex] = ringNumber
			ringNumber += 1
			# Append set of border hexes to 
			self.borderHexes.append(nextRing)