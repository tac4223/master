# -*- coding: utf-8 -*-
"""
Created on Wed Apr 20 12:00:29 2016

@author: mick
"""

import numpy as np
import dicom as dcm
import os
import dynalog as dl

class filetools:

    @classmethod
    def get_plans(self,top):
        dicom_files = []
        for root,dirs,files in os.walk(str(top)):
            for f in files:
                if f[-3:] == "dcm":
                    filename = "\\".join([root,f])
                    dicom_files.append(dcm.read_file(filename))
        plans = [dl.plan(plan) for plan in dicom_files if plan.Modality == "RTPLAN"]
#        return list(np.array(plans)[np.argsort(
#            [p.header["patient_name"][0] for p in plans])])
        return plans

    @classmethod
    def get_banks(self,top):
        banks = []
        for root,dirs,files in os.walk(str(top)):
            for f in files:
                if f[-3:] == "dlg":
                    filename = "\\".join([root,f])
                    banks.append(dl.leafbank(filename,f[0]))
        uids = np.unique([p.header["plan_uid"] for p in banks])
        output = {}
        for uid in uids:
            output[uid] = list(np.array(banks)[np.where(np.array(
            [b.header["plan_uid"] for b in banks])==uid)[0]])
        return output


if __name__ == "__main__":
    dcm_list = filetools.get_plans("D:\Echte Dokumente\github\master")
