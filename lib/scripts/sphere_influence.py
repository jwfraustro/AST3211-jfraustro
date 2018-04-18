import numpy as np
from math import sqrt

G = 6.674e-11


def calcSOI(star, bodies):
    for body in bodies:

        body.soi = body.sma*1000*(body.mass/star.mass)**(2/5)

def convertUnits(bodies):

    for body in bodies:
        body.x = 0
        body.y = body.sma * 1000 * np.cos(np.deg2rad(body.inc))
        body.z = body.sma * 1000 * np.sin(np.deg2rad(body.inc))
        body.vx = body.vel * 1000
        body.vy = 0
        body.vz = 0

    return

def checkDistance(star, bodies):

    for body in bodies:
        for other_body in bodies:
            if body == other_body:
                continue

            dist = (other_body.x - body.x)**2 + (other_body.y - body.y)**2 + (other_body.z-body.z)**2
            dist = sqrt(dist)

            if dist < other_body.soi:
                body.parent = other_body
            if dist > other_body.soi:
                body.parent = star

    return

def calcAcceleration(star, bodies, time_step):

    X, Y, Z = 0, 1, 2

    for body in bodies:
        a = [0,0,0]

        dist = (body.parent.x - body.x)**2 + (body.parent.y - body.y)**2 + (body.parent.z - body.z)**2
        dist = sqrt(dist)

        a_scal = G * body.parent.mass / dist**3
        a[X] += a_scal * (body.parent.x - body.x)
        a[Y] += a_scal * (body.parent.y - body.y)
        a[Z] += a_scal * (body.parent.z - body.z)

        body.vx += a[X] * time_step
        body.vy += a[Y] * time_step
        body.vz += a[Z] * time_step

        body.x += body.vx * time_step
        body.y += body.vy * time_step
        body.z += body.vz * time_step

    return

def reportPosition(bodies, body_history):

    if not body_history:
        for body in bodies:
            body_history.append([[body.x, body.y, body.z]])

    for i, body in enumerate(bodies):
        body_history[i].append([body.x, body.y, body.z])

    return

def main(star, bodies, steps, time_step, report):

    body_history = []

    calcSOI(star, bodies)
    convertUnits(bodies)
    checkDistance(star, bodies)

    reportPosition(bodies, body_history)

    for i in range(0, steps):

        calcAcceleration(star, bodies, time_step)

        if i % report == 0:

            reportPosition(bodies, body_history)
            checkDistance(star, bodies)

    return body_history




