import pyglet
#from pyglet.scene2d import *
from pyglet.gl import *
import hexagon
import random
import math

window = pyglet.window.Window()
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

def drawHex(fullHex=True, startPoint=(400,400), radius=50):
	edgeLength = radius
	sqrtThree = 1.73205080757
	innerRadius = (sqrtThree*radius)/2
	points=[]
	#Top point (North)
	points.append(startPoint[0])
	points.append(startPoint[1]+radius)
	#NE
	points.append(startPoint[0]+innerRadius)
	points.append(startPoint[1]+(edgeLength/2))
	#SE
	points.append(startPoint[0]+innerRadius)
	points.append(startPoint[1]-(edgeLength/2))
	#S
	points.append(startPoint[0])
	points.append(startPoint[1]-radius)

	# FullHex draws all six sides, otherwise only three are drawn
	# Missing out three sides reduces draws for gridded hexagons where edges overlap
	numEdges = 4
	if fullHex:
		#SW
		points.append(startPoint[0]-innerRadius)
		points.append(startPoint[1]-(edgeLength/2))
		#NW
		points.append(startPoint[0]-innerRadius)
		points.append(startPoint[1]+(edgeLength/2))
		numEdges = 6

	#Draw edges
	pyglet.gl.glColor4f(0.0,0.0,1.0,1.0)
	pyglet.graphics.draw(4, pyglet.gl.GL_LINE_STRIP,
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

@window.event
def on_draw():
	window.clear()
	#Draw centre
	cX = 250
	cY = 250
	drawGrid()
	#image.blit(0, 0)

print("Running app")
pyglet.app.run()
print("Ran app")
