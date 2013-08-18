import math

class Vertex():
	def __init__(self, coordinates, hexes=[], edges=[]):
		self.x = coordinates[0]
		self.y = coordinates[1]
		self.surroundingHexes = dict()
		self.addHexNeighbours(hexes)
		self.departingEdges = edges
		self.altitude = False

	def addHexNeighbours(self, hexes):
		for nextHex in hexes:
			# Only add hex if it isn't already included
			if not nextHex.hexIndex in self.surroundingHexes:
				self.surroundingHexes[len(self.surroundingHexes)] = nextHex

	def addDepartingEdge(self, edges):
		self.departingEdges.extend(edges)


class Edge():
	def __init__(self, vertices, hexes=[]):
		self.v1 = vertices[0]
		self.v2 = vertices[1]
		self.adjacentHexes = hexes

	def addAdjacentHexes(self, hexes):
		self.adjacentHexes.extend(hexes)