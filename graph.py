import math

class Vertex():
	def __init__(self, coordinates, hexes=[]):
		self.id = next(vertexIdGen)
		self.x = coordinates[0]
		self.y = coordinates[1]
		self.surroundingHexes = dict()
		self.neighbouringVertices = []
		self.addHexNeighbours(hexes)
		self.altitude = False
		# Neighbouring vertex which is drained into from this vertex
		self.drainingNeighbour = False
		# Neighbouring vertices which drain into this vertex
		self.drainedNeighbours = []
		self.minBorderDistance = False

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
			if nextHex.water:
				return True
		return False

	def distanceFrom(self, v1):
		return math.sqrt((v1.x - self.x)**2 + (v1.y - self.y)**2)

	def getCoords(self):
		return [self.x, self.y]

def vertexIdGenerator():
	i = 0
	while True:
		yield i
		i += 1

# Initialise the generator
vertexIdGen = vertexIdGenerator()