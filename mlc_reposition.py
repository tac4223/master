# -*- coding: utf-8 -*-
"""
Created on Fri Jul 01 08:30:25 2016

@author: mick
"""

import dicom as dcm
import time

class plan_manipulation:

    def __init__(self,filename):
        self.plan = dcm.read_file(filename)
        self.sides = {"x1":0,"x2":1}

    def change_mlc(self,beams,side,index,change):
        for beamnum in beams:
            beam = self.plan.BeamSequence[beamnum]
            for cp in beam.ControlPointSequence[1:]:
                for i in index:
                    cp.BeamLimitingDevicePositionSequence[0].LeafJawPositions[i+self.sides[side]*60] -= 0.1*change*((-1)**self.sides[side])
            for i in index:
                beam.ControlPointSequence[0].BeamLimitingDevicePositionSequence[2].LeafJawPositions[i+self.sides[side]*60] -= change*((-1)**self.sides[side])



    def fix_names(self):
        ltime = time.localtime()
        study_instance = self.plan.StudyInstanceUID.split(".")
        series_instance = self.plan.SeriesInstanceUID.split(".")
        instance_id = self.plan.SOPInstanceUID.split(".")

        self.plan.StudyInstanceUID = ".".join(study_instance[:-1])+\
            "."+"".join([str(t) for t in ltime[3:6]])
        self.plan.SeriesInstanceUID = ".".join(series_instance[:-1])+\
            "."+"".join([str(t) for t in ltime[:6]])
        self.plan.StudyID = "Id"+\
            "".join([str(t) for t in ltime[3:6]])
        self.plan.SOPInstanceUID = ".".join(instance_id[:-1])+\
            "."+"".join([str(t) for t in ltime[:6]])
        self.plan.ApprovalStatus = "UNAPPROVED"
        self.plan.RTPlanLabel = ("gap"+self.plan.RTPlanLabel)[:13]

    def export(self,filename):
        dcm.write_file(filename,self.plan)

if __name__ == "__main__":
    source = raw_input("Dateiname des zu ändernden Plans: ")
    beams = [num - 1 for num in input("Beamnummern (kommagetrennt) die geändert werden sollen: ")]
    side = raw_input("Seite (x1 oder x2): ")
    index = [num - 1 for num in input("Zu änderndes Leaf, kommagetrennt: ")]
    delta = input("Verschiebung in mm: ")
    target = raw_input("Ausgabe in: ")

    p = plan_manipulation(source)
    p.change_mlc(beams,side,index,delta)
    p.fix_names()
    p.export(target)