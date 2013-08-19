import math

class Vertex():
	def __init__(self, coordinates, hexes=[]):
		self.x = coordinates[0]
		self.y = coordinates[1]
		self.surroundingHexes = dict()
		self.neighbouringVertices = []
		self.addHexNeighbours(hexes)
		self.altitude = False
		# Neighbouring vertex which is drained into from this vertex
		self.drainageNeighbour = False
		# Neighbouring vertices which drain into this vertex
		self.drainedNeighbours = []

	def addHexNeighbours(self, hexes):
		for nextHex in hexes:
			# Only add hex if it isn't already included
			if not nextHex.hexIndex in self.surroundingHexes:
				self.surroundingHexes[len(self.surroundingHexes)] = nextHex

	def addVertexNeighbour(self, newVertex):
		for neighbour in self.neighbouringVertices:
			# Prevent a vertex from being added multiple times
			if neighbour == newVertex:
				return False
		self.neighbouringVertices.append(newVertex)
		# Ensure reciprocal relationship
		newVertex.addVertexNeighbour(self)
		return True

	def isByWater(self):
		for nextHex in self.surroundingHexes.values():
			if nextHex.isWater:
				return True
		return False

