import math
import pyglet
from pyglet.gl import *
from pyglet import image
import random

from noise import snoise2

import terrain
import drawUtils

class WeatherSystem():
	def __init__(self, width, height, gridDivisions = 10):
		self.systemWidth = width
		self.systemHeight = height
		self.particles = set()
		self.spawnMoistureParticles()
		#self.spatialGrid = [ [ [] for y in range(gridSize) ] for x in range(gridSize) ]
		self.noise = terrain.createNoiseList(self.systemWidth, self.systemHeight)

	def updateParticles(self, deltaTime=1):
		for particle in self.particles:
			newX = ((particle.position[0] + deltaTime * particle.velocity[0]) + self.systemWidth) % self.systemWidth
			newY = ((particle.position[1] + deltaTime * particle.velocity[1]) + self.systemHeight) % self.systemHeight
			particle.position = (newX, newY)

	def spawnMoistureParticles(self, totalParticles=1000):
		print("Generating particles of moisture for weather system...")
		# Using poisson discs, randomly place a 
		for i in range(totalParticles):
			x, y = self.generatePoint()
			self.particles.add( MoistureParticle( x, y, moisture=random.random() ) )

	def generatePoint(self):
		# Generate a point within width and height interval
		return random.uniform(0, self.systemWidth), random.uniform(0, self.systemHeight)

	def drawMoistureParticles(self):
		particle_batch = pyglet.graphics.Batch()
		verts = []
		width = 4
		for particle in self.particles:
			#particle.drawMoistureParticle()
			verts.extend([particle.position[0]-width/2, particle.position[1]-width/2,
				particle.position[0]+width/2, particle.position[1]-width/2,
				particle.position[0]+width/2, particle.position[1]+width/2,
				particle.position[0]-width/2, particle.position[1]-width/2,
				particle.position[0]+width/2, particle.position[1]+width/2,
				particle.position[0]-width/2, particle.position[1]+width/2
			])
		pyglet.gl.glColor4f(1, 1, 1, 0.5)
		pyglet.graphics.draw(len(verts)/2, pyglet.gl.GL_TRIANGLES,
			('v2f', verts)
		)

class MoistureParticle():
	def __init__(self, x, y, moisture):
		self.position = (x, y)
		velLimit = 10
		self.velocity = (random.uniform(-velLimit, velLimit), random.uniform(-velLimit, velLimit))
		self.moisture = moisture if moisture else random.random()
	def changeVelocity(self, xChange, yChange):
		self.velocity = (self.velocity[0]+xChange, self.velocity[1]+yChange)

	# Draw particle as scattering of low opacity white squares
	def drawMoistureParticle(self):
		drawUtils.drawSquare(self.position, 4, (1,1,1,0.5), True)
		# for i in range(random.randint(1,5)):
		# 	drawUtils.drawSquare((self.position[0]+random.uniform(-2, 2), self.position[1]+random.uniform(-2, 2)),
		# 		random.randint(3,4), 
		# 		(1,1,1, random.uniform(0.1 ,0.3))
		# 	)
