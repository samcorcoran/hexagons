import pyglet
from pyglet.gl import *
from pyglet import image
from pyglet import clock
from pyglet import window
from pyglet.window import mouse
import kytten
import string
import sys

import hexagon
import random
import math
import string

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

hex_inspector_dialog = None

selectedHex = None
selectedVertex = None

# GUI Theme
Theme = kytten.Theme('C:/Programming/Kytten/KyttenParashurama/theme', override={
    "gui_color": [200, 200, 200, 255],
    "text_color": [0,100,255,255],
    "font_size": 10
})

class GameWindow(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        pyglet.window.Window.__init__(self, *args, **kwargs)
        # Call update 120 per second

    def on_mouse_motion(self, x, y, dx, dy):
        global mouseX
        global mouseY
        mouseX = x
        mouseY = y

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        global mouseX
        global mouseY
        mouseX = x
        mouseY = y

    def update_hex_inspector(self):
        if not hex_inspector_dialog:
            return
        if selectedHex:
            kytten.GetObjectfromName("hexInsp_hexIndex").set_text(str(selectedHex.hexIndex))
            kytten.GetObjectfromName("hexInsp_altitude").set_text(str(selectedHex.centre.altitude))
            kytten.GetObjectfromName("hexInsp_distToBorder").set_text(str(selectedHex.distanceToBorder))
            containingLand = newWorld.getLandContainingHex(selectedHex)
            landName = "None"
            landSize = 0
            if containingLand:
                landName = containingLand.name
                landSize = len(containingLand.region.hexes)
            kytten.GetObjectfromName("hexInsp_landName").set_text(landName)
            kytten.GetObjectfromName("hexInsp_landSize").set_text(str(landSize))
        else:
            kytten.GetObjectfromName("hexInsp_hexIndex").set_text("None")
            kytten.GetObjectfromName("hexInsp_altitude").set_text("None")
            kytten.GetObjectfromName("hexInsp_distToBorder").set_text("None")
            kytten.GetObjectfromName("hexInsp_landName").set_text("None")
            kytten.GetObjectfromName("hexInsp_landSize").set_text("None")

    def on_mouse_release(self, x, y, button, modifiers):
        global selectedHex
        global selectedVertex
        if button == pyglet.window.mouse.LEFT:
            if not newWorld:
                return
            # select/deselect closest hex
            closestHex, closestVertex = newWorld.spatialGrid.findNearestHexAndVertex(x, y)
            # store if mouse location was actually inside hex
            if closestHex.isPointInsideHexRadius(x, y):
                if closestHex:
                    if closestHex != selectedHex:
                        selectedHex = closestHex
                    else:
                        selectedHex = None
                    self.update_hex_inspector()
                if closestVertex:
                    if closestVertex != selectedVertex:
                        selectedVertex = closestVertex
                    else:
                        selectedVertex = None

    def renderWorld(self):
        global gridChanged
        global hexGrid
        global selectedHex
        global selectedVertex

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
        if selectedHex:
            selectedHex.drawHex(edgeColor=(1.0,1.0,0.0,1.0), pointColor=(0.0,1.0,1.0,1.0))
        if selectedVertex:
            selectedVertex.drawVertex()

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

    hexesInOddRow = 30
    newWorld = None
    def generate_new_world(btn):
        global newWorld
        global maskImage
        selectedHex = None
        selectedVertex = None
        window.update_hex_inspector()
        print("Generating a new world...")
        hexesInOddRow = int(kytten.GetObjectfromName("txt_mapSize").get_value())
        t0 = time.clock()
        random.seed(kytten.GetObjectfromName("txt_randSeed").get_value())
        maskImage = pyglet.resource.image(kytten.GetObjectfromName("txt_maskFileName").get_value())
        newWorld = world.World(screenWidth, screenHeight, hexesInOddRow, True, maskImage, createWeather)
        t1 = time.clock()
        print("Total world gen time: ", t1-t0)

    def generate_new_seed(btn):
        seed = random.randint(0, sys.maxint)
        kytten.GetObjectfromName("txt_randSeed").set_text(str(seed))

    def handle_hex_inspector_dialog(btn):
        global hex_inspector_dialog
        if not hex_inspector_dialog:
            hex_inspector_dialog = kytten.Dialog(
                kytten.VerticalLayout([
                    kytten.Label("Hex info:"),
                    kytten.GridLayout([
                        [kytten.Label("id:"),
                            kytten.Label("!", name="hexInsp_hexIndex")],
                        [kytten.Label("Centre Altitude:"),
                            kytten.Label("!", name="hexInsp_altitude")],
                        [kytten.Label("Distance to border:"),
                            kytten.Label("!", name="hexInsp_distToBorder")],
                        [kytten.Label("Land Name:"),
                            kytten.Label("!", name="hexInsp_landName")],
                        [kytten.Label("Land Size:"),
                            kytten.Label("!", name="hexInsp_landSize")],
                    ]),
                ]),
            window=window, batch=kytten.KyttenManager, group=kytten.KyttenManager.foregroup,
            anchor=kytten.ANCHOR_BOTTOM_LEFT,
            theme=Theme)
            window.update_hex_inspector()
        else:
            hex_inspector_dialog.teardown()
            hex_inspector_dialog = None

    def create_file_load_dialog(button):
        fileDialog = None

        def on_select(filename):
            before, sep, after = filename.rpartition("\\")
            kytten.GetObjectfromName("txt_maskFileName").set_text(after)
            print("File load: %s" % filename)
            on_escape(fileDialog)

        def on_escape(fileDialog):
            fileDialog.teardown()

        fileDialog = kytten.FileLoadDialog(  # by default, path is current working dir
            extensions=['.png', '.jpg', '.bmp', '.gif'],
            window=window, batch=kytten.KyttenManager, group=kytten.KyttenManager.foregroup,
            anchor=kytten.ANCHOR_CENTER,
            theme=Theme, on_escape=on_escape, on_select=on_select)

    # UI Panel
    dialog = kytten.Dialog(
        kytten.TitleFrame('Terrain Controls',
            kytten.VerticalLayout([
                kytten.FoldingSection("Generation:",
                    kytten.VerticalLayout([
                        kytten.HorizontalLayout([
                            kytten.Input("1", name="txt_randSeed", length=10),
                            kytten.Button("New Seed", on_click=generate_new_seed),
                        ]),
                        kytten.HorizontalLayout([
                            kytten.Input("groundtruth5.jpg", name="txt_maskFileName"),
                            kytten.Button("Load", on_click=create_file_load_dialog),
                        ]),
                        kytten.HorizontalLayout([
                            kytten.Label("Size:"),
                            kytten.Input(str(hexesInOddRow), name="txt_mapSize", length=6),
                            kytten.Button("Generate", on_click=generate_new_world),
                        ]),
                        kytten.Button("Open Hex Inspector", on_click=handle_hex_inspector_dialog),
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
    maskImage = None
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
