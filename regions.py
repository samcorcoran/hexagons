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
		self.hexBorderDistances = dict()
		self.borderVertices = dict()
		self.vertexBorderDistances = dict()
		self.largestVertexBorderDistance = False
		self.borderEdges = []

	def findBorderHexes(self, ringDepth=False):
		print("Finding all border hexes...")
		unassignedHexes = copy.copy(self.hexes)
		borderHexes = []
		ringNumber = 0
		while unassignedHexes.values():
			if ringNumber <= ringDepth or not ringDepth:
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
					self.hexBorderDistances[borderHex.hexIndex] = ringNumber
				ringNumber += 1
				# Append set of border hexes to 
				self.borderHexes.append(nextRing)

	def findBorderVertices(self):
		print("Finding all border vertices...")
		if not self.borderHexes:
			# Find the outer ring of region hexes if not already known
			self.findBorderHexes()
		# Compile list of any points that have neighbours not in region
		#  only test points belonging to outer ring of border hexes
		for nextHex in self.borderHexes[0].values():
			for point in nextHex.points:
				# Don't include a point if it is already listed as a border vertex
				if not point in self.borderVertices:
					# Check point's neighbours to determine if it is on border
					for neighbourHex in point.surroundingHexes:
						# Check dictionary of region hexes to see if this neighbour is a member
						if not neighbourHex in self.hexes:
							# This point is a border vertex
							# Store point keyed on coordinates
							self.borderVertices[ (point.x, point.y) ] = point

	def findClosestBorderVertex(self, v1):
		if self.borderVertices:
			# Get any item from dictionary
			closestVertex = list(self.borderVertices.values())[0]
			shortestDistance = v1.distanceFrom(closestVertex)
			for borderVertex in self.borderVertices.values():
				nextDistance = v1.distanceFrom(borderVertex)
				if nextDistance < shortestDistance:
					closestVertex = borderVertex
			return closestVertex, shortestDistance
		return False

	def calculateAllVertexBorderDistances(self):
		print("Calculating all vertex border distances...")
		if not self.borderVertices:
			self.findBorderVertices()
		# Search border vertices for closest point
		for nextHex in self.hexes.values():
			for nextPoint in nextHex.points:
				# Store point's distance to border in dict with point coordinates as key
				closestBorderVertex, distance = self.findClosestBorderVertex(nextPoint)
				# Keep track of longest distance, for possible normalisation purposes
				if distance > self.largestVertexBorderDistance:
					self.largestVertexBorderDistance = distance
				# Register point's distance to border
				self.vertexBorderDistances[(nextPoint.x, nextPoint.y)] = closestBorderVertex
