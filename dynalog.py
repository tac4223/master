# -*- coding: utf-8 -*-
"""
Created on Wed Apr 13 09:23:30 2016

@author: mick
"""

import numpy as np

class leafbank:

    def __init__(self,filename):
        self.header = {}
        self.header["filename"] = filename
        self.header["side"] = filename[0]

        self.read_data(filename)
        self.build_header(filename)
        self.build_beam()
        self.build_gantry()
        self.build_mlc()
    def read_data(self,filename):
        with open(filename,"r") as data:
            raw = [line.strip().split(",") for line in data.readlines()]
            self.raw_header = raw[:6]
            self.raw_data = np.array(raw[6:]).astype(float)

    def build_header(self,filename):
        self.header["version"] = self.raw_header[0][0]
        self.header["patient_name"] = self.raw_header[1][:-1]
        self.header["patient_id"] = self.raw_header[1][-1]
        self.header["plan_uid"] = self.raw_header[2][0]
        self.header["beam_number"] = int(self.raw_header[2][1])
        self.header["tolerance"] = int(self.raw_header[3][0])
        self.header["leaf_count"] = int(self.raw_header[4][0])
        self.header["coord_system"] = int(self.raw_header[5][0])

    def build_gantry(self):
        self.gantry_angle = self.raw_data[:,6]
        self.previous_segment = self.raw_data[:,1]
        self.collimator_rotation = self.raw_data[:,7]
        self.y1 = self.raw_data[:,8]
        self.y1 = self.raw_data[:,9]
        self.x1 = self.raw_data[:,10]
        self.x2 = self.raw_data[:,11]

    def build_beam(self):
        self.dose_fraction = self.raw_data[:,0]
        self.beam_holdoff = self.raw_data[:,2]
        self.beam_on = self.raw_data[:,3]

    def build_mlc(self):
        self.carriage_expected = self.raw_data[:,12]
        self.carriage_actual = self.raw_data[:,13]
        self.leafs_expected = self.raw_data[:,14::4]
        self.leafs_actual = self.raw_data[:,15::4]

class DynalogMismatch(Exception):
    pass

class LeafbankMismatch(DynalogMismatch):
    def __init__(self,beam_number,key,msg="Must be identical"):
        self.beam = beam_number
        self.key = key
        self.msg = msg

class BeamMismatch(DynalogMismatch):
    def __init__(self,beam_number,leafbank,key,msg="must be identical"):
        self.beam_number = beam_number
        self.leafbank = leafbank
        self.key = key
        self.msg = msg

class beam:

    def __init__(self,plan_uid,beam_number,banks):
        self.verified = False
        self.header = {"beam_number":beam_number, "plan_uid":plan_uid}
        self.banks = banks

        self.verify_beam()

    def verify_beam(self):
        try:
            for key in self.banks[0].header.keys():
                if key in ["filename","side"]:
                    if self.banks[0].header[key] == self.banks[1].header[key]:
                        raise LeafbankMismatch(self.header["beam_number"],
                        key,"can't be identical for both banks")
                else:
                    if self.banks[0].header[key] != self.banks[1].header[key]:
                        raise LeafbankMismatch(self.header["beam_number"],key)

            for key in self.header.keys():
                    if self.header[key] != self.banks[0].header[key]:
                        raise BeamMismatch(self.header["beam_number"],
                                        self.banks[0].header["side"],key)
                    if self.header[key] != self.banks[1].header[key]:
                        raise BeamMismatch(self.header["beam_number"],
                                        self.banks[1].header["side"],key)
        except LeafbankMismatch as lbm:
            print("\nBeam {1}\n{0} mismatch between leafbanks A & B: {0} {2}"\
            .format(lbm.key,lbm.beam,lbm.msg))
            raise
        except BeamMismatch as bm:
            print("\nBeam {1}\n{0} mismatch between beam {1} and leafbank {2}: "\
            "{0} {3}".format(bm.key,bm.beam_number,bm.leafbank,bm.msg))
            raise
        else:
            self.verified = True

class plan:

    def __init__(self,plan_uid,number_of_beams,bank_pool):
        self.verified = False
        self.header = {"plan_uid":plan_uid,"number_of_beams":number_of_beams}
        self.beams = [None for k in range(self.header["number_of_beams"])]

    def construct_beams(self,bank_pool):
        if len(bank_pool) < 2*self.header["number_of_beams"]:
#            raise PlanMismatch




if __name__ == "__main__":
    dyn1 = leafbank("A20151125181338_Test40.dlg")
    dyn2 = leafbank("A20151125181338_Test40.dlg")

    beam1 = beam("derp",1,[dyn1,dyn2])