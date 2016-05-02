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

class leafbank:

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
        Funktionen zur weiteren Verarbeitung auf.
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
        self.header["patient_name"] = raw_header[1][:-1]
        self.header["patient_id"] = raw_header[1][-1]
        self.header["plan_uid"] = raw_header[2][0]
        self.header["beam_number"] = int(raw_header[2][1])
        self.header["tolerance"] = int(raw_header[3][0])
        self.header["leaf_count"] = int(raw_header[4][0])
        self.header["coord_system"] = int(raw_header[5][0])

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
        self.previous_segment = raw_data[:,1]
        self.collimator_rotation = raw_data[:,7]
        self.y1 = raw_data[:,8]
        self.y2 = raw_data[:,9]
        self.x1 = raw_data[:,10]
        self.x2 = raw_data[:,11]

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
        self.beam_holdoff = raw_data[:,2]
        self.beam_on = raw_data[:,3]

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
        self.carriage_expected = raw_data[:,12]
        self.carriage_actual = raw_data[:,13]
        self.leafs_expected = raw_data[:,14::4]
        self.leafs_actual = raw_data[:,15::4]

class beam:

    def __init__(self,banks,dicom_header=None,dicom_beam=None):
        """
        Parameter
        -----------------------------------------------------------------------
        dicom_header : dict
            Dictionary, das die erwarteten Metadaten enthält. Wird von Plan-
            Instanz in der Funktion create_beams erzeugt.

        dicom_beam : dicom.dataset.FileDataset
            Element der BeamSequence-Liste aus DICOM-Objekt. Übergibt alle
            anderen "Soll"-Werte für intuitive Aufbewahrung im jeweiligen Beam.

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

        if banks[0].header["side"] == "A": self.banks = banks
        elif banks[0].header["side"] == "B": self.banks = banks[::-1]
        #Stellt sicher dass stets Seite A an erster Stelle der Leafbänke steht.

        self.dicom_header = dicom_header
        self.dicom_beam = dicom_beam

        self.construct_dicomdata()
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

        self.dicom_mlc = [self.dicom_beam.ControlPointSequence[num].
            BeamLimitingDevicePositionSequence[0].
            LeafJawPositions for num in range(1,178)]
        self.dicom_mlc = np.insert(self.dicom_mlc,0,self.dicom_beam.
            ControlPointSequence[0].BeamLimitingDevicePositionSequence[2].
            LeafJawPositions)
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
            self.log_previous_segment = 1*self.banks[0].previous_segment
            del self.log_header["version"]
            del self.log_header["side"]
            del self.log_header["filename"]

    @classmethod
    def convert_angles(self,data,target_coord="log"):
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
        if target_coord == "log":
            if type(data) in [np.ndarray,list,tuple]:
                data = np.array(data)
            return 360 - (data - 180) % 360
        elif target_coord == "dicom":
            if type(data) in [np.ndarray,list,tuple]:
                data = np.array(data)
                output = 360 - (data - 180) % 360
                output[np.where(data == 180)] = 0
                return output
            else:
                if data == 180: return 0
                return 360 - (data - 180) % 360
        else:
            raise DynalogMismatchError

    def convert_mlc(self):
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
        return np.round(np.append(-1*self.banks[1].leafs_actual,
                             self.banks[0].leafs_actual,axis=1)/51.,2)

    def pick_controlpoints(self,criterion="segment",limit="last"):
        index = []
        if criterion == "dose":
            for dose in self.dicom_dose:
                if limit=="first": index.append(np.where(self.log_dose >= dose)[0][0])
                if limit=="last": index.append(np.where(self.log_dose <= dose)[0][-1])

        elif criterion == "angle":
            for angle in self.convert_angles(self.dicom_gantry_angle):
                if limit=="first" and self.direction == "CW":
                    try:
                        index.append(np.where(self.log_gantry_angle <= angle)[0][0])
                    except IndexError:
                        index.append(0)
                if limit=="first" and self.direction=="CC":
                    index.append(np.where(self.log_gantry_angle >= angle)[0][0])
                if limit=="last" and self.direction == "CW":
                    index.append(np.where(self.log_gantry_angle >= angle)[0][-1])
                if limit=="last" and self.direction=="CC":
                    index.append(np.where(self.log_gantry_angle <= angle)[0][-1])

        elif criterion == "segment":
            for segment in range(self.dicom_beam.NumberOfControlPoints):
                if limit=="first" and self.direction == "CW":
                    index.append(np.where(self.log_previous_segment <= segment)[0][0])
                if limit=="first" and self.direction=="CC":
                    index.append(np.where(self.log_previous_segment >= segment)[0][0])
                if limit=="last" and self.direction == "CW":
                    index.append(np.where(self.log_previous_segment >= segment)[0][-1])
                if limit=="last" and self.direction=="CC":
                    index.append(np.where(self.log_previous_segment <= segment)[0][-1])

        return np.sort(index).astype(int)

    def export_logbeam(self):
        index = self.pick_controlpoints()
        exportbeam = copy.deepcopy(self.dicom_beam)

        mlc = self.convert_mlc()[index]
        gantry_angle = self.convert_angles(self.log_gantry_angle[index],"dicom")
        dose = 1./25000*self.log_dose[index]


        exportbeam.ControlPointSequence[0].\
            BeamLimitingDevicePositionSequence[2].LeafJawPositions = list(mlc[0,:])

        for num in range(1,178):
            exportbeam.ControlPointSequence[num].\
                BeamLimitingDevicePositionSequence[0].LeafJawPositions = list(mlc[num,:])

            exportbeam.ControlPointSequence[num].\
                CumulativeMetersetWeight = dose[num]
            exportbeam.ControlPointSequence[num].ReferencedDoseReferenceSequence[0].\
                CumulativeDoseReferenceCoefficient = dose[num]

            exportbeam.ControlPointSequence[num].\
                GantryAngle = gantry_angle[num]

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

                if not np.all(self.banks[0].previous_segment ==
                    self.banks[1].previous_segment):
                    raise LeafbankMismatchError(self.dicom_header["plan_uid"],
                        self.dicom_header["beam_number"],"previous segment array")
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

        self.beams = [None for k in range(len(self.dicom_data.BeamSequence))]

    def construct_header(self):
        """
        Beschreibung
        -----------------------------------------------------------------------
        Nimmt DICOM-Datei auseinander und sammelt die Attribute Plan UID,
        Patientenname, Patienten ID und Plan Name in einem Dictionary.
        """
        self.header["plan_uid"] = self.dicom_data.SOPInstanceUID
        self.header["patient_name"] = self.dicom_data.PatientName.split("^")
        self.header["patient_id"] = self.dicom_data.PatientID
        self.header["plan_name"] = self.dicom_data.RTPlanLabel

    def construct_beams(self,bank_pool):
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
        if len(bank_pool) != 2*len(self.beams):
            raise PlanMismatchError(self.header["plan_uid"],"beam count",
                "plan needs {0} leafbanks for beam construction,"\
                " {1} were passed."\
                .format(2*len(self.beams),len(bank_pool)))

        else:
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

        self.validate_plan()

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
                current_beam = self.beams[num]
                current_beam.validate_beam()
                if current_beam.log_header["beam_number"] != num+1:
                    raise PlanMismatchError(self.header["plan_uid"],
                    "beam assignment","beam at index {0} of beam list"\
                    " identifies as beam {1} instead of beam {2}."\
                    .format(num,current_beam.log_header["beam_number"],num+1))
            if len(self.beams) != len(self.beams):
                raise PlanMismatchError(self.header["plan_uid"],"beam count",
                "beam list contains {0} entries, plan header requires {1}."\
                .format(len(self.beams),len(self.beams)))
        except PlanMismatchError:
            raise
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

    def change_all_header_data(self,key,new_value):
        """
        Parameter
        -----------------------------------------------------------------------
        key : str
            key für die 'header' Dictionaries, dessen Wert geändert werden soll.
            Muss bereits angelegt sein, Neueinträge sind mit der Funktion nicht
            möglich!

        new_value : str or int
            Der Wert, auf den header[key] gesetzt wird. Variablentyp ändert sich
            natürlich je nach editiertem Wert.

        Beschreibung
        -----------------------------------------------------------------------
        Ändert den Wert für angegebenes Header-Feld in Plan, Beam und Leafbank-
        Objekten. Nur möglich, wenn Plan nicht validiert ist, um Situationen
        zu vermeiden, in denen man davon ausgeht dass nicht geänderte Werte
        vorliegen, aber tatsächlich einzelne Einträge geändert wurden.
        'validated' bleibt auch nach Ausführung auf False, es wird aber
        check_plan ausgeführt, um zu prüfen ob die Änderungen konsistent erfolgten.
        """
        if self.validated == True:
            raise PlanMismatchError(self.header["plan_uid"],"validation",
            "can't modify validated plan, call invalidate_plan() first.")
        try:
            self.check_plan()
        except PlanMismatchError:
            raise PlanMismatchError(self.header["plan_uid"],"validation",
            "error while checking plan object before UID change."\
            " call check_plan() for error message.")
        else:
            if key not in self.header.keys():
                raise PlanMismatchError(self.header["plan_uid"],
                "header keyword","{0} is not a valid keyword for"\
                " plan object header data.".format(key))
            elif key in self.header.keys():
                self.header[key] = new_value
            for beam in self.beams:
                if key not in beam.log_header.keys():
                    raise PlanMismatchError(self.header["plan_uid"],
                    "header keyword","{0} is not a valid keyword for"\
                    " beam object header data.".format(key))
                elif key in beam.log_header.keys():
                    beam.log_header[key] = new_value
                if key not in beam.dicom_header.keys():
                    raise PlanMismatchError(self.header["plan_uid"],
                    "header keyword","{0} is not a valid keyword for"\
                    " beam object header data.".format(key))
                elif key in beam.dicom_header.keys():
                    beam.dicom_header[key] = new_value
                    for bank in beam.banks:
                        if key not in bank.header.keys():
                            raise PlanMismatchError(self.header["plan_uid"],
                            "header keyword","{0} is not a valid keyword for"\
                            " leafbank object header data.".format(key))
                        elif key in bank.header.keys():
                            bank.header[key] = new_value
                beam.validate_beam()
            self.check_plan()

    def export_dynalog_plan(self,plan_name,UID,filename):
        if self.validated == False:
            raise PlanMismatchError(self.header["plan_uid"],"validation",
            "can't export unvalidated plan.")
        exportplan = copy.deepcopy(self.dicom_data)
        for num in range(len(self.beams)):
            exportplan.BeamSequence[num] = self.beams[num].export_logbeam()
        exportplan.SOPInstanceUID = UID
        exportplan.RTPlanLabel = plan_name
        exportplan.StudyInstanceUID = "Dynalog"
        exportplan.SeriesInstanceUID = "Dynalog"
        exportplan.StudyID = "Dynalog"
        dcm.write_file(filename,exportplan)

if __name__ == "__main__":
    from get_dicom_data import filetools as ft
#    a1 = leafbank("A1.dlg")
#    b1 = leafbank("B1.dlg")
    p = ft.get_plans("D:\Echte Dokumente\uni\master\khdf\Yannick\systemtest\messungen\\2VMAT loose")[0]
    p.construct_beams(ft.get_banks("D:\Echte Dokumente\uni\master\khdf\Yannick\systemtest\messungen\\2VMAT loose")[p.header["plan_uid"]])
#    b = p.beams[0]

