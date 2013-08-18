import pyglet
from pyglet.gl import *
from pyglet import image
import random
import copy
from itertools import chain

import graph

class Hexagon():
	def __init__(self, centreCoordinates, radius=20, hexIndex=False, jitterStrength=False):
		self.hexIndex = hexIndex
		self.centre = graph.Vertex( coordinates=centreCoordinates )
		self.radius = radius
		self.points = []
		self.createVertices()
		self.edges = []
		self.regularHexPoints = copy.deepcopy(self.points)
		self.regularHexCentre = self.centre
		self.neighbours = dict()
		self.fillColor = False #(random.random(),random.random(),random.random(),0.5)
		self.isLand = False
		self.isWater = False
		if jitterStrength:
			self.jitterPoints(jitterStrength)
		self.centre = self.calculateCentrePoint()
	
	def createVertices(self):
		sqrtThree = 1.73205080757
		innerRadius = (sqrtThree*self.radius)/2
		#N, Top point
		self.points.append( graph.Vertex( coordinates=(self.centre.x, self.centre.y+self.radius) ) )
		#NE
		self.points.append( graph.Vertex( coordinates=(self.centre.x+innerRadius, self.centre.y+(self.radius/2)), hexes=[self] ))
		#SE
		self.points.append(graph.Vertex( coordinates=(self.centre.x+innerRadius, self.centre.y-(self.radius/2)), hexes=[self] ))
		#S
		self.points.append(graph.Vertex( coordinates=(self.centre.x, self.centre.y-self.radius), hexes=[self] ))
		#SW
		self.points.append(graph.Vertex( coordinates=(self.centre.x-innerRadius, self.centre.y-(self.radius/2)), hexes=[self] ))
		#NW
		self.points.append(graph.Vertex( coordinates=(self.centre.x-innerRadius, self.centre.y+(self.radius/2)), hexes=[self] ))

	def createEdges(self):
		# Create an edge for each pair of points
		for i in range(len(self.points)-1):
			self.edges.append(graph.Edge( vertices=(self.points[i], self.points[i+1]), hexes=[self] ))
		# Edge departing from last point returns to first point
		self.edges.append(graph.Edge( vertices=(self.points[5], self.points[0]), hexes=[self] ))

	def getPointCoordinatesList(self, pointNumber):
		if pointNumber < len(self.points):
			# Return coord list for given point
			return [self.points[pointNumber].x, self.points[pointNumber].y]
		return False

	def getPerimeterCoordinatesList(self):
		return list(chain.from_iterable( [(self.points[n].x, self.points[n].y) for n in range(len(self.points))]))

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
		return graph.Vertex( (xSum/totalPoints, ySum/totalPoints) )

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
		
	def drawFilledHex(self, drawFill=False, fillColor=False, drawRegularHexGrid=False):
		if self.fillColor:
			pointsList = self.regularHexPoints if drawRegularHexGrid else self.points
			centrePoint = self.regularHexCentre if drawRegularHexGrid else self.centre
			firstPoint = [pointsList[0].x, pointsList[0].y]
			# Polygon centre point coordinates are first values
			pointsList = [centrePoint.x, centrePoint.y] + self.getPerimeterCoordinatesList()
			pointsList.extend(firstPoint)
			# Draw filled polygon
			pyglet.gl.glColor4f(*self.fillColor)
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
		totalVotes = 0
		attenuatedPointsList = []
		for point in self.points:
			#print("Point: " + str(point))
			# Attenuated positions are closer to the centre of the hex
			attenuatedX = self.centre.x + (point.x - self.centre.x)*attenuation
			attenuatedY = self.centre.y + (point.y - self.centre.y)*attenuation

			i = int(int(attenuatedX) + ((int(attenuatedY)-1) * imageWidth))-1
			#print("Point [%f, %f] had an index of: %d" % (point[0], point[1], i))
			
			if maskImageData[i] > 0:
				totalVotes += 1

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