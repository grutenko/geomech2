from pony.orm import Database, Optional, PrimaryKey, Required, Set

db = Database()


def connect(login: str, password: str, host: str, port: int = 5432, database: str = "geomech"):
    global db
    db.bind(provider="postgres", user=login, password=password, host=host, database=database, port=port)
    db.generate_mapping(create_tables=False)


def is_entity(o: object) -> bool:
    global db
    return isinstance(o, db.Entity)


class MineObject(db.Entity):
    _table_ = "MineObjects"

    parent = Optional("MineObject", column="PID")
    coord_system = Required("CoordSystem", column="CSID")
    childrens = Set("MineObject")
    stations = Set("Station")
    bore_holes = Set("BoreHole")
    orig_sample_sets = Set("OrigSampleSet")
    discharge_series = Set("DischargeSeries")
    rock_bursts = Set("RockBurst")
    pm_sample_set = Set("PMSampleSet")

    RID = PrimaryKey(int, auto=True, column="RID")
    Level = Required(int, column="Level", volatile=True)
    HCode = Required(str, column="HCode", volatile=True)
    Name = Required(str, column="Name")
    Comment = Optional(str, column="Comment")
    Type = Required(str, column="Type")
    X_Min = Required(float, column="X_Min")
    Y_Min = Required(float, column="Y_Min")
    Z_Min = Required(float, column="Z_Min")
    X_Max = Required(float, column="X_Max")
    Y_Max = Required(float, column="Y_Max")
    Z_Max = Required(float, column="Z_Max")

    def get_tree_name(self):
        _m = {
            "REGION": "Регион",
            "ROCKS": "Горный массив",
            "FIELD": "Месторождение",
            "HORIZON": "Горизонт",
            "EXCAVATION": "Выработка",
        }
        return "[%s] %s" % (_m[self.Type], self.Name)

    @property
    def sp_own_type(self):
        return "MINE_OBJECT"


class CoordSystem(db.Entity):
    _table_ = "CoordSystems"

    parent = Optional("CoordSystem", column="PID")
    childrens = Set("CoordSystem")
    mine_objects = Set(MineObject)

    RID = PrimaryKey(int, auto=True, column="RID")
    Level = Required(int, column="Level")
    HCode = Required(str, column="HCode")
    Name = Required(str, column="Name")
    Comment = Optional(str, column="Comment")
    X_Min = Required(float, column="X_Min")
    Y_Min = Required(float, column="Y_Min")
    Z_Min = Required(float, column="Z_Min")
    X_Max = Required(float, column="X_Max")
    Y_Max = Required(float, column="Y_Max")
    Z_Max = Required(float, column="Z_Max")
    X_0 = Required(float, column="X_0")
    Y_0 = Required(float, column="Y_0")
    Z_0 = Required(float, column="Z_0")
    X_X = Required(float, column="X_X")
    X_Y = Required(float, column="X_Y")
    X_Z = Required(float, column="X_Z")
    Y_X = Required(float, column="Y_X")
    Y_Y = Required(float, column="Y_Y")
    Y_Z = Required(float, column="Y_Z")
    Z_X = Required(float, column="Z_X")
    Z_Y = Required(float, column="Z_Y")
    Z_Z = Required(float, column="Z_Z")

    @property
    def sp_own_type(self):
        return None


class Station(db.Entity):
    _table_ = "Stations"

    mine_object = Required(MineObject, column="MOID")
    bore_holes = Set("BoreHole")

    RID = PrimaryKey(int, auto=True, column="RID")
    Number = Required(str, column="Number")
    Name = Required(str, column="Name")
    Comment = Optional(str, column="Comment")
    X = Required(float, column="X")
    Y = Required(float, column="Y")
    Z = Required(float, column="Z")
    HoleCount = Required(int, column="HoleCount")
    StartDate = Required(int, column="StartDate", size=64)
    EndDate = Optional(int, column="EndDate", size=64)

    def get_tree_name(self):
        return "[Станция] %s" % self.Name

    @property
    def sp_own_type(self):
        return "STATION"


class BoreHole(db.Entity):
    _table_ = "BoreHoles"

    mine_object = Required(MineObject, column="MOID")
    orig_sample_sets = Set("OrigSampleSet")
    station = Optional(Station, column="SID")

    RID = PrimaryKey(int, auto=True, column="RID")
    Number = Required(str, column="Number")
    Name = Required(str, column="Name")
    Comment = Optional(str, column="Comment")
    X = Required(float, column="X")
    Y = Required(float, column="Y")
    Z = Required(float, column="Z")
    Azimuth = Required(float, column="Azimuth")
    Tilt = Required(float, column="Tilt")
    Diameter = Required(float, column="Diameter")
    Length = Required(float, column="Length")
    StartDate = Required(int, column="StartDate", size=64)
    EndDate = Optional(int, column="EndDate", size=64)
    DestroyDate = Optional(int, column="DestroyDate", size=64)

    def get_tree_name(self):
        return "[Скважина] %s" % self.Name

    @property
    def sp_own_type(self):
        return "BORE_HOLE"


class OrigSampleSet(db.Entity):
    _table_ = "OrigSampleSets"

    mine_object = Required(MineObject, column="MOID", volatile=True)
    bore_hole = Optional(BoreHole, column="HID")
    discharge_series = Set("DischargeSeries")
    discharge_measurements = Set("DischargeMeasurement")
    core_box_storage = Set("CoreBoxStorage")
    pm_samples = Set("PMSample")

    RID = PrimaryKey(int, auto=True, column="RID")
    Number = Required(str, column="Number")
    Name = Required(str, column="Name")
    Comment = Optional(str, column="Comment")
    SampleType = Required(str, column="SampleType")
    X = Required(float, column="X")
    Y = Required(float, column="Y")
    Z = Required(float, column="Z")
    StartSetDate = Required(int, column="StartSetDate", size=64)
    EndSetDate = Optional(int, column="EndSetDate", size=64)

    def get_tree_name(self):
        _m = {"CORE": "Керн", "STUFF": "Штуф", "DISPERCE": "Дисперсный материал"}
        return "[%s] %s" % (_m[self.SampleType], self.Name)

    @property
    def sp_own_type(self):
        return "ORIG_SAMPLE_SET"


class FoundationDocument(db.Entity):
    _table_ = "FoundationDocuments"

    discharge_series = Set("DischargeSeries")
    pm_test_series = Set("PMTestSeries")

    RID = PrimaryKey(int, auto=True, column="RID")
    Comment = Optional(str, column="Comment")
    Type = Optional(str, column="Type")
    Number = Optional(str, column="Number")
    DocDate = Required(int, column="DocDate", size=64)

    def get_tree_name(self):
        return "[Документ] %s" % self.Name

    @property
    def Name(self):
        return self.Number

    @property
    def sp_own_type(self):
        return "FOUNDATION_DOC"


class DischargeSeries(db.Entity):
    _table_ = "DischargeSeries"

    mine_object = Required(MineObject, column="MOID", volatile=True)
    orig_sample_set = Required(OrigSampleSet, column="OSSID")
    foundation_document = Optional(FoundationDocument, column="FDID")

    RID = PrimaryKey(int, auto=True, column="RID")
    Name = Required(str, column="Name")
    Comment = Optional(str, column="Comment")
    StartMeasure = Required(int, column="StartMeasure", size=64)
    EndMeasure = Optional(int, column="EndMeasure", size=64)

    def get_tree_name(self):
        return "[Набор замеров] %s" % self.Name


class DischargeMeasurement(db.Entity):
    _table_ = "DischargeMeasurements"

    orig_sample_set = Required(OrigSampleSet, column="OSSID")

    RID = PrimaryKey(int, auto=True, column="RID")
    DschNumber = Required(str, column="DschNumber")
    SampleNumber = Required(str, column="SampleNumber")
    Diameter = Required(float, column="Diameter")
    Length = Required(float, column="Length")
    Weight = Required(float, column="Weight")
    RockType = Optional(str, column="RockType")
    PartNumber = Required(str, column="PartNumber")
    RTens = Required(float, column="RTens")
    Sensitivity = Required(float, column="Sensitivity")
    TP1_1 = Optional(float, column="TP1_1")
    TP1_2 = Optional(float, column="TP1_2")
    TP2_1 = Optional(float, column="TP2_1")
    TP2_2 = Optional(float, column="TP2_2")
    TR_1 = Optional(float, column="TR_1")
    TR_2 = Optional(float, column="TR_2")
    TS_1 = Optional(float, column="TS_1")
    TS_2 = Optional(float, column="TS_2")
    PWSpeed = Optional(float, column="PWSpeed")
    RWSpeed = Optional(float, column="RWSpeed")
    SWSpeed = Optional(float, column="SWSpeed")
    PuassonStatic = Optional(float, column="PuassonStatic")
    YungStatic = Optional(float, column="YungStatic")
    CoreDepth = Required(float, column="CoreDepth")
    E1 = Required(float, column="E1")
    E2 = Required(float, column="E2")
    E3 = Required(float, column="E3")
    E4 = Required(float, column="E4")
    Rotate = Required(float, column="Rotate")

    @property
    def sp_own_type(self):
        return None


class SuppliedData(db.Entity):
    _table_ = "SuppliedData"

    parts = Set("SuppliedDataPart")

    RID = PrimaryKey(int, auto=True, column="RID")
    OwnID = Required(int, column="OwnID")
    OwnType = Required(str, column="OwnType")
    Number = Optional(str, column="Number")
    Name = Required(str, column="Name")
    Comment = Optional(str, column="Comment")
    DataDate = Optional(int, column="DataDate", size=64)


class SuppliedDataPart(db.Entity):
    _table_ = "SuppliedDataParts"

    parent = Required(SuppliedData, column="SDID")

    RID = PrimaryKey(int, auto=True, column="RID")
    Name = Required(str, column="Name")
    Comment = Optional(str, column="Comment")
    DType = Required(str, column="DType")
    FileName = Required(str, column="FileName")
    DataContent = Required(bytes, column="DataContent", lazy=True)
    DataDate = Optional(int, column="DataDate", size=64)

    @property
    def sp_own_type(self):
        return None


class RockBurst(db.Entity):
    _table_ = "RockBursts"

    mine_object = Required(MineObject, column="MOID")
    rb_type = Required("RBType", column="RBTID")
    rb_causes = Set("RBCause")
    rb_signs = Set("RBSign")
    rb_prevent_actions = Set("RBPreventAction")
    rb_gsras_events = Set("RBGSRASEvent")
    rb_asksm_events = Set("RBASKSMEvent")

    RID = PrimaryKey(int, auto=True, column="RID")
    Number = Optional(str, column="Number")
    Comment = Optional(str, column="Comment")
    BurstDate = Required(int, column="BurstDate", size=64)
    IsDynamic = Required(bool, column="IsDynamic")
    BurstDepth = Optional(float, column="BurstDepth")
    LayerFrom = Optional(float, column="LayerFrom")
    LayerTo = Optional(float, column="LayerTo")
    MagistralFrom = Optional(float, column="MagistralFrom")
    MagistralTo = Optional(float, column="MagistralTo")
    HeightFrom = Optional(float, column="HeightFrom")
    HeightTo = Optional(float, column="HeightTo")
    Place = Optional(str, column="Place")
    OccrVolume = Optional(float, column="OccrVolume")
    OccrWeight = Optional(float, column="OccrWeight")
    OccrSound = Optional(float, column="OccrSound")
    OccrComment = Optional(float, column="OccrComment")

    def get_tree_name(self):
        return "[Горный удар] №%s %s" % (self.Number, self.mine_object.Name)

    @property
    def sp_own_type(self):
        return "ROCK_BURST"


class RBASKSMEvent(db.Entity):
    _table_ = "RBASKSMEvents"

    rock_burst = Required(RockBurst, column="RBID")

    RID = PrimaryKey(int, auto=True, column="RID")
    Date = Required(int, column="Date", size=64)
    X = Required(float, column="X")
    Y = Required(float, column="Y")
    Z = Required(float, column="Z")
    Energy = Optional(str, column="Energy")
    Comment = Optional(str, column="Comment")
    ASKSM_ID = Required(str, column="ASKSM_ID")


class RBGSRASEvent(db.Entity):
    _table_ = "RBGSRASEvents"

    rock_burst = Required(RockBurst, column="RBID")

    RID = PrimaryKey(int, auto=True, column="RID")
    Date = Required(int, column="Date", size=64)
    Latitude = Required(float, column="Latitude")
    Longitude = Required(float, column="Longitude")
    Depth = Required(float, column="Depth")
    Magnitude = Optional(float, column="Magnitude")
    Comment = Optional(str, column="Comment")
    GSRAS_ID = Required(str, column="GSRAS_ID")

    @property
    def sp_own_type(self):
        return None


class RBTypicalPreventAction(db.Entity):
    _table_ = "RBTypicalPreventActions"

    rb_prevent_actions = Set("RBPreventAction")

    RID = PrimaryKey(int, auto=True, column="RID")
    Name = Required(str, column="Name")
    Comment = Optional(str, column="Comment")

    @property
    def sp_own_type(self):
        return None


class RBTypicalSign(db.Entity):
    _table_ = "RBTypicalSigns"

    rb_signs = Set("RBSign")

    RID = PrimaryKey(int, auto=True, column="RID")
    Name = Required(str, column="Name")
    Comment = Optional(str, column="Comment")

    @property
    def sp_own_type(self):
        return None


class RBTypicalCause(db.Entity):
    _table_ = "RBTypicalCauses"

    rb_causes = Set("RBCause")

    RID = PrimaryKey(int, auto=True, column="RID")
    Name = Required(str, column="Name")
    Comment = Optional(str, column="Comment")

    @property
    def sp_own_type(self):
        return None


class RBCause(db.Entity):
    _table_ = "RBCauses"

    rock_burst = Required(RockBurst, column="RBID")
    rb_typical_cause = Required(RBTypicalCause, column="RBCID")

    RID = PrimaryKey(int, auto=True, column="RID")

    @property
    def sp_own_type(self):
        return None


class RBSign(db.Entity):
    _table_ = "RBSigns"

    rb_typical_sign = Required(RBTypicalSign, column="RBSID")
    rock_burst = Required(RockBurst, column="RBID")

    RID = PrimaryKey(int, auto=True, column="RID")

    @property
    def sp_own_type(self):
        return None


class RBType(db.Entity):
    _table_ = "RBTypes"

    rock_bursts = Set("RockBurst")

    RID = PrimaryKey(int, auto=True, column="RID")
    Name = Required(str, column="Name")
    Comment = Optional(str, column="Comment")

    @property
    def sp_own_type(self):
        return None


class RBPreventAction(db.Entity):
    _table_ = "RBPreventActions"

    rb_typical_prevent_action = Required(RBTypicalPreventAction, column="RBPAID")
    rock_burst = Required(RockBurst, column="RBID")

    RID = PrimaryKey(int, auto=True, column="RID")
    ActDate = Optional(int, column="ActDate", size=64)

    @property
    def sp_own_type(self):
        return None


class CoreBoxStorage(db.Entity):
    _table_ = "CoreBoxStorage"

    orig_sample_set = Required(OrigSampleSet, column="OSSID")

    BoxNumber = Required(str, column="BoxNumber")
    PartNumber = PrimaryKey(str, column="PartNumber")
    StartPosition = Required(int, column="StartPosition")
    EndPosition = Required(int, column="EndPosition")

    @property
    def sp_own_type(self):
        return None


class Petrotype(db.Entity):
    _table_ = "Petrotypes"

    petrotype_structs = Set("PetrotypeStruct")

    RID = PrimaryKey(int, auto=True, column="RID")
    Name = Required(str, column="Name")
    Comment = Optional(str, column="Comment")

    @property
    def sp_own_type(self):
        return None


class PetrotypeStruct(db.Entity):
    _table_ = "PetrotypeStructs"

    petrotype = Required(Petrotype, column="PTID")
    pm_sample_sets = Set("PMSampleSet")

    RID = PrimaryKey(int, auto=True, column="RID")
    Name = Required(str, column="Name")
    Comment = Optional(str, column="Comment")

    @property
    def sp_own_type(self):
        return None


class PMTestSeries(db.Entity):
    _table_ = "PMTestSeries"

    foundation_document = Optional(FoundationDocument, column="FDID")
    pm_sample_sets = Set("PMSampleSet")

    RID = PrimaryKey(int, auto=True, column="RID")
    Number = Required(str, column="Number")
    Comment = Optional(str, column="Comment")
    Location = Optional(str, column="Location")

    @property
    def Name(self):
        return self.Number

    def get_tree_name(self):
        return "[Набор испытаний] " + self.Name

    @property
    def sp_own_type(self):
        return "PM_TEST_SERIES"


class PMSampleSet(db.Entity):
    _table_ = "PMSampleSets"

    mine_object = Required(MineObject, column="MOID")
    pm_test_series = Required(PMTestSeries, column="TSID")
    petrotype_struct = Required(PetrotypeStruct, column="PTSID")
    pm_samples = Set("PMSample")
    pm_user_properties = Set("PmSampleSetUsedProperties")

    RID = PrimaryKey(int, auto=True, column="RID")
    Number = Required(str, column="Number")
    Comment = Optional(str, column="Comment")
    SetDate = Optional(int, column="SetDate", size=64)
    TestDate = Optional(int, column="TestDate", size=64)
    CrackDescr = Optional(str, column="CrackDescr")
    RealDetails = Required(bool, column="RealDetails")
    SampleCount = Optional(int, column="SampleCount")

    def get_tree_name(self):
        return "[Проба] " + self.Name

    @property
    def Name(self):
        return self.Number

    @property
    def sp_own_type(self):
        return "PM_SAMPLE_SET"


class PMSample(db.Entity):
    _table_ = "PMSamples"

    pm_sample_set = Required(PMSampleSet, column="SSID")
    orig_sample_set = Required(OrigSampleSet, column="OSSID")
    pm_sample_property_values = Set("PmSamplePropertyValue")

    RID = PrimaryKey(int, auto=True, column="RID")
    Number = Required(str, column="Number")
    SetDate = Required(int, column="SetDate", size=64)
    StartPosition = Required(float, column="StartPosition")
    EndPosition = Optional(float, column="EndPosition")
    BoxNumber = Optional(str, column="BoxNumber")
    Length1 = Optional(float, column="Length1")
    Length2 = Optional(float, column="Length2")
    Height = Optional(float, column="Height")
    MassAirDry = Optional(float, column="MassAirDry")

    @property
    def Name(self):
        return self.Number

    def get_tree_name(self):
        return "[Образец] " + self.Name

    @property
    def sp_own_type(self):
        return None


class PmTestMethod(db.Entity):
    _table_ = "PMTestMethods"

    pm_sample_property_values = Set("PmSamplePropertyValue")
    pm_used_properties = Set("PmSampleSetUsedProperties")

    RID = PrimaryKey(int, auto=True, column="RID")
    Name = Required(str, column="Name")
    Comment = Optional(str, column="Comment")
    StartDate = Required(int, column="StartDate", size=64)
    EndDate = Optional(int, column="EndDate", size=64)
    Analytic = Optional(bool, column="Analytic")

    @property
    def sp_own_type(self):
        return None


class PmTestEquipment(db.Entity):
    _table_ = "PMTestEquipment"

    pm_used_properties = Set("PmSampleSetUsedProperties")

    RID = PrimaryKey(int, auto=True, column="RID")
    Name = Required(str, column="Name")
    Comment = Optional(str, column="Comment")
    SerialNo = Optional(str, column="SerialNo")
    StartDate = Required(int, column="StartDate", size=64)

    @property
    def sp_own_type(self):
        return None


class PmPropertyClass(db.Entity):
    _table_ = "PMPropertyClasses"

    pm_properties = Set("PmProperty")

    RID = PrimaryKey(int, auto=True, column="RID")
    Name = Required(str, column="Name")
    Comment = Optional(str, column="Comment")

    @property
    def sp_own_type(self):
        return None


class PmProperty(db.Entity):
    _table_ = "PMProperties"

    pm_property_class = Required(PmPropertyClass, column="PCID")
    pm_sample_property_values = Set("PmSamplePropertyValue")
    pm_used_properties = Set("PmSampleSetUsedProperties")

    RID = PrimaryKey(int, auto=True, column="RID")
    Name = Required(str, column="Name")
    Comment = Optional(str, column="Comment")
    Code = Optional(str, column="Code")
    Unit = Optional(str, column="Unit")

    @property
    def sp_own_type(self):
        return None


class PmSamplePropertyValue(db.Entity):
    _table_ = "PMSamplePropertyValues"

    pm_sample = Required(PMSample, column="RSID")
    pm_test_method = Required(PmTestMethod, column="TMID")
    pm_property = Required(PmProperty, column="PRID")

    RID = PrimaryKey(int, auto=True, column="RID")
    Value = Required(float, column="Value")

    @property
    def sp_own_type(self):
        return None


class PmPerformedTask(db.Entity):
    _table_ = "PMPerformedTasks"

    RID = PrimaryKey(int, auto=True, column="RID")
    Name = Required(str, column="Name")
    Comment = Optional(str, column="Comment")

    @property
    def sp_own_type(self):
        return None


class PmSampleSetUsedProperties(db.Entity):
    _table_ = "PMSampleSetUsedProperies"

    pm_sample_set = Required(PMSampleSet, column="PMSSID")
    pm_property = Required(PmProperty, column="PMPID")
    pm_method = Required(PmTestMethod, column="PMTMID")
    pm_equipment = Optional(PmTestEquipment, column="PMEQID")

    RID = PrimaryKey(int, auto=True, column="RID")

    @property
    def Name(self):
        return self.pm_property.Name

    @property
    def sp_own_type(self):
        return None
