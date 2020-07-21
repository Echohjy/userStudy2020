#!/usr/bin/python
import vtk
import sys
import random
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox
import fixedSurface
import pickle
import time
import vtk
import csv

import log

MARKED_COLOR = (0.2,0.2,0.2)
MARKED_OPACITY = 0.1

class MyInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):

    def __init__(self, parent=None):
        self.AddObserver("LeftButtonPressEvent", self.left_button_press_event)
        self.AddObserver("LeftButtonReleaseEvent", self.left_button_release_event)
        self.AddObserver("MiddleButtonPressEvent", self.middle_button_press_event)
        self.AddObserver("MiddleButtonReleaseEvent", self.middle_button_release_event)
        self.AddObserver("MouseWheelForwardEvent", self.wheel_forward_event)
        self.AddObserver("MouseWheelBackwardEvent", self.wheel_backward_event)
        self.AddObserver("MouseMoveEvent",self.mouse_move_event)
        self.leftButtonDown = False
        self.middleButtonDown = False
        self.logFile = None

    def setLogFile(self, logFile):
        self.logFile = logFile

    def left_button_press_event(self, obj, event):
        self.leftButtonDown = True
        self.OnLeftButtonDown()

    def left_button_release_event(self, obj, event):
        self.leftButtonDown = False
        self.OnLeftButtonUp()

    def middle_button_press_event(self, obj, event):
        self.middleButtonDown = True
        self.OnMiddleButtonDown()

    def middle_button_release_event(self, obj, event):
        self.middleButtonDown = False
        self.OnMiddleButtonUp()

    def wheel_forward_event(self, obj, event):
        self.cam = self.ren.GetActiveCamera()
        clipping = self.cam.GetClippingRange()
        self.cam.SetClippingRange(clipping[0]*0.9, clipping[1])
        self.cam.Dolly(1.1)
        if (self.logFile != None):
            self.logFile.record3DInteraction("ZoomIn", self.cam.GetPosition(), self.cam.GetFocalPoint(), self.cam.GetDistance())
        self.renwin.Render()

    def wheel_backward_event(self, obj, event):
        self.cam = self.ren.GetActiveCamera()
        clipping = self.cam.GetClippingRange()
        self.cam.SetClippingRange(clipping[0], clipping[1]*1.1)
        self.cam.Dolly(0.9)
        if (self.logFile != None):
            self.logFile.record3DInteraction("ZoomOut", self.cam.GetPosition(), self.cam.GetFocalPoint(), self.cam.GetDistance())
        self.renwin.Render()

    def mouse_move_event(self, obj, event):
        self.renwin = self.GetInteractor().GetRenderWindow()
        self.ren = self.renwin.GetRenderers().GetFirstRenderer()
        self.cam = self.ren.GetActiveCamera()
        position = self.cam.GetPosition()

        lastXYpos = self.GetInteractor().GetLastEventPosition()
        lastX = lastXYpos[0]
        lastY = lastXYpos[1]
        xypos = self.GetInteractor().GetEventPosition()
        x = xypos[0]
        y = xypos[1]
        center = self.renwin.GetSize()
        centerX = center[0]/2.0
        centerY = center[1]/2.0

        if (self.leftButtonDown):
            if (abs(x-lastX) >= abs(y-lastY)):
                self.cam.Azimuth((lastX-x)/8)
            else:
                self.cam.Elevation((lastY-y)/8)
                self.cam.OrthogonalizeViewUp()
            if (self.logFile != None):
                self.logFile.record3DInteraction("Rotate", self.cam.GetPosition(), self.cam.GetFocalPoint(), self.cam.GetDistance())
            self.renwin.Render()

        if (self.middleButtonDown):
            FPoint = self.cam.GetFocalPoint()
            PPoint = self.cam.GetPosition()
            self.ren.SetWorldPoint(FPoint[0], FPoint[1], FPoint[2], 1.0)
            self.ren.WorldToDisplay()
            DPoint = self.ren.GetDisplayPoint()
            focalDepth = DPoint[2]
            APoint0 = centerX+(x-lastX)
            APoint1 = centerY+(y-lastY)

            self.ren.SetDisplayPoint(APoint0, APoint1, focalDepth)
            self.ren.DisplayToWorld()
            RPoint = self.ren.GetWorldPoint()
            RPoint0 = RPoint[0]
            RPoint1 = RPoint[1]
            RPoint2 = RPoint[2]
            RPoint3 = RPoint[3]

            if RPoint3 != 0.0:
                RPoint0 = RPoint0/RPoint3
                RPoint1 = RPoint1/RPoint3
                RPoint2 = RPoint2/RPoint3

            self.cam.SetFocalPoint( (FPoint[0]-RPoint0)/2.0 + FPoint[0],
                                (FPoint[1]-RPoint1)/2.0 + FPoint[1],
                                (FPoint[2]-RPoint2)/2.0 + FPoint[2])
            self.cam.SetPosition( (FPoint[0]-RPoint0)/2.0 + PPoint[0],
                                (FPoint[1]-RPoint1)/2.0 + PPoint[1],
                                (FPoint[2]-RPoint2)/2.0 + PPoint[2])
            # self.cam.SetPosition(position[0]+lastX-x, position[1]+lastY-y, position[2])
            if (self.logFile != None):
                self.logFile.record3DInteraction("Pan", self.cam.GetPosition(), self.cam.GetFocalPoint(), self.cam.GetDistance())
            self.renwin.Render()


# Design the highlighted items' properties
def highLightTissue(getProperty):
    getProperty.SetColor(0.8,0,0)
    getProperty.SetOpacity(1.0)
    getProperty.SetDiffuse(1.0)
    getProperty.SetSpecular(0.0)

def highLightNeighbor(getProperty):
    getProperty.SetColor(0.8,0.8,0)
    getProperty.SetOpacity(1.0)
    getProperty.SetDiffuse(1.0)
    getProperty.SetSpecular(0.0)

def greyTissue(getProperty):
    getProperty.SetColor(MARKED_COLOR)
    getProperty.SetOpacity(MARKED_OPACITY)


def formTargetRandomNumber(length, targetSisterIndex):
    if (targetSisterIndex == None):
        assignedNumbers = [0] * length
        return assignedNumbers
    assignedNumbers = random.sample(range(1, 90), len(range(length)))
    maxValue = 0
    for i in assignedNumbers:
        if (i > maxValue):
            maxValue = i
    assignedNumbers[targetSisterIndex] = maxValue + random.randrange(10) + 1
    return assignedNumbers

def randomPoint(pos1, pos2, model):
    if (pos1[0] <= pos2[0]):    v0 = -1
    else:   v0 = 1
    if (pos1[1] <= pos2[1]):    v1 = -1
    else:   v1 = 1
    if (pos1[2] <= pos2[2]):    v2 = -1
    else:   v2 = 1

    if (model == "training"):
        pos = [pos1[0] + v0*random.uniform(0,1)*5*(pos2[0]-pos1[0]), pos1[1] + v1*random.uniform(0,1)*5*(pos2[1]-pos1[1]), pos1[2] + v2*random.uniform(0,1)*5*(pos2[2]-pos1[2])]
    else:
        pos = [pos1[0] + v0*random.uniform(0,1)*2*(pos2[0]-pos1[0]), pos1[1] + v1*random.uniform(0,1)*2*(pos2[1]-pos1[1]), pos1[2] + v2*random.uniform(0,1)*2*(pos2[2]-pos1[2])]
    return pos

def moveIndicateNumber(originalPos, actorPos):
    coordinate = []
    for i in range(3):
        coordinate.append(originalPos[i]+actorPos[i])
    return coordinate

# pos1: target cell center; pos2: neighbor center; pos3: camera position
def surfaceNearPoint(pos1, pos2, pos3, bounds):
    pos = [(pos1[0]+pos2[0])/2, (pos1[1]+pos2[1])/2, (pos1[2]+pos2[2])/2]
    xMin = bounds[0]
    xMax = bounds[1]
    yMin = bounds[2]
    yMax = bounds[3]
    zMin = bounds[4]
    zMax = bounds[5]

    x = abs(pos3[0] - pos[0])
    y = abs(pos3[1] - pos[1])
    z = abs(pos3[2] - pos[2])

    x1 = abs(pos1[0] - pos2[0])
    y1 = abs(pos1[1] - pos2[1])
    z1 = abs(pos1[2] - pos2[2])

    if (x>=y and x>=z):
        if (pos3[0] > pos[0]):
            if (x1>=y1 and x1>=z1 and pos2[0] > pos1[0]):
                position = (xMin, yMax, zMax)
            else:
                position = (xMin, (yMax+yMin)/2, (zMax+zMin)/2)
        else:      
            if (x1>=y1 and x1>=z1 and pos2[0] < pos1[0]):
                position = (xMax, yMax, zMax)
            else:                
                position = (xMax, (yMax+yMin)/2, (zMax+zMin)/2)
    if (y>=x and y>=z):
        if (pos3[1] > pos[1]):
            if (y1>=x1 and y1>=z1 and pos2[1] > pos1[1]):
                position = (xMax, yMin, zMax)
            else:     
                position = ((xMax+xMin)/2, yMin, (zMax+zMin)/2)
        else:
            if (y1>=x1 and y1>=z1 and pos2[1] < pos1[1]):
                position = (xMax, yMax, zMax)
            else:                      
                position = ((xMax+xMin)/2, yMax, (zMax+zMin)/2)
    if (z>=y and z>=x):
        if (pos3[2] > pos[2]):
            if (z1>=y1 and z1>=x1 and pos2[2] > pos1[2]):
                position = (xMax, yMax, zMin)
            else:     
                position = ((xMax+xMin)/2, (yMax+yMin)/2, zMin)
        else:
            if (z1>=y1 and z1>=x1 and pos2[2] < pos1[2]):
                position = (xMax, yMax, zMax)
            else:                      
                position = ((xMax+xMin)/2, (yMax+yMin)/2, zMax)
    
    return position
    
    # if (x>=y and x>=z):
    #     if (pos2[0] > pos1[0]):     return (xMax, (yMax+yMin)/2, (zMax+zMin)/2)
    #     else:                       return (xMin, (yMax+yMin)/2, (zMax+zMin)/2)
    # if (y>=x and y>=z):
    #     if (pos2[1] > pos1[1]):     return ((xMax+xMin)/2, yMax, (zMax+zMin)/2)
    #     else:                       return ((xMax+xMin)/2, yMin, (zMax+zMin)/2)
    # if (z>=y and z>=x):
    #     if (pos2[2] > pos1[2]):     return ((xMax+xMin)/2, (yMax+yMin)/2, zMax)
    #     else:                       return ((xMax+xMin)/2, (yMax+yMin)/2, zMin)


def zoomoutCam(camera):
    PPoint = camera.GetPosition()
    Fpoint = camera.GetFocalPoint()
    return ((PPoint[0] - Fpoint[0])/2.0 + PPoint[0],
            (PPoint[1] - Fpoint[1])/2.0 + PPoint[1],
            (PPoint[2] - Fpoint[2])/2.0 + PPoint[2])


def alert_pop(text):
    msg = QMessageBox()
    msg.setWindowTitle("Alert!")
    if (text == "sisters"):
        msg.setText("Please choose two cells!")
        msg.setIcon(QMessageBox.Critical)
        msg.setStandardButtons(QMessageBox.Ok)
    msg.exec_()     


def orderNeighbors(neighborsInOrderOfCells):
    orderNeighbors = []
    for neighborsOri in neighborsInOrderOfCells:
        neighbors = neighborsOri.copy()
        neighbors.sort()
        orderNeighbors.append(neighbors)
    return orderNeighbors

def presetDataset(number, start):
    dataset1_inside = [141, 178, 26, 171, 134, 201, 97, 209, 131, 90]
    dataset1_outside = [178, 141, 171, 26, 201, 134, 209, 97, 90, 131]

    dataset2_inside = [101, 116, 179, 11, 109, 204, 167, 186, 92, 33]
    dataset2_outside = [116, 101, 11, 179, 204, 109, 186, 167, 33, 92]

    dataset3_inside = [136, 100, 132, 69, 34, 207, 181, 18, 142, 20]
    dataset3_outside = [100, 136, 69, 132, 207, 34, 18, 181, 20, 142]
    
    if (number == 1 and start == 0):
        return dataset1_inside
    elif (number == 1 and start == 1):
        return dataset1_outside
    elif (number == 2 and start == 0):
        return dataset2_inside
    elif (number == 2 and start == 1):
        return dataset2_outside
    elif (number == 3 and start == 0):
        return dataset3_inside
    elif (number == 3 and start == 1):
        return dataset3_outside



def initialize(pickleFile):
    with open(pickleFile, 'rb') as input:
        data = pickle.load(input)
        startPoint = pickle.load(input)
        supportingCells = pickle.load(input)
        neighborsInOrderOfCells = pickle.load(input)
        presetSisters = pickle.load(input)
        actTissueList = list(set(list(range(0,len(neighborsInOrderOfCells)))) - set(supportingCells))
    
    if (len(neighborsInOrderOfCells) > 100):
        presetSisters[209] = 207
        presetSisters[207] = 209
        presetSisters[178] = 148
        presetSisters[148] = 178

    points = vtk.vtkPoints()
    for i in range(len(data.points)):
        points.InsertPoint(i, data.points[i])
    tissuesTriangles = []
    originalProperty = []
    modelActors = []
    for i in range(len(data.tissues)):
        if (i not in supportingCells):
            
            triangles = fixedSurface.tissueFindTriangle(i, data.tissues, data.trianglesInfo)
            tissuesTriangles.append(triangles)

            model = vtk.vtkPolyData()
            polys = vtk.vtkCellArray()
            model.SetPoints(points)

            for j in tissuesTriangles[-1]:
                for k in range(startPoint[j], startPoint[j]+ data.trianglesInfo[j][2]):
                    polys.InsertNextCell(fixedSurface.mkVTKIdList(data.triangles[k]))
                    model.SetPolys(polys)
            del polys
            # self.appendFilter.AddInputData(model)

            modelMapper = vtk.vtkPolyDataMapper()
            modelMapper.SetInputData(model)
            del model

            modelActor = vtk.vtkActor()
            modelActor.SetMapper(modelMapper)
            del modelMapper

            modelActor.GetProperty().SetDiffuseColor(1.0, 1.0, 1.0)
            modelActor.GetProperty().SetOpacity(1.0)
            temp = vtk.vtkProperty()
            temp.DeepCopy(modelActor.GetProperty())
            originalProperty.append(temp)
            del temp

            modelActors.append(modelActor)
            del modelActor

    return data, startPoint, supportingCells, neighborsInOrderOfCells, presetSisters, actTissueList, points, tissuesTriangles, originalProperty, modelActors



def dataToAnalyze(pickleFile):
    with open(pickleFile, 'rb') as input:
        data = pickle.load(input)
        startPoint = pickle.load(input)
        supportingCells = pickle.load(input)
        neighborsInOrderOfCells = pickle.load(input)
        presetSisters = pickle.load(input)
        presetSisters[209] = 207
        presetSisters[207] = 209
        presetSisters[178] = 148
        presetSisters[148] = 178

    return neighborsInOrderOfCells, presetSisters