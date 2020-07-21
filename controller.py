#!/usr/bin/python
import sys
import vtk
from PyQt5 import QtCore, QtGui, QtWidgets
import pickle
import copy
import time

import fixedSurface
import listSelection
import listExplosionSelection
import explosionSelection
import interact

# WIDTH = 1792
# HEIGHT = 1120
TASK_START = 0      # 0 means list selection, 1 means explosion selection
DATASET_ORDER = [1, 2, 3]
FIRST_START = 0     # 0 means inside, 1 means outside

class Controller:

    def __init__(self, width, height):
        self.initialize()
        self.centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        self.width = width
        self.height = height
        self.lastWindow = None

    def show_training1(self):
        self.training1 = listSelection.MainWindow("Training{}".format(TASK_START+1), self.width, self.height, self.dataTraining, self.startPointTraining, 
                    self.supportingCellsTraining, self.neighborsInOrderOfCellsTraining, self.presetSistersTraining,
                    self.actTissueListTraining, self.pointsTraining, self.tissuesTrianglesTraining, self.originalPropertyTraining, self.modelActorsTraining, 0, 0)
        self.training1.setGeometry(int(self.centerPoint.x() - self.width/2), int(self.centerPoint.y() - self.height/2), self.width, self.height)
        self.training1.next_task.connect(self.show_task1)
        if (self.lastWindow != None):
            self.lastWindow.close()
        self.training1.show()

    # Choose from list
    def show_task1(self):
        self.task1 = listSelection.MainWindow("Task{}".format(TASK_START+1), self.width, self.height, self.data, self.startPoint, 
                    self.supportingCells, self.neighborsInOrderOfCells, self.presetSisters,
                    self.actTissueList, self.points, self.tissuesTriangles, self.originalProperty, self.modelActors, DATASET_ORDER[TASK_START], FIRST_START)
        self.task1.setGeometry(int(self.centerPoint.x() - self.width/2), int(self.centerPoint.y() - self.height/2), self.width, self.height)
        if (TASK_START == 0):
            self.task1.next_task.connect(self.show_training2)
        else:
            self.task1.next_task.connect(self.show_training3)
        self.training1.close()
        # self.startTime = time.time()
        self.lastWindow = self.task1
        self.task1.show()

    def show_training2(self):
        # self.times.append(time.time() - self.startTime)
        self.training2 = explosionSelection.MainWindow("Training{}".format(2-TASK_START), self.width, self.height, self.dataTraining, self.startPointTraining, 
                    self.supportingCellsTraining, self.neighborsInOrderOfCellsTraining, self.presetSistersTraining,
                    self.actTissueListTraining, self.pointsTraining, self.tissuesTrianglesTraining, self.originalPropertyTraining, self.modelActorsTraining, 0, 0)
        self.training2.setGeometry(int(self.centerPoint.x() - self.width/2), int(self.centerPoint.y() - self.height/2), self.width, self.height)
        if (self.lastWindow != None):
            self.lastWindow.close()
        self.training2.next_task.connect(self.show_task2)
        self.training2.show()


    # Choose from exploded view + list
    def show_task2(self):
        self.task2 = explosionSelection.MainWindow("Task{}".format(2-TASK_START), self.width, self.height, self.data, self.startPoint, 
                    self.supportingCells, self.neighborsInOrderOfCells, self.presetSisters,
                    self.actTissueList, self.points, self.tissuesTriangles, self.originalProperty, self.modelActors, DATASET_ORDER[1-TASK_START], 1-FIRST_START)
        if (TASK_START == 0):
            self.task2.next_task.connect(self.show_training3)
        else:
            self.task2.next_task.connect(self.show_training1)
        self.task2.setGeometry(int(self.centerPoint.x() - self.width/2), int(self.centerPoint.y() - self.height/2), self.width, self.height)
        self.training2.close()
        # self.startTime = time.time()
        self.lastWindow = self.task2
        self.task2.show()

    def show_training3(self):
        # self.times.append(time.time() - self.startTime)
        self.training3 = listExplosionSelection.MainWindow("Training3", self.width, self.height, self.dataTraining, self.startPointTraining, 
                    self.supportingCellsTraining, self.neighborsInOrderOfCellsTraining, self.presetSistersTraining,
                    self.actTissueListTraining, self.pointsTraining, self.tissuesTrianglesTraining, self.originalPropertyTraining, self.modelActorsTraining, 0)
        self.training3.setGeometry(int(self.centerPoint.x() - self.width/2), int(self.centerPoint.y() - self.height/2), self.width, self.height)
        if (self.lastWindow != None):
            self.lastWindow.close()
        self.training3.next_task.connect(self.show_task3)
        self.training3.show()


    # Choose from exploded view
    def show_task3(self):
        # self.times.append(time.time() - self.startTime)
        self.task3 = listExplosionSelection.MainWindow("Task3", self.width, self.height, self.data, self.startPoint, 
                    self.supportingCells, self.neighborsInOrderOfCells, self.presetSisters,
                    self.actTissueList, self.points, self.tissuesTriangles, self.originalProperty, self.modelActors, DATASET_ORDER[2])
        self.task3.setGeometry(int(self.centerPoint.x() - self.width/2), int(self.centerPoint.y() - self.height/2), self.width, self.height)
        self.task3.next_task.connect(self.completeTasks)
        self.training3.close()
        # self.startTime = time.time()
        self.task3.show()

    def completeTasks(self):
        # self.times.append(time.time() - self.startTime)
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("Thanks!")
        msg.setText("Congratulations! You have finished all the tasks!")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.buttonClicked.connect(self.closeLastWindow)
        msg.exec_()

    def closeLastWindow(self, i):
        self.task3.close()


    def initialize(self):
        pickleFile = 'cell210.pickle'
        trainingFile = 'cell47.pickle'
        self.data, self.startPoint, self.supportingCells, self.neighborsInOrderOfCells, self.presetSisters, self.actTissueList, self.points, self.tissuesTriangles, self.originalProperty, self.modelActors = interact.initialize(pickleFile)
        self.dataTraining, self.startPointTraining, self.supportingCellsTraining, self.neighborsInOrderOfCellsTraining, self.presetSistersTraining, self.actTissueListTraining, self.pointsTraining, self.tissuesTrianglesTraining, self.originalPropertyTraining, self.modelActorsTraining = interact.initialize(trainingFile)

def main():
    app = QtWidgets.QApplication(sys.argv)
    screen_resolution = app.desktop().screenGeometry()
    width, height = screen_resolution.width(), screen_resolution.height()
    # width, height = 1280, 800 
    controller = Controller(width, height)
    if (TASK_START == 0):
        controller.show_training1()
    elif (TASK_START == 1):
        controller.show_training2()
        
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

    