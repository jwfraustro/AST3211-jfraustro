import numpy as np
from math import sqrt
from PyQt5 import QtWidgets

G = 6.674e-11

def calcAcceleration(star, bodies, skip_num):

    X,Y,Z = 0,1,2



    for currentBody in bodies:
        a = [0, 0, 0]
        for otherBody in bodies:
            if currentBody == otherBody:
                break
            dist = (currentBody.x - otherBody.x)**2 + (currentBody.y - otherBody.y)**2 + (currentBody.z - otherBody.z)**2
            dist = sqrt(dist)
            a_scal = G*otherBody.mass/dist**3
            a[X] += a_scal * (otherBody.x - currentBody.x)
            a[Y] += a_scal * (otherBody.y - currentBody.y)
            a[Z] += a_scal * (otherBody.z - currentBody.z)
        dist = (currentBody.x - star.x) ** 2 + (currentBody.y - star.y) ** 2 + (currentBody.z - star.z) ** 2
        dist = sqrt(dist)
        a_scal = G * star.mass / dist**3
        a[X] += a_scal * (star.x - currentBody.x)
        a[Y] += a_scal * (star.y - currentBody.y)
        a[Z] += a_scal * (star.z - currentBody.z)
        currentBody.vx += a[X] * skip_num
        currentBody.vy += a[Y] * skip_num
        currentBody.vz += a[Z] * skip_num
        currentBody.x += currentBody.vx * skip_num
        currentBody.y += currentBody.vy * skip_num
        currentBody.z += currentBody.vz * skip_num

    return

def convertUnits(bodies):

    for body in bodies:
        body.x = 0
        body.y = body.sma*1000*np.cos(np.deg2rad(body.inc))
        body.z = body.sma*1000*np.sin(np.deg2rad(body.inc))
        body.vx = body.vel*1000
        body.vy = 0
        body.vz = 0

    return

def main(star, bodies, t_step, skip_num, report):
    convertUnits(bodies)
    body_history = []
    progress = QtWidgets.QProgressDialog("Computing timesteps..","Cancel",0,t_step)
    progress.setWindowTitle('Please wait...')
    progress.setModal(True)
    progress.setValue(0)
    progress.show()
    QtWidgets.QApplication.processEvents()

    for body in bodies:
        body_history.append([[body.x, body.y, body.z]])
    for i in range(0, t_step):
        progress.setValue(i)
        if progress.wasCanceled() == True:
            break
        #QtWidgets.QApplication.processEvents()
        calcAcceleration(star, bodies, skip_num)
        if i % report == 0:
            for i, body in enumerate(bodies):
                body_history[i].append([body.x, body.y, body.z])
    progress.close()

    return body_history

if __name__ == '__main__':
    main()