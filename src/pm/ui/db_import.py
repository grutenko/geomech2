import io
import os
import warnings
from dataclasses import dataclass
from typing import List

import wx
from pony.orm import commit, db_session, select
from rapidfuzz import fuzz, process

from src.database import (
    FoundationDocument,
    MineObject,
    OrigSampleSet,
    Petrotype,
    PetrotypeStruct,
    PmPerformedTask,
    PmProperty,
    PMSample,
    PmSamplePropertyValue,
    PMSampleSet,
    PmTaskMethodForSample,
    PmTestEquipment,
    PmTestMethod,
    PMTestSeries,
)
from src.datetimeutil import encode_date
from src.ui.icon import get_icon
from src.ui.task import Task, TaskJob

warnings.filterwarnings("ignore", category=DeprecationWarning)

HANDMADE_PROPS = [
    "Масса в естественно-влажном состоянии",
    "Масса в воде",
    "Масса в водонасыщенном состоянии",
    "Масса в водонасыщенном состоянии в воде",
    "Масса в сухом состоянии",
]
PROPS = [
    "Естественная влажность",
    "Водопоглощение",
    "Плотность",
    "Удельный вес",
    "Разрушающая нагрузка при одноосном сжатии",
    "Предел прочности при одноосном сжатии",
    "Разрушающая нагрузка при одноосном растяжении",
    "Предел прочности при одноосном растяжении",
    "Коэффициент хрупкости",
    "Модуль упругости",
    "Модуль деформации",
    "Модуль спада",
    "Коэффициент Пуассона",
    "Коэффициент поперечных деформаций",
    "Коэффициент удароопасности",
    "Коэффициент крепости по М.М. Протодьяконову",
    "Коэффициент бокового распора",
    "Модуль сдвига",
    "Боковое давление",
    "Дифференциальная прочность",
    "Предел прочности при объемном сжатии",
    "Показатель абразивности",
]


@dataclass
class PmDbPropertyHeader:
    name: str
    field: int
    method: int
    equipment: int
    is_handmade_property: bool = False


@dataclass
class PmDbHeader:
    test_series_field: int
    doc_date_field: int
    sample_set_field: int
    mine_object_field: int
    sample_set_field: int
    bore_hole_field: int
    box_number_field: int
    depth_start_field: int
    depth_end_field: int
    petrotype_field: int
    petrotype_struct_field: int
    sample_type_field: int
    sample_field: int
    length1_field: int
    length2_field: int
    height_field: int
    mass_air_dry_field: int
    properties: List[PmDbPropertyHeader]


def find_header(df) -> PmDbHeader:
    h = PmDbHeader(
        test_series_field=df.columns.get_loc("Отчет по х/д №"),
        doc_date_field=df.columns.get_loc("Дата заключения х/д"),
        sample_set_field=df.columns.get_loc("№ пробы"),
        mine_object_field=df.columns.get_loc("Месторождение"),
        bore_hole_field=df.columns.get_loc("№ скважины"),
        box_number_field=df.columns.get_loc("№ ящиков"),
        depth_start_field=df.columns.get_loc("№ ящиков") + 1,
        depth_end_field=df.columns.get_loc("№ ящиков") + 2,
        sample_type_field=df.columns.get_loc("Тип каменного материала"),
        sample_field=df.columns.get_loc("№ образца"),
        length1_field=df.columns.get_loc("Диаметр, см"),
        length2_field=df.columns.get_loc("Высота, см"),
        height_field=df.columns.get_loc("Высота, см"),
        petrotype_field=df.columns.get_loc("Петротип"),
        petrotype_struct_field=df.columns.get_loc("Описание структуры петротипа"),
        mass_air_dry_field=df.columns.get_loc("Масса в воздушно-сухом состоянии, г"),
        properties=[],
    )
    for prop_name in HANDMADE_PROPS:
        h.properties.append(
            PmDbPropertyHeader(
                name=prop_name, field=df.columns.get_loc(prop_name), method=-1, equipment=-1, is_handmade_property=True
            )
        )
    return h


class DoImportTask(TaskJob):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.changed_objects = []

    @db_session
    def run(self):
        log = io.StringIO()
        self.do_import(log)

    def do_import(self, log):
        import pandas as pd

        pm_samples = list(select(s for s in PMSample).prefetch(PMSample.pm_sample_set, PMSampleSet.pm_test_series)[:])
        pm_properties = list(select(s for s in PmProperty)[:])
        pm_methods = list(select(s for s in PmTestMethod)[:])
        pm_equipments = list(select(s for s in PmTestEquipment)[:])
        pm_test_series = list(select(s for s in PMTestSeries)[:])
        pm_sample_sets = list(select(s for s in PMSampleSet)[:])
        pm_property_values = list(select(s for s in PmSamplePropertyValue)[:])
        petrotypes = list(select(s for s in Petrotype)[:])
        petrotype_structs = list(select(s for s in PetrotypeStruct)[:])

        threshold = 90

        def find_test_series(name):
            r = process.extractOne(name, [a.Name for a in pm_test_series], scorer=fuzz.ratio, score_cutoff=threshold)
            if r is None:
                return None
            return pm_test_series[r[2]]

        def find_sample_set(test_series, name):
            results = process.extract(
                name, [a.Number for a in pm_sample_sets], scorer=fuzz.ratio, limit=1000, score_cutoff=100
            )
            for _, _, index in results:
                result = pm_sample_sets[index]
                if result.pm_test_series == test_series:
                    return result
            return None

        def find_sample(sample_set, name):
            results = process.extract(
                name, [a.Number for a in pm_samples], scorer=fuzz.ratio, limit=1000, score_cutoff=100
            )
            for _, _, index in results:
                result = pm_samples[index]
                if result.pm_sample_set == sample_set:
                    return result
            return None

        @db_session
        def find_orig_sample_set(mine_object, name, _type):
            return select(
                o for o in OrigSampleSet if o.SampleType == _type and o.mine_object == mine_object and name in o.Number
            ).first()

        def find_property(name):
            r = process.extractOne(name, [a.Name for a in pm_properties], scorer=fuzz.ratio, score_cutoff=threshold)
            if r is None:
                return None
            return pm_properties[r[2]]

        def find_property_value(sample, property, method):
            for prop_value in pm_property_values:
                if (
                    prop_value.pm_sample == sample
                    and prop_value.pm_property == property
                    and prop_value.pm_test_method == method
                ):
                    return prop_value

            return None

        def find_method(name):
            r = process.extractOne(name, [a.Name for a in pm_methods], scorer=fuzz.ratio, score_cutoff=threshold)
            if r is None:
                return None
            return pm_methods[r[2]]

        def find_equipment(name):
            r = process.extractOne(name, [a.Name for a in pm_equipments], scorer=fuzz.ratio, score_cutoff=threshold)
            if r is None:
                return None
            return pm_equipments[r[2]]

        def find_document(name, date=None):
            return select(o for o in FoundationDocument if name == o.Number).first()

        def find_petrotype(name):
            r = process.extractOne(name, [a.Name for a in petrotypes], scorer=fuzz.ratio, score_cutoff=threshold)
            if r is None:
                return None
            return petrotypes[r[2]]

        def find_petrotype_struct(name, petrotype):
            r = process.extractOne(
                name,
                [a.Name for a in petrotype_structs if a.petrotype == petrotype],
                scorer=fuzz.ratio,
                score_cutoff=threshold,
            )
            if r is None:
                return None
            return petrotype_structs[r[2]]

        @db_session
        def find_mine_object(name):
            return select(o for o in MineObject if name in o.Name and o.Type == "FIELD").first()

        column_list = []
        df_column = pd.read_excel(self.path, 0).columns
        for i in df_column:
            column_list.append(i)
        converter = {col: str for col in column_list}
        df = pd.read_excel(self.path, sheet_name=0, header=0, converters=converter)

        hdr = find_header(df)

        for index, row in enumerate(df.iterrows()):
            if index == 0:
                continue

            self.set_progress(index, df.shape[0])

            # Выбрать столбцы для серии испытаний найти в БД. Найти в бд договор с таким номером если не выдать ошибку. Если есть создать и связать
            # Выбрать столбцы для пробы найти в бд или создать и связать с серией испытаний
            # Выбрать столбцы для набора образцов (скважина, штуф или дисперсный материал) найти в бд или выдать ошибку
            # Выбрать столбцы для образца найти в БД или создать связать с пробой и набором образцов
            # Выбрать столбцы для handmade props найти свойство Физическая энциклопедия и связать значение если нет выдать ошибку
            # Выбрать другие свойства с методами и используемым оборудованием связать с образцом методом испытаний и используемым оборудованием если метода или используемого оборудования нет то выдать ошибку

            if len(str(row[1][hdr.test_series_field])) == 0 or pd.isna(row[1][hdr.test_series_field]):
                continue

            test_series_name = (
                "№"
                + str(row[1][hdr.test_series_field])
                + " "
                + ".".join(reversed(str(row[1][hdr.doc_date_field]).split(" ")[0].split("-")))
            )
            test_series = find_test_series(test_series_name)
            if test_series is None:
                document = find_document("№" + str(row[1][hdr.test_series_field]))
                if document is None:
                    raise Exception("Документ №%s отсутствует в базе данных." % row[1][hdr.test_series_field])
                test_series = PMTestSeries(Number=test_series_name, foundation_document=document)
                pm_test_series.append(test_series)

            petrotype = find_petrotype(row[1][hdr.petrotype_field])
            if petrotype is None:
                petrotype = Petrotype(Name=row[1][hdr.petrotype_field])
                petrotypes.append(petrotype)

            petrotype_struct = find_petrotype_struct(row[1][hdr.petrotype_struct_field], petrotype)
            if petrotype_struct is None:
                petrotype_struct = PetrotypeStruct(Name=row[1][hdr.petrotype_struct_field], petrotype=petrotype)
                petrotype_structs.append(petrotype_struct)

            sample_set = find_sample_set(test_series, row[1][hdr.sample_set_field])
            if sample_set is None:
                mine_object = find_mine_object(row[1][hdr.mine_object_field])
                if mine_object is None:
                    raise Exception("Месторождение %s отсутствует в базе данных." % row[1][hdr.mine_object_field])
                sample_set = PMSampleSet(
                    pm_test_series=test_series,
                    mine_object=mine_object,
                    Number=row[1][hdr.sample_set_field],
                    RealDetails=True,
                    petrotype_struct=petrotype_struct,
                )
                pm_sample_sets.append(sample_set)

            sample = find_sample(sample_set, row[1][hdr.sample_field])
            if sample is None:
                if row[1][hdr.sample_type_field] == "Керн":
                    name = row[1][hdr.bore_hole_field]
                    _type = "CORE"
                else:
                    name = test_series_name
                    if row[1][hdr.sample_type_field] == "Штуф":
                        _type = "STUFF"
                    else:
                        _type = "DISPECE"
                orig_sample_set = find_orig_sample_set(sample_set.mine_object, name, _type)
                if orig_sample_set is None:
                    raise Exception("Набор образцов %s отсутствует в базе данных." % name)

                log.write("Create %s - %s - %s\n" % (test_series.Name, sample_set.Number, row[1][hdr.sample_field]))

                sample = PMSample(
                    pm_sample_set=sample_set,
                    orig_sample_set=orig_sample_set,
                    Number=row[1][hdr.sample_field],
                    SetDate=encode_date(row[1][hdr.doc_date_field]),
                    Length1=(
                        float(row[1][hdr.length1_field])
                        if len(row[1][hdr.length1_field]) > 0 and row[1][hdr.length1_field] != "-"
                        else None
                    ),
                    Length2=(
                        float(row[1][hdr.length2_field])
                        if len(row[1][hdr.length2_field]) > 0 and row[1][hdr.length2_field] != "-"
                        else None
                    ),
                    Height=(
                        float(row[1][hdr.height_field])
                        if len(row[1][hdr.height_field]) > 0 and row[1][hdr.height_field] != "-"
                        else None
                    ),
                    MassAirDry=(
                        float(row[1][hdr.mass_air_dry_field])
                        if len(row[1][hdr.mass_air_dry_field]) > 0 and row[1][hdr.mass_air_dry_field] != "-"
                        else None
                    ),
                )

                if _type == "CORE":
                    sample.StartPosition = float(row[1][hdr.depth_start_field])
                    sample.EndPosition = float(row[1][hdr.depth_end_field])
                    sample.BoxNumber = str(row[1][hdr.box_number_field])

                pm_samples.append(sample)
            else:
                log.write("Finded %s - %s - %s\n" % (test_series.Name, sample_set.Number, row[1][hdr.sample_field]))

            method_for_handmade_props = find_method("Физическая энцклопедия")
            for prop_name, prop_index in HANDMADE_PROPS:
                if len(row[1][prop_index]) == 0 or row[1][prop_index].strip() == "-":
                    continue

                prop = find_property(prop_name)
                if prop is None:
                    raise Exception("Свойство %s отсутствует в базе данных." % prop_name)

                if PmTaskMethodForSample.get(pm_sample=sample, pm_method=method_for_handmade_props) is None:
                    PmTaskMethodForSample(
                        pm_sample=sample, pm_method=method_for_handmade_props, pm_performed_task=PmPerformedTask[1]
                    )
                    print("Handmade PmTaskMethodForSample %s, %s" % (str(sample), str(method_for_handmade_props)))

                value = find_property_value(sample, prop, method_for_handmade_props)
                if value is None:
                    value = PmSamplePropertyValue(
                        pm_sample=sample,
                        pm_test_method=method_for_handmade_props,
                        pm_property=prop,
                        Value=float(row[1][prop_index]),
                    )
                    pm_property_values.append(value)
                else:
                    value.Value = float(row[1][prop_index])

            for prop_name, prop_value_index, prop_method_index, prop_equipment_index in PROPS:
                if len(row[1][prop_value_index]) == 0 or row[1][prop_value_index].strip() == "-":
                    continue

                prop = find_property(prop_name)
                if prop is None:
                    raise Exception("Свойство %s отсутствует в базе данных." % prop_name)
                prop_method = find_method(row[1][prop_method_index])
                if prop_method is None:
                    raise Exception("Метод %s отсутствует в базе данных." % row[1][prop_method_index])
                if len(row[1][prop_equipment_index]) == 0 or row[1][prop_equipment_index].strip() == "-":
                    prop_equipment = None
                else:
                    prop_equipment = find_equipment(row[1][prop_equipment_index])
                    if prop_equipment is None:
                        raise Exception("Оборудование %s отсутствует в базе данных." % row[1][prop_equipment_index])
                if PmTaskMethodForSample.get(pm_sample=sample, pm_method=prop_method) is None:
                    PmTaskMethodForSample(pm_sample=sample, pm_method=prop_method, pm_performed_task=PmPerformedTask[1])
                    print("PmTaskMethodForSample %s, %s" % (str(sample), str(prop_method)))

                value = find_property_value(sample, prop, prop_method)
                if value is None:
                    value = PmSamplePropertyValue(
                        pm_sample=sample,
                        pm_test_method=prop_method,
                        pm_property=prop,
                        Value=float(row[1][prop_value_index]),
                    )
                    pm_property_values.append(value)
                else:
                    value.Value = float(row[1][prop_value_index])

        commit()


class FmsImportDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.SetIcon(wx.Icon(get_icon("logo")))
        self.SetTitle("Импорт данных")
        self.SetSize((600, 160))
        sz = wx.BoxSizer(wx.VERTICAL)
        sz_in = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, label="Файл БД ФМС")
        sz_in.Add(label, 0, wx.EXPAND)
        self.file = wx.FilePickerCtrl(self, message="Выберите файл", wildcard="*.xlsx;*.xls")
        self.file.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_file_picker_changed)
        sz_in.Add(self.file, 0, wx.EXPAND | wx.BOTTOM, border=10)
        sz.Add(sz_in, 1, wx.EXPAND | wx.ALL, 10)
        line = wx.StaticLine(self)
        sz.Add(line, 0, wx.EXPAND)
        sz_btn = wx.StdDialogButtonSizer()
        self.ok_btn = wx.Button(self, wx.ID_OK, "Импортировать")
        self.ok_btn.SetBitmap(get_icon("import"))
        self.ok_btn.Disable()
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_import)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        sz_btn.Add(self.ok_btn)
        sz.Add(sz_btn, 0, wx.ALIGN_RIGHT | wx.ALL, border=10)
        self.SetSizer(sz)
        self.Layout()

    def on_close(self, event):
        self.EndModal(wx.ID_CANCEL)

    def on_file_picker_changed(self, event):
        self.ok_btn.Enable(os.path.exists(self.file.GetPath()))

    def on_import(self, event):
        self.task = Task("Импорт замеров...", "Идет импорт замеров", DoImportTask(self.file.GetPath()), self)
        self.task.then(self.on_import_resolve, self.on_import_reject)
        self.task.run()

    def on_import_resolve(self, data):
        wx.MessageBox("Импорт успешно завершено", "Импорт успешно завершен.")

    def on_import_reject(self, e):
        raise e
