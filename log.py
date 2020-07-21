#!/usr/bin/python
import csv
import time
import fixedSurface

class logFile:
    def __init__(self, fileName):
        self.fileName = fileName
        self.startTime = time.time()
        self.setupInteractionHeader()
        
        self.sister1 = "-"
        self.sister1_num = "-"
        self.sister1_pos = "-"
        self.sister2 = "-"
        self.sister2_num = "-"
        self.sister2_pos = "-"

    def setupInteractionHeader(self):
        with open(self.fileName, 'w', newline = '') as file:
                writer = csv.writer(file)
                writer.writerow(["Time", "Motion", "Target", "Details", "Cam_Position", "Cam_FocalPoint", "Cam_Distance", "Sister1", "inside/outside_1", "Number_of_neighbors", "Sister2", "inside/outside_2", "Sister2_in_Neighborhood"])

    def record3DInteraction(self, motion, cam_pos, cam_focal, cam_distance):
        with open(self.fileName, 'a+') as file:
            writer = csv.writer(file)
            writer.writerow(['%.6f'%(time.time()-self.startTime), motion, "MainView", "-", cam_pos, cam_focal, cam_distance, self.sister1, self.sister1_pos, self.sister1_num, self.sister2, self.sister2_pos, self.sister2_num])


    # details: increase 10, decrease -10
    def recordScroll(self, scrollBarName, details, cam_pos, cam_focal, cam_distance):
        with open(self.fileName, 'a+') as file:
            writer = csv.writer(file)
            writer.writerow(['%.6f'%(time.time()-self.startTime), "Scroll", scrollBarName, details, cam_pos, cam_focal, cam_distance, self.sister1, self.sister1_pos, self.sister1_num, self.sister2, self.sister2_pos, self.sister2_num])


    # press keyboard or button
    def recordPress(self, target, name, cam_pos, cam_focal, cam_distance):
        with open(self.fileName, 'a+') as file:
            writer = csv.writer(file)
            writer.writerow(['%.6f'%(time.time()-self.startTime), "Press", target, name, cam_pos, cam_focal, cam_distance, self.sister1, self.sister1_pos, self.sister1_num, self.sister2, self.sister2_pos, self.sister2_num])


    # sister should be the cell original number; pos = inside/outside
    def updateSister(self, number, sister, neighborNum, pos):
        if (number == 1):
            self.sister1 = sister
            self.sister1_num = neighborNum
            self.sister1_pos = pos
        else:
            self.sister2 = sister
            self.sister2_num = neighborNum # it is the order in the list
            self.sister2_pos = pos

    # clickName == "Click" or "Double Click"
    # cell is indexOfOri
    def recordClick(self, clickName, target, cell, cam_pos, cam_focal, cam_distance):
        with open(self.fileName, 'a+') as file:
            writer = csv.writer(file)
            writer.writerow(['%.6f'%(time.time()-self.startTime), clickName, target, cell, cam_pos, cam_focal, cam_distance, self.sister1, self.sister1_pos, self.sister1_num, self.sister2, self.sister2_pos, self.sister2_num])

        
    def recordOri(self, cam_pos, cam_focal, cam_distance, sister1, sister1_pos, sister1_num, sister2, sister2_pos, sister2_num):
        with open(self.fileName, 'a+') as file:
            writer = csv.writer(file)
            writer.writerow(['%.6f'%(time.time()-self.startTime), "-", "-", "-", cam_pos, cam_focal, cam_distance, sister1, sister1_pos, sister1_num, sister2, sister2_pos, sister2_num])