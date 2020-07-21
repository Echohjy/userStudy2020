#!/usr/bin/python
import vtk
import sys
import os
import bisect
import copy
import random

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
                if (i >= 8 and i <= 849):
                    if (len(line.split()) == 2 and line.split()[1] =='{'):
                        tempProperty = line.split()[0]
                        tissues.append(tempProperty)
                        continue
                if (i >= 854 and i <= 650021):
                    points.append( (float(line.split()[0]), float(line.split()[1]), float(line.split()[2])) )

                if (i >= 650026):
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


def findOutsideCells(tissues, trianglesInfo, supportingCells):
    outsideCells = []
    for i in range(len(trianglesInfo)):
        if (trianglesInfo[i][1] == 'Exterior'):
            outsideCells.append(findIndexWithName(tissues, trianglesInfo[i][0]))
    return list(set(outsideCells) - set(supportingCells))


def outsideOrInside(number):
    outsideCells = [2, 3, 4, 5, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 20, 21, 23, 24, 25, 27, 28, 29, 31, 33, 37, 38, 39, 42, 47, 52, 55, 57, 58, 59, 60, 67, 68, 69, 72, 74, 75, 76, 79, 80, 88, 90, 94, 95, 99, 100, 102, 104, 105, 111, 112, 114, 115, 116, 118, 119, 123, 126, 128, 129, 133, 135, 138, 139, 146, 147, 148, 149, 150, 156, 161, 162, 163, 165, 166, 169, 170, 171, 172, 173, 175, 176, 177, 178, 182, 183, 184, 185, 186, 188, 189, 190, 191, 192, 193, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209]
    if (number in outsideCells):
        return "outside"
    return "inside"


############################
### Totally Random

def findTargetCells(neighborsInOrderOfCells, insideCells, outsideCells, supportingCells, presetSisters):
    # random.shuffle(insideCells)
    # random.shuffle(outsideCells)
    # toLoop = insideCells.copy()
    # toLoop.extend(outsideCells)
    toLoop = outsideCells.copy()
    # random.shuffle(toLoop)

    # toLoop = calculateLayers(neighborsInOrderOfCells, outsideCells, supportingCells)
    # toLoop = calNeighborsNum(neighborsInOrderOfCells)

    noSupportingCells = list(set(list(range(0,len(neighborsInOrderOfCells)))) - set(supportingCells))
    targetCells = []
    allNeighbors = []
    temPresetSisters = []
    # while True:
    #     firstCell = random.randrange(len(noSupportingCells))
    #     # firstCell = toLoop[0]
    #     if (presetSisters[noSupportingCells[firstCell]] != None):
    #         targetCells.append(noSupportingCells[firstCell])
    #         break
    # allNeighbors.extend(neighborsInOrderOfCells[noSupportingCells[firstCell]])
    # temPresetSisters.append(presetSisters[noSupportingCells[firstCell]])

    shouldnot = [134, 141, 131, 26, 97, 209, 201, 178, 171, 90, 179, 109, 101, 167, 92, 204, 186, 116, 33, 11]
    targetCells = [34, 142, 181, 136, 132]
    for i in targetCells:
        allNeighbors.extend(neighborsInOrderOfCells[i])

    # targetCells.append(toLoop[5])
    # allNeighbors.extend(neighborsInOrderOfCells[toLoop[5]])
    while (True):
        for i in toLoop:
            if (i in allNeighbors or i in targetCells or presetSisters[i] == None or i in shouldnot): continue
            if (ifShareNeighbors(i, neighborsInOrderOfCells, allNeighbors) == False):
            # if (ifNeighborsInPresetSister(i, neighborsInOrderOfCells, temPresetSisters) == False):
                targetCells.append(i)
                allNeighbors.extend(neighborsInOrderOfCells[i])
                # temPresetSisters.append(presetSisters[i])
                break
        if (i == toLoop[-1]):
            break
    print(targetCells)
    print(len(targetCells))
    print(list(set(targetCells).intersection(outsideCells)))
    print(len(list(set(targetCells).intersection(outsideCells))))
    return targetCells

def ifShareNeighbors(tissue, neighborsInOrderOfCells, allNeighbors):
    if (len(list(set(neighborsInOrderOfCells[tissue]).intersection(allNeighbors))) == 0):
        return False
    return True

def ifNeighborsInPresetSister(tissue, neighborsInOrderOfCells, presetSisters):
    for neighbor in neighborsInOrderOfCells[tissue]:
        if (neighbor in presetSisters): 
            return True
    return False


#######################
### Get layers

def calculateLayers(neighborsInOrderOfCells, outsideCells, supportingCells):
    layers = [0] * len(neighborsInOrderOfCells)
    toLoop = []
    for i in outsideCells:
        layers[i] = 1
        toLoop.append(i)
    roundNum = 1
    while (layers.count(0) > len(supportingCells)):
        for i in range(len(neighborsInOrderOfCells)):
            if (layers[i] != 0):    continue
            if (neighborsInOrderOfCells[i] == []):  continue
            for j in neighborsInOrderOfCells[i]:
                if (layers[j] == roundNum):
                    layers[i] = roundNum + 1
                    toLoop.append(i)
                    break
        roundNum += 1
        # print(len(toLoop))
    toLoop.reverse()
    return toLoop


##########################
### From Neighbors

def calNeighborsNum(neighborsInOrderOfCells):
    toLoop = []
    neighborsNum = []
    maxNum = 0
    for i in range(len(neighborsInOrderOfCells)):
        num = len(neighborsInOrderOfCells[i])
        if (num > maxNum):
            maxNum = num
        neighborsNum.append(num)
    while (maxNum > 0):
        for i in range(len(neighborsNum)):
            if (neighborsNum[i] == maxNum):
                toLoop.append(i)
        maxNum -= 1
    toLoop.reverse()
    return toLoop




####################### 
#### Unit Testing #####
#######################


def main():
    file = "/Users/jiayihong/Documents/Code/plant_vis/data/trans_Col0_511.surf"

    data = loadData(file)
    supportingCells = [0, 1, 6, 12, 19, 32, 46, 64, 36, 124, 125]
    neighborsInOrderOfCells = []

    for i in range(len(data.tissues)):
        if (i in supportingCells):  neighborsInOrderOfCells.append([])
        else:   neighborsInOrderOfCells.append(findNeighbors(i, data.tissues, data.trianglesInfo, supportingCells))
    outsideCells = findOutsideCells(data.tissues, data.trianglesInfo, supportingCells)
    print(outsideCells)
    insideCells = list(set(list(range(0,len(neighborsInOrderOfCells)))) - set(outsideCells) - set(supportingCells))
    # calNeighborsNum(neighborsInOrderOfCells)
    presetSisters = fillPresetSister(copy.deepcopy(neighborsInOrderOfCells), supportingCells)
    # print(calculateLayers(neighborsInOrderOfCells, outsideCells, supportingCells))
    # print(outsideCells)
    # print(len(insideCells))
    # dataset = [134, 141, 131, 26, 97, 209, 201, 178, 171, 90, 179, 109, 101, 167, 131, 4, 20, 31, 129, 184, 159, 78, 85, 97, 141, 2, 60, 147, 192, 198]
    # checkPresetSisterNone(presetSisters, dataset)
    # targetCells = findTargetCells(neighborsInOrderOfCells, insideCells, outsideCells, supportingCells, presetSisters)
                
def checkPresetSisterNone(presetSisters, dataset):
    for i in dataset:
        if (presetSisters[i] == None):
            print(i)



if __name__ == '__main__':
    main()

