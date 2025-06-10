import os

import wx

from pony.orm import db_session, commit, select
from src.ui.icon import get_icon
from src.ui.task import Task, TaskJob
from src.datetimeutil import encode_date
from rapidfuzz import fuzz, process
from src.database import (
    PMTestSeries,
    PMSampleSet,
    PMSample,
    PmSamplePropertyValue,
    PmTestMethod,
    PmTestEquipment,
    FoundationDocument,
    BoreHole,
    OrigSampleSet,
    MineObject,
    PmTaskMethodForSample,
    PmPerformedTask,
    PmProperty,
)
import time

PROPS_STARTED_INDEX = 24
HANDMADE_PROPS = [
    ("Масса в естественно-влажном состоянии", 19),
    ("Масса в воде", 20),
    ("Масса в водонасыщенном состоянии", 21),
    ("Масса в водонасыщенном состоянии в воде", 22),
    ("Масса в сухом состоянии", 23),
]
PROPS = [
    ("Естественная влажность", 24, 25, 26),
    ("Водопоглощение", 27, 28, 29),
    ("Плотность", 30, 31, 32),
    ("Удельный вес", 33, 34, 35),
    ("Разрушающая нагрузка при одноосном сжатии", 36, 38, 39),
    ("Предел прочности при одноосном сжатии", 37, 38, 39),
    ("Разрушающая нагрузка при одноосном растяжении", 40, 42, 43),
    ("Предел прочности при одноосном растяжении", 41, 42, 43),
    ("Коэффициент хрупкости", 44, 45, 46),
    ("Модуль упругости", 47, 48, 49),
    ("Модуль деформации", 50, 51, 52),
    ("Модуль спада", 53, 54, 55),
    ("Коэффициент Пуассона", 56, 57, 58),
    ("Коэффициент поперечных деформаций", 59, 60, 61),
    ("Коэффициент удароопасности", 62, 63, 64),
    ("Коэффициент крепости по М.М. Протодьяконову", 65, 66, 67),
    ("Коэффициент бокового распора", 68, 69, 70),
    ("Модуль сдвига", 71, 72, 73),
    ("Боковое давление", 74, 77, 78),
    ("Дифференциальная прочность", 75, 77, 78),
    ("Предел прочности при объемном сжатии", 76, 77, 78),
    ("Показатель абразивности", 79, 80, 81),
]
BORE_HOLE_FIELD = 0
SAMPLE_TYPE_FIELD = 0
TEST_SERIES_FIELD = 0
DOC_DATE_FIELD = 0
SAMPLE_SET_FIELD = 0
MINE_OBJECT_FIELD = 0
SAMPLE_FIELD = 0
LENGTH1_FIELD = 0
LENGTH2_FIELD = 0
HEIGHT_FIELD = 0
MASS_AIR_DRY_FIELD = 0
START_POSITION_FIELD = 0
END_POSITION_FIELD = 0
BOX_NUMBER_FIELD = 0
SAMPLE_FIELDS = [("Набор испытаний", 1), ("Проба", 9), ("Образец", 14)]


class DoImportTask(TaskJob):
    def __init__(self, path):
        super().__init__()
        self.path = path

    @db_session
    def run(self):
        import pandas as pd

        pm_samples = select(s for s in PMSample).prefetch(PMSample.pm_sample_set, PMSampleSet.pm_test_series)[:]
        pm_properties = select(s for s in PmProperty)[:]
        pm_methods = select(s for s in PmTestMethod)[:]
        pm_equipments = select(s for s in PmTestEquipment)[:]
        pm_test_series = select(s for s in PMTestSeries)[:]
        pm_sample_sets = select(s for s in PMSampleSet)[:]
        orig_sample_sets = select(s for s in OrigSampleSet)[:]
        pm_property_values = select(s for s in PmSamplePropertyValue)[:]
        documents = select(s for s in FoundationDocument)[:]
        mine_objects = select(s for s in MineObject)[:]

        threshold = 90

        def find_test_series(name): ...

        def find_sample_set(test_series, name): ...

        def find_sample(sample_set, name):
            global pm_samples
            results = process.extract(
                name, [a.Number for a in pm_samples], scorer=fuzz.ratio, limit=1000, score_cutoff=threshold
            )
            for find_name, score, index in results:
                result = pm_samples[index]
                if (
                    result.pm_sample_set == sample_set
                    and fuzz.ratio(result.pm_sample_set.pm_test_series.Name, test_series_name) >= threshold
                ):
                    return result
            return None

        def find_orig_sample_set(mine_object, name, _type): ...

        def find_property(name):
            global pm_properties
            r = process.extractOne(name, [a.Name for a in pm_properties], scorer=fuzz.ratio, score_cutoff=threshold)
            if r is None:
                return None
            return pm_properties[r[2]]

        def find_property_value(sample, property, method): ...

        def find_method(name):
            global pm_methods
            r = process.extractOne(name, [a.Name for a in pm_methods], scorer=fuzz.ratio, score_cutoff=threshold)
            if r is None:
                return None
            return pm_methods[r[2]]

        def find_equipment(name):
            global pm_equipments
            r = process.extractOne(name, [a.Name for a in pm_equipments], scorer=fuzz.ratio, score_cutoff=threshold)
            if r is None:
                return None
            return pm_equipments[r[2]]

        def find_document(name, date=None): ...

        def find_mine_object(name): ...

        column_list = []
        df_column = pd.read_excel(self.path, 0).columns
        for i in df_column:
            column_list.append(i)
        converter = {col: str for col in column_list}
        df = pd.read_excel(self.path, sheet_name=0, header=0, converters=converter)
        rows = []

        for index, row in enumerate(df.iterrows()):
            if index == 0:
                continue

            # Выбрать столбцы для серии испытаний найти в БД. Найти в бд договор с таким номером если не выдать ошибку. Если есть создать и связать
            # Выбрать столбцы для пробы найти в бд или создать и связать с серией испытаний
            # Выбрать столбцы для набора образцов (скважина, штуф или дисперсный материал) найти в бд или выдать ошибку
            # Выбрать столбцы для образца найти в БД или создать связать с пробой и набором образцов
            # Выбрать столбцы для handmade props найти свойство Физическая энциклопедия и связать значение если нет выдать ошибку
            # Выбрать другие свойства с методами и используемым оборудованием связать с образцом методом испытаний и используемым оборудованием если метода или используемого оборудования нет то выдать ошибку

            test_series_name = "№" + row[1][TEST_SERIES_FIELD] + " " + row[1][DOC_DATE_FIELD]
            test_series = find_test_series(test_series_name)
            if test_series is None:
                document = find_document(row[1][TEST_SERIES_FIELD])
                if document is None:
                    raise Exception("Документ №%s отсутствует в базе данных." % row[1][TEST_SERIES_FIELD])
                test_series = PMTestSeries(Number=test_series_name, foundation_document=document)

            sample_set = find_sample_set(test_series, row[1][SAMPLE_SET_FIELD])
            if sample_set is None:
                mine_object = find_mine_object(row[1][MINE_OBJECT_FIELD])
                if mine_object is None:
                    raise Exception("Месторождение %s отсутствует в базе данных." % row[1][MINE_OBJECT_FIELD])
                sample_set = PMSampleSet(
                    pm_test_series=test_series,
                    mine_object=mine_object,
                    Number=row[1][SAMPLE_SET_FIELD],
                    RealDetails=True,
                )

            sample = find_sample(sample_set, row[1][SAMPLE_FIELD])
            if sample is None:
                if row[1][SAMPLE_TYPE_FIELD] == "Керн":
                    name = row[1][BORE_HOLE_FIELD]
                    _type = "CORE"
                else:
                    name = test_series_name + "" + row[1][SAMPLE_SET_FIELD]
                    if row[1][SAMPLE_TYPE_FIELD] == "Штуф":
                        _type = "STUFF"
                    else:
                        _type = "DISPECE"
                orig_sample_set = find_orig_sample_set(sample_set.mine_object, name, _type)
                if orig_sample_set is None:
                    raise Exception("Набор образцов %s отсутствует в базе данных." % name)

                sample = PMSample(
                    pm_sample_set=sample_set,
                    orig_sample_set=orig_sample_set,
                    Number=str(row[1][SAMPLE_SET_FIELD]),
                    SetDate=encode_date(row[1][DOC_DATE_FIELD]),
                    Length1=float(row[1][LENGTH1_FIELD]),
                    Length2=float(row[1][LENGTH2_FIELD]),
                    Height=float(row[1][HEIGHT_FIELD]),
                    MassAirDry=float(row[1][MASS_AIR_DRY_FIELD]),
                )

                if _type == "CORE":
                    sample.StartPosition = float(row[1][START_POSITION_FIELD])
                    sample.EndPosition = float(row[1][END_POSITION_FIELD])
                    sample.BoxNumber = float(row[1][BOX_NUMBER_FIELD])

            method_for_handmade_props = find_method("Физическая энцклопедия")
            for prop_name, prop_index in HANDMADE_PROPS:
                prop = find_property(prop_name)
                if prop is None:
                    raise Exception("Свойство %s отсутствует в базе данных." % prop_name)
                value = PmSamplePropertyValue(
                    pm_sample=sample,
                    pm_test_method=method_for_handmade_props,
                    pm_property=prop,
                    Value=float(row[1][1][prop_index]),
                )

            for prop_name, prop_value_index, prop_method_index, prop_equipment_index in PROPS:
                prop = find_property(prop_name)
                if prop is None:
                    raise Exception("Свойство %s отсутствует в базе данных." % prop_name)
                prop_method = find_method(row[1][1][prop_method_index])
                if prop_method is None:
                    raise Exception("Метод %s отсутствует в базе данных." % row[1][1][prop_method_index])
                prop_equipment = find_equipment(row[1][1][prop_equipment_index])
                if prop_equipment is None:
                    raise Exception("Оборудование %s отсутствует в базе данных." % row[1][1][prop_equipment_index])
                if (
                    PmTaskMethodForSample.get(
                        pm_sample=sample, pm_method=prop_method, pm_performed_task=PmPerformedTask[1]
                    )
                    is None
                ):
                    PmTaskMethodForSample(pm_sample=sample, pm_method=prop_method, pm_performed_task=PmPerformedTask[1])
                value = PmSamplePropertyValue(
                    pm_sample=sample, pm_test_method=prop_method, pm_property=prop, Value=float(row[1][1][prop_index])
                )

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
        self.task = Task("Импорт замеров...", "Идет импорт замеров", DoImportTask(), self)
        self.task.then(self.on_import_resolve, self.on_import_reject)
        self.task.run()

    def on_import_resolve(self, data): ...

    def on_import_reject(self, e):
        raise e
