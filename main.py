import pyglet
#from pyglet.scene2d import *
from pyglet.gl import *
import hexagon
import random
import math

window = pyglet.window.Window()
screenWidth = 800
screenHeight = 600
window.set_size(800, 600)
image = pyglet.resource.image('kitten.jpg')

gridLength = 10
grid = [[hexagon.Hexagon() for x in range(gridLength)] for y in range(gridLength)]

#Hexagon dimensions
radius = 10 #also is sidelength
#Hex Point Offsets from centre
hexPointOffsets = []
nextVector = (0,1)
for i in range(6):
	hexPointOffsets.append(nextVector)
	nextVector = (math.cos(60)*nextVector[0], -1*math.sin(60)*nextVector[1])

##print(hexPointOffsets)
#pyglet.gl.glColor4f(1.0,0,0,1.0)
#pyglet.graphics.draw(1, pyglet.gl.GL_POINTS,
#    	('v2i', (250, 250))
#)

def drawHex(fullHex=True, centrePoint=(400,400), radius=50, innerRadius=False, edgeColor=(0.0,0.0,1.0,1.0)):
	edgeLength = radius
	if not innerRadius:
		sqrtThree = 1.73205080757
		innerRadius = (sqrtThree*radius)/2
	points=[]
	#Top point (North)
	points.append(centrePoint[0])
	points.append(centrePoint[1]+radius)
	#NE
	points.append(centrePoint[0]+innerRadius)
	points.append(centrePoint[1]+(edgeLength/2))
	#SE
	points.append(centrePoint[0]+innerRadius)
	points.append(centrePoint[1]-(edgeLength/2))
	#S
	points.append(centrePoint[0])
	points.append(centrePoint[1]-radius)
	# FullHex draws all six sides, otherwise only three are drawn
	# Missing out three sides reduces draws for gridded hexagons where edges overlap
	numEdges = 4
	if fullHex:
		#SW
		points.append(centrePoint[0]-innerRadius)
		points.append(centrePoint[1]-(edgeLength/2))
		#NW
		points.append(centrePoint[0]-innerRadius)
		points.append(centrePoint[1]+(edgeLength/2))
		numEdges = 6
	# Draw edges
	pyglet.gl.glColor4f(*edgeColor)
	pyglet.graphics.draw(numEdges, pyglet.gl.GL_LINE_STRIP,
    	('v2f', points)
	)
	# Draw points
	pyglet.gl.glColor4f(0.0,1.0,0.0,1.0)
	pyglet.graphics.draw(numEdges, pyglet.gl.GL_POINTS,
    	('v2f', points)
	)
	
def drawGrid():
	sqrtThree = 1.73205080757
	radius = 50
	innerRadius = (sqrtThree*radius)/2
	startX = 0
	startY = 0
	rows = 15
	cols = 15
	for y in range(rows):
		for x in range(cols):
			xoffset = 0
			if y%2==0:
				xoffset = innerRadius
			drawHex(False, (startX+xoffset+x*2*innerRadius, startY+y*(radius*1.5)), radius)

def drawFittedGrid(hexesInRow=10):
	# Width of hexagons (w=root3*Radius/2) is calculated from screenwidth, which then determines hex radius
	hexWidthRadius = (screenWidth / hexesInRow) / 2
	hexRadius = (2*hexWidthRadius) / math.sqrt(3) # Also edge length
	# Loop over hex coordinate locations
	hexCentreY = 0
	rowNumber = 0
	while hexCentreY - hexRadius < screenHeight:
		hexCentreX = 0 
		# Offset each row to allow for tesselation
		if rowNumber%2==1:
			hexCentreX += hexWidthRadius
		# Draw all hexagons in row
		colNumber = 0
		while hexCentreX - hexWidthRadius < screenWidth:
			hexPolygon = hexagon.Hexagon((hexCentreX, hexCentreY), hexRadius)
			if rowNumber == 0:
				# Full hex must be drawn as West side will be seen
				hexPolygon.drawHex(True)
			else:
				hexPolygon.drawHex(False)
			#drawHex(False, (hexCentreX, hexCentreY), hexRadius, hexWidthRadius, (1.0, 0.0, 0.0, 1.0))
			hexCentreX += 2 * hexWidthRadius
			colNumber += 1
		rowNumber += 1
		hexCentreY += hexRadius * 1.5

@window.event
def on_draw():
	window.clear()
	#Draw centre
	cX = 250
	cY = 250
	#drawGrid()
	drawFittedGrid()
	#hexPolygon = hexagon.Hexagon((100, 100), 30)
	#hexPolygon.drawHex()
	#image.blit(0, 0)

print("Running app")
pyglet.app.run()
print("Ran app")
