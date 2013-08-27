import pyglet
from pyglet.gl import *
from pyglet import image
import random
import copy
from itertools import chain
import struct

import graph
import drawUtils

class Hexagon():
	def __init__(self, centreCoordinates, radius=20, hexIndex=False, jitterStrength=False):
		self.hexIndex = hexIndex
		self.centre = graph.Vertex( coordinates=centreCoordinates, hexes=[self])
		self.radius = radius
		self.points = []
		self.lowestPoint = False
		self.createVertices()
		self.edges = dict()
		self.regularHexPoints = copy.deepcopy(self.points)
		self.regularHexCentre = copy.deepcopy(self.centre)
		self.neighbours = dict()
		self.drainageNeighbour = False
		self.drainedNeighbours = []
		self.fillColor = False #(random.random(),random.random(),random.random(),0.5)
		self.land = False
		self.distanceFromWater = False
		self.water = False
		if jitterStrength:
			self.jitterPoints(jitterStrength)
		self.centre = self.calculateCentrePoint()
	
	def createVertices(self):
		sqrtThree = 1.73205080757
		innerRadius = (sqrtThree*self.radius)/2
		#N, Top point
		self.points.append( graph.Vertex( coordinates=(self.centre.x, self.centre.y+self.radius), hexes=[self] ))
		#NE
		self.points.append( graph.Vertex( coordinates=(self.centre.x+innerRadius, self.centre.y+(self.radius/2)), hexes=[self] ))
		#SE
		self.points.append( graph.Vertex( coordinates=(self.centre.x+innerRadius, self.centre.y-(self.radius/2)), hexes=[self] ))
		#S
		self.points.append( graph.Vertex( coordinates=(self.centre.x, self.centre.y-self.radius), hexes=[self] ))
		#SW
		self.points.append( graph.Vertex( coordinates=(self.centre.x-innerRadius, self.centre.y-(self.radius/2)), hexes=[self] ))
		#NW
		self.points.append( graph.Vertex( coordinates=(self.centre.x-innerRadius, self.centre.y+(self.radius/2)), hexes=[self] ))

	def createEdges(self):
		# Create an edge for each pair of points
		for i in range(len(self.points)-1):
			self.edges.append(graph.Edge( vertices=(self.points[i], self.points[i+1]), hexes=[self] ))
		# Edge departing from last point returns to first point
		self.edges.append(graph.Edge( vertices=(self.points[5], self.points[0]), hexes=[self] ))

	def getSuccessivePoint(self, v0):
		#print("getSuccessivePoint calling get point index")
		v0index, indexFound = self.getPointIndex(v0)
		if indexFound:
			return self.points[ (v0index+1) % len(self.points) ]
		#print("getSuccessivePoint returning false")
		return False

	def getPointIndex(self, v0):
		for i in range(len(self.points)):
			if self.points[i] == v0:
				# Return index at which point is found
				#print("... point index determined as " + str(i))
				# Zeroy is a 'falsy' value in python, so accompany index with a flag
				return i, True
		# Point was not found
		#print("getPointIndex returning false")		
		return False, False

	def getPointCoordinatesList(self, pointNumber):
		if pointNumber < len(self.points):
			# Return coord list for given point
			return [self.points[pointNumber].x, self.points[pointNumber].y]
		return False

	def getPerimeterCoordinatesList(self):
		return list(chain.from_iterable( [(self.points[n].x, self.points[n].y) for n in range(len(self.points))]))

	def getCentreCoordinates(self):
		return [self.centre.x, self.centre.y]

	# Randomly shifts all point locations by a random value between +/-(edgeLength * jitterStrength)
	def jitterPoints(self, jitterStrength=0.2):
		maxJitter = jitterStrength*self.radius
		for i in range(len(self.points)):
			self.points[i].x += random.uniform(-maxJitter, maxJitter)
			self.points[i].y += random.uniform(-maxJitter, maxJitter)

	def calculateCentrePoint(self, points=False):
		points = points if points else self.points
		xSum = 0
		ySum = 0
		totalPoints = 0
		for point in points:
			xSum += point.x
			ySum += point.y
			totalPoints += 1
		return graph.Vertex( (xSum/totalPoints, ySum/totalPoints), hexes=[self] )

	def addHexToNeighbourhood(self, hexGrid, hexesInOddRow):
		#print("Adding hex %s to nhood..." % (str(self.hexIndex)))

		# Identify new hex's index
		rowIsOdd = self.hexIndex[1]%2 == 1

		# Identify SE neighbouring hex, if one exists
		hasSENeighbour = self.hexIndex[0] < hexesInOddRow or rowIsOdd
		# Identify SW neighbouring hex, if one exists
		hasSWNeighbour = self.hexIndex[0] > 0 or rowIsOdd
		# No southern neighbours for the first row... 
		if self.hexIndex[1] == 0:
			hasSENeighbour = False
			hasSWNeighbour = False

		# Not last column, unless this row is odd (previous row is therefore longer)
		if hasSENeighbour:
			x = self.hexIndex[0]+1 if rowIsOdd else self.hexIndex[0]
			y = self.hexIndex[1]-1
			#print("SE Neighbour of Hex %s has x,y: (%d, %d)" % (self.hexIndex, x, y))
			southeastNeighbour = hexGrid[y][x]
			## Adopt SE neighbour's points
			### self SE point is neighbour's N point
			self.points[2] = southeastNeighbour.points[0]
			self.points[2].addHexNeighbours([self])
			### self S point is neighbour's NW point
			self.points[3] = southeastNeighbour.points[5]
			self.points[3].addHexNeighbours([self])
			## Log neighbour relationship
			self.neighbours[2] = southeastNeighbour
			southeastNeighbour.neighbours[5] = self
			# Records points as neighbours to each other if not already
			#  reciprocal relationship is automatically handled
			self.points[2].addVertexNeighbour(self.points[3])
		else:
			#print("No SE neighbour for hex %s." % (str(self.hexIndex)))
			pass

		# Not first column, unless this row is even (previous row is therefore longer)
		if hasSWNeighbour:
			x = self.hexIndex[0]-1 if not rowIsOdd else self.hexIndex[0]
			y = self.hexIndex[1]-1
			#print("SW Neighbour of Hex %s has x,y: (%d, %d)" % (self.hexIndex, x, y))
			southwestNeighbour = hexGrid[y][x]
			## Adopt SW neighbour's points
			### self S point is neighbour's NE point
			# This may have already been added from the SE neighbour
			if not hasSENeighbour:
				self.points[3] = southwestNeighbour.points[1]
				self.points[3].addHexNeighbours([self])
			### self SW point is neighbour's N point
			self.points[4] = southwestNeighbour.points[0]
			self.points[4].addHexNeighbours([self])
			## Log neighbour relationship
			self.neighbours[3] = southwestNeighbour
			southwestNeighbour.neighbours[0] = self
			# Records points as neighbours to each other if not already
			#  reciprocal relationship is automatically handled
			self.points[3].addVertexNeighbour(self.points[4])
		else:
			#print("No SW neighbour for hex %s." % (str(self.hexIndex)))
			pass

		# Identify W neighbouring hex, if one exists
		# Not first column...
		if self.hexIndex[0] > 0:
			x = self.hexIndex[0]-1
			y = self.hexIndex[1]
			#print("W Neighbour of Hex %s has x,y: (%d, %d)" % (self.hexIndex, x, y))		
			westNeighbour = hexGrid[y][x]
			## Adopt W neighbour's points
			### self SW point is neighbour's SE point
			# This may have already been added from the SW neighbour
			if not hasSWNeighbour:
				self.points[4] = westNeighbour.points[2]
				self.points[4].addHexNeighbours([self])
			### self NW point is neighbour's NE point
			self.points[5] = westNeighbour.points[1]
			self.points[5].addHexNeighbours([self])
			## Log neighbour relationship
			self.neighbours[4] = westNeighbour
			westNeighbour.neighbours[1] = self
			# Records points as neighbours to each other if not already
			#  reciprocal relationship is automatically handled
			self.points[4].addVertexNeighbour(self.points[5])			
		else:
			#print("No W neighbour for hex %s." % (str(self.hexIndex)))
			pass

	def drawHex(self, fullHex=True, drawEdges=True, drawPoints=False, edgeColor=(1.0,0.0,0.0,1.0), pointColor=(0.0,1.0,0.0,1.0), drawRegularHexGrid=False):
		pointsList = self.points if not drawRegularHexGrid else self.regularHexPoints
		pointsList = list(chain.from_iterable(pointsList))
		numEdges = 6
		if not fullHex:
			numEdges = 4
			pointsList = pointsList[:numEdges*2]
			if drawEdges:
				# Draw edges
				pyglet.gl.glColor4f(*edgeColor)
				# Line strip instead of loop
				pyglet.graphics.draw(numEdges, pyglet.gl.GL_LINE_STRIP,
					('v2f', pointsList)
				)
		else:
			if drawEdges:
				# Draw edges
				pyglet.gl.glColor4f(*edgeColor)
				# Line loop to reduce vertex list requirements
				pyglet.graphics.draw(numEdges, pyglet.gl.GL_LINE_LOOP,
					('v2f', pointsList)
				)
		if drawPoints:
			# Draw points
			pyglet.gl.glColor4f(*pointColor)
			pyglet.graphics.draw(numEdges, pyglet.gl.GL_POINTS,
				('v2f', pointsList)
			)
		
	def drawFilledHex(self, fillColor=False, drawRegularHexGrid=False):
		if not fillColor:
			fillColor = self.fillColor
		if fillColor:
			pointsList = self.regularHexPoints if drawRegularHexGrid else self.points
			centrePoint = self.regularHexCentre if drawRegularHexGrid else self.centre
			firstPoint = [pointsList[0].x, pointsList[0].y]
			# Polygon centre point coordinates are first values
			pointsList = [centrePoint.x, centrePoint.y] + self.getPerimeterCoordinatesList()
			pointsList.extend(firstPoint)
			# Draw filled polygon
			# Scale opacity by centre point's altitude
			color = tuple()
			if self.land:
				color = tuple([self.centre.altitude * fillColor[x] for x in range(3)] + [fillColor[3]])
				#pyglet.gl.glColor4f(fillColor[0], fillColor[1], fillColor[2], fillColor[3]*self.centre.altitude)
			else: 
				# Not land, so do not colour by altitude
				color = tuple(fillColor)
			pyglet.gl.glColor4f(*color)
			# Polygon is always drawn as fullHex
			glEnable(GL_BLEND)
			glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
			pyglet.graphics.draw(int(len(pointsList)/2), pyglet.gl.GL_TRIANGLE_FAN,
				('v2f', pointsList)
			)		

	def drawHexCentrePoint(self, drawRegularHexCentre=False, pointColor=(1.0,0.0,1.0,1.0)):
		point = self.regularHexCentre if drawRegularHexCentre else self.centre
		pyglet.gl.glColor4f(*pointColor)
		pyglet.graphics.draw(1, pyglet.gl.GL_POINTS,
			('v2f', point)
		)

	def clipPointsToScreen(self, widthInterval=[0,800], heightInterval=[0,600], useRegularPoints=True):
		#print("Clipping hex " + str(self.hexIndex))
		if useRegularPoints:
			# Even if regular points are being clipped, jittered must be clipped first
			# this accomodates scenario where the regular point was valid but was jittered out
			# of bounds. 
			self.clipPointsToScreen(widthInterval, heightInterval, False)
		# Regular hexagon points can be used to avoid jittering causing gaps around perimeter
		hexPoints = self.regularHexPoints if useRegularPoints else self.points
		for i in range(len(hexPoints)):
			#print(" p%d: (%f, %f)" % (i, hexPoints[i][0], hexPoints[i][1]))
			clipped = False
			# Clip y values to screen
			if hexPoints[i].y >= heightInterval[1]:
				#print(" ..clipped hexpoints[%d][1] (%d) to heightInterval[1] %d" % (i, hexPoints[i][1], heightInterval[1]))
				clipped = True
				# Set y to top edge of screen
				self.points[i].y = heightInterval[1]
			elif hexPoints[i].y <=  heightInterval[0]:
				#print(" ..clipped hexpoints[%d][1] (%d) to heightInterval[0] %d" % (i, hexPoints[i][1],heightInterval[0]))
				clipped = True
				# Set y to bottom of screen
				self.points[i].y =  heightInterval[0]

			# Clip x values to screen
			if hexPoints[i].x >= widthInterval[1]:
				#print(" ..clipped hexpoints[%d][0] (%d) to widthInterval[1] %d" % (i, hexPoints[i][0],widthInterval[1]))
				clipped = True
				# Set x to east edge of screen
				self.points[i].x = widthInterval[1]
			elif hexPoints[i].x <=  widthInterval[0]:
				#print(" ..clipped hexpoints[%d][0] (%d) to widthInterval[0] %d" % (i, hexPoints[i][0],widthInterval[0]))				
				clipped = True
				# Set x to west edge of screen
				self.points[i].x =  widthInterval[0]
			
			if clipped:
				#print(" after clipping, point: " + str(self.points[i]))
				pass
			else:
				#print(" no clipping required, point:"  + str(self.points[i]))
				pass
		self.centre = self.calculateCentrePoint(self.points)

	def compareToMaskImage(self, maskImageData, imageWidth, passRate=0.4, attenuation=0.8, drawAttenuatedPoints=False):
		# Perimeter points and centre point each get a 'vote'
		# Check points against mask image, register votes if point and mask location match
		if not self.land or self.water:
			totalVotes = 0
			attenuatedPointsList = []
			for point in self.points:
				#print("Point: " + str(point))
				# Attenuated positions are closer to the centre of the hex
				attenuatedX = int(self.centre.x + (point.x - self.centre.x)*attenuation)
				attenuatedY = int(self.centre.y + (point.y - self.centre.y)*attenuation)

				i = int(int(attenuatedX) + ((int(attenuatedY)-1) * imageWidth))-1
				#print("Point [%f, %f] had an index of: %d" % (point[0], point[1], i))
				#if maskImageData[i] > 0:
				#image_data = maskImageData.get_region(attenuatedX, attenuatedY, 1, 1).get_image_data()
				# Extract intensity info
				#data = image_data.get_data('I', 1)
				data = maskImageData[i]
				# Convert from byte to int
				data = struct.unpack('<B', data)[0]

				if data > 0:
				#	print("Vote")
				 	totalVotes += 1
				# else:
				# 	print("No votes")

				# If points are to be drawn, assemble them into a list
				if drawAttenuatedPoints:
					attenuatedPointsList.extend([attenuatedX, attenuatedY])

			if drawAttenuatedPoints:
				pyglet.gl.glColor4f(1.0,0.0,0.0,1.0)
				pyglet.graphics.draw(int(len(attenuatedPointsList)/2), pyglet.gl.GL_POINTS,
					('v2f', attenuatedPointsList)
				)

			if totalVotes >= passRate*len(self.points):
				#print("Hex %s passed mask-match with %d votes (%d to pass)." % (self.hexIndex, totalVotes, passRate*len(self.points)))
				return True
		return False

	def findLowestPoint(self, forceRecalculation=False):
		# Check if it has already been calculated
		if not self.lowestPoint or forceRecalculation:
			# Find the lowest perimeter point in hex perimeter
			self.lowestPoint = self.points[0]
			for point in self.points:
				if point.altitude < self.lowestPoint.altitude:
					# A new lowest has been found
					self.lowestPoint = point
		return self.lowestPoint