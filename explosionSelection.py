#!/usr/bin/python
import vtk
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap, QImage   
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtWidgets import QMessageBox
import time
import random
import copy
import math
import re
import os

import interact
import fixedSurface
import log

VIS_WIDTH_RATIO = 0.7
VIS_HEIGHT_RATIO = 0.78

BUTTON_WIDTH_RATIO = 0.2
LIST_WIDTH_RATIO = 0.11
LIST_HEIGHT_RATIO = 0.5
SPACING = 0.035

TO_MARK = 10
TRAINING_CELLS = 50

class MainWindow(QtWidgets.QMainWindow):

    next_task = QtCore.pyqtSignal(str)

    def __init__(self, name, width, height, data, startPoint, supportingCells, neighborsInOrderOfCells, presetSisters, actTissueList, points, tissuesTriangles, originalProperty, modelActors, datasetNum, firstCell):
        QtWidgets.QMainWindow.__init__(self)
        
        self.setWindowTitle(name)
        self.width = width
        self.height = height
        self.data = data
        self.startPoint = startPoint
        self.supportingCells = supportingCells
        self.neighborsInOrderOfCells = neighborsInOrderOfCells
        self.presetSisters = presetSisters
        self.actTissueList =actTissueList
        self.points = points
        self.tissuesTriangles = tissuesTriangles
        self.originalProperty = originalProperty
        self.modelActors = modelActors
        self.datasetNum = datasetNum

        self.centralwidget = QtWidgets.QWidget()
        self.frame = QtWidgets.QFrame(self.centralwidget)

        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
        self.vtkWidget.setFixedSize(self.width * VIS_WIDTH_RATIO, self.height * VIS_HEIGHT_RATIO)

        self.wholeVL = QtWidgets.QVBoxLayout(self.centralwidget)

        self.value = int(re.split('(\d+)',name)[1])
        self.wholeProgressHL = QtWidgets.QHBoxLayout()
        self.wholeProgressLabel = QtWidgets.QLabel(self.centralwidget)
        self.wholeProgressHL.addWidget(self.wholeProgressLabel)
        if (len(self.modelActors) > TRAINING_CELLS):    self.isTraining = False
        else:                                           self.isTraining = True
        if (self.isTraining):
            self.wholeProgressLabel.setText("<h3>Training Session{}</h3>".format(self.value))
        else:   
            self.wholeProgressLabel.setText("<h3>Task Progress: {} / {}</h3>".format(0, TO_MARK))
            self.task1Progress = QtWidgets.QProgressBar(self.centralwidget)
            self.task2Progress = QtWidgets.QProgressBar(self.centralwidget)
            self.task3Progress = QtWidgets.QProgressBar(self.centralwidget)
            self.progressBar = []
            self.progressBar.append(self.task1Progress)
            self.progressBar.append(self.task2Progress)
            self.progressBar.append(self.task3Progress)
            for i in range(self.value-1):
                self.progressBar[i].setValue(100)
            self.wholeProgressHL.addWidget(self.task1Progress)
            self.wholeProgressHL.addWidget(self.task2Progress)
            self.wholeProgressHL.addWidget(self.task3Progress)

        self.hl = QtWidgets.QHBoxLayout()

        self.taskLabel = QtWidgets.QLabel(self.centralwidget)
        self.taskLabel.setText("In this task, you could only select cells from objects in the main view and move the scroll bar enables to get the exploded view.")
        self.taskLabel.setWordWrap(True)
        self.taskLabel.setFixedSize(self.width * (VIS_WIDTH_RATIO-LIST_WIDTH_RATIO), 40)
        if (sys.platform == 'darwin'):  self.font_size = [20, 50]
        else:   self.font_size = [15,25]
        font = QtGui.QFont("Times", self.font_size[0], QtGui.QFont.Bold) 
        self.taskLabel.setFont(font)
        self.mainVL = QtWidgets.QGridLayout()
        self.mainVL.addWidget(self.taskLabel,0,0,1,9)
        self.setAsSisterButton = QtWidgets.QPushButton(self.centralwidget)
        self.setAsSisterButton.setText("Set as Sister")
        self.setAsSisterButton.setFixedSize(self.width*LIST_WIDTH_RATIO, 50)
        self.mainVL.addWidget(self.setAsSisterButton, 0,9,1,1)
        self.mainVL.addWidget(self.vtkWidget,1,0,10,10)

        # Add a horizontal ScrollBar
        self.horizontalScrollBar = QtWidgets.QScrollBar(self.centralwidget)
        self.horizontalScrollBar.setOrientation(QtCore.Qt.Horizontal)
        self.preBarValue = 0
        self.horizontalScrollBar.sliderMoved.connect(lambda:self.update_scrollBar())
        self.mainVL.addWidget(self.horizontalScrollBar, 11,0,1,10)

        self.zoomExtentsButton = QtWidgets.QPushButton(self.centralwidget)
        self.zoomExtentsButton.setText("Zoom Extents")
        self.zoomExtentsButton.setFixedSize(self.width*BUTTON_WIDTH_RATIO, 50)
        self.zoomExtentsButton.clicked.connect(self.pressZoomExtents)
        self.chooseLayout = QtWidgets.QHBoxLayout()
        self.chooseLayout.addWidget(self.zoomExtentsButton)
        self.nextTaskButton = QtWidgets.QPushButton(self.centralwidget)
        self.nextTaskButton.setText("Next Task")
        self.nextTaskButton.setFixedSize(self.width*BUTTON_WIDTH_RATIO, 50)
        self.nextTaskButton.clicked.connect(self.switch)
        # self.nextTaskButton.setEnabled(False)

        self.rightVL = QtWidgets.QVBoxLayout()
        self.rightVL.addLayout(self.chooseLayout)
        self.nextTaskLayout = QtWidgets.QVBoxLayout()
        if (self.isTraining):
            self.toMarkTissues = list(range(0, len(self.presetSisters)))
            random.shuffle(self.toMarkTissues)
        else:
            self.toMarkTissues = interact.presetDataset(datasetNum, firstCell)
        self.nextTaskLayout.addWidget(self.nextTaskButton)
        self.rightVL.addLayout(self.nextTaskLayout)
        self.rightVL.setAlignment(QtCore.Qt.AlignHCenter)

        self.hl.addLayout(self.mainVL)
        self.hl.addLayout(self.rightVL)

        self.wholeVL.addLayout(self.wholeProgressHL)
        self.wholeVL.addLayout(self.hl)

        self.frame.setLayout(self.wholeVL)
        self.setCentralWidget(self.frame)

        self.menubar = QtWidgets.QMenuBar()
        self.menubar.setGeometry(QtCore.QRect(0, 0, self.width, 22))
        self.menuEdit = QtWidgets.QMenu(self.menubar)
        self.menuEdit.setTitle("Edit")
        self.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar()
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)
        self.actionAssign = QtWidgets.QAction()
        self.menuEdit.addAction(self.actionAssign)
        self.menubar.addAction(self.menuEdit.menuAction())
        self.actionAssign.triggered.connect(lambda:self.spaceSetSister())
        self.actionAssign.setShortcut("Space")
        self.actionAssign.setText("Set as Sister")

        self.Initialize()

    def switch(self):
        self.next_task.emit("True")
        self.vtkWidget.GetRenderWindow().Finalize()
        self.interactor.TerminateApp()


    def createCSVfile(self):
        self.trialNumber = int(len(self.markedTissues)/2)
        self.csvFileName = "log/{}_ExplosionSelection_{}_{}.csv".format(self.value, self.datasetNum, self.trialNumber)
        i = 1
        while os.path.exists(self.csvFileName):
            self.csvFileName = "log/{}_ExplosionSelection_{}_{}({}).csv".format(self.value, self.datasetNum, self.trialNumber, i)
            i += 1

        self.logFile = log.logFile(self.csvFileName)
        self.myInteractorStyle.setLogFile(self.logFile)


    def Initialize(self):
        self.renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()

        self.centerOfPolyData = vtk.vtkCenterOfMass()
        self.markedTissues = []
        self.lastSelectedItemIndex = None
        self.chosenNeighbor = None
        self.sister1 = None     # set these two as sisters
        self.sister2 = None
        self.correctness = 0

        self.resetActors()
        self.addActorsToRender()
        self.calCenter()
        self.setupCamera()
        self.zoomExtents() 

        self.myInteractorStyle = interact.MyInteractorStyle()
        self.interactor.SetInteractorStyle(self.myInteractorStyle)
        self.continueMarking()
        if (not self.isTraining):
            def kayboardPressedActor(obj, ev):
                self.logFile.recordPress("Keyboard", obj.GetKeySym(), self.camera.GetPosition(), self.camera.GetFocalPoint(), self.camera.GetDistance())
            self.interactor.AddObserver('KeyPressEvent', kayboardPressedActor, -1.0)       

        self.numberOfClicks = 0
        self.prePosition = [0,0]
        self.lastSingleClicked = None
        self.lastDoubleClicked = None
        def leftClickedActorHighlight(obj, ev):
            self.numberOfClicks += 1
            clickPos = obj.GetEventPosition()
            xdist = clickPos[0] - self.prePosition[0]
            ydist = clickPos[1] - self.prePosition[1]
            self.prePosition = clickPos
            moveDistance = int(math.sqrt(xdist*xdist + ydist*ydist))

            picker = vtk.vtkPropPicker()
            picker.Pick(clickPos[0], clickPos[1], 0, obj.FindPokedRenderer(clickPos[0], clickPos[1]))
            NewPickedActor = picker.GetActor()

            if (moveDistance > 0):
                self.numberOfClicks = 1
                if (NewPickedActor and NewPickedActor in self.modelActors):
                    index = self.modelActors.index(NewPickedActor)
                    if (index != self.lastDoubleClicked):
                        if (self.lastSingleClicked != None and self.lastSingleClicked not in self.markedTissues):
                            self.modelActors[self.lastSingleClicked].GetProperty().DeepCopy(self.originalProperty[self.lastSingleClicked])
                        # if in focus view, highlight item in the neighbor list. or highlight in tissue list
                        if (self.lastDoubleClicked != None and self.lastDoubleClicked not in self.markedTissues):
                            if (self.findIndexOfOri(index) in self.neighbors):
                                self.formNeighborText(index, self.neighbors.index(self.findIndexOfOri(index)))
                            interact.highLightNeighbor(self.modelActors[index].GetProperty())
                            if (not self.isTraining):   self.logFile.updateSister(2, self.findIndexOfOri(index), "-", fixedSurface.outsideOrInside(self.findIndexOfOri(index)))
                        else:
                            interact.highLightTissue(self.modelActors[index].GetProperty())
                        self.lastSingleClicked = index
                    if (not self.isTraining):
                        self.logFile.recordClick("Click", "MainView", self.findIndexOfOri(index), self.camera.GetPosition(), self.camera.GetFocalPoint(), self.camera.GetDistance())

            if (self.numberOfClicks == 2):
                if (NewPickedActor and NewPickedActor in self.modelActors):
                    index = self.modelActors.index(NewPickedActor)
                    if (self.textOn == True):
                        self.renderer.RemoveActor2D(self.neighborTextActor)
                        self.textOn = False
                    self.showNeighbors(self.findIndexOfOri(index))
                    if (self.lastSingleClicked != None and self.lastSingleClicked not in self.markedTissues):
                        self.modelActors[self.lastSingleClicked].GetProperty().DeepCopy(self.originalProperty[self.lastSingleClicked])
                        self.lastSingleClicked = None
                    # if (self.lastDoubleClicked != None and self.lastDoubleClicked not in self.markedTissues):
                    #     self.modelActors[self.lastDoubleClicked].GetProperty().DeepCopy(self.originalProperty[self.lastDoubleClicked])
                    if (self.lastDoubleClicked == None):
                        for actor in self.renderer.GetActors():
                            self.renderer.RemoveActor(actor)
                        self.renderer.AddActor(self.modelActors[index])
                        interact.highLightTissue(self.modelActors[index].GetProperty())
                        neighbors = self.neighborsInOrderOfCells[self.findIndexOfOri(index)].copy()
                        for neighbor in neighbors:
                            if (self.findIndexOfList(neighbor) not in self.markedTissues):
                                self.renderer.AddActor(self.modelActors[self.findIndexOfList(neighbor)])
                        if (not self.isTraining):   self.logFile.updateSister(1, self.findIndexOfOri(index), len(neighbors), fixedSurface.outsideOrInside(self.findIndexOfOri(index)))
                        self.camera.SetFocalPoint(self.modelActors[index].GetCenter())
                        # interact.highLightTissue(self.modelActors[index].GetProperty())
                        self.lastDoubleClicked = index
                    elif (self.lastDoubleClicked == index):
                        if (not self.isTraining):
                            self.logFile.updateSister(1, "-", "-", "-")
                            self.logFile.updateSister(2, "-", "-", "-")
                        for actor in self.modelActors:
                            if (self.modelActors.index(actor) not in self.markedTissues and actor not in self.renderer.GetActors()):
                                self.renderer.AddActor(actor)
                        self.modelActors[index].GetProperty().DeepCopy(self.originalProperty[self.lastDoubleClicked])
                        self.lastDoubleClicked = None
                        self.lastSingleClicked = None                
                    self.vtkWidget.GetRenderWindow().Render()
                    if (not self.isTraining):
                        self.logFile.recordClick("DoubleClick", "MainView", self.findIndexOfOri(index), self.camera.GetPosition(), self.camera.GetFocalPoint(), self.camera.GetDistance())
                self.numberOfClicks = 0

        self.interactor.AddObserver('LeftButtonPressEvent', leftClickedActorHighlight, -1.0)
        
        self.setAsSisterButton.clicked.connect(self.clickSetSister)

        self.show()
        self.interactor.Initialize()
        self.interactor.Start()

    def resetActors(self):
        for pro in self.originalProperty:
            pro.SetColor(1.0, 1.0, 1.0)
        for i in range(len(self.modelActors)):
            self.modelActors[i].GetProperty().DeepCopy(self.originalProperty[i])
            self.modelActors[i].SetPosition(0.0, 0.0, 0.0)

    def continueMarking(self):
        if (self.isTraining):
            while (len(self.toMarkTissues) != 0):
                self.toMark = self.toMarkTissues.pop(0)
                if (self.presetSisters[self.toMark] == None):   continue
                break
        elif (len(self.toMarkTissues) != 0):
            self.toMark = self.toMarkTissues.pop(0)
            self.createCSVfile()
        else:
            msg = QMessageBox()
            msg.setWindowTitle("Alert!")
            msg.setText("You have already finished this task!\nAre you sure to continue now?")
            msg.setIcon(QMessageBox.Information)
            msg.setStandardButtons(QMessageBox.Ok|QMessageBox.Ignore)
            msg.buttonClicked.connect(self.popup_button)
            msg.exec_()
        index = self.findIndexOfList(self.toMark)
        self.originalProperty[index].SetColor(1, 0.6, 0)
        self.modelActors[index].GetProperty().DeepCopy(self.originalProperty[index])

    def popup_button(self, i):
        print(i.text())
        if (i.text() == "OK"):
            self.switch()

    def calCenter(self):
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(self.points)
        self.centerOfPolyData.SetInputData(polydata)
        del polydata
        self.centerOfPolyData.SetUseScalarsAsWeights(False)
        self.centerOfPolyData.Update()

    def addActorsToRender(self):
        # set up neighbor text actor
        self.neighborTextActor = vtk.vtkBillboardTextActor3D()
        self.neighborTextActor.GetTextProperty().SetFontSize(self.font_size[1])
        self.neighborTextActor.GetTextProperty().SetColor(1.0,1.0,0)
        self.neighborTextActor.GetTextProperty().SetJustificationToCentered()
        self.textOn = False

        for actor in self.modelActors:
            self.renderer.AddActor(actor)

    def setupCamera(self):
        self.camera = vtk.vtkCamera()
        self.camera.SetViewUp(0.0, 0.0, 0.0)
        # set the focal point the center of the model
        self.camera.SetFocalPoint(self.centerOfPolyData.GetCenter())
        # self.camera.SetPosition(interact.zoomoutCam(self.camera))
        self.renderer.SetActiveCamera(self.camera)

    #### Interaction

    # Function to show the neighbors in the second column
    def showNeighbors(self, index):
        self.neighbors = self.neighborsInOrderOfCells[index].copy()
        sister = self.presetSisters[index] #indexOfOri
        if (sister == None):
            self.assignedNumbers = interact.formTargetRandomNumber(len(self.neighbors), None)
        else:
            self.assignedNumbers = interact.formTargetRandomNumber(len(self.neighbors), self.neighbors.index(sister))

    def pressZoomExtents(self):
        if (not self.isTraining):
            self.logFile.recordPress("Button", "AutoScale", self.camera.GetPosition(), self.camera.GetFocalPoint(), self.camera.GetDistance())
        self.zoomExtents()

    def zoomExtents(self):
        self.existingActorsIndex = self.calExistingActorsIndex()
        self.recalculateCenter(self.existingActorsIndex)
        self.camera.SetFocalPoint(self.centerOfPolyData.GetCenter())
        self.camera.SetPosition(interact.zoomoutCam(self.camera))
        self.vtkWidget.GetRenderWindow().Render()


        # Get the existing actors indexes
    def calExistingActorsIndex(self):
        actors = self.renderer.GetActors()
        existingActorsIndex = []
        for actor in actors:
            existingActorsIndex.append(self.modelActors.index(actor))
        return list(set(existingActorsIndex))

    def recalculateCenter(self, actorsIndex):
        points = vtk.vtkPoints()
        for i in range(len(actorsIndex)):
            points.InsertPoint(i, self.modelActors[actorsIndex[i]].GetCenter())
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        self.centerOfPolyData.SetInputData(polydata)
        del points
        del polydata
        self.centerOfPolyData.Update()

    def formNeighborText(self, index, numberIndex):
        if (self.textOn == False):
            self.renderer.AddActor2D(self.neighborTextActor)
            self.textOn = True
        self.neighborTextActor.SetInput(str(self.assignedNumbers[numberIndex]))
        position = self.modelActors[index].GetCenter()
        pos1 = self.modelActors[self.lastDoubleClicked].GetCenter()
        appendFilter = vtk.vtkAppendPolyData()
        appendFilter.AddInputData(self.modelActors[index].GetMapper().GetInput())
        appendFilter.Update()
        polyData = vtk.vtkPolyData()
        polyData = appendFilter.GetOutput()
        bounds = [0 for i in range(6)]
        polyData.GetBounds(bounds)
        self.indicateNumberOriginPos = interact.surfaceNearPoint(pos1, position, self.camera.GetPosition(), bounds)
        self.neighborTextActor.SetPosition(interact.moveIndicateNumber(self.indicateNumberOriginPos, self.modelActors[index].GetPosition()))
        # self.renderer.AddActor2D(self.neighborTextActor)


    def spaceSetSister(self):
        if (not self.isTraining):
            self.logFile.recordPress("Keyboard", "Space", self.camera.GetPosition(), self.camera.GetFocalPoint(), self.camera.GetDistance())
        self.setSister()

    def clickSetSister(self):
        if (not self.isTraining):
            self.logFile.recordPress("Button", "SetAsSister", self.camera.GetPosition(), self.camera.GetFocalPoint(), self.camera.GetDistance())
        self.setSister()

    # Set as sister
    def setSister(self):
        # index of list
        self.sister1 = self.lastDoubleClicked
        self.sister2 = self.lastSingleClicked
        if (self.sister1 == None or self.sister2 == None):
            interact.alert_pop("sisters")
            return
        self.markedTissues.append(self.sister1)
        self.markedTissues.append(self.sister2)

        self.renderer.RemoveActor(self.modelActors[self.sister1])
        self.renderer.RemoveActor(self.modelActors[self.sister2])
        self.continueMarking()
        self.lastSingleClicked = None
        self.lastDoubleClicked = None

        if (not self.isTraining):
            self.wholeProgressLabel.setText("<h3>Task Progress: {} / {}</h3>".format(int(len(self.markedTissues)/2), TO_MARK))
            self.progressBar[self.value-1].setValue(int(len(self.markedTissues)/(TO_MARK * 2)*100))
            # if (self.presetSisters[self.findIndexOfOri(self.sister1)] == self.findIndexOfOri(self.sister2)):
            #     self.correctness += int(100 / TO_MARK)

        if (self.textOn == True):
            self.renderer.RemoveActor2D(self.neighborTextActor)
            self.textOn = False
        for actor in self.modelActors:
            if (self.modelActors.index(actor) not in self.markedTissues and actor not in self.renderer.GetActors()):
                self.renderer.AddActor(actor)
        self.camera.SetFocalPoint(self.centerOfPolyData.GetCenter())
        self.vtkWidget.GetRenderWindow().Render()
        
        if (len(self.markedTissues) == 40):
            self.nextTaskButton.setEnabled(True)


    #########################
    ##### Exploded View #####
    #########################

    def update_scrollBar(self):
        value = self.horizontalScrollBar.value()
        if (not self.isTraining):
            diff = value - self.preBarValue
            self.logFile.recordScroll("ExplosionBar", diff, self.camera.GetPosition(), self.camera.GetFocalPoint(), self.camera.GetDistance())
            self.preBarValue = value
        current_scroll = value / 50
        coordinates = self.explodedViewDisplay(current_scroll)
        if (self.lastDoubleClicked != None):
            position = coordinates[self.lastDoubleClicked]
            for index in range(len(self.modelActors)):
                self.modelActors[index].SetPosition(self.keepTargetStill(coordinates[index], position))
        else:
            for index in range(len(self.modelActors)):
                self.modelActors[index].SetPosition(coordinates[index])
        if (self.textOn == True):
            self.neighborTextActor.SetPosition(interact.moveIndicateNumber(self.indicateNumberOriginPos, self.modelActors[self.lastSingleClicked].GetPosition()))
        self.vtkWidget.GetRenderWindow().Render()
    
    
    def explodedViewDisplay(self, scrollValue):
        coordinates = []
        for index in range(len(self.modelActors)):
            coordinate = []
            for i in range(3):
                coordinate.append(scrollValue * (self.modelActors[index].GetCenter()[i] - self.centerOfPolyData.GetCenter()[i]))
            coordinates.append(coordinate)
        return coordinates

    def keepTargetStill(self, pos1, pos2):
        return [pos1[0] - pos2[0], pos1[1] - pos2[1], pos1[2] - pos2[2]]


    ### The index is different with the original one
    ### The list does not include supporting cells

    def findIndexOfOri(self, indexOfList):
        return self.actTissueList[indexOfList]

    def findIndexOfList(self, indexOfOri):
        return self.actTissueList.index(indexOfOri)  