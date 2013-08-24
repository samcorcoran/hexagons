import math
import random

from noise import snoise2

import graph
import regions
import drawUtils

def assignHexMapAltitudes(hexMap):
	# Iterate over hexes in may
	for nextHex in hexMap.values():
		# Iterate over hex's points
		cumulativeAltitude = 0
		for point in nextHex.points:
			# If point has no altitude, assign one randomly
			if not point.altitude:
				point.altitude = random.uniform(0.1,1)
				#print("Assigning altitude: %f" % (point.altitude))
			cumulativeAltitude += point.altitude
		# After all perimeter points are complete, take average for hex centre altitude
		nextHex.centre.altitude = cumulativeAltitude/len(nextHex.points)
		#print("Hex %s centre altitude is %f" % (str(nextHex.hexIndex), nextHex.centre.altitude))

def assignHexMapAltitudesFromCoast(hexRegion):
	minimumAltitude = 0.1
	for nextHex in hexRegion.hexes.values():
		#print("Altitudes for hex %s " % (str(nextHex.hexIndex)))
		altitudes = []
		for point in nextHex.points:
			if not point.altitude:
				distanceFromCoast = hexRegion.hexBorderDistances[nextHex.hexIndex]+1
				# Plus one to offset zero indexing, plus another to prevent altitudes of 1
				largestDist = len(hexRegion.borderHexes)+1
				#print("Altitude: %f/%f" % (distanceFromCoast, largestDist)) 
				point.altitude = 0 if largestDist == 0 else (distanceFromCoast**2)/(largestDist**2)
				# Add some randomness
				point.altitude *= random.triangular(0.5, 1.5, 1)
				point.altitude += minimumAltitude
			altitudes.append( point.altitude )
		nextHex.centre.altitude = sum(altitudes)/len(altitudes)
		#print("  Altitudes: %s, centre: %s" % (str(altitudes), str(nextHex.centre.altitude)))

def assignRegionVertexAltitudesFromCoast(hexRegion, noiseArray):
	print("Assigning region vertex altitudes")
	minimumAltitude = 0.1
	for nextHex in hexRegion.hexes.values():
		#print("Altitudes for hex %s " % (str(nextHex.hexIndex)))
		altitudes = []
		for point in nextHex.points:
			if not point.altitude:
				closestBorderVertex = hexRegion.vertexBorderDistances[ point.id ]
				distanceFromCoast = point.distanceFrom(closestBorderVertex)
				#print("Altitude: %f/%f" % (distanceFromCoast, largestDist))
				point.altitude = 0 if hexRegion.largestVertexBorderDistance == 0 else (distanceFromCoast**2)/(hexRegion.largestVertexBorderDistance**2)
				# Add some randomness
				#point.altitude *= random.uniform(0.5, 1.5)
				#print("Pre noise altitude: " + str(point.altitude))
				#print("Point coordinates: " + str((int(point.x), int(point.y))))
				# Set noise between -0.1 and 0.1
				noise = ((noiseArray[int(point.y)-1][int(point.x)]) / 2) + 1
				#print("Noise:")
				#print(noise)
				point.altitude *= noise
				point.altitude += minimumAltitude
			altitudes.append( point.altitude )
		nextHex.centre.altitude = sum(altitudes)/len(altitudes)
		#print("  Altitudes: %s, centre: %s" % (str(altitudes), str(nextHex.centre.altitude)))

def assignEqualAltitudes(hexMap):
	for nextHex in hexMap.values():
		for point in nextHex.points:
			point.altitude = 1
		nextHex.centre.altitude = 1

def createNoiseList(width, height, inBytes=False):
	octaves = 4
	freq = 8.0 * octaves
	# minZ= 0
	# maxZ = 0
	# cumulativeZ = 0
	# count = 0
	texels = [] #[0 for n in range(width*height)]
	for y in range(height):
		row = []
		for x in range(width):
			#z = int(snoise2(x / freq, y / freq, octaves) * 127.0 + 128.0)
			# Noise between 0 and 1
			z = snoise2(x / freq, y / freq, octaves)
			if inBytes:
				z = struct.pak('<B', z & 0xFFFF)

			# if z < minZ:
			# 	minZ = z
			# if z > maxZ:
			# 	maxZ = z
			# cumulativeZ += z
			# count += 1
			
			row.append(z)
		texels.append(row)
	# print("minZ: " + str(minZ))
	# print("maxZ: " + str(maxZ))
	# print("Average Z: " + (str(cumulativeZ/count)))
	return texels
