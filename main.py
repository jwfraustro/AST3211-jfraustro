from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import lib.assets.gui.mainWindow as mainWindow
from lib.assets.gui.bodyWidget import Ui_bodyForm as bodyWidget
import sys, os, csv, glob


def my_exception_hook(exctype, value, traceback):
    # Print the error and traceback
    print(exctype, value, traceback)
    # Call the normal Exception hook after
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)

class Body:
    def __init__(self, body_type, name, mass, radius, sma, vel, inc):
        self.body_type = body_type
        self.name = name
        self.mass = mass
        self.radius = radius
        self.sma = sma
        self.vel = vel
        self.inc = inc


class SimMainWindow(QtWidgets.QMainWindow, mainWindow.Ui_SimMainWindow):
    def __init__(self, parent=None):
        super(SimMainWindow, self).__init__(parent)

        self.body_list = []

        self.setupUi(self)

        self.loadPresetFiles()

        self.body_list_model = QStandardItemModel(self.lv_bodies)
        self.lv_bodies.setModel(self.body_list_model)
        self.lv_bodies.doubleClicked.connect(self.editBody)

        self.btn_loadpreset.clicked.connect(self.loadPreset)
        self.btn_addbody.clicked.connect(self.addBody)
        self.btn_rmbody.clicked.connect(self.removeBody)
        self.btn_reset.clicked.connect(self.reset)
        self.btn_clear.clicked.connect(self.clearPlot)
        self.btn_plot.clicked.connect(self.handlePlot)

    def clearPlot(self):
        return
    def handlePlot(self):
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

        for preset in glob.glob('./lib/systems/presets/*.csv'):
            self.cmb_preset.addItem(os.path.basename(preset))

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

        bodyDialog.btn_ok.clicked.connect(lambda: returnBodyVals())
        bodyDialog.btn_cancel.clicked.connect(lambda: dialog.done(1))

        bodyDialog.le_name.setText(str(selected_body.name))
        bodyDialog.le_radius.setText(str(selected_body.vel))
        bodyDialog.le_mass.setText(str(selected_body.mass))
        bodyDialog.le_sma.setText(str(selected_body.sma))
        bodyDialog.le_vel.setText(str(selected_body.vel))
        bodyDialog.le_inc.setText(str(selected_body.inc))

        if selected_body.body_type == "s":
            bodyDialog.cb_star.setChecked(True)

        def returnBodyVals():
            name = bodyDialog.le_name.text()
            mass = float(bodyDialog.le_mass.text())
            radius = float(bodyDialog.le_radius.text())
            sma = float(bodyDialog.le_sma.text())
            vel = float(bodyDialog.le_vel.text())
            inc = float(bodyDialog.le_inc.text())
            if bodyDialog.cb_star.isChecked():
                body_type = "s"
            else:
                body_type = "p"

            selected_body.name = name
            selected_body.mass = mass
            selected_body.radius = radius
            selected_body.sma = sma
            selected_body.vel = vel
            selected_body.inc = inc
            selected_body.body_type = body_type


            self.updateListModel()
            dialog.done(0)

        dialog.show()
        dialog.exec_()


    def addBody(self):
        dialog = QtWidgets.QDialog()
        bodyDialog = bodyWidget()
        bodyDialog.setupUi(dialog)
        dialog.setWindowTitle("Add a New Body")

        bodyDialog.btn_ok.clicked.connect(lambda: returnBodyVals())
        bodyDialog.btn_cancel.clicked.connect(lambda: dialog.done(1))

        def returnBodyVals():
            name = bodyDialog.le_name.text()
            mass = float(bodyDialog.le_mass.text())
            radius = float(bodyDialog.le_radius.text())
            sma = float(bodyDialog.le_sma.text())
            vel = float(bodyDialog.le_vel.text())
            inc = float(bodyDialog.le_inc.text())
            if bodyDialog.cb_star.isChecked():
                body_type = "s"
            else:
                body_type = "p"
            body = Body(body_type, name, mass, radius, sma, vel, inc)
            self.body_list.append(body)
            self.body_list_model.appendRow(QStandardItem(body.name))
            dialog.done(0)

        dialog.show()
        dialog.exec_()


    def loadPreset(self):

        preset = ('./lib/systems/presets/'+self.cmb_preset.currentText())

        self.reset()

        with open(preset, 'r') as f:
            reader = csv.reader(f, delimiter=',')
            next(reader)
            for row in reader:
                self.body_list.append(Body(row[0],row[1],row[2],row[3],row[4],row[5],row[6]))
            for body in self.body_list:
                item = QStandardItem(body.name)
                self.body_list_model.appendRow(item)




def main():
    app = QtWidgets.QApplication(sys.argv)
    win = SimMainWindow()
    win.show()
    app.exec_()
    return

if __name__ == '__main__':
    sys.excepthook = my_exception_hook
    main()
