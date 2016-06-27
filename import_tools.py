# -*- coding: utf-8 -*-
"""
Created on Thu Jun 09 11:47:16 2016

@author: mick
"""
import os
import numpy as np
import plan_logic as pl
import dicom as dcm

class filetools:

    @classmethod
    def get_plans(self,top):
        dicom_files = []
        for root,dirs,files in os.walk(str(top)):
            for f in files:
                if f[-3:] == "dcm":
                    filename = "\\".join([root,f])
                    dicom_files.append(dcm.read_file(filename))
        plans = [pl.plan(plan) for plan in dicom_files if plan.Modality == "RTPLAN"]
        return [plan for plan in plans if (plan.arcs > 0) == True]

    @classmethod
    def get_banks(self,top):
        banks = []
        for root,dirs,files in os.walk(str(top)):
            for f in files:
                if f[-3:] == "dlg":
                    filename = "\\".join([root,f])
                    banks.append(leafbank_dynalog(filename,f[0]))
        uids = np.unique([p.header["plan_uid"] for p in banks])
        output = {}
        for uid in uids:
            output[uid] = list(np.array(banks)[np.where(np.array(
            [b.header["plan_uid"] for b in banks])==uid)[0]])
        return output


class leafbank_dynalog:

    def __init__(self,filename,side=None):
        """
        Parameter
        -----------------------------------------------------------------------
        filename : str
            Dateiname der zu importierenden DynaLog-Datei. Erstes Zeichen des
            Dateinamens wird als Bezeichnung der Leafbank (in der Regel A oder B)
            verwendet.

        Funktionen
        -----------------------------------------------------------------------
        read_data :
            Liest Textdokument ein, trennt Header ab, ruft weitere Funktionen
            auf

        build_header :
            Überträgt die Informationen aus dem Header in Objekteigenschaften.

        build_beam :
            Importiert Dosis und Einschaltzeiten.

        build_gantry :
            Importiert Gantrywinkel etc.

        build_mlc :
            Importiert die Leafpositionen.

        Instanzvariablen
        -----------------------------------------------------------------------
        header : dict
            Enthält die Schlüsselwörter und zugehörigen Werte der Headerzeilen im
            DynaLog File

        gantry_angle : ndarray
           nthält die Gantry-Winkel des Logfiles, aufgenommen alle ~50 ms.

        previous_segment : ndarray
            Enthält den Wert der "Previous Segment Number" Spalte, in der Hoffnung
            dass sich damit die Kontrollpunkte rekonstruieren lassen.

        collimator_rotation : ndarray
           thält die Kollimatorrotation im Zeitverlauf.

        y1,y2 : ndarray
           osition der y-Blenden.

        x1, x2 : ndarray
            Position der x-Blenden.

        dose_fraction : ndarray
            Kumulative, applizierte Dosis, von 0 bis 25000.

        beam_holdoff : ndarray
            In Situationen in denen der Beschleuniger die Bestrahlungsunterbrechnung
            triggert, wechselt der Wert auf 1.

        beam_on : ndarray
            Wechselt auf 0 wenn Beam abgeschaltet ist.

        carriage_expected : ndarray
            Die Sollposition vom Leaf-Carriage.

        carriage_actual : ndarray
            Tatsächlich gemessene Position Leaf-Carriage.

        leaf_expected : ndarray
            Erwartete Leaf-Position.

        leaf_actual : ndarray
            Tatsächliche Leaf-Position.

        Beschreibung
        -----------------------------------------------------------------------
        Stellt die Informationen im DynaLog-File bequem zur Verfügung. Die
        Informationen der Headerzeilen werden komplett übernommen, die Spalten
        des Datenteils entweder verworfen oder in Numpy-Arrays eingelesen.
        """
        self.header = {}
        self.header["filename"] = filename

        if side == None:
            self.header["side"] = filename[0]
        else:
            self.header["side"] = side

        self.read_data()

    def read_data(self):
        """
        Beschreibung
        -----------------------------------------------------------------------
        Öffnet die Dynalog-Datei, teilt den Header zur weiteren Verarbeitung ab,
        wandelt den Datenteil in ein Numpy-Array mit float-Zahlen und ruft
        Funktionen zur weiteren Verarbeitung auf. Nimmt eine Headerlänge von
        6 Zeilen an.
        """
        with open(self.header["filename"],"r") as data:
            raw = [line.strip().split(",") for line in data.readlines()]

            self.build_header(raw[:6])

            data = np.array(raw[6:]).astype(float)
            self.build_beam(data)
            self.build_gantry(data)
            self.build_mlc(data)

    def build_header(self,raw_header):
        """
        Parameter
        -----------------------------------------------------------------------
        raw_header : list, [[str,str],...]
            Enthält die Wertepaare der Kopfzeile als Liste.

        Beschreibung
        -----------------------------------------------------------------------
        Erweitert das header-Dictionary um die Einträge aus den Kopfzeilen des
        DynaLog-Files.
        """
        self.header["version"] = raw_header[0][0]
        self.header["patient_id"] = raw_header[1][-1]
        self.header["plan_uid"] = raw_header[2][0]
        self.header["beam_number"] = int(raw_header[2][1])
        self.header["tolerance"] = int(raw_header[3][0])
        self.header["leaf_count"] = int(raw_header[4][0])
        self.header["coord_system"] = int(raw_header[5][0])

        name = raw_header[1][:-1]
        if len(name) == 1:
            name.append("N/A")
        if "" in name:
            name = [n if n != "" else "N/A" for n in name]
        self.header["patient_name"] = name
    def build_gantry(self,raw_data):
        """
        Parameter
        -----------------------------------------------------------------------
        raw_data : ndarray
            Enthält die Daten des DynaLog-Files als Array.

        Beschreibung
        -----------------------------------------------------------------------
        Extrahiert die Werte der Gantry-bezogenen Parameter Winkel, Segment,
        Kollimator-Rotation und Jaw-Positionen.
        """
        self.gantry_angle = raw_data[:,6]
#        self.previous_segment = raw_data[:,1]
#        self.collimator_rotation = raw_data[:,7]
#        self.y1 = raw_data[:,8]
#        self.y2 = raw_data[:,9]
#        self.x1 = raw_data[:,10]
#        self.x2 = raw_data[:,11]
        #derzeit nicht benötigte Daten, auskommentiert zwecks Beschleunigung.

    def build_beam(self,raw_data):
        """
        Parameter
        -----------------------------------------------------------------------
        raw_data : ndarray
            Enthält die Daten des DynaLog-Files als Array.

        Beschreibung
        -----------------------------------------------------------------------
        Extrahiert Beamdaten wie kumulative Dosisfraktion und Einschaltstatus.
        """
        self.dose_fraction = raw_data[:,0]
#        self.beam_holdoff = raw_data[:,2]
#        self.beam_on = raw_data[:,3]
        #derzeit nicht benötigte Daten, auskommentiert zwecks Beschleunigung.

    def build_mlc(self,raw_data):
        """
        Parameter
        -----------------------------------------------------------------------
        raw_data : ndarray
            thält die Daten des DynaLog-Files als Array.

        Beschreibung
        -----------------------------------------------------------------------
        Extrahiert die eigentlich spannenden Daten zu Carriage- und Leafposition,
        Soll- und Ist-Zustand.
        """
#        self.carriage_expected = raw_data[:,12]
#        self.carriage_actual = raw_data[:,13]
        self.leafs_expected = raw_data[:,14::4]
        self.leafs_actual = raw_data[:,15::4]

