

class Hexagon():
	def __init__(self, centrePoint=(0,0), radius=20):
		self.centre = centrePoint
		self.radius = radius

	def getPerimeterCoords(self):
		topPointX = self.centre[0]
		topPointY = self.centre[1]