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
        self.clear()
        # Display FPS on screen
        if kytten.GetObjectfromName("cb_displayFPS").get_value():
            fps_display.draw()
        # Render GUI
        kytten.KyttenRenderGUI()

        # Mask image for determining land shapes
        if kytten.GetObjectfromName("cb_drawMask").get_value():
            pyglet.gl.glColor4f(1,1,1,1)
            maskImage.blit(0, 0)
        # Hexagon borders and fillings
        if kytten.GetObjectfromName("cb_drawHexagons").get_value():
            newWorld.drawHexGrid(drawHexEdges=False, drawHexFills=True, drawHexCentres=True, drawLand=True, drawWater=False)
        # Drainage routes and sink locations
        if kytten.GetObjectfromName("cb_drawDrainage").get_value():
            newWorld.drawDrainageRoutes(useSimpleRoutes=False, minHexesDrainedAbove=3)
        # Rivers
        if kytten.GetObjectfromName("cb_drawRivers").get_value():
            newWorld.drawRivers(useSimpleRoutes=False, minDrainedAbove=1, minTotalDrainedAtMouth=10)
        # Land outlines
        if kytten.GetObjectfromName("cb_drawIslandBorders").get_value():
            newWorld.drawIslandBorders()
        # Water outlines (seas, lakes)
        if drawWatersBorders and createWeather:
            newWorld.drawWatersBorders()
        # Draw moisture/cloud particles
        if drawWeatherFeatures:
            newWorld.weatherSystem.drawMoistureParticles()

        if drawLandBorderHexes:
            newWorld.drawGeographicZoneBorderHexes()

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
    uiPanelWidth = 224
    window = GameWindow(screenWidth+uiPanelWidth, screenHeight, caption="Hexagons", resizable=True, vsync=False)
    # Pyglet FPS Overlay
    fps_display = pyglet.clock.ClockDisplay()
    # Initialize GUI library
    kytten.SetWindow(window)

    # GUI Theme
    Theme = kytten.Theme('C:/Programming/Kytten/KyttenParashurama/theme', override={
        "gui_color": [200, 200, 200, 255],
        "text_color": [0,100,255,255],
        "font_size": 10
    })

    # UI Panel
    dialog = kytten.Dialog(
        kytten.TitleFrame('Terrain Controls',
            kytten.VerticalLayout([
                kytten.Label("Draw controls:"),
                kytten.VerticalLayout([
                    kytten.Checkbox(name="cb_drawHexagons", text="Draw Hexagons"),
                    kytten.Checkbox(name="cb_drawRivers", text="Draw Rivers"),
                    kytten.Checkbox(name="cb_drawDrainage", text="Draw Drainage"),
                    kytten.Checkbox(name="cb_drawIslandBorders", text="Draw Island Borders"),
                    kytten.Checkbox(name="cb_drawMask", text="Draw Mask"),
                    kytten.Checkbox(name="cb_displayFPS", text="Show FPS"),
                ], align=kytten.ANCHOR_LEFT),
            ], minwidth=192, minheight=550),
        ),
        window=window, batch=kytten.KyttenManager, group=kytten.KyttenManager.foregroup,
        anchor=kytten.ANCHOR_TOP_RIGHT,
        theme=Theme,
        movable=False)

    # Create world
    maskImage = pyglet.resource.image('groundtruth5.jpg')
    hexesInOddRow = 40
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
