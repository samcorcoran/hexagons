import pyglet
from pyglet.gl import *
from pyglet import image
import hexagon
import random
import math
import copy

window = pyglet.window.Window()
screenWidth = 800
screenHeight = 600
window.set_size(800, 600)
maskImage = pyglet.resource.image('groundtruth2.bmp')
gridChanged = True
hexGrid = []
landHexes = dict()
waterHexes = dict()
islands = []

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
	totalHexes = 0
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
			#print("Creating hex %d, with (col,row): (%d, %d)" % (totalHexes, col, row))
			hexPolygon = hexagon.Hexagon((hexCentreX, hexCentreY), hexRadius, hexIndex=(col, row), jitterStrength=0.25)
			totalHexes += 1
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
		#print("Length of nextRow: %d" % (len(nextRow)))
		gridRows.append(nextRow)
		row += 1
		hexCentreY += hexRadius * 1.5
	return gridRows

# Compile list of neighbours that currently exist (southerly and westerly)
def assignExistingNeighbours(hexGrid):
	totalHexes = 0
	for row in hexGrid:
		for nextHex in row:
			#print("Assigning neighbours for nextHex index: " + str(nextHex.hexIndex) + "(Hexagon " + str(totalHexes) + ")")
			totalHexes += 1
			# Odd-numbered rows are right-shifted, so their southernly neighbours are offset relatively by 1
			# Odd rows SE neighbour has xIndex + 1
			# Odd rows SW neighbour shares an x index
			# Even rows SE neighbour shares an x index
			# Even rows SW neighbour has xIndex - 1
			# First row has no southern neighbours
			if not nextHex.hexIndex[1] == 0:
				# y is identical for both southernly neighbours
				y = nextHex.hexIndex[1]-1
				# SE
				# This xOffset is 1 on even rows and 0 on odd
				xOffset = 1 if nextHex.hexIndex[1] % 2 == 1 else 0
				x = nextHex.hexIndex[0]+xOffset
				# If right column on an 
				#print("SE x, y: %d, %d" % (x, y))
				# Odd rows are one hex shorter, so subtract 1 from row length when handling an even row
				# If you are on an odd row, previous row length is len(row)+1
				previousRowLength = len(row)+int(nextHex.hexIndex[1] % 2)-int((nextHex.hexIndex[1]+1) % 2)
				if x >= 0 and x < previousRowLength:
					#print("SE neighbour was found")
					neighbour = hexGrid[y][x]
					nextHex.neighbours["SE"] = neighbour
					# Add reciprocal neighbouring information
					neighbour.neighbours["NW"] = nextHex
				else:
					#print("No SE Neighbour")
					pass
				# SW
				# This xOffset is 0 on even rows and 1 on odd
				xOffset = 1 if nextHex.hexIndex[1] % 2 == 0 else 0
				x = nextHex.hexIndex[0]-xOffset
				#print("SW x, y: %d, %d" % (x, y))
				# Odd rows are one hex shorter, so subtract 1 from row length when handling an even row
				# If on an odd row, the previous row is len(row) - 1
				previousRowLength = len(row)-int((nextHex.hexIndex[1]+1) % 2)
				if x >= 0 and x < previousRowLength:
					#print("SW neighbour was found")
					neighbour = hexGrid[y][x]
					nextHex.neighbours["SW"] = neighbour
					# Add reciprocal neighbouring information
					neighbour.neighbours["NE"] = nextHex
				else:
					#print("No SW Neighbour")
					pass
			# First column has no 
			if not nextHex.hexIndex[0] == 0:
				#print("West neighbour was found: (%d, %d)" % (nextHex.hexIndex[0]-1, nextHex.hexIndex[1]))
				# W
				neighbour = hexGrid[nextHex.hexIndex[1]][nextHex.hexIndex[0]-1]
				nextHex.neighbours["W"] = neighbour
				# Add reciprocal neighbouring information
				neighbour.neighbours["E"] = nextHex

def screenClipGridHexagons(hexGrid):
	# Loop over boundary hexes, fixing their off-screen points to the screen boundary
	# Check works on regular hexagon's points rather than jittered points
	widthInterval = [0, screenWidth]
	heightInterval = [0, screenHeight]
	# Bottom row
	#print("Clipping bottom row")
	for nextHex in hexGrid[0]:
		nextHex.clipPointsToScreen(widthInterval, heightInterval)
	# Top row
	#print("Clipping top row")
	for nextHex in hexGrid[-1]:
		nextHex.clipPointsToScreen(widthInterval, heightInterval)
	# Left and right columns
	#print("Clipping left and right column of each row")
	for nextRow in hexGrid:
		nextRow[0].clipPointsToScreen(widthInterval, heightInterval)
		nextRow[-1].clipPointsToScreen(widthInterval, heightInterval)

def checkForOutOfBounds(hexGrid, printOOB=False):
	hexCount = 0
	for row in hexGrid:
		for nextHex in row:
			for i in range(len(nextHex.points)):
				if nextHex.points[i][0] < 0 or nextHex.points[i][0] > screenWidth or nextHex.points[i][1] < 0 or nextHex.points[i][1] > screenHeight:
					print("Hex %d (%d, %d) is out of bounds." % (hexCount, nextHex.hexIndex[0], nextHex.hexIndex[1]))
					print("Hex point %d: %s" % (i, str(nextHex.points[i])))
					return True
			hexCount += 1
	return False

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
				nextHex.isLand = True
				landHexes[nextHex.hexIndex] = nextHex
			else:
				# Indicate hex is water
				nextHex.isWater = True
				waterHexes[nextHex.hexIndex] = nextHex
			hexCount += 1
	print("Finished finding masked hexes")

def countHexesInGrid(hexGrid):
	total = 0
	for row in hexGrid:
		for nextHex in row:
			total += 1
	print("Total hexes: %d" % (total))

def countNeighbours(hexGrid):
	totalHexes = 0
	for row in hexGrid:
		for nextHex in row:
			print("Hex %d %s has total neighbours = %d" % (totalHexes, nextHex.hexIndex, len(nextHex.neighbours)))
			totalHexes += 1

# Takes a grid of hexes in staggered row format and returns a dictionary using axial coordinates
def createHexMap(hexGrid):	
	hexMap = dict()
	for y in range(len(hexGrid)):
		for x in range(len(hexGrid[y])):
			# Determine hex key
			key = hexGrid[y][x].hexIndex
			hexMap.insert(key, nextHex)

def floodFillLandRegions(hexMap):
	# Copy map so this dict can have keys removed without losing items from other dict
	unassignedHexes = copy.copy(hexMap)
	while unassignedHexes:
		# Choose a new land color
		fillColor = (random.random(), random.random(), random.random(), 0.8)
		# Take a hex from the list of unassigned
		nextHex = unassignedHexes.pop(random.choice(list(unassignedHexes.keys())))
		groupedHexes = [nextHex]
		# Add it and its like-regioned neighbours to a list
		if unassignedHexes:
			groupedHexes.extend(floodFillLandNeighbours(nextHex, unassignedHexes))
		for gHex in groupedHexes:
			gHex.fillColor = fillColor

# Depth first search for neighbouring land hexes which appear in remainingHexes
def floodFillLandNeighbours(nextHex, remainingHexes):
	#print("Hex "  + str(nextHex.hexIndex))
	groupedNeighbours = []
	# Only continue of there are hexes remaining
	#print("Hex has %d neighbours." % (len(nextHex.neighbours)))
	# Determine which neighbours are valid
	neighboursForExploration = []
	for neighbour in nextHex.neighbours.values():
		# If neighbour is tagged as land and exists in remainingHexes
		if neighbour.hexIndex in remainingHexes and neighbour.isLand:
			# Add this neighbour to group
			groupedNeighbours.append(remainingHexes.pop(neighbour.hexIndex))
			# Keep list of neighbours to be explored
			neighboursForExploration.append(neighbour)
	# Explore the neighbours neighbours, if remaningHexes is not empty
	if remainingHexes.keys():
		for neighbour in neighboursForExploration:
			groupedNeighbours.extend(floodFillLandNeighbours(neighbour, remainingHexes))
	else:
		#print("Key is not in list")
		pass
	#print("Returning grouped neighbours:")
	#print(groupedNeighbours)
	return groupedNeighbours

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
		# Adopt neighbour point locations
		assignExistingNeighbours(hexGrid)
		#countNeighbours(hexGrid)
		screenClipGridHexagons(hexGrid)
		
		#print("Any points out of bounds?")
		#print(checkForOutOfBounds(hexGrid))
		
		findMarkedHexes(hexGrid)
		floodFillLandRegions(landHexes)
		countHexesInGrid(hexGrid)
		gridChanged = False
	drawHexGrid(hexGrid)

print("Running app")
pyglet.app.run()
print("Ran app")
