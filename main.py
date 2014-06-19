import pyglet
from pyglet.gl import *
from pyglet import image
from pyglet import clock
from pyglet import window
from pyglet.window import mouse
import kytten

import hexagon
import random
import math

# Import 2d Simplex Noise
from noise import snoise2

import graph
import terrain
import regions
import lands
import world
import time

# DRAW CONTROLS #
drawMaskImage = False
drawHexagons = True
drawDrainage = False
drawRivers = True

drawIslandBorders = True
drawWatersBorders = True
drawLandBorderHexes = False

drawWeatherFeatures = False
drawDrainageBasins = False

createWeather = False

mouseX = 0
mouseY = 0

class GameWindow(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        pyglet.window.Window.__init__(self, *args, **kwargs)
        # Call update 120 per second

    def on_mouse_motion(self, x, y, dx, dy):
        global mouseX
        global mouseY
        mouseX = x
        mouseY = y

    def on_draw(self):
        global gridChanged
        global hexGrid
        window.clear()
        # Mask image for determining land shapes
        if drawMaskImage:
            pyglet.gl.glColor4f(1,1,1,1)
            maskImage.blit(0, 0)
        # Hexagon borders and fillings
        if drawHexagons:
            newWorld.drawHexGrid(drawHexEdges=False, drawHexFills=True, drawHexCentres=False, drawLand=True, drawWater=False)
        # Drainage routes and sink locations
        if drawDrainage:
            newWorld.drawDrainageRoutes(useSimpleRoutes=False, minHexesDrainedAbove=3)
        # Rivers
        if drawRivers:
            newWorld.drawRivers(useSimpleRoutes=False, minDrainedAbove=1, minTotalDrainedAtMouth=10)
        # Land outlines
        if drawIslandBorders:
            newWorld.drawIslandBorders()
        # Water outlines (seas, lakes)
        if drawWatersBorders and createWeather:
            newWorld.drawWatersBorders()
        # Draw moisture/cloud particles
        if drawWeatherFeatures:
            newWorld.weatherSystem.drawMoistureParticles()

        if drawLandBorderHexes:
            for island in newWorld.islands:
                island.drawGeographicZoneBorderHexes()

        if drawDrainageBasins:
            for island in newWorld.islands:
                island.drawDrainageBasins()

        # Spatial Grid
        #newWorld.spatialGrid.drawGridCells()
        #newWorld.spatialGrid.drawAllPoints()
        # Draw closest vertex to mouse
        #print("Mouse in draw: %f, %f" % (mouseX, mouseY))
        closestHex, closestVertex = newWorld.spatialGrid.findNearestHexAndVertex(mouseX, mouseY)
        if closestHex:
            closestHex.drawHex(edgeColor=(1.0,0.0,0.0,1.0), pointColor=(0.0,1.0,0.0,1.0))
        if closestVertex:
            closestVertex.drawVertex()

        # Draw experimental noise texture
        #noiseTexture.blit(0,0)

    def update(self, deltaTime):
        #newWorld.weatherSystem.updateParticles(deltaTime)
        pass

if __name__ == '__main__':
    print("Running app")
    screenWidth = 800
    screenHeight = 600
    window = GameWindow(screenWidth, screenHeight, caption="Hexagons", resizable=True, vsync=False)
    # Initialize GUI library
    kytten.SetWindow(window)

    # Create world
    maskImage = pyglet.resource.image('groundtruth5.jpg')
    hexesInOddRow = 80
    t0 = time.clock()
    newWorld = world.World(screenWidth, screenHeight, hexesInOddRow, True, maskImage, createWeather)
    t1 = time.clock()
    print("Total world gen time: ", t1-t0)
    # Create local noise texture to blit
    noiseTexture = image.Texture.create(screenWidth, screenHeight, GL_RGBA, True)
    noiseTexData = noiseTexture.get_image_data()
    noiseArray = terrain.createNoiseList(screenWidth, screenHeight, inBytes=False)
    #noiseTexData.set_data('I', 800, noiseArray)
    #noiseTexData.blit_to_texture(noiseTexture, 1, 0, 0, 0)
    #noiseTexData.blit(0,0)

    pyglet.clock.schedule_interval(window.update, 1/120.0)
    pyglet.app.run()
    print("Ran app")
