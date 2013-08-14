import pyglet
from itertools import chain

class Hexagon():
	def __init__(self, centrePoint=(0,0), radius=20):
		self.centre = centrePoint
		self.radius = radius
		self.points = self.calculatePoints()
	
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

	def drawHex(self, fullHex=True, edgeColor=(1.0,0.0,0.0,1.0)):
		pointsList = []
		pointsList = list(chain.from_iterable(self.points))
		numEdges = 6
		if not fullHex:
			numEdges = 4
			pointsList = pointsList[:numEdges*2]
			# Draw edges
			pyglet.gl.glColor4f(*edgeColor)
			# Line strip instead of loop
			pyglet.graphics.draw(numEdges, pyglet.gl.GL_LINE_STRIP,
				('v2f', pointsList)
			)
		else:
			# Draw edges
			pyglet.gl.glColor4f(*edgeColor)
			# Line loop to reduce vertex list requirements
			pyglet.graphics.draw(numEdges, pyglet.gl.GL_LINE_LOOP,
				('v2f', pointsList)
			)
		# Draw points
		pyglet.gl.glColor4f(0.0,1.0,0.0,1.0)
		pyglet.graphics.draw(numEdges, pyglet.gl.GL_POINTS,
			('v2f', pointsList)
		)