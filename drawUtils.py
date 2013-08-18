import pyglet
import math

def drawArrow(v0, v1):
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