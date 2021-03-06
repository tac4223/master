# -*- coding: utf-8 -*-
"""
Klassen
-------------------------------------------------------------------------------
DynalogMismatchError :
    Basis-Fehlerklasse für im Modul verwendete Exceptions.

LeafbankMismatchError :
    Verwendet bei Metadaten-Fehlern der Leafbänke.

BeamMismatchError :
    Wird bei Metadatenfehlern innerhalb der Beamerzeugung und -validierung ausgelöst.

PlanMismatchError :
    Wird bei Metadatenfehlern auf Planobjekt-Ebene ausgelöst.

leafbank :
    Stellt die Informationen einer DynaLog-Datei in leicht zugänglicher Weise bereit.

beam :
    Fasst 2 leafbank-Objekte mit übereinstimmenden Header-Daten zu einem Beam
    zusammen.

plan :
    Fasst beliebig viele Beams zu einem Plan unter einer Plan-UID zusammen. Es
    müssen wiederum alle Header-Daten übereinstimmen.

Beschreibung
-------------------------------------------------------------------------------
Enthält Fehler und Objektklassen, um den Umgang mit DynaLog-Dateien bequem und
einfach zu machen.
"""

import numpy as np
import dicom as dcm
import copy
import time

class DynalogMismatchError(Exception):
    """
    Beschreibung:
    ---------------------------------------------------------------------------
    Basisklasse für Exceptions im Modul, keine weitere Funktion.
    """
    pass

class LeafbankMismatchError(DynalogMismatchError):

    def __init__(self,plan_uid,beam_number,key,msg="Must be identical"):
        """
        Parameter
        -----------------------------------------------------------------------
        plan_uid : str
            Die UID des Planobjekts, in dessen Kontext der Fehler auftritt.

        beam_number : int
            Die Nummer des Beams in dem der Fehler auftritt.

        key : str
            Der Key für das header-Dictionary, bei dem eine Abweichung festgestellt
            wurde.

        msg : str, default "Must be identical"
            Zusätzlicher Fehlertext. Vollständiger Fehlertext ist "<key> mismatch
            between leafbanks A & B: <key> <msg>".

        Beschreibung
        -----------------------------------------------------------------------
        Verwendet bei Abweichungen zwischen Headerdaten der Leafbänke eines Beams.
        """
        self.uid = plan_uid
        self.beam = beam_number
        self.key = key
        self.msg = msg

    def __str__(self):
        return "\nPlan {0}\nBeam {2}\n"\
        "{1} mismatch between leafbanks A & B: {1} {3}"\
            .format(self.uid,self.key,self.beam,self.msg)

class BeamMismatchError(DynalogMismatchError):

    def __init__(self,plan_uid,beam_number,key,msg="must be identical"):
        """
        Parameter
        -----------------------------------------------------------------------
        plan_uid : str
            Die UID des Planobjekts, in dessen Kontext der Fehler auftritt.

        beam_number : int
            Die Nummer des Beams in dem der Fehler auftritt.

        leafbank : str
            Bezeichnung der Leafbank, die eine Abweichung zum Beamheader aufweist.
            In der Regel A oder B.

        key : str
            Der Key für das header-Dictionary, bei dem eine Abweichung festgestellt
            wurde.

        msg : str, default "Must be identical"
            Zusätzlicher Fehlertext. Vollständiger Fehlertext ist "<key> mismatch
            between beam <beam_number> and leafbank <leafbank>: <key> <msg>".

        Beschreibung
        -----------------------------------------------------------------------
        Wird bei Metadatenfehlern innerhalb der Beamerzeugung und -validierung ausgelöst.
        """
        self.uid = plan_uid
        self.beam_number = beam_number
        self.key = key
        self.msg = msg

    def __str__(self):
        return "\nPlan {0}\nBeam {2}\n"\
        "{1} mismatch between beam {2} DICOM header and DynaLog header: "\
        "{1} {3}".format(self.uid,self.key,self.beam_number,self.msg)

class PlanMismatchError(DynalogMismatchError):

    def __init__(self,plan_uid,key,msg):
        """
        Parameter
        -----------------------------------------------------------------------
        plan_uid : str
            Die UID des Planobjekts, in dessen Kontext der Fehler auftritt.

        key : str
            Der Key für das header-Dictionary, bei dem eine Abweichung festgestellt
            wurde.

        msg : str
            Zusätzlicher Fehlertext. Vollständiger Fehlertext ist "<key> mismatch
            : <msg>".

        Beschreibung
        -----------------------------------------------------------------------
        Wird bei Metadatenfehlern auf Planobjekt-Ebene ausgelöst.
        """
        self.plan_uid = plan_uid
        self.key = key
        self.msg = msg

    def __str__(self):
        return "\nPlan {0}\n{1} mismatch: {2}"\
        .format(self.plan_uid,self.key,self.msg)

class beam:

    def __init__(self,banks,dicom_header=None,dicom_beam=None):
        """
        Parameter
        -----------------------------------------------------------------------
        dicom_header : dict, default None
            Dictionary, das die erwarteten Metadaten enthält. Wird von Plan-
            Instanz in der Funktion create_beams erzeugt. Falls kein Wert
            übergeben wird, überspringt die Init-Funktion den DICOM-Teil.

        dicom_beam : dicom.dataset.FileDataset, default None
            Element der BeamSequence-Liste aus DICOM-Objekt. Übergibt alle
            anderen "Soll"-Werte für intuitive Aufbewahrung im jeweiligen Beam.
            Falls kein Wert übergeben wird, überspringt die Init-Funktion den
            DICOM-Teil.

        banks : list
            Liste von 2 Leafbank-Objekten, die dann im Beam-Objekt gespeichert
            werden.

        Funktionen
        -----------------------------------------------------------------------
        construct_dicomdata :
            Falls dicom_header übergeben wurde, wird dieser in Objekteigenschaft
            übernommen und anschließend dicom_beam ausgewertet. Falls nicht,
            wird die Funktion beendet.

        construct_logdata :
            Prüft zunächst mittels check_leafbank_data, ob die Leafbankdaten
            stimmig sind. Falls ja, werden Dosis, Gantrywinkel, identische
            Headerdaten und das previous segment Array in Eigenschaften des
            Beams übertragen, um sie leichter zugänglich zu machen.

        convert_angles :
            Rechnet Winkel vom Plan- ins Dynalog-Format um (und umgekehrt).

        convert_mlc :
            Fügt die Leafbank-Daten (leafbank.leafs_actual) von Seite A und B
            so zusammen, dass sie Zeile für Zeile der Formatierung im DICOM-
            File entsprechen. Nur möglich für validierte Beams.

        pick_controlpoints :
            Wählt unter verschiedenen Kriterien aus der Vielzahl aufgezeichneter
            Daten Kontrollpunkte aus, die sinnvoll mit dem DICOM-Plan verglichen
            werden können.

        correct_leafgap :
            Sorgt dafür, dass in MLC-Positionen immer ein Spalt von mindestens
            0,02 cm bleibt (Anforderung des Planungssystems).

        export_logbeam :
            Erstellt ein DICOM-Beamobjekt das die Daten aus den DynaLog-Files
            enthält.

        check_leafbank_data :
            Prüft, ob die Metadaten der Leafbänke sinnvoll übereinstimmen.

        check_beam_metadata :
            Prüft, ob die Metadaten der Dynalog- und DICOM-Header des Beams
            zusammen passen.

        validate_beam :
            Führt check_leafbank_data und check_beam_metadata aus, bei
            positivem Ergebnis wird Instanzvariable 'verified' auf True gesetzt.

        Instanzvariablen
        -----------------------------------------------------------------------
        validated : boolean
            Gibt an, ob die Metadaten des Beams und der Leafbänke bereits auf
            Konsistenz geprüft wurden.

        dicom_header : dict
            Enthält die Soll-Metadaten, die aus dem DICOM Planobjekt ausgelesen
            werden.

        dicom_beam : dicom.dataset.FileDataset
            Element der BeamSequence-Liste aus DICOM-Objekt.

        dicom_dose : ndarray
            Enthält die Dosis aus dem DICOM-Beam als numpy-Array. Dosis wird in
            Integers zwischen 0 und 25000 übersetzt, um identisch zu DynaLog-
            Konvention zu werden.

        dicom_gantry_angle : ndarray
            Gantrywinkel in Grad als Array.

        dicom_mlc : ndarray
            Die MLC-Positionen aus DICOM-File. Format:
             (Anzahl Kontrollpunkte,Anzahl Leafpaare), wobei Seite B zuerst
             kommt.

        log_dose : ndarray
            DynaLog-Daten zur Dosis.

        log_gantry_angle : ndarray
            DynaLog-Daten zum Gantrywinkel.

        log_header : dict
            Header-Daten aus DynaLog Files, die zwischen beiden Bänken identisch
            sind.

        log_previous_segment : ndarray
            Die Segmentangaben aus den DynaLog-Files.

        banks : list
            Liste von 2 leafbank-Objekten.

        Beschreibung
        -----------------------------------------------------------------------
        Fasst jeweils 2 leafbank-Objekte zu einem Beam zusammen, und stellt eine
        einfache Möglichkeit bereit, sie auf korrekt zusammenpassende Metadaten zu
        prüfen.
        """
        self.validated = False

        self.dicom_header = dicom_header
        self.dicom_beam = dicom_beam
        self.construct_dicomdata()

        if banks != None:
            self.banks = list(np.array(banks)[np.argsort([banks[0].\
                header["side"],banks[0].header["side"]])])
            #Stellt sicher dass stets Seite A an erster Stelle der Leafbänke steht.
            self.construct_logdata()
            self.validate_beam()

    def construct_dicomdata(self):
        """
        Beschreibung
        -----------------------------------------------------------------------
        Nimmt das DICOM-Objekt in self.dicom_beam auseinander. Dosis der
        einzelnen Kontrollpunkte wird in Array gepackt, mit 25000 multipliziert
        um mit DynaLog konform zu gehen.

        Gantrywinkel wird direkt übernommen. Wichtig: Unterschiede im Koordinaten-
        system bzgl. Winkel beachten.

        MLC-Positionen werden ohne weitere Änderungen aus den Kontrollpunkten
        rausgezogen.
        """
        if self.dicom_header == None:
            return None
        self.dicom_dose = 25000*np.array([self.dicom_beam.ControlPointSequence[num].
        CumulativeMetersetWeight for num in range(self.dicom_beam.NumberOfControlPoints)])

        self.dicom_gantry_angle = np.array([self.dicom_beam.ControlPointSequence[num].
        GantryAngle for num in range(self.dicom_beam.NumberOfControlPoints)])

#        self.dicom_mlc = [[self.dicom_beam.ControlPointSequence[num].
#            BeamLimitingDevicePositionSequence[0].
#            LeafJawPositions] for num in range(1,self.dicom_beam.NumberOfControlPoints)]
#        self.dicom_mlc = np.insert(self.dicom_mlc,0,self.dicom_beam.
#            ControlPointSequence[0].BeamLimitingDevicePositionSequence[2].
#            LeafJawPositions)

        #derzeit nicht benötigte Daten, auskommentiert zwecks Beschleunigung.

        self.direction = self.dicom_beam.ControlPointSequence[0].GantryRotationDirection


    def construct_logdata(self):
        """
        Beschreibung
        -----------------------------------------------------------------------
        Schreibt Dosis, Gantrywinkel, Header und Segmentnummern aus den
        Leafbänken in Beamvariablen, da sie so logischer/bequemer anzusprechen
        sind.
        """
        if self.check_leafbank_data() == True:
            self.log_dose = 1*self.banks[0].dose_fraction
            self.log_gantry_angle = self.banks[0].gantry_angle/10.
            self.log_header = copy.deepcopy(self.banks[0].header)
#            self.log_previous_segment = 1*self.banks[0].previous_segment
            #derzeit nicht benötigte Daten, auskommentiert zwecks Beschleunigung.

            del self.log_header["version"]
            del self.log_header["side"]
            del self.log_header["filename"]

    @classmethod
    def convert_angles(self,data):
        """
        Parameter
        -----------------------------------------------------------------------
        data : int or array-like
            Die Winkel (einer oder mehrere) in 0-360 Grad, die von Dynalog in
            Dicom-System umgerechnet werden sollen.

        target_coord : str, "log" or "dicom"
            Das Zielkoordinatensystem.

        Beschreibung
        -----------------------------------------------------------------------
        DICOM- und DynaLog-Dateien unterscheiden sich im Ort des Nullpunkts für
        den Gantrywinkel (12 bzw. 6 Uhr). Diese Funktion rechnet zwischen beiden
        um.

        Ausgabe
        -----------------------------------------------------------------------
        output : ndarray
            Die passenden Werte im anderen Koordinatensystem.
        """
        return (540 - np.array(data))%360

    def convert_mlc(self,export_expected=False,leafgap=0.7):
        """
        Beschreibung
        -----------------------------------------------------------------------
        Fügt die Leafpositionen von Bank A und B passend aneinander, um sie
        in DICOM-Format zu bringen.

        Ausgabe
        -----------------------------------------------------------------------
        output : ndarray
            Dimension (x,120), wobei x die Anzahl an aufgezeichneten Datenpunkten
            des DynaLogs ist.
        -----------------------------------------------------------------------
        """
        if self.validated == False: raise BeamMismatchError(
            self.dicom_header["plan_uid"],self.dicom_header["beam_number"],
            "validation","cannot export MLC positions of unvalidated beam.")

        elif self.validated == True:

            if export_expected == False:
                s2 = np.round(self.banks[0].leafs_actual/51.,2)
                s1 = np.round(-1*self.banks[1].leafs_actual/51.,2)

            elif export_expected == True:
                s2 = np.round(self.banks[0].leafs_expected/51.,2)
                s1 = np.round(-1*self.banks[1].leafs_expected/51.,2)

            x1 = np.where(s2-s1 < 0,s1+(s2-s1)/2.-0.01,s1)
            x2 = np.where(s2-s1 < 0,s2-(s2-s1)/2.+0.01,s2)
            #sorgt dafür, dass keine negativen Feldgrößen auftauchen.

            x11 = np.where((x2-x1 < 0.6)*(x2-x1 > 0.02),x1-(leafgap-(x2-x1))/2.,x1)
            x22 = np.where((x2-x1 < 0.6)*(x2-x1 > 0.02),x2+(leafgap-(x2-x1))/2.,x2)
            #Stellt sicher, dass der Dynamic Leaf Gap stets ausreichend groß
            #für Verarbeitung in Eclipse ist. Dynamic Leafs werden angenommen,
            #wenn der Abstand größer als 0,6 mm ist. Sicher nicht die schönste
            #Art, diese beiden Probleme zu lösen...

            return np.append(x11,x22,axis=1)
    def pick_controlpoints(self,criterion="angle"):
        """
        Parameter
        -----------------------------------------------------------------------
        criterion : str
            Möglich sind "dose" oder "angle". Wählt aus, nach welchem
            Kriterium die Kontrollpunkte zusammengestellt werden.


        Beschreibung
        -----------------------------------------------------------------------
        Da DynaLogs deutlich mehr Einträge enthalten als im DICOM-Plan
        Kontrollpunkte vorhanden sind, muss eine Auswahl getroffen werden. Hierzu
        lassen sich die drei Kriterien Dosis, Gantrywinkel und Segmentnummer
        verwenden, die alle mit Planparametern abgeglichen und dementsprechend
        zur Kontrollpunktauswahl verwendet werden können.

        Die Stadardwerte (segment und last) lieferten in kurzen Tests die
        besten Ergebnisse.

        Ausgabe
        -----------------------------------------------------------------------
        output : ndarray
            Array mit Indizes, das ohne weitere Verarbeitung für log_dose,
            log_gantry_angle und Leafbank-Positionen verwendet werden kann.
        """
        index = []

        if criterion == "dose":
            for dose in self.dicom_dose[:-1]:
                index.append(np.nonzero(self.log_dose >= dose)[0][0])
            index.append(-1)
            return index

        elif criterion == "angle":
            if self.direction == "CW":
                for angle in self.convert_angles(self.dicom_gantry_angle)[:-1]:
                    index.append(np.nonzero(self.log_gantry_angle <= angle)[0][0])
                index.append(-1)
                return index

            if self.direction=="CC":
                for angle in self.convert_angles(self.dicom_gantry_angle)[:-1]:
                    index.append(np.nonzero(self.log_gantry_angle >= angle)[0][0])
                index.append(-1)
                return index

    def export_logbeam(self,export_expected=False,leafgap=0.7):
        """
        Beschreibung
        -----------------------------------------------------------------------
        Ersetzt MLC, Gantrywinkel und Dosis einer Kopie des DICOM Beamobjekts
        mit den Werten aus DynaLogs.

        Ausgabe
        -----------------------------------------------------------------------
        output : dicom.dataset.Dataset
            DICOM Beam-Objekt das direkt in Plan-Objekte als Teil von BeamSequence
            integriert werden kann.
        """
        index = self.pick_controlpoints()
        exportbeam = copy.deepcopy(self.dicom_beam)

        mlc = self.convert_mlc(export_expected,leafgap)[index]
        dose = 1./25000*self.log_dose[index]

        exportbeam.ControlPointSequence[0].\
            BeamLimitingDevicePositionSequence[2].LeafJawPositions = list(mlc[0,:])

        for num in range(1,len(self.dicom_beam.ControlPointSequence)):
            exportbeam.ControlPointSequence[num].\
                BeamLimitingDevicePositionSequence[0].LeafJawPositions = list(mlc[num,:])

            exportbeam.ControlPointSequence[num].\
                CumulativeMetersetWeight = dose[num]
            exportbeam.ControlPointSequence[num].ReferencedDoseReferenceSequence[0].\
                CumulativeDoseReferenceCoefficient = dose[num]

        return exportbeam


    def check_leafbank_data(self):
        """
        Beschreibung
        -----------------------------------------------------------------------
        Prüft, ob Metadaten der Leafbänke sinnvoll zusammen passen, und ob
        Daten des Beams und der Bänke übereinstimmen.

        Ausgabe
        -----------------------------------------------------------------------
        output : boolean
            Gibt 'True' zurück, sofern der Check erfolgreich war.
        """
        try:
            for key in self.banks[0].header.keys():
                if key in ["filename","side"]:
                    if self.banks[0].header[key] == self.banks[1].header[key]:
                        raise LeafbankMismatchError(self.dicom_header["plan_uid"],
                            self.dicom_header["beam_number"],
                            key,"can't be identical for both banks")
                else:
                    if self.banks[0].header[key] != self.banks[1].header[key]:
                        raise LeafbankMismatchError(self.dicom_header["plan_uid"],
                        self.dicom_header["beam_number"],key)

                if not np.all(self.banks[0].dose_fraction ==
                    self.banks[1].dose_fraction):
                    raise LeafbankMismatchError(self.dicom_header["plan_uid"],
                        self.dicom_header["beam_number"],"dose array")

                if not np.all(self.banks[0].gantry_angle ==
                    self.banks[1].gantry_angle):
                    raise LeafbankMismatchError(self.dicom_header["plan_uid"],
                        self.dicom_header["beam_number"],"gantry angle array")

#                if not np.all(self.banks[0].previous_segment ==
#                    self.banks[1].previous_segment):
#                    raise LeafbankMismatchError(self.dicom_header["plan_uid"],
#                        self.dicom_header["beam_number"],"previous segment array")
        #derzeit nicht benötigte Daten, auskommentiert zwecks Beschleunigung.

        except LeafbankMismatchError:
            raise
        else:
            return True
        return False

    def check_beam_metadata(self):
        """
        Beschreibung
        -----------------------------------------------------------------------
        Prüft, ob die Metadaten des Beams in DICOM- und DynaLog-Header zueinander
        passen.

        Ausgabe
        -----------------------------------------------------------------------
        output : boolean
            True wenn alles stimmt, Exception wenn nicht.
        """
        if self.dicom_header == None:
            return None
        try:
            for key in self.dicom_header.keys():
                if self.dicom_header[key] != self.log_header[key]:
                    raise BeamMismatchError(self.dicom_header["plan_uid"],
                    self.dicom_header["beam_number"],key)
        except BeamMismatchError:
            raise
        else:
            return True
        return False

    def validate_beam(self):
        """
        Beschreibung
        -----------------------------------------------------------------------
        Ruft check_beam auf, und setzt, falls erfolgreich, 'validated' auf True.
        """
        try:
            self.check_leafbank_data()
            self.check_beam_metadata()
        except BeamMismatchError:
            self.validated = False
            raise
        else:
            self.validated = True

class plan:

    def __init__(self,dicom_file):
        """
        Parameter
        -----------------------------------------------------------------------
        plan_uid : str
            Die UID des zu erstellenden Plans.

        number_of_beams : int
            Anzahl der Beams, die im Plan enthalten sind.

        bank_pool : list of leafbank objects
            Vollständige Liste aller Leafbänke, aus denen der Plan besteht.

        Funktionen
        -----------------------------------------------------------------------
        construct_beams :
            Baut aus den leafbank-Objekten in bank_pool die einzelnen Beams.

        check_plan :
            Prüft Metadaten.

        validate_plan :
            Führt check_plan aus, bei positivem Ergebnis wird 'validated = True'
            gesetzt.

        invalidate_plan :
            'validated' wird False gesetzt.

        change_header_data :
            Ändert Werte von vorhandenen Datenfeldern in 'header'.

        Instanzvariablen
        -----------------------------------------------------------------------
        validated : boolean
            Gibt an, ob Metadaten auf Konsistenz geprüft wurden.

        header : dict
            Metadaten des Planobjekts.

        beams : list of beam objects
            Die Beams aus denen sich der Plan zusammensetzt.

        Beschreibung
        -----------------------------------------------------------------------
        Fasst Beams zu Plänen zusammen. Bietet wiederum Möglichkeit zur
        Validierung.
        """
        self.validated = False
        self.header = {}
        self.dicom_data = dicom_file
        self.construct_header()
        self.arcs = 0
        self.construct_dicombeams()


    def construct_dicombeams(self):
        self.beams = []
        for beam in self.dicom_data.BeamSequence:
            if beam.BeamType == "DYNAMIC":
                self.beams.append("dynamic")
                self.arcs += 1
            else:
                self.beams.append(beam)

    def construct_header(self):
        """
        Beschreibung
        -----------------------------------------------------------------------
        Nimmt DICOM-Datei auseinander und sammelt die Attribute Plan UID,
        Patientenname, Patienten ID und Plan Name in einem Dictionary.
        """
        self.header["plan_uid"] = self.dicom_data.SOPInstanceUID
        self.header["patient_id"] = self.dicom_data.PatientID
        self.header["plan_name"] = self.dicom_data.RTPlanLabel

        name = self.dicom_data.PatientName.split("^")
        if len(name) == 1:
            name.append("N/A")
        if "" in name:
            name = [n if n != "" else "N/A" for n in name]
        self.header["patient_name"] = name

    def construct_logbeams(self,bank_pool=None):
        """
        Parameter
        -----------------------------------------------------------------------
        bank_pool : list of leafbank objects
            Alle leafbanks müssen zur gleichen UID gehören, kompatible Metadaten
            aufweisen und in ausreichender Zahl vorhanden sein um alle Beams
            zu bevölkern.

        Beschreibung
        -----------------------------------------------------------------------
        Fügt leafbank-Objekte zu Beams zusammen und sortiert sie an passender
        Stelle in der Beam-Liste ein.
        """
        if bank_pool == None:
            for num in range(len(self.beams)):
                beam_header = copy.deepcopy(self.header)
                del beam_header["plan_name"]
                beam_header["beam_number"] = num+1
                beam_header["leaf_count"] = int(self.dicom_data.\
                    BeamSequence[num].BeamLimitingDeviceSequence[2].\
                    NumberOfLeafJawPairs)

                self.beams[num] = beam(None,beam_header,self.dicom_data.BeamSequence[num])


        elif len(bank_pool) != 2*len(self.beams):
            raise PlanMismatchError(self.header["plan_uid"],"beam count",
                "plan needs {0} leafbanks for beam construction,"\
                " {1} were passed."\
                .format(2*len(self.beams),len(bank_pool)))

        elif len(bank_pool) == 2*len(self.beams):
            beam_nums = [bank.header["beam_number"] for bank in bank_pool]
            sort_index = np.argsort(beam_nums)
            for num in range(len(self.beams)):
                beam_header = copy.deepcopy(self.header)
                del beam_header["plan_name"]
                beam_header["beam_number"] = num+1
                beam_header["leaf_count"] = int(self.dicom_data.
                    BeamSequence[num].BeamLimitingDeviceSequence[2].
                    NumberOfLeafJawPairs)

                self.beams[num] = beam([bank_pool[sort_index[2*num]],
                       bank_pool[sort_index[2*num+1]]],beam_header,
                        self.dicom_data.BeamSequence[num])

#        self.validate_plan()

    def check_plan(self):
        """
        Beschreibung
        -----------------------------------------------------------------------
        Prüft Konsistenz der Metadaten zwischen Beams und Leafbanks sowie Beams
        und Plan. Wirft Exception falls Abweichungen vorhanden sind, gibt
        ansonsten True zurück.

        Ausgabe
        -----------------------------------------------------------------------
        output : boolean
        """
        try:
            for num in range(len(self.beams)):
                self.beams[num].validate_beam()
                if self.beams[num].log_header["beam_number"] != num+1:
                    raise PlanMismatchError(self.header["plan_uid"],
                    "beam assignment","beam at index {0} of beam list"\
                    " identifies as beam {1} instead of beam {2}."\
                    .format(num,self.beams[num].log_header["beam_number"],num+1))
            if len(self.beams) != len(self.dicom_data.BeamSequence):
                raise PlanMismatchError(self.header["plan_uid"],"beam count",
                "beam list contains {0} entries, plan header requires {1}."\
                .format(len(self.beams),len(self.dicom_data.BeamSequence)))
        except PlanMismatchError:
            raise
            return False
        else:
            return True
        return False

    def validate_plan(self):
        """
        Beschreibung
        -----------------------------------------------------------------------
        Ruft check_plan auf, und setzt bei korrekten Metadaten 'validated' auf
        True.
        """
        try:
            self.validated = self.check_plan()
        except PlanMismatchError:
            self.validated = False
            raise

    def invalidate_plan(self):
        """
        Beschreibung
        -----------------------------------------------------------------------
        Setzt 'validated' von Plan und allen Beams auf False.
        """
        self.validated = False
        for beam in self.beams:
            beam.validated = False

#    def change_all_header_data(self,key,new_value):
#        """
#        Parameter
#        -----------------------------------------------------------------------
#        key : str
#            key für die 'header' Dictionaries, dessen Wert geändert werden soll.
#            Muss bereits angelegt sein, Neueinträge sind mit der Funktion nicht
#            möglich!
#
#        new_value : str or int
#            Der Wert, auf den header[key] gesetzt wird. Variablentyp ändert sich
#            natürlich je nach editiertem Wert.
#
#        Beschreibung
#        -----------------------------------------------------------------------
#        Ändert den Wert für angegebenes Header-Feld in Plan, Beam und Leafbank-
#        Objekten. Nur möglich, wenn Plan nicht validiert ist, um Situationen
#        zu vermeiden, in denen man davon ausgeht dass nicht geänderte Werte
#        vorliegen, aber tatsächlich einzelne Einträge geändert wurden.
#        'validated' bleibt auch nach Ausführung auf False, es wird aber
#        check_plan ausgeführt, um zu prüfen ob die Änderungen konsistent erfolgten.
#        """
#        if self.validated == True:
#            raise PlanMismatchError(self.header["plan_uid"],"validation",
#            "can't modify validated plan, call invalidate_plan() first.")
#        try:
#            self.check_plan()
#        except PlanMismatchError:
#            raise PlanMismatchError(self.header["plan_uid"],"validation",
#            "error while checking plan object before UID change."\
#            " call check_plan() for error message.")
#        else:
#            if key not in self.header.keys():
#                raise PlanMismatchError(self.header["plan_uid"],
#                "header keyword","{0} is not a valid keyword for"\
#                " plan object header data.".format(key))
#            elif key in self.header.keys():
#                self.header[key] = new_value
#            for beam in self.beams:
#                if key not in beam.log_header.keys():
#                    raise PlanMismatchError(self.header["plan_uid"],
#                    "header keyword","{0} is not a valid keyword for"\
#                    " beam object header data.".format(key))
#                elif key in beam.log_header.keys():
#                    beam.log_header[key] = new_value
#                if key not in beam.dicom_header.keys():
#                    raise PlanMismatchError(self.header["plan_uid"],
#                    "header keyword","{0} is not a valid keyword for"\
#                    " beam object header data.".format(key))
#                elif key in beam.dicom_header.keys():
#                    beam.dicom_header[key] = new_value
#                    for bank in beam.banks:
#                        if key not in bank.header.keys():
#                            raise PlanMismatchError(self.header["plan_uid"],
#                            "header keyword","{0} is not a valid keyword for"\
#                            " leafbank object header data.".format(key))
#                        elif key in bank.header.keys():
#                            bank.header[key] = new_value
#                beam.validate_beam()
#            self.check_plan()

    def export_dynalog_plan(self,plan_name,filename,export_expected=False,leafgap=0.7):
        """
        Parameter
        -----------------------------------------------------------------------
        plan_name : str
            Wert des RTPlanLabel-Tags im exportierten Plan. Maximal 13
            Zeichen, längere Namen werden abgeschnitten.

        UID : str
            Wert des SOPInstanceUID-Tags im exportierten Plan. Muss der UID-Syntax
            entsprechen.

        filename : str
            Der Dateiname, unter dem das exportierte RTPLAN Objekt abgelegt
            werden soll.

        Beschreibung
        -----------------------------------------------------------------------
        Exportiert den derzeitigen Planzustand als DICOM-Objekt. Basis ist eine
        Kopie des DICOM-Files mit dem der Plan initialisiert wurde. StudyInstance,
        SeriesInstance und Study UIDs werden ersetzt/geändert. Alle im DynaLog
        enthaltenen Werte werden anstelle der Originalparameter exportiert.

        Plan muss validiert sein bevor der Export erfolgen kann!

        Ausgabe
        -----------------------------------------------------------------------
        output : DICOM RTPLAN Objekt
            Planobjekt mit DynaLog-Werten.

        """
        if self.validated == False:
            raise PlanMismatchError(self.header["plan_uid"],"validation",
            "can't export unvalidated plan.")
        exportplan = copy.deepcopy(self.dicom_data)
        for num in range(len(self.beams)):
            exportplan.BeamSequence[num] = self.beams[num].export_logbeam(export_expected,leafgap)
        exportplan.RTPlanLabel = ("dyn_"+plan_name)[:13]

        ltime = time.localtime()
        study_instance = exportplan.StudyInstanceUID.split(".")
        series_instance = exportplan.SeriesInstanceUID.split(".")
        instance_id = exportplan.SOPInstanceUID.split(".")

        exportplan.StudyInstanceUID = ".".join(study_instance[:-1])+\
            "."+"".join([str(t) for t in ltime[3:6]])
        exportplan.SeriesInstanceUID = ".".join(series_instance[:-1])+\
            "."+"".join([str(t) for t in ltime[:6]])
        exportplan.StudyID = "Id"+\
            "".join([str(t) for t in ltime[3:6]])
        exportplan.SOPInstanceUID = ".".join(instance_id[:-1])+\
            "."+"".join([str(t) for t in ltime[:6]])
        exportplan.ApprovalStatus = "UNAPPROVED"
        dcm.write_file(filename,exportplan)

#    def strip_privates(self,plan):
#        del plan[0x3287,0x1000]
#        del plan[3287,0x0010]
#        return plan
#
if __name__ == "__main__":
    from import_tools import filetools as ft
##    import matplotlib.pyplot as plt
#    banks = ft.get_banks("D:\Echte Dokumente\uni\master\khdf\Yannick\systemtest\messungen\\2VMAT loose","patient_name")
    p1 = ft.get_plans("D:\Echte Dokumente\uni\master\khdf\Yannick\systemtest\messungen\\2VMAT loose")[0]
#    p1.construct_logbeams(banks[p1.header["plan_uid"]])
#    p1.validate_plan()
#
#    banks = ft.get_banks("D:\Echte Dokumente\uni\master\khdf\Yannick\systemtest\messungen\\1VMAT loose")
#    p2 = ft.get_plans("D:\Echte Dokumente\uni\master\khdf\Yannick\systemtest\messungen\\1VMAT loose")[0]
#    p2.construct_logbeams(banks[p2.header["plan_uid"]])
#    p2.validate_plan()
##    b2_dcm = p2.beams[0].dicom_mlc.reshape((178,120))
#    b2_log = p2.beams[0].convert_mlc()
#    s2 = b2_log[0][:60]
#    s1 = b2_log[0][60:]
#
#    index = p1.beams[0].pick_controlpoints(),p1.beams[1].pick_controlpoints()
#
#    beams = p1.beams[0],p1.beams[1]
#
##    plt.close("all")
##    for num in range(2):
##        plt.figure(num)
##        plt.plot(beams[num].convert_angles(beams[num].log_gantry_angle[index[num]],"dicom"),label="DynaLog")
##        plt.plot(beams[num].dicom_gantry_angle,label="DICOM")
##        plt.xlabel("Control Points")
##        plt.ylabel("Gantry Angle / Degrees")
##        plt.title("Gantry Angle")
##        plt.legend()
##        plt.show()
##
##        plt.figure(num+2)
##        plt.plot(beams[num].log_dose[index[num]]/25000,label="DynaLog")
##        plt.plot(beams[num].dicom_dose/25000,label="DICOM")
##        plt.xlabel("Control Points")
##        plt.ylabel("Relative Dose")
##        plt.title("Dose")
##        plt.legend()
##        plt.show()
##
##        plt.figure(num+4)
##        plt.plot((beams[num].log_dose[index[num]]-beams[num].dicom_dose)/12500.,label="Deviation from DICOM")
##        plt.xlabel("Control Points")
##        plt.ylabel("Absolute Error / Gy")
##        plt.title("Deviation")
##        plt.show()
#
