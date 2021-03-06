#!/usr/bin/python
import vtk
import sys
import os
import bisect
import copy

class Data:
    def __init__(self, points, triangles, trianglesInfo, tissues):
        self.points = points
        self.triangles = triangles
        self.trianglesInfo = trianglesInfo      # Include triangles inner && outer regions && number of triangles involved
        self.tissues = tissues      # Tissues000 is Exterior


def loadData(surfaceFilename):
    points = []
    triangles = []
    trianglesInfo = []
    tissues = []            # record the colors of the tissue
    # center = []

    try:
        with open(surfaceFilename) as sfp:

            tempProperty = ''

            for i, line in enumerate(sfp):
                line = line.strip()
                # print(flag)
                if (i >= 8 and i <= 229):
                    if (len(line.split()) == 2 and line.split()[1] =='{'):
                        tempProperty = line.split()[0]
                        tissues.append(tempProperty)
                        continue
                if (i >= 234 and i <= 529993):
                    points.append( (float(line.split()[0]), float(line.split()[1]), float(line.split()[2])) )

                if (i >= 529998):
                    if (line == ''):    continue
                    if ( line.split()[0] == 'InnerRegion'): 
                        tempInner = line.split()[1] 
                        continue
                    if ( line.split()[0] == 'OuterRegion'): 
                        tempOuter = line.split()[1]
                        continue
                    if (line.split()[0] == 'Triangles'):
                        ## inner tissue, outer tissue, amount of triangles
                        trianglesInfo.append((tempInner, tempOuter, int(line.split()[1])) )
                        continue
                    if ( len(line.split()) == 3):
                    ## Record all the triangles x y z 
                        triangles.append( (int(line.split()[0]), int(line.split()[1]), int(line.split()[2])) )

            # center = [(dataRange[0]+dataRange[1])/2, (dataRange[2]+dataRange[3])/2, (dataRange[4]+dataRange[5])/2]

    except IOError:
        return None            
            
    return Data(points, triangles, trianglesInfo, tissues)



def mkVTKIdList(it):
    vil = vtk.vtkIdList()
    for i in it:
        vil.InsertNextId(int(i)-1)
    return vil


def updateRange(dataRange, lastPoints):
    dataRange[0] = min(dataRange[0], lastPoints[0])
    dataRange[1] = max(dataRange[1], lastPoints[0])
    dataRange[2] = min(dataRange[2], lastPoints[1])
    dataRange[3] = max(dataRange[3], lastPoints[1])
    dataRange[4] = min(dataRange[4], lastPoints[2])
    dataRange[5] = max(dataRange[5], lastPoints[2])
    return dataRange

    

# Find the certain triangle belong to which tissues
def triangleFindTissue(triangleIndex, trianglesInfo, tissues):
    tissuesList = []
    for i in range(len(tissues)):
        if (tissues[i] == trianglesInfo[triangleIndex][0]):
            tissuesList.append(i)
    return tissuesList


# Find which triangles belong to a specific tissue
def tissueFindTriangle(tissueIndex, tissues, trianglesInfo):
    # return triangle index list
    triangleList = []
    for i in range(len(trianglesInfo)):
        if (trianglesInfo[i][0] == tissues[tissueIndex] or
            trianglesInfo[i][1] == tissues[tissueIndex]):
            triangleList.append(i)

    return triangleList


def findNeighbors(tissueIndex, tissues, trianglesInfo, supportingCells):
    sharedTriangles = [0] * len(trianglesInfo)
    neighborsInOrder = []
    for i in range(len(trianglesInfo)):
        if (trianglesInfo[i][0] == tissues[tissueIndex] and
            trianglesInfo[i][1] != 'Exterior'):
            index = findIndexWithName(tissues, trianglesInfo[i][1])
            if (index not in supportingCells):  sharedTriangles[index] += trianglesInfo[i][2]
        elif (trianglesInfo[i][1] == tissues[tissueIndex]):
            index = findIndexWithName(tissues, trianglesInfo[i][0])
            if (index not in supportingCells):  sharedTriangles[index] += trianglesInfo[i][2]
    sortedTriangles = sorted(sharedTriangles, reverse=True)
    for i in sortedTriangles:
        if (i == 0): break
        index = sharedTriangles.index(i)
        neighborsInOrder.append(index)
    return neighborsInOrder


def fillPresetSister(neighborsInOrderOfCells, supportingCells):
    marked = supportingCells.copy()
    sisterOfEveryCell = [None] * len(neighborsInOrderOfCells)
    while True:
        neighborsInOrderOfCells, marked, sisterOfEveryCell, change = roundAssign(neighborsInOrderOfCells, marked, sisterOfEveryCell)
        if (change == 0):   break
    return sisterOfEveryCell
    # print(sisterOfEveryCell)
    # print(removeWithOrder(list(range(len(neighborsInOrderOfCells))),marked ))


# two variables are index of Origin
def roundAssign(neighborsInOrderOfCells, marked, sisterOfEveryCell):
    for i in range(len(neighborsInOrderOfCells)):
        if ( i in marked):  continue
        # neighborsInOrderOfCells[i] = list(set(neighborsInOrderOfCells[i]) - set(marked))
        neighborsInOrderOfCells[i] = removeWithOrder(neighborsInOrderOfCells[i], marked)
    change = 0
    for i in range(len(neighborsInOrderOfCells)):
        if ( i in marked):  continue
        for j in neighborsInOrderOfCells[i]:
            if (neighborsInOrderOfCells[j][0] == i):
                sisterOfEveryCell[i] = j
                sisterOfEveryCell[j] = i
                marked.append(i)
                marked.append(j)
                change += 1
                break
    return neighborsInOrderOfCells, marked, sisterOfEveryCell, change


def removeWithOrder(mainList, removeList):
    for i in removeList:
        if (i in mainList):
            mainList.remove(i)
    return mainList



# find tissue's index by its name
def findIndexWithName(tissues, name):
    for i in range(len(tissues)):
        if (name == tissues[i]):
            return i
    return -1




####################### 
#### Unit Testing #####
#######################


def main():
    file = "/Users/jiayihong/Documents/Code/plantvis/data/trans_Col0_511.surf"

    data = loadData(file)
    supportingCells = [0, 1, 6, 12, 19, 32, 46, 64, 36, 124, 125]
    neighborsInOrderOfCells = []

    for i in range(len(data.tissues)):
        if (i in supportingCells):  neighborsInOrderOfCells.append([])
        else:   neighborsInOrderOfCells.append(findNeighbors(i, data.tissues, data.trianglesInfo, supportingCells))
    print(neighborsInOrderOfCells[51])
    # print(fillPresetSister(neighborsInOrderOfCells, supportingCells))


if __name__ == '__main__':
    main()

