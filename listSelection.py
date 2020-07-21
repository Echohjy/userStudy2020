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
import re
import os
import math

import fixedSurface
import interact
import log

VIS_WIDTH_RATIO = 0.7
VIS_HEIGHT_RATIO = 0.83

BUTTON_WIDTH_RATIO = 0.2
LIST_WIDTH_RATIO = 0.11
LIST_HEIGHT_RATIO = 0.5
SPACING = 0.035

TO_MARK = 10
TRAINING_CELLS = 50
DISTANCE = 0.4


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
        self.neighborsInOrderOfCells = interact.orderNeighbors(neighborsInOrderOfCells)
        self.presetSisters = presetSisters
        self.actTissueList = actTissueList
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
        if (len(self.modelActors) < TRAINING_CELLS):    self.isTraining = True
        else:   self.isTraining = False
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
        self.taskLabel.setText("In this task, you could select cells from the lists on the right part.")
        if (sys.platform.startswith('darwin')):  self.font_size = [20, 50]
        else:   self.font_size = [15,25]
        font = QtGui.QFont("Times", self.font_size[0], QtGui.QFont.Bold)
        self.taskLabel.setWordWrap(True)
        self.taskLabel.setFont(font)
        self.taskLabel.setFixedSize(self.width * (VIS_WIDTH_RATIO-LIST_WIDTH_RATIO), 40)
        self.mainVL = QtWidgets.QGridLayout()
        self.mainVL.addWidget(self.taskLabel, 0,0,1,9)
        self.setAsSisterButton = QtWidgets.QPushButton()
        self.setAsSisterButton.setText("Set As Sister")
        self.setAsSisterButton.setFixedSize(self.width*LIST_WIDTH_RATIO, 50)
        self.mainVL.addWidget(self.setAsSisterButton, 0,9,1,1)
        self.mainVL.addWidget(self.vtkWidget, 1,0,10,10)

        self.tissueLabel = QtWidgets.QLabel(self.centralwidget)
        self.tissueLabel.setText("Tissues' names")
        self.tissueLabel.setFixedSize(self.width*LIST_WIDTH_RATIO,10)
        self.tissueList = QtWidgets.QListWidget()
        self.tissueList.setFixedSize(self.width*LIST_WIDTH_RATIO, self.height*LIST_HEIGHT_RATIO)
        self.tissueList.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tissueLayout = QtWidgets.QVBoxLayout()
        self.tissueLayout.addWidget(self.tissueLabel)
        self.tissueLayout.addWidget(self.tissueList)

        self.neighborLabel = QtWidgets.QLabel(self.centralwidget)
        self.neighborLabel.setText("Neighbors")
        self.neighborLabel.setFixedSize(self.width*LIST_WIDTH_RATIO,10)
        self.neighborList = QtWidgets.QListWidget()
        self.neighborList.setFixedSize(self.width*LIST_WIDTH_RATIO,self.height*LIST_HEIGHT_RATIO)
        self.neighborList.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.neighborWidget = QtWidgets.QVBoxLayout()
        self.neighborWidget.addWidget(self.neighborLabel)
        self.neighborWidget.addWidget(self.neighborList)

        self.listLayout = QtWidgets.QHBoxLayout()
        self.listLayout.addLayout(self.tissueLayout)
        self.listLayout.addLayout(self.neighborWidget)

        self.zoomExtentsButton = QtWidgets.QPushButton(self.centralwidget)
        self.zoomExtentsButton.setText("Zoom Extents")
        self.zoomExtentsButton.setFixedSize(self.width*BUTTON_WIDTH_RATIO, 50)
        self.zoomExtentsButton.clicked.connect(self.pressZoomExtents)
        self.chooseLayout = QtWidgets.QHBoxLayout()
        self.chooseLayout.addWidget(self.zoomExtentsButton)
        
        self.rightVL = QtWidgets.QVBoxLayout()
        self.rightVL.addLayout(self.chooseLayout)
        self.rightVL.addLayout(self.listLayout)

        self.nextTaskLayout = QtWidgets.QHBoxLayout()
        if (len(self.modelActors) < TRAINING_CELLS):
            self.toMarkTissues = list(range(0, len(self.presetSisters)))
            random.shuffle(self.toMarkTissues)
        else:
            self.toMarkTissues = interact.presetDataset(datasetNum, firstCell)
        self.nextTaskButton = QtWidgets.QPushButton(self.centralwidget)
        self.nextTaskButton.setText("Next Task")
        self.nextTaskButton.setFixedSize(self.width*BUTTON_WIDTH_RATIO, 50)
        self.nextTaskButton.clicked.connect(self.switch)
        self.nextTaskLayout.addWidget(self.nextTaskButton)
        # self.nextTaskButton.setEnabled(False)

        self.rightVL.addLayout(self.nextTaskLayout)
        self.rightVL.setAlignment(QtCore.Qt.AlignHCenter)
        self.rightVL.setSpacing(self.height*SPACING)

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
        self.csvFileName = "log/{}_ListSelection_{}_{}.csv".format(self.value, self.datasetNum, self.trialNumber)
        i = 1
        while os.path.exists(self.csvFileName):
            self.csvFileName = "log/{}_ListSelection_{}_{}({}).csv".format(self.value, self.datasetNum, self.trialNumber, i)
            i += 1
        self.logFile = log.logFile(self.csvFileName)
        self.myInteractorStyle.setLogFile(self.logFile)
        # self.logFile.recordOri(self.camera.GetPosition(), self.camera.GetFocalPoint(), self.camera.GetDistance(), self.toMark, len(self.neighborsInOrderOfCells[self.toMark]), fixedSurface.outsideOrInside(self.toMark), self.presetSisters[self.toMark], len(self.neighborsInOrderOfCells[self.presetSisters[self.toMark]]), fixedSurface.outsideOrInside(self.presetSisters[self.toMark]))

    def Initialize(self):
        self.renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()

        self.centerOfPolyData = vtk.vtkCenterOfMass()
        self.markedTissues = []
        self.lastSelectedItemIndex = None
        self.chosenNeighbor = None
        self.showedNeighborListOwner = None
        self.sister1 = None     # set these two as sisters
        self.sister2 = None
        self.correctness = 0

        self.resetActors()
        self.fillListWidget()
        self.addActorsToRender()
        self.calCenter()
        self.setupCamera()

        self.myInteractorStyle = interact.MyInteractorStyle()
        self.interactor.SetInteractorStyle(self.myInteractorStyle)
        self.continueMarking()
        if (not self.isTraining):
            def kayboardPressedActor(obj, ev):
                self.logFile.recordPress("Keyboard", obj.GetKeySym(), self.camera.GetPosition(), self.camera.GetFocalPoint(), self.camera.GetDistance())
            self.interactor.AddObserver('KeyPressEvent', kayboardPressedActor, -1.0)

            self.numberOfClicks = 0
            self.prePosition = [0,0]
            def leftClickedMainView(obj, ev):
                self.numberOfClicks += 1
                xypos = obj.GetEventPosition()
                xdist = xypos[0] - self.prePosition[0]
                ydist = xypos[1] - self.prePosition[1]
                moveDistance = int(math.sqrt(xdist*xdist + ydist*ydist))
                if (moveDistance > 0):
                    self.numberOfClicks = 1
                    self.logFile.recordClick("Click", "MainView", "-", self.camera.GetPosition(), self.camera.GetFocalPoint(), self.camera.GetDistance())
                if (self.numberOfClicks == 2):
                    self.logFile.recordClick("DoubleClick", "MainView", "-", self.camera.GetPosition(), self.camera.GetFocalPoint(), self.camera.GetDistance())
                    self.numberOfClicks = 0
            self.interactor.AddObserver('LeftButtonPressEvent', leftClickedMainView, -1.0)

            self.listScrollBar = self.tissueList.verticalScrollBar()
            self.preBarValue = 0
            self.listScrollBar.valueChanged.connect(lambda:self.update_scrollBar())

        self.neighborList.itemSelectionChanged.connect(self.neighborListClicked)
        self.setAsSisterButton.clicked.connect(self.clickSetSister)
        self.tissueList.itemSelectionChanged.connect(self.listPressed)

        self.interactor.Initialize()
        self.interactor.Start()

    def resetActors(self):
        for pro in self.originalProperty:
            pro.SetColor(1.0, 1.0, 1.0)
        for i in range(len(self.modelActors)):
            self.modelActors[i].GetProperty().DeepCopy(self.originalProperty[i])
            self.modelActors[i].SetPosition(0.0, 0.0, 0.0)
        
    def continueMarking(self):
        if (len(self.modelActors) < TRAINING_CELLS):
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
        pixmap = QtGui.QPixmap(16,16)
        pixmap.fill(QtGui.QColor(255, 153, 0))
        index = self.findIndexOfList(self.toMark)
        self.tissueList.item(index).setIcon(QtGui.QIcon(pixmap))

    def popup_button(self, i):
        if (i.text() == "OK"):
            self.switch()

    def fillListWidget(self):
        # Fill in the tissues' information(listWidgets)
        for item in self.data.tissues:
            index = self.data.tissues.index(item)
            if (index not in self.supportingCells):
                pixmap = QtGui.QPixmap(16,16)
                pixmap.fill(QtGui.QColor(255, 255, 255))
                listItem = QtWidgets.QListWidgetItem()
                listItem.setText(item)
                listItem.setIcon(QtGui.QIcon(pixmap))
                self.tissueList.addItem(listItem)
                del listItem

        for i in self.markedTissues:
            # Unable to click
            self.tissueList.item(i).setFlags(QtCore.Qt.NoItemFlags)
            self.tissueList.item(i).setForeground(QtGui.QColor("gray"))

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

        for actor in self.modelActors:
            self.renderer.AddActor(actor)

    def setupCamera(self):
        self.camera = vtk.vtkCamera()
        self.camera.SetViewUp(0.0, 0.0, 0.0)
        # set the focal point the center of the model
        # self.camera.SetFocalPoint(self.centerOfPolyData.GetCenter())
        self.zoomExtents()
        self.camera.SetPosition(interact.zoomoutCam(self.camera))
        self.renderer.SetActiveCamera(self.camera)
        
    def randomlyRotateCam(self):
        x = random.randrange(300)
        y = random.randrange(300)
        if (x >= y):
            self.camera.Azimuth(x)
        else:
            self.camera.Elevation(y)
            self.camera.OrthogonalizeViewUp()


    def update_scrollBar(self):
        value = self.listScrollBar.value()
        diff = value - self.preBarValue
        self.logFile.recordScroll("TissueList", diff, self.camera.GetPosition(), self.camera.GetFocalPoint(), self.camera.GetDistance())
        self.preBarValue = value

    #### Interaction

    def listPressed(self):
        if (self.tissueList.selectedItems() == []): return
        item = self.tissueList.selectedItems()[0]
        indexOfList = self.tissueList.row(item)
        indexOfOri = self.findIndexOfOri(indexOfList)
        if (not self.isTraining):
            self.logFile.updateSister(1, indexOfOri, len(self.neighborsInOrderOfCells[indexOfOri]), fixedSurface.outsideOrInside(indexOfOri))
            if (self.chosenNeighbor and not self.isTraining):
                self.logFile.updateSister(2, "-", "-", "-")
            self.logFile.recordClick("Click", "TissueList", indexOfOri, self.camera.GetPosition(), self.camera.GetFocalPoint(), self.camera.GetDistance())
        if (self.chosenNeighbor):
            self.modelActors[self.chosenNeighbor].SetPosition(0,0,0)
            # self.renderer.RemoveActor(self.neighborTextActor)
            for actor in self.renderer.GetActors():
                self.renderer.RemoveActor(actor)
            if (self.renderer.GetActors2D()):
                self.renderer.RemoveActor2D(self.neighborTextActor)
            for actor in self.modelActors:
                index = self.modelActors.index(actor)
                if (actor not in self.markedTissues):
                    self.renderer.AddActor(actor)
            self.chosenNeighbor = None
        self.zoomExtents()
        interact.highLightTissue(self.modelActors[indexOfList].GetProperty())
        if ((self.lastSelectedItemIndex != None) and  (self.lastSelectedItemIndex >= 0) and
            self.lastSelectedItemIndex not in self.markedTissues):
            self.modelActors[self.lastSelectedItemIndex].GetProperty().DeepCopy(self.originalProperty[self.lastSelectedItemIndex])
        self.lastSelectedItemIndex = indexOfList
        self.showedNeighborListOwner = indexOfList
        self.showNeighbors(indexOfOri)
        self.vtkWidget.GetRenderWindow().Render()


    def neighborListClicked(self):
        # if (self.chosenNeighbor != None):
        #     self.renderer.RemoveActor(self.neighborTextActor)
        if (self.neighborList.selectedItems() == []):   return
        item = self.neighborList.selectedItems()[0]
        for actor in self.renderer.GetActors():
            self.renderer.RemoveActor(actor)
            if (self.chosenNeighbor):
                self.modelActors[self.chosenNeighbor].SetPosition(0,0,0)
        self.chosenNeighbor = self.findIndexOfList(fixedSurface.findIndexWithName(self.data.tissues, item.text()))
        indexOfOri = self.findIndexOfOri(self.chosenNeighbor)
        if (not self.isTraining):
            self.logFile.updateSister(2, indexOfOri, self.neighbors.index(indexOfOri), fixedSurface.outsideOrInside(indexOfOri))
            self.logFile.recordClick("Click", "NeighborList", indexOfOri, self.camera.GetPosition(), self.camera.GetFocalPoint(), self.camera.GetDistance())
        self.renderer.AddActor(self.modelActors[self.showedNeighborListOwner])
        self.renderer.AddActor(self.modelActors[self.chosenNeighbor])
        self.modelActors[self.chosenNeighbor].SetPosition(self.keepDistanceBetweenTwo())
        self.camera.SetFocalPoint(self.modelActors[self.showedNeighborListOwner].GetCenter())
        # self.addNeighborText(self.chosenNeighbor, self.neighbors.index(self.findIndexOfOri(self.chosenNeighbor)))
        self.formNeighborText(self.chosenNeighbor, self.neighbors.index(indexOfOri))
        self.vtkWidget.GetRenderWindow().Render()


    def keepDistanceBetweenTwo(self):
        oriPos = self.modelActors[self.chosenNeighbor].GetCenter()
        targetPos = self.modelActors[self.showedNeighborListOwner].GetCenter()
        diff = []
        for i in range(3):
            diff.append(oriPos[i] - targetPos[i])
        coordinate = []
        for i in range(3):
            coordinate.append(DISTANCE * diff[i])
        return coordinate

    # Function to show the neighbors in the second column
    def showNeighbors(self, index):
        # clear the contents in the first column
        self.neighborList.clear()
        self.neighbors = self.neighborsInOrderOfCells[index].copy()
        # Show the neighbors in the next column
        for i in self.neighbors:
            listItem = QtWidgets.QListWidgetItem()
            listItem.setText(self.data.tissues[i])
            if (self.findIndexOfList(i) in self.markedTissues):
                listItem.setFlags(QtCore.Qt.NoItemFlags)
            self.neighborList.addItem(listItem)
        
        sister = self.presetSisters[index] #indexOfOri
        if (sister == None):
            self.assignedNumbers = interact.formTargetRandomNumber(len(self.neighbors), None)
        else:
            self.assignedNumbers = interact.formTargetRandomNumber(len(self.neighbors), self.neighbors.index(sister))

        self.neighborList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.neighborList.customContextMenuRequested.connect(self.generateMenu)
        self.neighborList.viewport().installEventFilter(self)

    def pressZoomExtents(self):
        if (len(self.modelActors) > TRAINING_CELLS):
            self.logFile.recordPress("Button", "AutoScale", self.camera.GetPosition(), self.camera.GetFocalPoint(), self.camera.GetDistance())
        self.zoomExtents()

    def zoomExtents(self):
        self.existingActorsIndex = self.calExistingActorsIndex()
        self.recalculateCenter(self.existingActorsIndex)
        self.camera.SetFocalPoint(self.centerOfPolyData.GetCenter())
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
        if (self.neighborTextActor not in self.renderer.GetActors()):
            self.renderer.AddActor(self.neighborTextActor)
        self.neighborTextActor.SetInput(str(self.assignedNumbers[numberIndex]))
        position = self.modelActors[index].GetCenter()
        pos1 = self.modelActors[self.showedNeighborListOwner].GetCenter()
        appendFilter = vtk.vtkAppendPolyData()
        appendFilter.AddInputData(self.modelActors[index].GetMapper().GetInput())
        appendFilter.Update()
        polyData = vtk.vtkPolyData()
        polyData = appendFilter.GetOutput()
        bounds = [0 for i in range(6)]
        polyData.GetBounds(bounds)
        indicateNumPos = interact.surfaceNearPoint(pos1, position, self.camera.GetPosition(), bounds)
        self.neighborTextActor.SetPosition(interact.moveIndicateNumber(indicateNumPos, self.modelActors[index].GetPosition()))
        self.renderer.AddActor2D(self.neighborTextActor)

    #########################
    ####### List Menu #######
    #########################

    # rightclick the tissue list
    # define the Menu shown by right clicked
    def generateMenu(self, pos):
        self.menu.exec_(self.neighborList.mapToGlobal(pos))

    def eventFilter(self, source, event):
        if (event.type() == QtCore.QEvent.MouseButtonPress and
            event.buttons() == QtCore.Qt.RightButton and
            source is self.neighborList.viewport()):
            item = self.neighborList.itemAt(event.pos())
            if (item is not None):
                self.chosenNeighbor = fixedSurface.findIndexWithName(self.data.tissues, item.text())
                self.menu = QtWidgets.QMenu(self)
                setAsSister = self.menu.addAction("Set As Sisters")
                setAsSister.triggered.connect(lambda:self.setSister())
        return super(MainWindow, self).eventFilter(source, event)

    def spaceSetSister(self):
        if (len(self.modelActors) > TRAINING_CELLS):
            self.logFile.recordPress("Keyboard", "Space", self.camera.GetPosition(), self.camera.GetFocalPoint(), self.camera.GetDistance())
        self.setSister()

    def clickSetSister(self):
        if (len(self.modelActors) > TRAINING_CELLS):
            self.logFile.recordPress("Button", "SetAsSister", self.camera.GetPosition(), self.camera.GetFocalPoint(), self.camera.GetDistance())
        self.setSister()

    # Set as sister
    def setSister(self):
        if (self.showedNeighborListOwner == None or self.chosenNeighbor == None):
            interact.alert_pop("sisters")
            return
        
        # index of list
        self.sister1 = self.showedNeighborListOwner
        self.sister2 = self.chosenNeighbor
        self.markedTissues.append(self.sister1)
        self.markedTissues.append(self.sister2)


        self.renderer.RemoveActor(self.modelActors[self.sister1])
        self.renderer.RemoveActor(self.modelActors[self.sister2])
        self.showedNeighborListOwner = None
        self.chosenNeighbor = None
        self.neighborList.clear()

        pixmap = QtGui.QPixmap(16,16)
        pixmap.fill(QtGui.QColor(0, 255, 0))
        if (self.findIndexOfOri(self.sister1) == self.toMark):    
            self.tissueList.item(self.sister1).setIcon(QtGui.QIcon(pixmap))
        if (self.findIndexOfOri(self.sister2) == self.toMark):
            self.tissueList.item(self.sister2).setIcon(QtGui.QIcon(pixmap))
        self.tissueList.item(self.sister1).setFlags(QtCore.Qt.NoItemFlags)
        self.tissueList.item(self.sister2).setFlags(QtCore.Qt.NoItemFlags)
        self.continueMarking()

        if (len(self.modelActors) > TRAINING_CELLS):
            self.wholeProgressLabel.setText("<h3>Task Progress: {} / {}</h3>".format(int(len(self.markedTissues)/2), TO_MARK))
            self.progressBar[self.value-1].setValue(int(len(self.markedTissues)/(TO_MARK * 2)*100))
            # if (self.presetSisters[self.findIndexOfOri(self.sister1)] == self.findIndexOfOri(self.sister2)):
            #     self.correctness += int(100 / TO_MARK)

        
        if (self.renderer.GetActors2D()):
            self.renderer.RemoveActor2D(self.neighborTextActor)
        for actor in self.modelActors:
            if (actor not in self.renderer.GetActors() and self.modelActors.index(actor) not in self.markedTissues):
                self.renderer.AddActor(actor)
        self.zoomExtents()
        
        if (len(self.markedTissues) == 40):
            self.nextTaskButton.setEnabled(True)
                    

    ### The index is different with the original one
    ### The list does not include supporting cells

    def findIndexOfOri(self, indexOfList):
        return self.actTissueList[indexOfList]

    def findIndexOfList(self, indexOfOri):
        return self.actTissueList.index(indexOfOri)  