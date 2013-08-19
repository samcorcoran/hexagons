import pyglet
from pyglet.gl import *
from pyglet import image
import hexagon
import random
import math
import copy

import graph
import terrain
import regions

window = pyglet.window.Window()
screenWidth = 800
screenHeight = 600
window.set_size(800, 600)
maskImage = pyglet.resource.image('groundtruth3.bmp')
gridChanged = True
hexGrid = []
landHexes = dict()
waterHexes = dict()
islands = []

def drawHexGrid(hexGrid, drawHexEdges=True, drawHexFills=True, drawHexCentres=False, drawRegularGrid=False):
	if hexGrid:
		linePoints = []
		for row in hexGrid:
			for nextHex in row:
				if drawHexFills:
					# Draw hexagon fill
					nextHex.drawFilledHex()
				# Draw hexagon edges and/or points
				#nextHex.drawHex()
				if drawHexCentres:
					# Draw hexagon centres
					#nextHex.drawHexCentrePoint()
					nextHex.drawHexCentrePoint(True, (0,1,1,1))
				# Draw regular hexagon grid
				if drawRegularGrid:
					nextHex.drawHex(True, True, False, (0.0, 0.0, 1.0, 1.0), True)
				# Compile points of hexagon into list for batch rendering of gl_lines
				linePoints.extend(nextHex.getPointCoordinatesList(pointNumber=0))
				for i in range(len(nextHex.points)):
					# Enter each point twice, for the two consecutive lines
					nextCoordinates = nextHex.getPointCoordinatesList(pointNumber=i)
					linePoints.extend(nextCoordinates + nextCoordinates)
				# Last point is first point, completing the loop
				linePoints.extend(nextHex.getPointCoordinatesList(pointNumber=0))
		print("linePoints length: " + str(len(linePoints)))
		if drawHexEdges:
			pyglet.gl.glColor4f(0.0,0.0,1.0,1.0)
			pyglet.graphics.draw(int(len(linePoints)/2), pyglet.gl.GL_LINES,
				('v2f', linePoints)
			)
		print("Finished drawing")

# Build a hex grid, hex by hex, using points of neighbouring generated hexagons where possible
def createHexGridFromPoints(hexesInRow=10, clipPointsToScreen=True):
	print("Creating hex grid from points (hexesInRow: %d)" % (hexesInRow))
	# Width of hexagons (w=root3*Radius/2) is calculated from screenwidth, which then determines hex radius
	hexWidth = (screenWidth/hexesInRow)
	hexRadius = (hexWidth) / math.sqrt(3) # Also edge length

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
		# Add another row to gridRows
		gridRows.append([])
		# Draw one less hex on odd-numbered rows
		for col in range(hexesInRow+1-(row%2)):
			#print("Hex %d in row %d" % (col, row))
			#print("Creating hex %d, with (col,row): (%d, %d)" % (totalHexes, col, row))
			hexPolygon = hexagon.Hexagon((hexCentreX, hexCentreY), hexRadius, hexIndex=(col, row), jitterStrength=0.2)
			hexPolygon.addHexToNeighbourhood(gridRows, hexesInRow)
			totalHexes += 1
			# Add hex to current top row of hex grid
			gridRows[-1].append(hexPolygon)
			hexCentreX += hexWidth
		#print("Length of nextRow: %d" % (len(nextRow)))
		#gridRows.append(nextRow)
		row += 1
		hexCentreY += hexRadius * 1.5
	print("Created a hexGrid with %d rows. Odd rows are length %d and even are %d." % (len(gridRows), len(gridRows[0]), len(gridRows[1])))
	return gridRows

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
				if nextHex.points[i].x < 0 or nextHex.points[i].x > screenWidth or nextHex.points[i].y < 0 or nextHex.points[i].y > screenHeight:
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
		fillColor = (random.random(), random.random(), random.random(), 1.0)
		# Take a hex from the list of unassigned
		nextHex = unassignedHexes.pop(random.choice(list(unassignedHexes.keys())))

		groupedHexes = []
		# Add it and its like-regioned neighbours to a list
		explorableHexes = [nextHex]
		while explorableHexes:
			unexploredHex = explorableHexes.pop()
			groupedHexes.append(unexploredHex)
			# If there are still hexes left to find, check hex's neighbours
			if unassignedHexes:
				explorableHexes.extend(floodFillLandNeighbours(unexploredHex, unassignedHexes))
		island = dict()
		for gHex in groupedHexes:
			island[gHex.hexIndex] = gHex
			# Apply some behaviour to hexes in region
			gHex.fillColor = fillColor
		islands.append(island)

# Check nextHex's neighbours for validity, return list of those which are valid
def floodFillLandNeighbours(nextHex, remainingHexes):
	#print("Hex "  + str(nextHex.hexIndex))
	groupedNeighbours = []
	# Only continue of there are hexes remaining
	#print("Hex has %d neighbours." % (len(nextHex.neighbours)))
	# Determine which neighbours are valid
	for neighbour in nextHex.neighbours.values():
		# If neighbour is tagged as land and exists in remainingHexes
		if neighbour.hexIndex in remainingHexes and neighbour.isLand:
			# Add this neighbour to group
			groupedNeighbours.append(remainingHexes.pop(neighbour.hexIndex))
	#print("Returning grouped neighbours:")
	#print(groupedNeighbours)
	return groupedNeighbours

def drawDrainageRoutes(hexMap):
	for nextHex in hexMap.values():
		#nextHex.drawPerimeterDrainageRoutes()
		#nextHex.drawVertexDrainageRoute()
		nextHex.drawDrainageRoute()

@window.event
def on_draw():
	global gridChanged
	global hexGrid
	hexesInRow = 20
	if gridChanged:
		window.clear()
		if True:
			maskImage.blit(0, 0)
		hexGrid = createHexGridFromPoints(hexesInRow)
		#countNeighbours(hexGrid)
		screenClipGridHexagons(hexGrid)
		
		#print("Any points out of bounds?")
		#print(checkForOutOfBounds(hexGrid))
		
		findMarkedHexes(hexGrid)
		floodFillLandRegions(landHexes)
		countHexesInGrid(hexGrid)

		for island in islands:
			islandRegion = regions.Region(island)
			islandRegion.findBorderHexes()

			islandRegion.calculateAllVertexBorderDistances()

			# Assign heights to land vertices
			#terrain.assignEqualAltitudes(landHexes)
			#terrain.assignHexMapAltitudes(landHexes)
			#terrain.assignHexMapAltitudesFromCoast(islandRegion)
			terrain.assignRegionVertexAltitudesFromCoast(islandRegion)

		gridChanged = False
	drawHexGrid(hexGrid, drawHexEdges=False, drawHexFills=True, drawHexCentres=False)
	if True:
		drawDrainageRoutes(landHexes)

print("Running app")
pyglet.app.run()
print("Ran app")
