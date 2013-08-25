import pyglet
from pyglet.gl import *
from pyglet import image
import random
import copy
from itertools import chain
import struct

import graph
import drawUtils

# Based on point altitudes, determine which neighbouring hex is the steeper descent
# Used for drainage basin calculation
def findDrainageNeighbour(hexagon):
	if hexagon.land == True:
		lowestPoint = hexagon.findLowestPoint()
		# Determine which of the hexagons neighbouring this point has the lowest altitude
		lowestHexes = [lowestPoint.surroundingHexes[0]]
		for nextHex in lowestPoint.surroundingHexes.values():
			if nextHex.centre.altitude < lowestHexes[0].centre.altitude:
				# A preferred draining hex has been found
				lowestHexes = [nextHex]
			elif nextHex.centre.altitude == lowestHexes[0].centre.altitude:
				# This hex is equal altitude so equally suitable
				lowestHexes.append(nextHex)
		# If hexagon would be best choice for draining, indicate that draining should be terminated
		random.shuffle(lowestHexes)
		for chosenHex in lowestHexes:
			if not chosenHex == hexagon:
				hexagon.drainageNeighbour = chosenHex
				chosenHex.drainedNeighbours.append(hexagon)
				return chosenHex
		# chosenHex must have been hexagon
		hexagon.drainageNeighbour = hexagon
		return True
	else:
		return False

def drawDrainageRoute(hexagon, drainageRouteColor=(1.0,0,0,1), sinkColor=(0,1.0,0,1), drawMouthsAsSinks=False):
	if not hexagon.drainageNeighbour:
		# Calculate drainage neighbour if not already known
		findDrainageNeighbour(hexagon)
	if hexagon.drainageNeighbour == hexagon or (drawMouthsAsSinks and not hexagon.drainageNeighbour.land):
		# Draw a square to indicate sink
		drawUtils.drawSquare([hexagon.centre.x, hexagon.centre.y], 4, sinkColor)
	else:
		drawUtils.drawArrow(hexagon.getCentreCoordinates(), hexagon.drainageNeighbour.getCentreCoordinates(), drainageRouteColor)

def drawVertexDrainageRoute(hexagon, drainageRouteColor=(1.0,0,0,1), sinkColor=(0,1.0,0,1), drawMouthsAsSinks=False):
	#print("Drainage for hex %s..." % str(hexagon.hexIndex))
	if hexagon.land == True:
		lowestPoint = hexagon.centre
		terminates = False
		while not terminates:
			lowestNeighbouringPoints = [lowestPoint]
			coastal = False
			if len(lowestPoint.neighbouringVertices) > 0:
				# Point is a perimeter vertex! Drain to other perimeter points or to centre points
				for neighbouringPoint in lowestPoint.neighbouringVertices:
					if neighbouringPoint.altitude:
						# Compare own altitude with neighbouring point
						if neighbouringPoint.altitude < lowestNeighbouringPoints[0].altitude:
							lowestNeighbouringPoints = [neighbouringPoint]
						elif neighbouringPoint.altitude == lowestNeighbouringPoints[0].altitude:
							lowestNeighbouringPoints.append(neighbouringPoint)
					else:
						# Has reached a water body
						coastal = True
				# Provide option to run to centre of neighbouring hex if preferable
				for neighbouringHex in lowestPoint.surroundingHexes.values():
					if neighbouringHex.centre.altitude:
						# If a hex centre is even just equal to current point, it is preferable
						#  this deals with the unlikely case of flat hexagons, incorporating all drainage that terminates on perimeter
						if neighbouringHex.centre.altitude < lowestNeighbouringPoints[0].altitude:
							#print("lowest point was a hex centre (%s)" % (str(neighbouringHex.hexIndex)))
							lowestNeighbouringPoints = [neighbouringHex.centre]
						elif neighbouringHex.centre.altitude == lowestNeighbouringPoints[0].altitude:
							lowestNeighbouringPoints.append(neighbouringHex.centre)
					else:
						# Neighbouring hex is part of a water body
						coastal = True
			else:
				# Point is a hex centre point! Drain to perimeter vertices
				currentHex = lowestPoint.surroundingHexes[0]
				for perimeterPoint in currentHex.points:
					if perimeterPoint.altitude:
						if perimeterPoint.altitude < lowestNeighbouringPoints[0].altitude:
							lowestNeighbouringPoints = [perimeterPoint]
						elif perimeterPoint.altitude == lowestNeighbouringPoints[0].altitude:
							lowestNeighbouringPoints.append(perimeterPoint)
					else:
						# One of the perimeter points is part of water body
						coastal = True

			chosenPoint = random.choice(lowestNeighbouringPoints)
			# Has now found the lowest point
			if chosenPoint == lowestPoint:
				# Terminates here at a sink point
				terminates = True
				drawUtils.drawSquare([lowestPoint.x, lowestPoint.y], 4, sinkColor)
			elif coastal:
				# Has reached a water body
				terminates = True
			else:
				# Draw drainage route
				drawUtils.drawArrow([lowestPoint.x, lowestPoint.y], [chosenPoint.x, chosenPoint.y], drainageRouteColor)
				# Set the lowestPoint, ready for the next iteration
				lowestPoint = chosenPoint
	
def drawPerimeterDrainageRoutes(hexagon, drainageRouteColor=(1.0,0,0,1), sinkColor=(0,1.0,0,1), mouthColor=(0,0,1,1), drawSinks=True, drawMouths=True):
	if hexagon.land:
		# If not already done, calculate the drainage direction for each point, and draw it 
		for point in hexagon.points:
			if not point.isByWater():
				# Check if drainage has already been calculated
				if not point.drainageNeighbour:
					lowestPoints = [point]
					for neighbouringPoint in point.neighbouringVertices:
						if neighbouringPoint.altitude < lowestPoints[0].altitude:
							lowestPoints = [neighbouringPoint]
						elif neighbouringPoint.altitude == lowestPoints[0].altitude:
							lowestPoints.append(neighbouringPoint)
					chosenPoint = random.choice(lowestPoints)
					if chosenPoint == point:
						# This point is a sink
						if drawSinks:
							drawUtils.drawSquare([chosenPoint.x, chosenPoint.y], 4, sinkColor)
					else:
						# This neighbour is the drainage neighbour
						point.drainageNeighbour = chosenPoint
						chosenPoint.drainedNeighbours.append(point)
						# Draw drainage route
						drawUtils.drawArrow([point.x, point.y], [chosenPoint.x, chosenPoint.y], drainageRouteColor)
			else:
				# This vertex is coastal
				if point.drainedNeighbours:
					# Point drained some neighbours, may be a river mouth
					if drawMouths:
						drawUtils.drawSquare([point.x, point.y], 4, mouthColor)
					pass
				pass