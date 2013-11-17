import pyglet
from pyglet.gl import *
from pyglet import image
import random
import copy
from itertools import chain
import struct

import graph
import drawUtils

class Hexagon():
    def __init__(self, centreCoordinates, radius=20, hexIndex=False, jitterStrength=False, existingNeighbours=(None,None,None), isBorderHex=False):
        self.hexIndex = hexIndex
        self.centre = graph.Vertex( coordinates=centreCoordinates, hexes=[self])
        #print("Creating hex with centre: %f, %f" % (self.centre.x, self.centre.y))
        self.radius = radius
        # The innerRadius = (sqrt(3) * self.radius) / 2 = (1.73205080757 / 2) * self.radius = 0.866025403785 * self.radius
        self.innerRadius = 0.8660254 * self.radius # aka hexagon width

        self.points = [None for a in range(6)]
        self.lowestPoint = False
        self.neighbours = dict()
        self.createVertices(existingNeighbours, jitterStrength, isBorderHex)
        # Hex that drains from this one
        self.drainingNeighbour = False
        # Hexes which drain into this one
        self.drainedNeighbours = []
        self.hexesDrainedAbove = []
        self.waterReceived = 1
        # Amount of water drained
        self.quantityDrained = 0
        self.fillColor = False #(random.random(),random.random(),random.random(),0.5)
        self.land = False
        self.distanceFromWater = False
        self.water = False
        if jitterStrength and not isBorderHex:
            self.calculateCentrePoint()
    
    def createVertices(self, existingNeighbours, jitterStrength, isBorderHex):
        southeastNeighbour = existingNeighbours[0]
        southwestNeighbour = existingNeighbours[1]
        westNeighbour = existingNeighbours[2]

        radius = self.radius
        innerRadius = self.innerRadius

        maxJitter = 0
        if not isBorderHex:
            maxJitter = self.radius*jitterStrength

        x = self.centre.x
        y = self.centre.y
        #N, Top point
        self.points[0] = ( graph.Vertex( coordinates=(x, y+radius), hexes=[self], maxJitter=maxJitter ))
        #NE
        self.points[1] = ( graph.Vertex( coordinates=(x+innerRadius, y+(radius/2)), hexes=[self], maxJitter=maxJitter ))
        #SE
        if southeastNeighbour:
            ### self SE point is seNeighbour's N point
            self.points[2] = southeastNeighbour.points[0]
            self.points[2].addHexNeighbours([self])
            ### self S point is seNeighbour's NW point
            self.points[3] = southeastNeighbour.points[5]
            self.points[3].addHexNeighbours([self])
            ## Log neighbour relationship
            self.neighbours[2] = southeastNeighbour
            southeastNeighbour.neighbours[5] = self
            # Records points as neighbours to each other if not already
            #  reciprocal relationship is automatically handled
            self.points[2].addVertexNeighbour(self.points[3])
        else:
            #print("No SE neighbour for hex %s." % (str(self.hexIndex)))
            self.points[2] = ( graph.Vertex( coordinates=(self.centre.x+self.innerRadius, self.centre.y-(self.radius/2)), hexes=[self], maxJitter=maxJitter ))    

        #SW
        if southwestNeighbour:
            ## Adopt SW neighbour's points
            ### self SW point is neighbour's N point
            self.points[4] = southwestNeighbour.points[0]
            self.points[4].addHexNeighbours([self])
            ## Log neighbour relationship
            self.neighbours[3] = southwestNeighbour
            southwestNeighbour.neighbours[0] = self
            # If no seNeighbour existed, use swNeighbour to set southern vertex
            if not southeastNeighbour:
                self.points[3] = southwestNeighbour.points[1]
                self.points[3].addHexNeighbours([self])
            # Records points as neighbours to each other if not already
            #  reciprocal relationship is automatically handled
            self.points[3].addVertexNeighbour(self.points[4])
        else:
            # No swNeighbout guarantees no w neighbour either, so vertex must be created
            #print("No SW neighbour for hex %s." % (str(self.hexIndex)))
            self.points[4] = ( graph.Vertex( coordinates=(self.centre.x-self.innerRadius, self.centre.y-(self.radius/2)), hexes=[self], maxJitter=maxJitter ))

        #S
        if not self.points[3]:
            # if it hasn't be set by se or sw neigbours
            self.points[3] = ( graph.Vertex( coordinates=(x, y-radius), hexes=[self], maxJitter=maxJitter ))

        #NW
        if westNeighbour:
            ## Adopt W neighbour's points
            ### self NW point is neighbour's NE point
            self.points[5] = westNeighbour.points[1]
            self.points[5].addHexNeighbours([self])
            ## Log neighbour relationship
            self.neighbours[4] = westNeighbour
            westNeighbour.neighbours[1] = self
            ### self SW point is neighbour's SE point
            # This may have already been added from the SW neighbour
            if not southwestNeighbour:
                self.points[4] = westNeighbour.points[2]
                self.points[4].addHexNeighbours([self])
            # Records points as neighbours to each other if not already
            #  reciprocal relationship is automatically handled
            self.points[4].addVertexNeighbour(self.points[5])
        else:
            #print("No W neighbour for hex %s." % (str(self.hexIndex)))
            self.points[5] = ( graph.Vertex( coordinates=(self.centre.x-self.innerRadius, self.centre.y+(self.radius/2)), hexes=[self], maxJitter=maxJitter ))

    def getSuccessivePoint(self, v0):
        #print("getSuccessivePoint calling get point index")
        v0index, indexFound = self.getPointIndex(v0)
        if indexFound:
            return self.points[ (v0index+1) % len(self.points) ]
        #print("getSuccessivePoint returning false")
        return False

    def getPointIndex(self, v0):
        for i in range(len(self.points)):
            if self.points[i] == v0:
                # Return index at which point is found
                #print("... point index determined as " + str(i))
                # Zeroy is a 'falsy' value in python, so accompany index with a flag
                return i, True
        # Point was not found
        #print("getPointIndex returning false")     
        return False, False

    def getPointCoordinatesList(self, pointNumber):
        if pointNumber < len(self.points):
            # Return coord list for given point
            return [self.points[pointNumber].x, self.points[pointNumber].y]
        return False

    def getPerimeterCoordinatesList(self):
        return list(chain.from_iterable( [(self.points[n].x, self.points[n].y) for n in range(len(self.points))]))

    def getCentreCoordinates(self):
        return [self.centre.x, self.centre.y]

    def calculateCentrePoint(self):
        xSum = 0
        ySum = 0
        totalPoints = 0
        for point in self.points:
            xSum += point.x
            ySum += point.y
            totalPoints += 1  
        self.centre.x = xSum/float(totalPoints)
        self.centre.y = ySum/float(totalPoints)

    def addHexToNeighbourhood(self, hexGrid, hexesInOddRow):
        #print("Adding hex %s to nhood..." % (str(self.hexIndex)))

        # Identify new hex's index
        rowIsOdd = self.hexIndex[1]%2 == 1

        # Identify SE neighbouring hex, if one exists
        hasSENeighbour = self.hexIndex[0] < hexesInOddRow or rowIsOdd
        # Identify SW neighbouring hex, if one exists
        hasSWNeighbour = self.hexIndex[0] > 0 or rowIsOdd
        # No southern neighbours for the first row... 
        if self.hexIndex[1] == 0:
            hasSENeighbour = False
            hasSWNeighbour = False

        # Not last column, unless this row is odd (previous row is therefore longer)
        if hasSENeighbour:
            x = self.hexIndex[0]+1 if rowIsOdd else self.hexIndex[0]
            y = self.hexIndex[1]-1
            #print("SE Neighbour of Hex %s has x,y: (%d, %d)" % (self.hexIndex, x, y))
            southeastNeighbour = hexGrid[y][x]
            ## Adopt SE neighbour's points
            ### self SE point is neighbour's N point
            self.points[2] = southeastNeighbour.points[0]
            self.points[2].addHexNeighbours([self])
            ### self S point is neighbour's NW point
            self.points[3] = southeastNeighbour.points[5]
            self.points[3].addHexNeighbours([self])
            ## Log neighbour relationship
            self.neighbours[2] = southeastNeighbour
            southeastNeighbour.neighbours[5] = self
            # Records points as neighbours to each other if not already
            #  reciprocal relationship is automatically handled
            self.points[2].addVertexNeighbour(self.points[3])
        else:
            #print("No SE neighbour for hex %s." % (str(self.hexIndex)))
            pass

        # Not first column, unless this row is even (previous row is therefore longer)
        if hasSWNeighbour:
            x = self.hexIndex[0]-1 if not rowIsOdd else self.hexIndex[0]
            y = self.hexIndex[1]-1
            #print("SW Neighbour of Hex %s has x,y: (%d, %d)" % (self.hexIndex, x, y))
            southwestNeighbour = hexGrid[y][x]
            ## Adopt SW neighbour's points
            ### self S point is neighbour's NE point
            # This may have already been added from the SE neighbour
            if not hasSENeighbour:
                self.points[3] = southwestNeighbour.points[1]
                self.points[3].addHexNeighbours([self])
            ### self SW point is neighbour's N point
            self.points[4] = southwestNeighbour.points[0]
            self.points[4].addHexNeighbours([self])
            ## Log neighbour relationship
            self.neighbours[3] = southwestNeighbour
            southwestNeighbour.neighbours[0] = self
            # Records points as neighbours to each other if not already
            #  reciprocal relationship is automatically handled
            self.points[3].addVertexNeighbour(self.points[4])
        else:
            #print("No SW neighbour for hex %s." % (str(self.hexIndex)))
            pass

        # Identify W neighbouring hex, if one exists
        # Not first column...
        if self.hexIndex[0] > 0:
            x = self.hexIndex[0]-1
            y = self.hexIndex[1]
            #print("W Neighbour of Hex %s has x,y: (%d, %d)" % (self.hexIndex, x, y))       
            westNeighbour = hexGrid[y][x]
            ## Adopt W neighbour's points
            ### self SW point is neighbour's SE point
            # This may have already been added from the SW neighbour
            if not hasSWNeighbour:
                self.points[4] = westNeighbour.points[2]
                self.points[4].addHexNeighbours([self])
            ### self NW point is neighbour's NE point
            self.points[5] = westNeighbour.points[1]
            self.points[5].addHexNeighbours([self])
            ## Log neighbour relationship
            self.neighbours[4] = westNeighbour
            westNeighbour.neighbours[1] = self
            # Records points as neighbours to each other if not already
            #  reciprocal relationship is automatically handled
            self.points[4].addVertexNeighbour(self.points[5])           
        else:
            #print("No W neighbour for hex %s." % (str(self.hexIndex)))
            pass

    def drawHex(self, fullHex=True, drawEdges=True, drawPoints=False, edgeColor=(1.0,0.0,0.0,1.0), pointColor=(0.0,1.0,0.0,1.0)):
        pointsList = self.points
        pointsList = list(chain.from_iterable(pointsList))
        numEdges = 6
        if not fullHex:
            numEdges = 4
            pointsList = pointsList[:numEdges*2]
            if drawEdges:
                # Draw edges
                pyglet.gl.glColor4f(*edgeColor)
                # Line strip instead of loop
                pyglet.graphics.draw(numEdges, pyglet.gl.GL_LINE_STRIP,
                    ('v2f', pointsList)
                )
        else:
            if drawEdges:
                # Draw edges
                pyglet.gl.glColor4f(*edgeColor)
                # Line loop to reduce vertex list requirements
                pyglet.graphics.draw(numEdges, pyglet.gl.GL_LINE_LOOP,
                    ('v2f', pointsList)
                )
        if drawPoints:
            # Draw points
            pyglet.gl.glColor4f(*pointColor)
            pyglet.graphics.draw(numEdges, pyglet.gl.GL_POINTS,
                ('v2f', pointsList)
            )
        
    def drawFilledHex(self, fillColor=False, weightByAltitude=True):
        if not fillColor:
            fillColor = self.fillColor
        if fillColor:
            # Polygon centre point coordinates are first values
            pointsList = [self.centre.x, self.centre.y] + self.getPerimeterCoordinatesList()
            pointsList.extend([self.points[0].x, self.points[0].y])
            # Draw filled polygon
            # Scale opacity by centre point's altitude
            color = tuple()
            if self.land and weightByAltitude:
                color = tuple([self.centre.altitude * fillColor[x] for x in range(3)] + [fillColor[3]])
                #pyglet.gl.glColor4f(fillColor[0], fillColor[1], fillColor[2], fillColor[3]*self.centre.altitude)
            else: 
                # Not land, so do not colour by altitude
                color = tuple(fillColor)
            pyglet.gl.glColor4f(*color)
            # Polygon is always drawn as fullHex
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            pyglet.graphics.draw(int(len(pointsList)/2), pyglet.gl.GL_TRIANGLE_FAN,
                ('v2f', pointsList)
            )       

    def drawHexCentrePoint(self, pointColor=(1.0,0.0,1.0,1.0)):
        point = self.centre
        pyglet.gl.glColor4f(*pointColor)
        pyglet.graphics.draw(1, pyglet.gl.GL_POINTS,
            ('v2f', point)
        )

    def clipPointsToScreen(self, widthInterval=[0,800], heightInterval=[0,600]):
        #print("Clipping hex " + str(self.hexIndex))
        #print("self.points:")
        #print(self.points)
        for i, nextPoint in enumerate(self.points):
            #print(" p%d: (%f, %f)" % (i, self.points[i].x, self.points[i].y))
            clipped = False
            # Clip y values to screen
            if self.points[i].y >= heightInterval[1]:
                #print(" ..clipped self.points[%d].y (%f) to heightInterval[1] %d" % (i, self.points[i].y, heightInterval[1]))
                clipped = True
                # Set y to top edge of screen
                self.points[i].y = heightInterval[1]
            elif self.points[i].y <=  heightInterval[0]:
                #print(" ..clipped self.points[%d].y (%f) to heightInterval[0] %d" % (i, self.points[i].y,heightInterval[0]))
                clipped = True
                # Set y to bottom of screen
                self.points[i].y =  heightInterval[0]

            # Clip x values to screen
            if self.points[i].x >= widthInterval[1]:
                #print(" ..clipped self.points[%d].x (%f) to widthInterval[1] %d" % (i, self.points[i].x,widthInterval[1]))
                clipped = True
                # Set x to east edge of screen
                self.points[i].x = widthInterval[1]
            elif self.points[i].x <=  widthInterval[0]:
                #print(" ..clipped self.points[%d].x (%f) to widthInterval[0] %d" % (i, self.points[i].x,widthInterval[0]))               
                clipped = True
                # Set x to west edge of screen
                self.points[i].x =  widthInterval[0]
            
            if clipped:
                #print(" after clipping, point: " + str(self.points[i]))
                pass
            else:
                #print(" no clipping required, point:"  + str(self.points[i]))
                pass
        #print("Hex index: ")
        #print(self.hexIndex)
        self.calculateCentrePoint()

    def compareToMaskImage(self, maskImageData, imageWidth, passRate=0.4, attenuation=0.8, drawAttenuatedPoints=False):
        # Perimeter points and centre point each get a 'vote'
        # Check points against mask image, register votes if point and mask location match
        if not self.land or self.water:
            totalVotes = 0
            attenuatedPointsList = []
            for point in self.points:
                #print("Point: " + str(point))
                # Attenuated positions are closer to the centre of the hex
                attenuatedX = int(self.centre.x + (point.x - self.centre.x)*attenuation)
                attenuatedY = int(self.centre.y + (point.y - self.centre.y)*attenuation)

                i = int(int(attenuatedX) + ((int(attenuatedY)-1) * imageWidth))-1
                #print("Point [%f, %f] had an index of: %d" % (point[0], point[1], i))
                #if maskImageData[i] > 0:
                #image_data = maskImageData.get_region(attenuatedX, attenuatedY, 1, 1).get_image_data()
                # Extract intensity info
                #data = image_data.get_data('I', 1)
                data = maskImageData[i]
                # Convert from byte to int
                data = struct.unpack('<B', data)[0]

                if data > 0:
                #   print("Vote")
                    totalVotes += 1
                # else:
                #   print("No votes")

                # If points are to be drawn, assemble them into a list
                if drawAttenuatedPoints:
                    attenuatedPointsList.extend([attenuatedX, attenuatedY])

            if drawAttenuatedPoints:
                pyglet.gl.glColor4f(1.0,0.0,0.0,1.0)
                pyglet.graphics.draw(int(len(attenuatedPointsList)/2), pyglet.gl.GL_POINTS,
                    ('v2f', attenuatedPointsList)
                )

            if totalVotes >= passRate*len(self.points):
                #print("Hex %s passed mask-match with %d votes (%d to pass)." % (self.hexIndex, totalVotes, passRate*len(self.points)))
                return True
        return False

    def findLowestPoint(self, forceRecalculation=False):
        # Check if it has already been calculated
        if not self.lowestPoint or forceRecalculation:
            # Find the lowest perimeter point in hex perimeter
            self.lowestPoint = self.points[0]
            for point in self.points:
                if point.altitude < self.lowestPoint.altitude:
                    # A new lowest has been found
                    self.lowestPoint = point
        return self.lowestPoint