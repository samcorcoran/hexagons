import pyglet
from pyglet.gl import *
from pyglet import image
import random
import copy
from itertools import chain

class Hexagon():
	def __init__(self, centrePoint=(0,0), radius=20, hexIndex=False, jitterStrength=False):
		self.hexIndex = hexIndex
		self.centre = centrePoint
		self.radius = radius
		self.points = self.calculatePoints()
		self.regularHexPoints = copy.deepcopy(self.points)
		self.regularHexCentre = self.centre
		self.neighbours = dict()
		self.fillColor = False #(random.random(),random.random(),random.random(),0.5)
		self.isLand = False
		self.isWater = False
		if jitterStrength:
			self.jitterPoints(jitterStrength)
		self.centre = self.calculateCentrePoint()
	
	def calculatePoints(self):
		sqrtThree = 1.73205080757
		innerRadius = (sqrtThree*self.radius)/2
		points=[]
		#N, Top point
		points.append([self.centre[0], self.centre[1]+self.radius])
		#NE
		points.append([self.centre[0]+innerRadius, self.centre[1]+(self.radius/2)])
		#SE
		points.append([self.centre[0]+innerRadius, self.centre[1]-(self.radius/2)])
		#S
		points.append([self.centre[0], self.centre[1]-self.radius])
		#SW
		points.append([self.centre[0]-innerRadius, self.centre[1]-(self.radius/2)])
		#NW
		points.append([self.centre[0]-innerRadius, self.centre[1]+(self.radius/2)])
		return points

	# Randomly shifts all point locations by a random value between +/-(edgeLength * jitterStrength)
	def jitterPoints(self, jitterStrength=0.2):
		maxJitter = jitterStrength*self.radius
		for i in range(len(self.points)):
			self.points[i][0] += random.uniform(-maxJitter, maxJitter)
			self.points[i][1] += random.uniform(-maxJitter, maxJitter)

	def calculateCentrePoint(self, points=False):
		points = points if points else self.points 
		xPoints, yPoints = zip(*points)
		return [sum(xPoints)/len(xPoints), sum(yPoints)/len(yPoints)]

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
			firstPoint = pointsList[0]
			# Polygon centre point are first values
			pointsList = centrePoint + list(chain.from_iterable(pointsList))
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
			if hexPoints[i][1] >= heightInterval[1]:
				#print(" ..clipped hexpoints[%d][1] (%d) to heightInterval[1] %d" % (i, hexPoints[i][1], heightInterval[1]))
				clipped = True
				# Set y to top edge of screen
				self.points[i][1] = heightInterval[1]
			elif hexPoints[i][1] <=  heightInterval[0]:
				#print(" ..clipped hexpoints[%d][1] (%d) to heightInterval[0] %d" % (i, hexPoints[i][1],heightInterval[0]))
				clipped = True
				# Set y to bottom of screen
				self.points[i][1] =  heightInterval[0]

			# Clip x values to screen
			if hexPoints[i][0] >= widthInterval[1]:
				#print(" ..clipped hexpoints[%d][0] (%d) to widthInterval[1] %d" % (i, hexPoints[i][0],widthInterval[1]))
				clipped = True
				# Set x to east edge of screen
				self.points[i][0] = widthInterval[1]
			elif hexPoints[i][0] <=  widthInterval[0]:
				#print(" ..clipped hexpoints[%d][0] (%d) to widthInterval[0] %d" % (i, hexPoints[i][0],widthInterval[0]))				
				clipped = True
				# Set x to west edge of screen
				self.points[i][0] =  widthInterval[0]
			
			if clipped:
				#print(" after clipping, point: " + str(self.points[i]))
				pass
			else:
				#print(" no clipping required, point:"  + str(self.points[i]))
				pass
		self.centre = self.calculateCentrePoint(self.points)

	def compareToMaskImage(self, maskImageData, imageWidth, passRate=0.5, attenuation=0.95):
		# Perimeter points and centre point each get a 'vote'
		xPoints, yPoints = zip(*self.points)
		attenuatedPerimeterX = [self.centre[0] + (x - self.centre[0])*attenuation for x in xPoints]
		attenuatedPerimeterY = [self.centre[1] + (y - self.centre[1])*attenuation for y in yPoints]
		attenuatedPerimeter = zip(attenuatedPerimeterX, attenuatedPerimeterY)

		totalVotes = 0
		# Check points against mask image
		for point in attenuatedPerimeter:
			#print("Point: " + str(point))
			i = int(int(point[0]) + ((int(point[1])-1) * imageWidth))-1
			#print("Point [%f, %f] had an index of: %d" % (point[0], point[1], i))
			if maskImageData[i] > 0:
				totalVotes += 1
		if totalVotes > 1:
			return True
		return False