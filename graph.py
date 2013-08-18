import math

class Vertex():
	def __init__(self, coordinates, hexes=[], edges=[]):
		self.x = coordinates[0]
		self.y = coordinates[1]
		self.surroundingHexes = hexes
		self.departingEdges = edges

	def addHexNeighbours(self, hexes):
		self.hexes.extend(hexes)

	def addDepartingEdge(self, edges):
		self.edges.extend(edges)


class Edge():
	def __init__(self, vertices, hexes=[]):
		self.v1 = vertices[0]
		self.v2 = vertices[1]
		self.adjacentHexes = hexes

	def addAdjacentHexes(self, hexes):
		self.adjacentHexes.extend(hexes)