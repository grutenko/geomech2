import os
import io
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
    OrigSampleSet,
    MineObject,
    PmTaskMethodForSample,
    PmPerformedTask,
    PmProperty,
)

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

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
BORE_HOLE_FIELD = 5
SAMPLE_TYPE_FIELD = 13
TEST_SERIES_FIELD = 0
DOC_DATE_FIELD = 1
SAMPLE_SET_FIELD = 9
MINE_OBJECT_FIELD = 4
SAMPLE_FIELD = 14
LENGTH1_FIELD = 15
LENGTH2_FIELD = 16
HEIGHT_FIELD = 17
MASS_AIR_DRY_FIELD = 18
START_POSITION_FIELD = 7
END_POSITION_FIELD = 8
BOX_NUMBER_FIELD = 6
SAMPLE_FIELDS = [("Набор испытаний", 1), ("Проба", 9), ("Образец", 14)]


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

        @db_session
        def find_mine_object(name):
            return select(o for o in MineObject if name in o.Name and o.Type == "FIELD").first()

        column_list = []
        df_column = pd.read_excel(self.path, 0).columns
        for i in df_column:
            column_list.append(i)
        converter = {col: str for col in column_list}
        df = pd.read_excel(self.path, sheet_name=0, header=0, converters=converter)

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

            if len(str(row[1][TEST_SERIES_FIELD])) == 0 or pd.isna(row[1][TEST_SERIES_FIELD]):
                continue

            test_series_name = (
                "№"
                + str(row[1][TEST_SERIES_FIELD])
                + " "
                + ".".join(reversed(str(row[1][DOC_DATE_FIELD]).split(" ")[0].split("-")))
            )
            test_series = find_test_series(test_series_name)
            if test_series is None:
                document = find_document(row[1][TEST_SERIES_FIELD])
                if document is None:
                    raise Exception("Документ №%s отсутствует в базе данных." % row[1][TEST_SERIES_FIELD])
                test_series = PMTestSeries(Number=test_series_name, foundation_document=document)
                pm_test_series.append(test_series)

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
                pm_sample_sets.append(sample_set)

            sample = find_sample(sample_set, row[1][SAMPLE_FIELD])
            if sample is None:
                if row[1][SAMPLE_TYPE_FIELD] == "Керн":
                    name = row[1][BORE_HOLE_FIELD]
                    _type = "CORE"
                else:
                    name = test_series_name
                    if row[1][SAMPLE_TYPE_FIELD] == "Штуф":
                        _type = "STUFF"
                    else:
                        _type = "DISPECE"
                orig_sample_set = find_orig_sample_set(sample_set.mine_object, name, _type)
                if orig_sample_set is None:
                    raise Exception("Набор образцов %s отсутствует в базе данных." % name)

                log.write("Create %s - %s - %s\n" % (test_series.Name, sample_set.Number, row[1][SAMPLE_FIELD]))

                sample = PMSample(
                    pm_sample_set=sample_set,
                    orig_sample_set=orig_sample_set,
                    Number=row[1][SAMPLE_FIELD],
                    SetDate=encode_date(row[1][DOC_DATE_FIELD]),
                    Length1=(
                        float(row[1][LENGTH1_FIELD])
                        if len(row[1][LENGTH1_FIELD]) > 0 and row[1][LENGTH1_FIELD] != "-"
                        else None
                    ),
                    Length2=(
                        float(row[1][LENGTH2_FIELD])
                        if len(row[1][LENGTH2_FIELD]) > 0 and row[1][LENGTH2_FIELD] != "-"
                        else None
                    ),
                    Height=(
                        float(row[1][HEIGHT_FIELD])
                        if len(row[1][HEIGHT_FIELD]) > 0 and row[1][HEIGHT_FIELD] != "-"
                        else None
                    ),
                    MassAirDry=(
                        float(row[1][MASS_AIR_DRY_FIELD])
                        if len(row[1][MASS_AIR_DRY_FIELD]) > 0 and row[1][MASS_AIR_DRY_FIELD] != "-"
                        else None
                    ),
                )

                if _type == "CORE":
                    sample.StartPosition = float(row[1][START_POSITION_FIELD])
                    sample.EndPosition = float(row[1][END_POSITION_FIELD])
                    sample.BoxNumber = str(row[1][BOX_NUMBER_FIELD])

                pm_samples.append(sample)
            else:
                log.write("Finded %s - %s - %s\n" % (test_series.Name, sample_set.Number, row[1][SAMPLE_FIELD]))

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
