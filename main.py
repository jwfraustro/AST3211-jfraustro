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

        self.btn_loadpreset.clicked.connect(self.loadPreset)
        self.btn_addbody.clicked.connect(self.addBody)


    def loadPresetFiles(self):

        for preset in glob.glob('./lib/systems/presets/*.csv'):
            self.cmb_preset.addItem(os.path.basename(preset))

    def addBody(self):
        dialog = QtWidgets.QDialog()
        bodyDialog = bodyWidget()
        bodyDialog.setupUi(dialog)

        bodyDialog.btn_ok.clicked.connect(lambda: returnBodyVals())
        bodyDialog.btn_cancel.clicked.connect(lambda: dialog.done(0))

        def returnBodyVals():
            name = bodyDialog.le_name.text()
            mass = float(bodyDialog.le_mass.text())
            radius = float(bodyDialog.le_radius.text())
            sma = float(bodyDialog.le_sma.text())
            vel = float(bodyDialog.le_vel.text())
            inc = float(bodyDialog.le_inc.text())


        dialog.show()
        dialog.exec_()


    def loadPreset(self):

        preset = ('./lib/systems/presets/'+self.cmb_preset.currentText())

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
