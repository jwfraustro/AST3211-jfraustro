import csv
import glob
import os
import sys
from random import random

import pyqtgraph.opengl as gl
from PyQt5 import QtWidgets
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtGui import QVector3D as Vector
from numpy import array

import lib.assets.gui.mainWindow as mainWindow
from lib.assets.gui.bodyWidget import Ui_bodyForm as bodyWidget
from lib.scripts.euler import main as Euler
from lib.scripts.sphere_influence import main as SOI

star_preset_path = './lib/presets/stars/star_presets.csv'
body_preset_path = './lib/presets/bodies/body_presets.csv'


def my_exception_hook(exctype, value, traceback):
    # Print the error and traceback
    print(exctype, value, traceback)
    # Call the normal Exception hook after
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)

class Body:
    def __init__(self, name, mass, radius, sma, vel, inc):
        self.name = name
        self.mass = mass
        self.radius = radius
        self.sma = sma
        self.vel = vel
        self.inc = inc
        self.x = None
        self.y = None
        self.z = None
        self.vx = None
        self.vy = None
        self.vz = None
        self.soi = None
        self.parent = None

class Star:
    def __init__(self, name, mass, radius):
        self.name = name
        self.mass = mass
        self.radius = radius
        self.x = 0
        self.y = 0
        self.z = 0
        self.soi = None


class SimMainWindow(QtWidgets.QMainWindow, mainWindow.Ui_SimMainWindow):
    def __init__(self, parent=None):
        super(SimMainWindow, self).__init__(parent)

        self.body_list = []
        self.star_presets = []
        self.body_presets = []
        self.star = None
        self.camera_focus = 0

        self.setupUi(self)

        self.loadPresetFiles()
        self.loadStarPreset()

        self.gv_3d.opts['distance'] = (4e11)

        self.btn_focus_prv.clicked.connect(lambda: self.setCameraFocus('last'))
        self.btn_focus_next.clicked.connect(lambda: self.setCameraFocus('next'))
        self.body_list_model = QStandardItemModel(self.lv_bodies)
        self.lv_bodies.setModel(self.body_list_model)
        self.lv_bodies.doubleClicked.connect(self.editBody)

        self.cb_starPreset.currentTextChanged.connect(self.loadStarPreset)

        self.btn_starSave.clicked.connect(self.saveStar)

        self.btn_loadpreset.clicked.connect(self.loadPreset)
        self.btn_addbody.clicked.connect(self.addBody)
        self.btn_rmbody.clicked.connect(self.removeBody)
        self.btn_reset.clicked.connect(self.reset)
        self.btn_clear.clicked.connect(self.clearPlot)
        self.btn_plot.clicked.connect(self.handlePlot)

    def setCameraFocus(self, direction):

        if direction == 'next':
            self.camera_focus += 1
            if self.camera_focus == len(self.body_list):
                self.camera_focus = 0
            pos = Vector(self.results[self.camera_focus][-1][0], self.results[self.camera_focus][-1][1], self.results[self.camera_focus][-1][2])
            print(pos)
            self.gv_3d.opts['center'] = pos
            self.lbl_body_focus.setText(self.body_list[self.camera_focus].name)
            self.gv_3d.update()
            return
        if direction == 'last':
            self.camera_focus -= 1
            if self.camera_focus == 0:
                self.camera_focus = len(self.body_list)-1
            pos = Vector(self.results[self.camera_focus][-1][0], self.results[self.camera_focus][-1][1],
                         self.results[self.camera_focus][-1][2])
            print(pos)
            self.gv_3d.opts['center'] = pos
            self.lbl_body_focus.setText(self.body_list[self.camera_focus].name)
            self.gv_3d.update()
            return



    def loadStarPreset(self):

        for star in self.star_presets:
            if star.name == self.cb_starPreset.currentText():
                self.star = star

        self.le_starname.setText(str(self.star.name))
        self.le_starmass.setText(str(self.star.mass))
        self.le_starradius.setText(str(self.star.radius))

    def saveStar(self):

        name = self.le_starname.text()
        mass = float(self.le_starmass.text())
        radius = float(self.le_starradius.text())

        self.star = Star(name, mass, radius)
        print(self.star.name)

    def clearPlot(self):
        self.gv_3d.items.clear()
        return

    def handlePlot(self):

        self.gv_3d.clear()

        if self.cmb_solmethod.currentText() == "Euler Integration":
            self.results = Euler(self.star, self.body_list, int(self.le_n.text()), int(self.le_s.text()), int(self.le_r.text()))
        if self.cmb_solmethod.currentText() == "Sphere of Influence":
            self.results = SOI(self.star, self.body_list, int(self.le_n.text()), int(self.le_s.text()), int(self.le_r.text()))

        for body in range(0, len(self.body_list)):
            self.gv_3d.addItem(gl.GLLinePlotItem(pos=array(self.results[body]), color=(random(), random(), random(), 1.0), antialias=True, mode='line_strip',width=3.0))
            self.gv_3d.addItem(gl.GLGridItem())
        return

    def reset(self):

        self.body_list.clear()
        self.body_list_model.clear()


    def removeBody(self):

        row = self.lv_bodies.selectionModel().selection().indexes()[0].row()
        body_name = self.body_list_model.item(row, 0).text()

        for body in self.body_list:
            if body.name == body_name:
                self.body_list.remove(body)
        self.body_list_model.removeRow(row)

    def loadPresetFiles(self):

        for preset in glob.glob('./lib/presets/systems/*.csv'):
            self.cmb_preset.addItem(os.path.basename(preset))
        with open(star_preset_path, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                self.star_presets.append(Star(row[0], float(row[1]), float(row[2])))
                self.cb_starPreset.addItem(row[0])
        with open(body_preset_path, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                self.body_presets.append(Body(row[0], float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5])))

    def updateListModel(self):

        self.body_list_model.clear()
        for body in self.body_list:
            self.body_list_model.appendRow(QStandardItem(body.name))

    def editBody(self):

        row = self.lv_bodies.selectionModel().selection().indexes()[0].row()
        body_name = self.body_list_model.item(row, 0).text()

        for body in self.body_list:
            if body.name == body_name:
                selected_body = body

        dialog = QtWidgets.QDialog()
        bodyDialog = bodyWidget()
        bodyDialog.setupUi(dialog)
        dialog.setWindowTitle("Edit an Orbital Body")

        for body in self.body_presets:
            bodyDialog.cb_preset.addItem(body.name)

        bodyDialog.cb_preset.currentTextChanged.connect(lambda: loadPreset())
        bodyDialog.btn_ok.clicked.connect(lambda: returnBodyVals())
        bodyDialog.btn_cancel.clicked.connect(lambda: dialog.done(1))

        bodyDialog.le_name.setText(str(selected_body.name))
        bodyDialog.le_radius.setText(str(selected_body.vel))
        bodyDialog.le_mass.setText(str(selected_body.mass))
        bodyDialog.le_sma.setText(str(selected_body.sma))
        bodyDialog.le_vel.setText(str(selected_body.vel))
        bodyDialog.le_inc.setText(str(selected_body.inc))

        def loadPreset():
            chosen_preset = bodyDialog.cb_preset.currentText()
            for preset in self.body_presets:
                if preset.name == chosen_preset:
                    bodyDialog.le_name.setText(preset.name)
                    bodyDialog.le_mass.setText(str(preset.mass))
                    bodyDialog.le_radius.setText(str(preset.radius))
                    bodyDialog.le_vel.setText(str(preset.vel))
                    bodyDialog.le_sma.setText(str(preset.sma))
                    bodyDialog.le_inc.setText(str(preset.inc))


        def returnBodyVals():
            name = bodyDialog.le_name.text()
            mass = float(bodyDialog.le_mass.text())
            radius = float(bodyDialog.le_radius.text())
            sma = float(bodyDialog.le_sma.text())
            vel = float(bodyDialog.le_vel.text())
            inc = float(bodyDialog.le_inc.text())

            selected_body.name = name
            selected_body.mass = mass
            selected_body.radius = radius
            selected_body.sma = sma
            selected_body.vel = vel
            selected_body.inc = inc

            self.updateListModel()
            dialog.done(0)

        dialog.show()
        dialog.exec_()


    def addBody(self):
        dialog = QtWidgets.QDialog()
        bodyDialog = bodyWidget()
        bodyDialog.setupUi(dialog)
        dialog.setWindowTitle("Add a New Body")

        for body in self.body_presets:
            bodyDialog.cb_preset.addItem(body.name)

        bodyDialog.cb_preset.currentTextChanged.connect(lambda: loadPreset())
        bodyDialog.btn_ok.clicked.connect(lambda: returnBodyVals())
        bodyDialog.btn_cancel.clicked.connect(lambda: dialog.done(1))

        def loadPreset():
            chosen_preset = bodyDialog.cb_preset.currentText()
            for preset in self.body_presets:
                if preset.name == chosen_preset:
                    bodyDialog.le_name.setText(preset.name)
                    bodyDialog.le_mass.setText(str(preset.mass))
                    bodyDialog.le_radius.setText(str(preset.radius))
                    bodyDialog.le_vel.setText(str(preset.vel))
                    bodyDialog.le_sma.setText(str(preset.sma))
                    bodyDialog.le_inc.setText(str(preset.inc))

        def returnBodyVals():
            name = bodyDialog.le_name.text()
            mass = float(bodyDialog.le_mass.text())
            radius = float(bodyDialog.le_radius.text())
            sma = float(bodyDialog.le_sma.text())
            vel = float(bodyDialog.le_vel.text())
            inc = float(bodyDialog.le_inc.text())
            body = Body(name, mass, radius, sma, vel, inc)
            self.body_list.append(body)
            self.body_list_model.appendRow(QStandardItem(body.name))
            dialog.done(0)

        dialog.show()
        dialog.exec_()


    def loadPreset(self):

        preset = ('./lib/presets/systems/'+self.cmb_preset.currentText())

        self.reset()

        with open(preset, 'r') as f:
            reader = csv.reader(f, delimiter=',')
            next(reader)
            for row in reader:
                if row[0] == "s":
                    self.star = Star(row[1],float(row[2]),float(row[3]))
                if row[0] == "p":
                    self.body_list.append(Body(row[1],float(row[2]),float(row[3]),float(row[4]),float(row[5]),float(row[6])))
            for body in self.body_list:
                item = QStandardItem(body.name)
                self.body_list_model.appendRow(item)
            self.le_starname.setText(str(self.star.name))
            self.le_starmass.setText(str(self.star.mass))
            self.le_starradius.setText(str(self.star.radius))



def main():
    app = QtWidgets.QApplication(sys.argv)
    win = SimMainWindow()
    win.show()
    app.exec_()
    return

if __name__ == '__main__':
    sys.excepthook = my_exception_hook
    main()
