import pyglet
import random
from itertools import chain

class Hexagon():
	def __init__(self, centrePoint=(0,0), radius=20, jitterStrength=False):
		self.centre = centrePoint
		self.radius = radius
		self.points = self.calculatePoints()
		if jitterStrength:
			self.jitterPoints(jitterStrength)
	
	def calculatePoints(self):
		sqrtThree = 1.73205080757
		innerRadius = (sqrtThree*self.radius)/2
		points=[]
		#N, Top point
		points.append((self.centre[0], self.centre[1]+self.radius))
		#NE
		points.append((self.centre[0]+innerRadius, self.centre[1]+(self.radius/2)))
		#SE
		points.append((self.centre[0]+innerRadius, self.centre[1]-(self.radius/2)))
		#S
		points.append((self.centre[0], self.centre[1]-self.radius))
		#SW
		points.append((self.centre[0]-innerRadius, self.centre[1]-(self.radius/2)))
		#NW
		points.append((self.centre[0]-innerRadius, self.centre[1]+(self.radius/2)))
		return points

	# Randomly shifts all point locations by a random value between +/-(edgeLength * jitterStrength)
	def jitterPoints(self, jitterStrength=0.2):
		maxJitter = jitterStrength*self.radius
		for i in range(len(self.points)):
			x = self.points[i][0] + random.uniform(-maxJitter, maxJitter)
			y = self.points[i][1] + random.uniform(-maxJitter, maxJitter)
			self.points[i] = (x, y)

	def drawHex(self, fullHex=True, drawEdges=True, drawPoints=False, edgeColor=(1.0,0.0,0.0,1.0)):
		pointsList = []
		pointsList = list(chain.from_iterable(self.points))
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
			pyglet.gl.glColor4f(0.0,1.0,0.0,1.0)
			pyglet.graphics.draw(numEdges, pyglet.gl.GL_POINTS,
				('v2f', pointsList)
			)