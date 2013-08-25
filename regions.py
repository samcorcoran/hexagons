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
		self.orderedBorderVertices = []
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

	def findBorderVertices(self, drawBorderVertices=False):
		print("Finding all border vertices...")
		if not self.borderHexes:
			# Find the outer ring of region hexes if not already known
			self.findBorderHexes()
		# Compile list of any points that have neighbours not in region
		#  only test points belonging to outer ring of border hexes
		for nextHex in self.borderHexes[0].values():
			#nextHex.drawFilledHex((1,0,0,0.5))
			for point in nextHex.points:
				# Don't include a point if it is already listed as a border vertex
				if not point in self.borderVertices:
					# Check point's neighbours to determine if it is on border
					hasExternalNeighbour = False
					for neighbourHex in point.surroundingHexes.values():
						# Check dictionary of region hexes to see if this neighbour is a member
						if not neighbourHex.hexIndex in self.hexes:
							# This point is a border vertex
							hasExternalNeighbour = True
							# No need to check other neighbours
							break
					if hasExternalNeighbour:
						# Store point keyed on coordinates
						self.borderVertices[ point.id ] = point
						# Draw diagnostic points if required
						if drawBorderVertices:
							drawUtils.drawSquare([point.x, point.y], 4, (1,0,1,1))						
					else:
						#print("point had no neighbours outside of region")
						pass

	def findOrderedBorderVertices(self, drawBorderVertices=True, borderVertexColor=(0.1, 0.5, 0.5, 1)):
		print("Finding all border vertices and storing them as an ordered sequence...")
		if not self.borderVertices:
			# Find the outer ring of region hexes if not already known
			self.findBorderVertices()

		# Handle non-contiguous borders by 
		remainingBorderVertices = copy.copy(self.borderVertices)		
		while remainingBorderVertices:
			#print("Taking another starting point... total left: %d" % (len(remainingBorderVertices)))
			# Take first point from those still undrawn
			startingPoint = list(remainingBorderVertices.values())[0]
			currentHex = False
			for neighbour in startingPoint.surroundingHexes.values():
				if neighbour.hexIndex in self.hexes:
					currentHex = neighbour
					break

			if not currentHex:
				print("WARNING: Starting point for border drawing was not found.")
			currentPoint = startingPoint

			borderList = []
			# Continue while list is empty or start has not been reached in looping exploration
			while not startingPoint == currentPoint or not borderList:
				# Add point to list
				borderList.append(currentPoint)
				# Remove point from the list of remaining border vertices
				if currentPoint.id in remainingBorderVertices:
					#print("Removing point from remainingBorderVertices. Is %d in borderList %d." % (len(borderList)-1, len(self.orderedBorderVertices)))
					del remainingBorderVertices[ currentPoint.id ]
				# Attempt to determine if currentPoint straddles a second hex which should now be explored
				i, indexFound = currentHex.getPointIndex(currentPoint)
				if not indexFound:
					print("WARNING: Index for current point was not found in currentHex.")
				# Look in ith direction, to obey winding order			
				#  Check if neighbour exists before accessing, as border hexes may be missing neighbours
				if i in currentHex.neighbours and currentHex.neighbours[i].hexIndex in self.hexes:
					#print("Hex %s is being replaced by hex %s as current hex" % (str(currentHex.hexIndex), str(currentHex.neighbours[i].hexIndex)))
					currentHex = currentHex.neighbours[i]
					currentPoint = currentHex.getSuccessivePoint(currentPoint)
				else:
					nextI = (i+1) % len(currentHex.points)
					#print("Hex %s is staying current hex. Incrementing i to %d" % (str(currentHex.hexIndex), nextI))
					currentPoint = currentHex.points[ nextI ]
			self.orderedBorderVertices.append(borderList)
		# Now all points have been found, draw them if required
		if drawBorderVertices:
			for borderList in self.orderedBorderVertices:
				for point in borderList:
					pyglet.gl.glColor4f(*borderVertexColor)
					pyglet.graphics.draw(1, pyglet.gl.GL_POINTS,
						('v2f', point.getCoords())
					)

	def findClosestBorderVertex(self, v1):
		if self.borderVertices:
			# Get any item from dictionary
			closestVertex = list(self.borderVertices.values())[0]
			shortestDistance = v1.distanceFrom(closestVertex)
			for borderVertex in self.borderVertices.values():
				nextDistance = v1.distanceFrom(borderVertex)
				if nextDistance < shortestDistance:
					closestVertex = borderVertex
					shortestDistance = nextDistance
			return closestVertex, shortestDistance
		return False

	def calculateAllVertexBorderDistances(self, drawArrowsToCoast=False):
		print("Calculating all vertex border distances...")
		if not self.borderVertices:
			self.findBorderVertices()
		# Search border vertices for closest point
		for nextHex in self.hexes.values():
			for nextPoint in nextHex.points:
				# Store point's distance to border in dict with point coordinates as key
				closestBorderVertex, distance = self.findClosestBorderVertex(nextPoint)
				# Draw diagnostic arrows from region points to nearest coastal points if required
				if drawArrowsToCoast:
					drawUtils.drawArrow([nextPoint.x, nextPoint.y], [closestBorderVertex.x, closestBorderVertex.y], (0,1,0,1))
				# Keep track of longest distance, for possible normalisation purposes
				if distance > self.largestVertexBorderDistance:
					self.largestVertexBorderDistance = distance
				# Register point's distance to border
				self.vertexBorderDistances[ nextPoint.id ] = closestBorderVertex

	def doesPointBorderRegion(self, v0):
		internalNeighbour = False
		externalNeighbour = True
		for neighbour in v0.surroundingHexes.values():
			if neighbour.hexIndex in self.hexes:
				internalNeighbour = True
			else:
				externalNeighbour = True
		# Returns false if either is false
		return (internalNeighbour and externalNeighbour)

	def drawRegionBorder(self, borderColor=(0.8,0.5,0.1,1)):
		if not self.orderedBorderVertices:
			self.findOrderedBorderVertices()
		#print("Drawing region border...")
		# Convert vertices into list of coordinates
		for borderList in self.orderedBorderVertices:
			pointsList = [x.getCoords() for x in borderList]
			pointsList = list(chain.from_iterable(pointsList))
			# Draw line loop
			pyglet.gl.glColor4f(*borderColor)
			pyglet.graphics.draw(len(borderList), pyglet.gl.GL_LINE_LOOP,
				('v2f', pointsList)
			)