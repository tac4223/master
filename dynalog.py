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

    def __init__(self,plan_uid,beam_number,leafbank,key,msg="must be identical"):
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

    def __init__(self,filename):
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
        self.header["side"] = filename[0]

        self.read_data(filename)
        self.build_header(filename)
        self.build_beam()
        self.build_gantry()
        self.build_mlc()
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

    def __init__(self,plan_uid,beam_number,banks):
        """
        Parameter
        -----------------------------------------------------------------------
        plan_uid : str
            Die UID des Plans, den man am Ende rekonstruieren möchte. Muss
            spezifiziert werden, um auszuschließen dass irrtümlich falsche Leafbänke
            berücksichtigt werden.

        beam_number : int
            Gibt an, welche Beamnummer der angelegte Beam bekommt. Muss natürlich
            später deckungsgleich mit den aus DynaLogs ausgelesenen Werten sein.

        banks : list
            Liste von 2 Leafbank-Objekten, die dann im Beam-Objekt gespeichert
            werden.

        Funktionen
        -----------------------------------------------------------------------
        check_beam :
            Prüft, ob alle Metadaten sowohl zwischen den beiden Leafbänken als
            auch dem Beam selbst konsistent sind

        validate_beam :
            Führt check_beam aus, bei positivem Ergebnis wird Instanzvariable
            'verified' auf True gesetzt.

        Instanzvariablen
        -----------------------------------------------------------------------
        validated : boolean
            Gibt an, ob die Metadaten des Beams und der Leafbänke bereits auf
            Konsistenz geprüft wurden.

        header : dict
            Enthält die Metadaten, die mit anderen Objekten abgeglichen werden.

        banks : list
            Liste von 2 leafbank-Objekten.

        Beschreibung
        -----------------------------------------------------------------------
        Fasst jeweils 2 leafbank-Objekte zu einem Beam zusammen, und stellt eine
        einfache Möglichkeit bereit, sie auf korrekt zusammenpassende Metadaten zu
        prüfen.
        """
        self.validated = False
        self.header = {"beam_number":beam_number, "plan_uid":plan_uid}
        self.banks = banks

        self.validate_beam()

    def check_beam(self):
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
            raise
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
            self.validated = self.check_beam()
        except BeamMismatchError:
            raise

class plan:

    def __init__(self,plan_uid,number_of_beams,bank_pool):
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
        self.header = {"plan_uid":plan_uid,"number_of_beams":number_of_beams}
        self.beams = [None for k in range(self.header["number_of_beams"])]

        self.construct_beams(bank_pool)
        self.validate_plan()

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
                if current_beam.header["beam_number"] != num+1:
                    raise PlanMismatchError(self.header["plan_uid"],
                    "beam assignment","beam at position {0} of beam list"\
                    " identifies as beam {1} instead of beam {2}."\
                    .format(num,current_beam.header["beam_number"],num+1))
            if len(self.beams) != self.header["number_of_beams"]:
                raise PlanMismatchError(self.header["plan_uid"],"beam count",
                "beam list contains {0} entries, plan header requires {1}."\
                .format(len(self.beams),self.header["number_of_beams"]))
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

    def change_header_data(self,key,new_value):
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
        Objekten. Nur mäglich, wenn Plan nicht validiert ist, um Situationen
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
                if key not in beam.header.keys():
                    raise PlanMismatchError(self.header["plan_uid"],
                    "header keyword","{0} is not a valid keyword for"\
                    " beam object header data.".format(key))
                elif key in beam.header.keys():
                    beam.header[key] = new_value
                    for bank in beam.banks:
                        if key not in bank.header.keys():
                            raise PlanMismatchError(self.header["plan_uid"],
                            "header keyword","{0} is not a valid keyword for"\
                            " leafbank object header data.".format(key))
                        elif key in bank.header.keys():
                            bank.header[key] = new_value
                beam.validate_beam()
            self.check_plan()

if __name__ == "__main__":
    dyn1 = leafbank("A1.dlg")
    dyn2 = leafbank("B1.dlg")
    dyn3 = leafbank("A2.dlg")
    dyn4 = leafbank("B2.dlg")

#    beam1 = beam("derp",1,[dyn1,dyn2])
    plan1 = plan("derp",2,[dyn1,dyn2,dyn3,dyn4])