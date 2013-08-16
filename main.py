import pyglet
from pyglet.gl import *
from pyglet import image
import hexagon
import random
import math

window = pyglet.window.Window()
screenWidth = 800
screenHeight = 600
window.set_size(800, 600)
maskImage = pyglet.resource.image('groundtruth.bmp')
gridChanged = True
hexGrid = []
landHexes = []
islands = []

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
	
def drawHexGrid(hexGrid, drawHexEdges=True, drawHexFills=True):
	if hexGrid:
		linePoints = []
		for row in hexGrid:
			for nextHex in row:
				if drawHexFills:
					# Draw hexagon fill
					nextHex.drawFilledHex()
				# Draw hexagon edges and/or points
				#nextHex.drawHex()
				# Draw hexagon centres
				#nextHex.drawHexCentrePoint()
				#nextHex.drawHexCentrePoint(True, (0,1,1,1))
				# Draw regular hexagon grid
				#nextHex.drawHex(True, True, False, (0.0, 0.0, 1.0, 1.0), True)
				linePoints.extend(nextHex.points[0])
				for point in nextHex.points:
					# Enter each point twice, for the two consecutive lines
					linePoints.extend(point + point)
				# Last point is first point, completing the loop
				linePoints.extend(nextHex.points[0])
		print("linePoints length: " + str(len(linePoints)))
		if drawHexEdges:
			pyglet.gl.glColor4f(0.0,0.0,1.0,1.0)
			pyglet.graphics.draw(int(len(linePoints)/2), pyglet.gl.GL_LINES,
				('v2f', linePoints)
			)
		print("Finished drawing")	

# Build a hex grid, hex by hex, using points of neighbouring generated hexagons where possible
def createHexGridFromPoints(hexesInRow=10, clipPointsToScreen=True):
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
	for nextHex in hexGrid[0]:
		nextHex.clipPointsToScreen(widthInterval, heightInterval)
	# Top row
	for nextHex in hexGrid[-1]:
		nextHex.clipPointsToScreen(widthInterval, heightInterval)
	# Left and right columns
	for nextRow in hexGrid:
		nextRow[0].clipPointsToScreen(widthInterval, heightInterval)
		nextRow[-1].clipPointsToScreen(widthInterval, heightInterval)

def findMarkedHexes(hexGrid):
	print("Begun finding masked hexes")
	maskImageData = maskImage.get_image_data()
	data = maskImageData.get_data('I', maskImage.width)
	totalHits = 0
	for n in range(len(data)):
		if not data[n] == 0:
			totalHits += 1 #print("n: %d contains %d" % (n, data[n]))
	print("Total hits: " + str(totalHits))
	print("Length of data: " + str(len(data)))
	hexCount = 0
	for row in hexGrid:
		for nextHex in row:
			#print("Hex " + str(hexCount))
			if nextHex.compareToMaskImage(data, maskImage.width):
				nextHex.fillColor = (1.0,0.0,0.0,1.0)
				# Indicate that hex must be land
				landHexes.append(nextHex)

			hexCount += 1
	print("Finished finding masked hexes")

def countHexesInGrid(hexGrid):
	total = 0
	for row in hexGrid:
		for nextHex in row:
			total += 1
	print("Total hexes: %d" % (total))

@window.event
def on_draw():
	global gridChanged
	global hexGrid
	hexesInRow = 100
	if gridChanged:
		window.clear()
		maskImage.blit(0, 0)
		#drawGrid()
		#drawFittedGrid()
		#createFittedHexGrid()
		hexGrid = createHexGridFromPoints(hexesInRow)
		screenClipGridHexagons(hexGrid)
		findMarkedHexes(hexGrid)
		countHexesInGrid(hexGrid)
		#hexPolygon = hexagon.Hexagon((100, 100), 30)
		#hexPolygon.drawHex()
		gridChanged = False
	drawHexGrid(hexGrid)

print("Running app")
pyglet.app.run()
print("Ran app")
