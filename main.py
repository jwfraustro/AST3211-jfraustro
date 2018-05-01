import csv
import glob
import os
import sys
from random import random

from scipy.misc import imread

import pyqtgraph as pyqtg
import pyqtgraph.opengl as gl
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap, QIcon, QColor
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtGui import QVector3D as Vector
from numpy import array
from numpy import max

import lib.assets.gui.mainWindow as mainWindow
from lib.assets.gui.bodyWidget import Ui_bodyForm as bodyWidget
from lib.assets.gui.starWidget import Ui_starPresetDialog as starWidget
from lib.scripts.euler import main as Euler
from lib.scripts.sphere_influence import main as SOI

star_preset_path = './lib/presets/stars/star_presets.csv'
body_preset_path = './lib/presets/bodies/body_presets.csv'

SECS_MINUTE = 60
SECS_DAY = 86400
SECS_YEAR = 86400*365
AU = 1.496e+8

def my_exception_hook(exctype, value, traceback):
    # Print the error and traceback
    print(exctype, value, traceback)
    # Call the normal Exception hook after
    sys.excepthook(exctype, value, traceback)
    sys.exit(1)

class Body:
    def __init__(self, name, mass, radius, sma, vel, inc):
        self.name = name
        self.color = None
        self.mass = mass
        self.radius = radius
        self.sma = sma
        self.vel = vel
        self.inc = inc
        self.x = None
        self.y = None
        self.z = None
        self.ax = 0
        self.ay = 0
        self.az = 0
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

        self.current_color = None

        self.setupUi(self)

        self.loadPresetFiles()
        self.loadStarPreset()

        self.btn_starbrowser.clicked.connect(lambda: self.launchStarWidget())

        #self.gv_xy.enableAutoRange(axis = self.gv_xy.ViewBox.YAxis, enable=True)

        self.gv_3d.opts['distance'] = (4e11)
        self.cmb_preset.setCurrentIndex(1)

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

        self.loadPreset()


    def launchStarWidget(self):

        dialog = QtWidgets.QDialog()
        starDialog = starWidget()
        starDialog.setupUi(dialog)
        dialog.setWindowTitle('Star Browser')

        star_lv_model = QStandardItemModel(starDialog.lv_stars)
        starDialog.lv_stars.setModel(star_lv_model)

        starDialog.lv_stars.doubleClicked.connect(lambda: updateFields(starDialog.lv_stars.selectionModel().selection().indexes()[0].row()))

        star_list = []

        def loadStars():

            with open('./lib/presets/stars/star_data.csv','r') as f:
                reader = csv.reader(f, delimiter=',')
                next(reader)
                for row in reader:
                    name = row[0]
                    alt_name = row[1]
                    mass = row[2]
                    radius = row[3]
                    dist = row[4]
                    spec_class = row[5]
                    sol_mass = row[6]
                    sol_radius = row[7]
                    temp = row[8]
                    mag = row[9]
                    index = row[10]
                    star = [name, alt_name, mass, radius,dist,spec_class,sol_mass,sol_radius,temp, mag, index]
                    star_list.append(star)

            for star in star_list:
                item = QStandardItem(star[0])
                star_lv_model.appendRow(item)

            updateFields(index=0)

        def updateFields(index):

            starDialog.le_name.setText(star_list[index][0])
            starDialog.le_altname.setText(star_list[index][1])
            starDialog.le_dist.setText(star_list[index][4])
            starDialog.le_specclass.setText(star_list[index][5])
            starDialog.le_solmass.setText(star_list[index][6])
            starDialog.le_mass.setText(star_list[index][2])
            starDialog.le_radius.setText(star_list[index][3])
            starDialog.le_radius_2.setText(star_list[index][7])
            starDialog.le_temp.setText(star_list[index][8])
            starDialog.le_mag.setText(star_list[index][9])

            loadStarModel(index)

            return

        def loadStarModel(index):

            starDialog.gv_star.clear()

            star_class =  star_list[index][5][0]

            colors = imread('./lib/presets/stars/'+star_class+'.png')
            colors = colors / 255
            md = gl.MeshData.sphere(rows=600, cols=800, radius=1)
            md.setVertexColors(colors=colors)
            mi = gl.GLMeshItem(meshdata=md, smooth=True, computeNormals=False, shader='balloon')
            mi.scale(4,4,4)
            starDialog.gv_star.addItem(mi)


        loadStars()

        dialog.show()
        dialog.exec_()

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

        self.saveStar()

    def saveStar(self):

        name = self.le_starname.text()
        mass = float(self.le_starmass.text())
        radius = float(self.le_starradius.text())

        self.star = Star(name, mass, radius)
        self.gb_star.setTitle("Current Star: "+self.star.name)
        print(self.star.name)

    def clearPlot(self):
        self.gv_3d.clear()
        self.gv_xy.clear()

        return

    def handlePlot(self):

        if self.cmb_tsteps.currentText() == "Seconds":
            step_value = int(self.le_stepvalue.text())
        if self.cmb_tsteps.currentText() == "Minutes":
            step_value = int(self.le_stepvalue.text())*SECS_MINUTE
        if self.cmb_tsteps.currentText() == "Days":
            step_value = int(self.le_stepvalue.text())*SECS_DAY
        if self.cmb_tsteps.currentText() == "Years":
            step_value = int(self.le_stepvalue.text())*SECS_YEAR

        steps = int(self.le_nsteps.text())
        report = int(self.le_stepfreq.text())

        print(steps, step_value, report)

        self.gv_3d.clear()
        self.gv_xy.clear()

        self.gv_xy.setAspectLocked(lock=True, ratio=1)
        self.gv_xy.enableAutoRange(enable=True)

        if self.rb_multiprocess.isChecked() == True:
            print("true")
            self.results = Euler(self.star, self.body_list, steps, step_value, report, 1)


        if self.rb_multiprocess.isChecked() == False:
            if self.cmb_solmethod.currentText() == "Euler Integration":
                self.results = Euler(self.star, self.body_list, steps, step_value, report, 0)

            if self.cmb_solmethod.currentText() == "Sphere of Influence":
                self.results = SOI(self.star, self.body_list, int(self.le_n.text()), int(self.le_s.text()), int(self.le_r.text()))

        for body in range(0, len(self.body_list)):
            self.gv_xy.addItem(pyqtg.PlotDataItem(x=array(self.results[body][:])[:,0], y=array(self.results[body][:])[:,1], antialiasing=True, name=self.body_list[body].name, ))
            self.gv_3d.addItem(gl.GLLinePlotItem(pos=array(self.results[body]), color=self.body_list[body].color, antialias=True, mode='line_strip',width=3.0))
        self.gv_xy.addItem(pyqtg.ScatterPlotItem(x=[0 for x in range(steps)], y=[0 for x in range(steps)]))


    def reset(self):

        self.body_list.clear()
        self.body_list_model.clear()
        self.gv_3d.clear()
        self.gv_xy.clear()


    def removeBody(self):

        try:
            row = self.lv_bodies.selectionModel().selection().indexes()[0].row()
        except IndexError:
            QtWidgets.QMessageBox.warning(self, 'Error', 'Please choose a body to remove.', QtWidgets.QMessageBox.Ok)
            return
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
            pix = QPixmap(20, 20)
            pix.fill(QColor(body.color[0] * 255, body.color[1] * 255, body.color[2] * 255))
            icon = QIcon(pix)
            item = QStandardItem(icon, body.name)
            self.body_list_model.appendRow(item)

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

        self.current_color = selected_body.color
        pix = QPixmap(20, 20)
        pix.fill(QColor(self.current_color[0] * 255, self.current_color[1] * 255, self.current_color[2] * 255))
        bodyDialog.lbl_col_pixmap.setPixmap(pix)

        for body in self.body_presets:
            bodyDialog.cb_preset.addItem(body.name)

        bodyDialog.btn_color_choose.clicked.connect(lambda: chooseColor())
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

        def chooseColor():
            color = QtWidgets.QColorDialog.getColor(initial=QColor(self.current_color[0] * 255, self.current_color[1] * 255, self.current_color[2] * 255))
            temp_color = (float(color.red()/255), float(color.green()/255), float(color.blue()/255), 1.0)
            self.current_color = temp_color
            pix = QPixmap(20, 20)
            pix.fill(QColor(self.current_color[0] * 255, self.current_color[1] * 255, self.current_color[2] * 255))
            bodyDialog.lbl_col_pixmap.setPixmap(pix)
            print(self.current_color)


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
            selected_body.color = self.current_color
            self.updateListModel()
            dialog.done(0)

        dialog.show()
        dialog.exec_()


    def addBody(self):
        dialog = QtWidgets.QDialog()
        bodyDialog = bodyWidget()
        bodyDialog.setupUi(dialog)
        dialog.setWindowTitle("Add a New Body")

        self.current_color = None

        if self.current_color == None:
            self.current_color = (random(), random(), random(), 1.0)

        bodyDialog.btn_color_choose.clicked.connect(lambda: chooseColor())

        pix = QPixmap(20,20)
        pix.fill(QColor(self.current_color[0] * 255, self.current_color[1] * 255, self.current_color[2] * 255))
        bodyDialog.lbl_col_pixmap.setPixmap(pix)

        for body in self.body_presets:
            bodyDialog.cb_preset.addItem(body.name)

        bodyDialog.cb_preset.currentTextChanged.connect(lambda: loadPreset())
        bodyDialog.btn_ok.clicked.connect(lambda: returnBodyVals())
        bodyDialog.btn_cancel.clicked.connect(lambda: dialog.done(1))

        def chooseColor():
            color = QtWidgets.QColorDialog.getColor(initial=QColor(self.current_color[0] * 255, self.current_color[1] * 255, self.current_color[2] * 255))
            temp_color = (float(color.red()/255), float(color.green()/255), float(color.blue()/255), 1.0)
            self.current_color = temp_color
            pix = QPixmap(20, 20)
            pix.fill(QColor(self.current_color[0] * 255, self.current_color[1] * 255, self.current_color[2] * 255))
            bodyDialog.lbl_col_pixmap.setPixmap(pix)
            print(self.current_color)

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
            body.color = self.current_color
            pix = QPixmap(20, 20)
            pix.fill(QColor(self.current_color[0] * 255, self.current_color[1] * 255, self.current_color[2] * 255))
            icon = QIcon(pix)
            self.body_list.append(body)
            self.body_list_model.appendRow(QStandardItem(icon, body.name))
            dialog.done(0)

        loadPreset()

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
                    body = Body(row[1],float(row[2]),float(row[3]),float(row[4]),float(row[5]),float(row[6]))
                    if body.color == None:
                        body.color = (random(),random(),random(),1.0)
                    self.body_list.append(body)
                    print(body.color)
            for body in self.body_list:
                pix = QPixmap(20,20)
                pix.fill(QColor(body.color[0]*255, body.color[1]*255, body.color[2]*255))
                icon = QIcon(pix)
                item = QStandardItem(icon, body.name)
                self.body_list_model.appendRow(item)
            self.le_starname.setText(str(self.star.name))
            self.le_starmass.setText(str(self.star.mass))
            self.le_starradius.setText(str(self.star.radius))

        colors = imread('./lib/presets/stars/G.png')
        colors = colors / 255
        md = gl.MeshData.sphere(rows=600, cols=800, radius=1)
        md.setVertexColors(colors=colors)
        mi = gl.GLMeshItem(meshdata=md, smooth=True, computeNormals=False, shader='balloon')
        mi.scale(695000000, 695000000, 695000000)
        self.gv_3d.addItem(mi)



def main():
    app = QtWidgets.QApplication(sys.argv)
    win = SimMainWindow()
    win.show()
    app.exec_()
    return

if __name__ == '__main__':
    sys.excepthook = my_exception_hook
    main()
