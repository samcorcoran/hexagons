import pyglet
from pyglet.gl import *

import math
import random

def drawArrow(v0, v1, color):
    pyglet.gl.glColor4f(*color)

    headLength = 0.15
    internalAngle = 0.1

    xMag = v1[0]-v0[0]
    yMag = v1[1]-v0[1]

    pyglet.graphics.draw(2, pyglet.gl.GL_LINES,
        ('v2f', v0 + v1)
    )

    # Create a barb extending directly forwards
    barbBaseX = v1[0] + xMag*headLength
    barbBaseY = v1[1] + yMag*headLength

    # Rotate forwards-barb to to correct barb locations
    firstBarbX = v1[0] + (barbBaseX - v1[0])*math.cos((1-internalAngle)*math.pi) - (barbBaseY - v1[1])*math.sin((1-internalAngle)*math.pi)
    firstBarbY = v1[1] + (barbBaseX - v1[0])*math.sin((1-internalAngle)*math.pi) + (barbBaseY - v1[1])*math.cos((1-internalAngle)*math.pi)

    secondBarbX = v1[0] + (barbBaseX - v1[0])*math.cos((1+internalAngle)*math.pi) - (barbBaseY - v1[1])*math.sin((1+internalAngle)*math.pi)
    secondBarbY = v1[1] + (barbBaseX - v1[0])*math.sin((1+internalAngle)*math.pi) + (barbBaseY - v1[1])*math.cos((1+internalAngle)*math.pi)

    pyglet.graphics.draw(3, pyglet.gl.GL_TRIANGLES,
        ('v2f', v1 + [firstBarbX, firstBarbY, secondBarbX, secondBarbY])
    )

def drawSquare(v0, width, color, blend=False):
    if blend:
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    pyglet.gl.glColor4f(*color)
    pyglet.graphics.draw_indexed(4, pyglet.gl.GL_TRIANGLES,
        [0, 1, 2, 0, 2, 3],
        ('v2f', [v0[0]-width/2, v0[1]-width/2, 
            v0[0]+width/2, v0[1]-width/2,
            v0[0]+width/2, v0[1]+width/2,
            v0[0]-width/2, v0[1]+width/2
            ])
    )

def drawRivers(verts, arrowHeads=False):
    if len(verts) > 0:
        pyglet.gl.glColor4f(0.0, 0.1, 1.0, 1.0)
        numVerts = len(verts)/2
        pyglet.graphics.draw(numVerts, pyglet.gl.GL_LINES,
            ('v2f', verts)
        )

def drawHexagonBatch(verts, colours = []):
    numVerts = len(verts)/2
    if len(colours) == 0:
        # Green default hex fills
        colours = [100,200,100,100]*numVerts
        # TEST: Randomised colours
        #colours = [random.randint(1,255) for n in range(numVerts*4)]
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    pyglet.graphics.draw(numVerts, pyglet.gl.GL_TRIANGLES,
        ('v2f', verts),
        ('c4B', colours)
    )

def drawPointBatch(verts, colours = []):
    numVerts = len(verts)/2
    if len(colours) == 0:
        colours = [255,255,255,255]*numVerts
    pyglet.graphics.draw(numVerts, pyglet.gl.GL_POINTS,
        ('v2f', verts),
        ('c4B', colours)
    )

def drawLineBatch(verts, colours = []):
    numVerts = len(verts)/2
    if len(colours) == 0:
        colours = [200,100,100,255]*numVerts
    pyglet.graphics.draw(len(verts)/2, pyglet.gl.GL_LINES,
        ('v2f', verts),
        ('c4B', colours)
    )

# Draws a square at centre of hex, as diagnostic tool to determine which hexes an algorithm is reaching
def highlightHex(hex, colour=(1.0, 0.75, 0.1, 1.0)):
    drawSquare([hex.centre.x, hex.centre.y], 2, colour)

