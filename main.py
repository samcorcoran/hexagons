import pyglet
from pyglet.gl import *
from pyglet import image
from pyglet import clock
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

window = pyglet.window.Window()
screenWidth = 800
screenHeight = 600
window.set_size(screenWidth, screenHeight)
maskImage = pyglet.resource.image('groundtruth5.bmp')

# DRAW CONTROLS #
drawMaskImage = False
drawHexagons = True
drawDrainage = True
drawIslandBorders = False
drawWatersBorders = True
drawWeatherFeatures = False

@window.event
def on_draw():
	global gridChanged
	global hexGrid
	window.clear()
	# Mask image for determining land shapes
	if drawMaskImage:
		pyglet.gl.glColor4f(1,1,1,1)
		maskImage.blit(0, 0)
	# Hexagon borders and fillings
	if drawHexagons:
		newWorld.drawHexGrid(drawHexEdges=False, drawHexFills=True, drawHexCentres=False, drawLand=False, drawWater=True)
	# Drainage routes and sink locations
	if drawDrainage:
		newWorld.drawDrainageRoutes()
	# Land outlines
	if drawIslandBorders:
		newWorld.drawIslandBorders()
	# Water outlines (seas, lakes)
	if drawWatersBorders:
		newWorld.drawWatersBorders()
	# Draw moisture/cloud particles
	if drawWeatherFeatures:
		newWorld.weatherSystem.drawMoistureParticles()
	# Draw experimental noise texture
	#noiseTexture.blit(0,0)

def update(deltaTime):
	#newWorld.weatherSystem.updateParticles(deltaTime)
	pass

print("Running app")
# Create world
hexesInRow = 10
newWorld = world.World(screenWidth, screenHeight, hexesInRow, True, maskImage)
# Create local noise texture to blit
noiseTexture = image.Texture.create(screenWidth, screenHeight, GL_RGBA, True)
noiseTexData = noiseTexture.get_image_data()
noiseArray = terrain.createNoiseList(screenWidth, screenHeight, inBytes=False)
#noiseTexData.set_data('I', 800, noiseArray)
#noiseTexData.blit_to_texture(noiseTexture, 1, 0, 0, 0)
#noiseTexData.blit(0,0)

# Call update 120 per second
pyglet.clock.schedule_interval(update, 1/120.0)
pyglet.app.run()
print("Ran app")
