# -*- coding: utf-8 -*-
"""
Created on Wed Apr 13 09:23:30 2016

@author: mick
"""

import numpy as np

class DynalogMismatchError(Exception):
    pass

class LeafbankMismatchError(DynalogMismatchError):
    def __init__(self,plan_uid,beam_number,key,msg="Must be identical"):
        self.uid = plan_uid
        self.beam = beam_number
        self.key = key
        self.msg = msg

    def __str__(self):
        return "\nPlan {0}\nBeam {2}\n"\
        "{1} mismatch between leafbanks A & B: {1} {3}"\
            .format(self.uid,self.key,self.beam,self.msg)

class BeamMismatchError(DynalogMismatchError):
    def __init__(self,plan_uid,beam_number,leafbank,key,msg="must be identical"):
        self.uid = plan_uid
        self.beam_number = beam_number
        self.leafbank = leafbank
        self.key = key
        self.msg = msg

    def __str__(self):
        return "\nPlan {0}\nBeam {2}\n"\
        "{1} mismatch between beam {2} and leafbank {3}: "\
        "{1} {4}".format(self.uid,self.key,self.beam_number,
        self.leafbank,self.msg)

class PlanMismatchError(DynalogMismatchError):
    def __init__(self,plan_uid,key,msg):
        self.plan_uid = plan_uid
        self.key = key
        self.msg = msg

    def __str__(self):
        return "\nPlan {0}\n{1} mismatch: {2}"\
        .format(self.plan_uid,self.key,self.msg)

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
                        raise LeafbankMismatchError(self.header["plan_uid"],
                            self.header["beam_number"],
                            key,"can't be identical for both banks")
                else:
                    if self.banks[0].header[key] != self.banks[1].header[key]:
                        raise LeafbankMismatchError(self.header["plan_uid"],
                                               self.header["beam_number"],key)

            for key in self.header.keys():
                    if self.header[key] != self.banks[0].header[key]:
                        raise BeamMismatchError(self.header["plan_uid"],
                                           self.header["beam_number"],
                                        self.banks[0].header["side"],key)
                    if self.header[key] != self.banks[1].header[key]:
                        raise BeamMismatchError(self.header["plan_uid"],
                                           self.header["beam_number"],
                                        self.banks[1].header["side"],key)
        except LeafbankMismatchError:
            self.verified = False
            raise
        except BeamMismatchError:
            self.verified = False
            raise
        else:
            self.verified = True

class plan:

    def __init__(self,plan_uid,number_of_beams,bank_pool):
        self.verified = False
        self.header = {"plan_uid":plan_uid,"number_of_beams":number_of_beams}
        self.beams = [None for k in range(self.header["number_of_beams"])]

        self.construct_beams(bank_pool)

    def construct_beams(self,bank_pool):
        if len(bank_pool) < 2*self.header["number_of_beams"]:
            raise PlanMismatchError(self.header["plan_uid"],"beam count",
                "plan needs {0} leafbanks for beam construction,"\
                " only {1} were passed."\
                .format(2*self.header["number_of_beams"],len(bank_pool)))
        else:
            beam_nums = [bank.header["beam_number"] for bank in bank_pool]
            sort_index = np.argsort(beam_nums)
            for num in range(self.header["number_of_beams"]):
                self.beams[num] = beam(self.header["plan_uid"],
                num+1,[bank_pool[sort_index[2*num]],
                       bank_pool[sort_index[2*num+1]]])

    def verify_plan(self):
        try:
            for num in range(self.header["number_of_beams"]):
                current_beam = self.beams[num]
                current_beam.verify_beam()
                if current_beam.header["beam_number"] != num+1:
                    raise PlanMismatchError(self.header["plan_uid"],
                    "beam assignment","beam at position {0} of beam list"\
                    " identifies as beam {1} instead of beam {2}."\
                    .format(num,current_beam.header["beam_number"],num+1))
        except PlanMismatchError:
            self.verified = False
            raise
        else:
            self.verified = True




if __name__ == "__main__":
    dyn1 = leafbank("A1.dlg")
    dyn2 = leafbank("B1.dlg")
    dyn3 = leafbank("A2.dlg")
    dyn4 = leafbank("B2.dlg")

#    beam1 = beam("derp",1,[dyn1,dyn2])
    plan1 = plan("derp",2,[dyn1,dyn2,dyn3,dyn4])