# -*- coding: utf-8 -*-
"""
Created on Tue Apr 19 09:51:55 2016

@author: mick
"""

import dynalog as dl
import dicom
import numpy as np

a1 = dl.leafbank("A1.dlg")
b1 = dl.leafbank("B1.dlg")
a2 = dl.leafbank("A2.dlg")
b2 = dl.leafbank("B2.dlg")

pr = dl.plan("derp",2,[a1,b1,a2,b2])

logdose = pr.beams[0].banks[0].dose_fraction
pp = dicom.read_file("plan.dcm")
dicomdose = np.array([pp.BeamSequence[0].ControlPointSequence[_].CumulativeMetersetWeight for _ in range(178)])*25000

reco_dose = []
for dose in dicomdose:
    index = np.where(logdose < dose)[0]
    if len(index) > 0:
        reco_dose.append(logdose[index[-1]+1])