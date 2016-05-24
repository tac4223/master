# -*- coding: utf-8 -*-
"""
Created on Mon May 02 10:23:12 2016

@author: mick
"""

from PyQt4 import uic, QtGui, QtCore
from get_dicom_data import filetools as ft
import os
import dynalog
import threading

Ui_Mainwindow, QMainwindow = uic.loadUiType("master.ui")

class Main(QMainwindow,Ui_Mainwindow):

    progress = QtCore.pyqtSignal()

    def __init__(self,):
        super(Main,self).__init__()
        self.setupUi(self)
        self.table_plans.resizeColumnsToContents()

        self.progress.connect(self.update_bar)

        self.button_dicomdir.clicked.connect(self.pick_dicomdir)
        self.edit_dicomdir.editingFinished.connect(self.changed_dicomdir)
        self.button_dynadir.clicked.connect(self.pick_dynadir)
        self.edit_dynadir.editingFinished.connect(self.changed_dynadir)
        self.button_outputdir.clicked.connect(self.pick_outputdir)

        self.button_plans_refresh.clicked.connect(self.populate_table)

        self.button_export.clicked.connect(self.export_thread)

        self.plans = []
        self.banks = {}

    def pick_dicomdir(self):
        filename = QtGui.QFileDialog.getExistingDirectory(self,\
            "DICOM-Verzeichnis")
        self.edit_dicomdir.setText(filename)

        self.plans = ft.get_plans(self.edit_dicomdir.text())
        self.populate_table()

    def changed_dicomdir(self):
        self.plans = ft.get_plans(self.edit_dicomdir.text())
        self.populate_table()

    def changed_dynadir(self):
        self.banks = ft.get_banks(self.edit_dynadir.text())
        self.populate_table()

    def pick_dynadir(self):
        filename = QtGui.QFileDialog.getExistingDirectory(self,\
            "DynaLog-Verzeichnis")
        self.edit_dynadir.setText(filename)
        self.banks = ft.get_banks(self.edit_dynadir.text())

        self.populate_table()

    def pick_outputdir(self):
        filename = QtGui.QFileDialog.getExistingDirectory(self,
        "Ausgabe-Verzeichnis")
        self.edit_outputdir.setText(filename)

    def populate_table(self):
        self.table_plans.setSortingEnabled(False)
        self.table_plans.setRowCount(len(self.plans))

        for num in range(len(self.plans)):
            self.table_plans.setItem(num,0,QtGui.QTableWidgetItem(",".join(
                [self.plans[num].header["patient_name"][0],
                 self.plans[num].header["patient_name"][1]])))
            self.table_plans.setItem(num,1,QtGui.QTableWidgetItem(
                self.plans[num].header["plan_name"]))
            self.table_plans.setItem(num,3,QtGui.QTableWidgetItem(
                self.plans[num].header["plan_uid"]))
            self.table_plans.setItem(num,2,QtGui.QTableWidgetItem("N/A"))
            try:
                complete = len(self.banks[self.plans[num].header["plan_uid"]])\
                    == 2*self.plans[num].arcs
            except KeyError:
                complete = False
            answer = {True:"Ja",False:"Nein"}
            self.table_plans.setItem(num,2,QtGui.QTableWidgetItem(answer[complete]))

        self.table_plans.resizeColumnsToContents()
        self.table_plans.setSortingEnabled(True)

    def update_bar(self):
        self.progressbar_export.setValue(self.progressbar_export.value()+1)
        if self.progressbar_export.value() == self.progressbar_export.maximum():
            self.busybar.setMaximum(1)

    def export_thread(self):
        self.progressbar_export.setMinimum(1)
        self.progressbar_export.setValue(1)
        self.busybar.setMaximum(0)
        self.progressbar_export.setMaximum(len(self.banks.keys())-1)

        for plan in self.plans:
            try:
                if 2*plan.arcs == len(self.banks[plan.header["plan_uid"]]):
                    t = threading.Thread(target=self.export,args=(plan,))
                    t.start()
            except KeyError:
                pass
            except:
                raise

    def export(self,plan):
        delchars = "".join(c for c in map(chr, range(256)) if not c.isalnum())

        filename = "_".join([plan.header["patient_name"][0],plan.header["patient_name"][1],plan.header["plan_name"]])
        filename = filename.replace(" ","_")
        filename = filename.translate(None,delchars) + ".dcm"
        try:
            plan.construct_logbeams(self.banks[plan.header["plan_uid"]])
            plan.validate_plan()
            os.chdir(str(self.edit_outputdir.text()))
            plan.export_dynalog_plan(plan.header["plan_name"],filename)
            self.progress.emit()

        except (KeyError,IndexError,dynalog.PlanMismatchError):
            raise

if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    main = Main()
    main.show()
    sys.exit(app.exec_())