import pyglet
from pyglet.gl import *
from pyglet import image
from pyglet import clock
from pyglet import window
from pyglet.window import mouse
import kytten
import string

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

    def renderWorld(self):
        global gridChanged
        global hexGrid
        # Mask image for determining land shapes
        if kytten.GetObjectfromName("cb_drawMask").get_value():
            pyglet.gl.glColor4f(1,1,1,1)
            maskImage.blit(0, 0)
        # Hexagon borders and fillings
        if kytten.GetObjectfromName("cb_drawHexagons").get_value():
            newWorld.drawHexGrid(drawHexEdges=kytten.GetObjectfromName("cb_drawHexEdges").get_value(),
                                 drawHexFills=kytten.GetObjectfromName("cb_drawHexFills").get_value(),
                                 drawHexCentres=kytten.GetObjectfromName("cb_drawHexCentres").get_value(),
                                 drawLand=kytten.GetObjectfromName("cb_drawLand").get_value(),
                                 drawWater=kytten.GetObjectfromName("cb_drawWater").get_value())

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

    def on_draw(self):
        global newWorld
        self.clear()
        # Display FPS on screen
        if kytten.GetObjectfromName("cb_displayFPS").get_value():
            fps_display.draw()
        # Render GUI
        kytten.KyttenRenderGUI()
        if newWorld:
            self.renderWorld()

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

    hexesInOddRow = 60
    newWorld = None
    def generate_new_world(btn):
        global newWorld
        print("Generating a new world...")
        hexesInOddRow = int(kytten.GetObjectfromName("txt_mapSize").get_value())
        t0 = time.clock()
        newWorld = world.World(screenWidth, screenHeight, hexesInOddRow, True, maskImage, createWeather)
        t1 = time.clock()
        print("Total world gen time: ", t1-t0)

    # UI Panel
    dialog = kytten.Dialog(
        kytten.TitleFrame('Terrain Controls',
            kytten.VerticalLayout([
                kytten.FoldingSection("Generation:",
                    kytten.VerticalLayout([
                        kytten.Label("Map size:"),
                        kytten.Input(str(hexesInOddRow), name="txt_mapSize"),
                        kytten.Button("Generate", on_click=generate_new_world),
                    ]),
                ),
                kytten.VerticalLayout([
                    kytten.FoldingSection("Hexagon Drawing",
                        kytten.VerticalLayout([
                            kytten.Checkbox(name="cb_drawHexagons",
                                            text="Draw Hexagons",
                                            is_checked=True
                            ),
                            kytten.Checkbox(name="cb_drawHexFills",
                                            text="Draw Fills",
                                            is_checked=True
                            ),
                            kytten.Checkbox(name="cb_drawHexCentres", text="Draw Centres"),
                            kytten.Checkbox(name="cb_drawHexEdges", text="Draw Edges"),
                        ], align=kytten.ANCHOR_LEFT)
                    ),
                    kytten.FoldingSection("River Drawing",
                        kytten.VerticalLayout([
                            kytten.Checkbox(name="cb_drawRivers", text="Draw Rivers"),
                            kytten.Checkbox(name="cb_drawDrainage", text="Draw Drainage"),
                        ], align=kytten.ANCHOR_LEFT)
                    ),
                    kytten.Checkbox(name="cb_drawLand",
                                    text="Draw Land Hexes",
                                    is_checked=True
                    ),
                    kytten.Checkbox(name="cb_drawWater", text="Draw Water Hexes"),
                    kytten.Checkbox(name="cb_drawIslandBorders",
                                    text="Draw Island Borders",
                                    is_checked=True
                    ),
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
