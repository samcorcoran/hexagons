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
	hexGrid = createFittedHexGrid(hexesInRow)
	for row in hexGrid:
		for nextHex in row:
			nextHex.drawHex()

# Returns grid of hexagons
def createFittedHexGrid(hexesInRow=10):
	# Width of hexagons (w=root3*Radius/2) is calculated from screenwidth, which then determines hex radius
	hexWidth = (screenWidth/hexesInRow)
	hexRadius = hexWidth / math.sqrt(3) # Also edge length

	hexesInCol = int(screenHeight / (hexRadius))
	gridRows = []

	# Loop over hex coordinate locations
	hexCentreY = 0
	row = 0
	while hexCentreY - hexRadius < screenHeight:
		#print("Row number: %d" % (row))
		hexCentreX = 0 
		# Offset each row to allow for tesselation
		if row%2==1:
			hexCentreX += hexWidth / 2
		# Draw all hexagons in row
		nextRow = []
		col = 0
		while hexCentreX - (hexWidth/2) < screenWidth:
			#print("Col number: %d" % (col))
			hexPolygon = hexagon.Hexagon((hexCentreX, hexCentreY), hexRadius)
			nextRow.append(hexPolygon)
			hexCentreX += hexWidth
			col += 1
		gridRows.append(nextRow)
		row += 1
		hexCentreY += hexRadius * 1.5
	return gridRows

def drawHexGridFromPoints(hexesInRow=10):
	hexGrid = createHexGridFromPoints(hexesInRow)
	screenClipGridHexagons(hexGrid)
	for row in hexGrid:
		for nextHex in row:
			nextHex.drawHex()
			nextHex.drawHex(True, True, False, (0.0, 0.0, 1.0, 1.0), True)


# Build a hex grid, hex by hex, using points of neighbouring generated hexagons where possible
def createHexGridFromPoints(hexesInRow=10):
	# Width of hexagons (w=root3*Radius/2) is calculated from screenwidth, which then determines hex radius
	hexWidth = (screenWidth/hexesInRow)
	hexRadius = (hexWidth) / math.sqrt(3) # Also edge length

	hexesInCol = int(screenHeight / (hexRadius))
	gridRows = []

	# Loop through hexagon locations, using index to determine if some points should be taken from neighbours
	# Loop over hex coordinate locations
	hexCentreY = 0
	row = 0
	while hexCentreY - hexRadius < screenHeight:
		#print("Row number: %d" % (row))
		hexCentreX = 0 
		# Offset each row to allow for tesselation
		if row%2==1:
			hexCentreX += hexWidth / 2
		# Draw all hexagons in row
		nextRow = []
		col = 0
		while hexCentreX - (hexWidth/2) < screenWidth:
			#print("Col number: %d" % (colNumber))
			hexPolygon = hexagon.Hexagon((hexCentreX, hexCentreY), hexRadius, jitterStrength=0.25)

			# Adopt neighbour point locations
			# Non-first row must adopt southern points locations from the previous row
			if row > 0 :
				# Even rows start with a x offset, so must index a different southern hexagon
				colIndexOffset = row%2

				# Last hex on row cannot look SE
				if col < hexesInRow:
					# SE, take SE neighbour's N point
					hexPolygon.points[2] = gridRows[row-1][col+colIndexOffset].points[0]
					# S, take SE neighbour's NW point
					hexPolygon.points[3] = gridRows[row-1][col+colIndexOffset].points[5]
				else:
					# S; Alternatively, take SW neighbour's NE point
					hexPolygon.points[3] = gridRows[row-1][col-1+colIndexOffset].points[1]

				# If hex isn't in first column, there will be a SW neighbour too, 
				#  otherwise, retain generated point
				if col+colIndexOffset > 0:
					# SW, take SW neighbour's N point
					hexPolygon.points[4] = gridRows[row-1][col-1+colIndexOffset].points[0]
			if col > 0:
				if row == 0:
					# SW, take west neighbour SE point
					hexPolygon.points[4] = nextRow[col-1].points[2]
				# NW, Adopt W neighbour's NE point as this
				hexPolygon.points[5] = nextRow[col-1].points[1]
			# Remaining points (N, NE) are not overwritten				

			nextRow.append(hexPolygon)
			hexCentreX += hexWidth
			col += 1
		gridRows.append(nextRow)
		row += 1
		hexCentreY += hexRadius * 1.5
	return gridRows

def screenClipGridHexagons(hexGrid):
	# Loop over boundary hexes, fixing their off-screen points to the screen boundary
	# Check works on regular hexagon's points rather than jittered points
	widthInterval = [0, screenWidth]
	heightInterval = [0, screenHeight]
	# Bottom row
	for nextHex in hexGrid[0][:]:
		nextHex.clipPointsToScreen(widthInterval, heightInterval)
	# Top row
	for nextHex in hexGrid[-1][:]:
		nextHex.clipPointsToScreen(widthInterval, heightInterval)
	# Left and right columns
	for nextRow in hexGrid:
		nextRow[0].clipPointsToScreen(widthInterval, heightInterval)
		nextRow[-1].clipPointsToScreen(widthInterval, heightInterval)


@window.event
def on_draw():
	window.clear()
	#Draw centre
	cX = 250
	cY = 250
	#drawGrid()
	#drawFittedGrid()
	#createFittedHexGrid()
	drawHexGridFromPoints(5)
	#hexPolygon = hexagon.Hexagon((100, 100), 30)
	#hexPolygon.drawHex()
	#image.blit(0, 0)

print("Running app")
pyglet.app.run()
print("Ran app")
