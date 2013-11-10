import math
import random
import copy
import pyglet

import hexagon
import graph
import regions
import drawUtils
import terrain
import lands
import weather
import drainage

class World():
	def __init__(self, worldWidth, worldHeight, hexesInRow=10, clipPointsToWorldLimits=True, maskImage=False):
		# World dimensions
		self.worldWidth = worldWidth
		self.worldHeight = worldHeight
		self.hexesInRow = hexesInRow
		# Structures for holding hexes
		self.landHexes = dict()
		self.waterHexes = dict()
		# Create a hex grid
		self.hexMap = dict()
		self.hexGrid = self.createHexGridFromPoints(hexesInRow, clipPointsToWorldLimits)
		if clipPointsToWorldLimits:
			self.clipGridHexagonsToWorldDimensions()
		# Tag hexagons/vertices according to masks
		self.landMask = maskImage
		## Collect land and water hexagons
		self.findLandMarkedHexes()
		# Create noise for world altitudes
		self.noise = terrain.createNoiseList(self.worldWidth, self.worldHeight, inBytes=False)
		# Create lands - creation process involves finding borders
		self.islands = []
		self.createLands()
		# Create oceans/seas and lakes
		self.waters = []
		self.createWaters()
		# Use land borders to avoid recomputing the same vertex sequences
		for water in self.waters:
			water.receiveBordersFromLands(self.islands)
		# Create weather system
		self.weatherSystem = weather.WeatherSystem(worldWidth, worldHeight)

	# Build a hex grid, hex by hex, using points of neighbouring generated hexagons where possible
	def createHexGridFromPoints(self, hexesInRow, clipPointsToWorldLimits=True):
		print("Creating hex grid from points (hexesInRow: %d)" % (hexesInRow))
		# Width of hexagons (w=root3*Radius/2) is calculated from self.worldWidth, which then determines hex radius
		hexWidth = float(self.worldWidth)/float(hexesInRow)
		hexRadius = (hexWidth) / math.sqrt(3) # Also edge length

		gridRows = []

		# Loop through hexagon locations, using index to determine if some points should be taken from neighbours
		# Loop over hex coordinate locations
		hexCentreY = 0
		totalHexes = 0
		row = 0
		while hexCentreY - hexRadius < self.worldHeight:
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
				self.hexMap[(col, row)] = hexPolygon
				hexCentreX += hexWidth
			#print("Length of nextRow: %d" % (len(nextRow)))
			#gridRows.append(nextRow)
			row += 1
			hexCentreY += hexRadius * 1.5

		print("Created a hexGrid with %d rows. Odd rows are length %d and even are %d." % (len(gridRows), len(gridRows[0]), len(gridRows[1])))
		return gridRows

	# Examine mask image and tag hexagons as land or water
	def findLandMarkedHexes(self):
		print("Begun finding masked hexes")
		if self.landMask:
			maskImageData = self.landMask.get_image_data()
			data = maskImageData.get_data('I', self.landMask.width)

			hexCount = 0
			for row in self.hexGrid:
				for nextHex in row:
					#print("Hex " + str(hexCount))
					if nextHex.compareToMaskImage(data, self.landMask.width):
						nextHex.fillColor = (1.0,0.0,0.0,1.0)
						# Indicate that hex must be land
						nextHex.land = True
						self.landHexes[nextHex.hexIndex] = nextHex
					else:
						# Indicate hex is water
						nextHex.fillColor = (0.0,0.0,1.0,1.0)
						nextHex.water = True
						self.waterHexes[nextHex.hexIndex] = nextHex
					#print("hexCount: " + str(hexCount))
					hexCount += 1
			print("Finished finding masked hexes")

	def createLands(self):
		unassignedHexes = copy.copy(self.landHexes)
		while unassignedHexes:
			landRegion = self.createContiguousRegion(unassignedHexes)
			self.islands.append(lands.Land(self, landRegion, self.noise))

	def createWaters(self):
		unassignedHexes = copy.copy(self.waterHexes)
		while unassignedHexes:
			waterRegion = self.createContiguousRegion(unassignedHexes)
			self.waters.append( lands.GeographicZone(self, waterRegion, self.noise) )

	# Using dict of landHexes, floodfilling finds distinct tracts of land from which regions can be created.
	def createContiguousRegion(self, unassignedHexes):
		# Copy map so this dict can have keys removed without losing items from other dict
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
				explorableHexes.extend(self.floodFillLandNeighbours(unexploredHex, unassignedHexes))
		island = dict()
		for gHex in groupedHexes:
			island[gHex.hexIndex] = gHex
			# Apply some behaviour to hexes in region
			gHex.fillColor = fillColor
		# Create region with hexes and store as an island
		return regions.Region(island)

	# Check nextHex's neighbours for validity, return list of those which are valid
	def floodFillLandNeighbours(self, nextHex, remainingHexes):
		#print("Hex "  + str(nextHex.hexIndex))
		groupedNeighbours = []
		# Only continue of there are hexes remaining
		#print("Hex has %d neighbours." % (len(nextHex.neighbours)))
		# Determine which neighbours are valid
		for neighbour in nextHex.neighbours.values():
			# If neighbour is tagged as land and exists in remainingHexes
			if neighbour.hexIndex in remainingHexes:
				# Add this neighbour to group
				groupedNeighbours.append(remainingHexes.pop(neighbour.hexIndex))
		#print("Returning grouped neighbours:")
		#print(groupedNeighbours)
		return groupedNeighbours

	# Hexagons which are created with points outside of world limits which must have their OOB points shifted to the perimeter
	def clipGridHexagonsToWorldDimensions(self, printOOBChecks=False):
		print("Screen-clipping hexagons")
		# Loop over boundary hexes, fixing their off-screen points to the screen boundary
		# Check works on regular hexagon's points rather than jittered points
		widthInterval = [0, self.worldWidth]
		heightInterval = [0, self.worldHeight]
		# Bottom row
		#print("Clipping bottom row")
		for nextHex in self.hexGrid[0]:
			nextHex.clipPointsToScreen(widthInterval, heightInterval)
		# Top row
		#print("Clipping top row")
		for nextHex in self.hexGrid[-1]:
			nextHex.clipPointsToScreen(widthInterval, heightInterval)
		# Left and right columns
		#print("Clipping left and right column of each row")
		for nextRow in self.hexGrid:
			nextRow[0].clipPointsToScreen(widthInterval, heightInterval)
			nextRow[-1].clipPointsToScreen(widthInterval, heightInterval)
		if printOOBChecks:
			self.checkForOutOfBounds()

	# Utility function to optionally run after clipping to be informed of any vertices which continue to be out of bounds
	def checkForOutOfBounds(self):
		hexCount = 0
		for row in self.hexGrid:
			for nextHex in row:
				for i in range(len(nextHex.points)):
					if nextHex.points[i].x < 0 or nextHex.points[i].x > self.worldWidth or nextHex.points[i].y < 0 or nextHex.points[i].y > self.worldHeight:
						print("Hex %d (%d, %d) is out of bounds." % (hexCount, nextHex.hexIndex[0], nextHex.hexIndex[1]))
						print("Hex point %d: %s" % (i, str(nextHex.points[i])))
						return True
				hexCount += 1
		return False

	# Use pyglet GL calls to draw hexagons
	def drawHexGrid(self, drawHexEdges=True, drawHexFills=True, drawHexCentres=False, drawRegularGrid=False, drawLand=False, drawWater=True):
		if self.hexGrid:
			linePoints = []
			for row in self.hexGrid:
				for nextHex in row:
					if drawLand and nextHex.land or drawWater and nextHex.water:
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
			#print("linePoints length: " + str(len(linePoints)))
			if drawHexEdges:
				pyglet.gl.glColor4f(0.0,0.0,1.0,1.0)
				pyglet.graphics.draw(int(len(linePoints)/2), pyglet.gl.GL_LINES,
					('v2f', linePoints)
				)
			#print("Finished drawing")

	# Use pyglet GL calls to draw drainage routes
	def drawDrainageRoutes(self, useSimpleRoutes):
		for nextHex in self.landHexes.values():
			#nextHex.drawPerimeterDrainageRoutes()
			#nextHex.drawVertexDrainageRoute()
			drainage.drawDrainageRoute(nextHex, useSimpleRoutes=useSimpleRoutes)

	# Use pyglet GL calls to draw drainage routes for each river hex
	def drawRivers(self, useSimpleRoutes):
		for nextLand in self.islands:
			nextLand.drawRivers(useSimpleRoutes)

	# Draw borders of each distinct land region
	def drawIslandBorders(self):
		for island in self.islands:
			island.drawGeographicZoneBorders()

	# Draw borders of each distinct waters region
	def drawWatersBorders(self):
		for water in self.waters:
			water.drawGeographicZoneBorders()
