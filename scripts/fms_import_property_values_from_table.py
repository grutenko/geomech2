"""
Используя таблицу, созданную в fms_make_property_values_table.py,
импортирует значения свойств в БД Геомеханики в таблицу PMSamplePropertyValues

Серии испытаний, пробы, образцы, методы, свойства должны быть предварительно добавлены в БД если отсутствуют
"""

import os
import sys

import pandas as pd
import wx
from pony.orm import commit, db_session, rollback, select
from rapidfuzz import fuzz, process

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database import (
    PmPerformedTask,
    PmProperty,
    PMSample,
    PmSamplePropertyValue,
    PMSampleSet,
    PmTaskMethodForSample,
    PmTestEquipment,
    PmTestMethod,
    connect,
)
from src.ui.windows.login import LoginDialog

app = wx.App(False)
dlg = LoginDialog(None, without_config=True)
if dlg.ShowModal() != wx.ID_OK:
    exit(0)
connect(dlg.login, dlg.password, dlg.host, dlg.port, dlg.database)
dlg.Destroy()

dlg = wx.FileDialog(
    None,
    "Select the FMS property values file",
    wildcard="CSV files (*.csv)|*.csv",
    style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
)
if dlg.ShowModal() != wx.ID_OK:
    exit(0)
file_path = dlg.GetPath()

with db_session:

    pm_samples = select(s for s in PMSample).prefetch(PMSample.pm_sample_set, PMSampleSet.pm_test_series)[:]
    pm_properties = select(s for s in PmProperty)[:]
    pm_methods = select(s for s in PmTestMethod)[:]
    pm_equipments = select(s for s in PmTestEquipment)[:]

    threshold = 90

    def find_sample(name, sample_set_name, test_series_name):
        global pm_samples
        results = process.extract(
            name, [a.Number for a in pm_samples], scorer=fuzz.ratio, limit=1000, score_cutoff=threshold
        )
        for find_name, score, index in results:
            result = pm_samples[index]
            if (
                fuzz.ratio(result.pm_sample_set.Number, sample_set_name) >= threshold
                and fuzz.ratio(result.pm_sample_set.pm_test_series.Name, test_series_name) >= threshold
            ):
                return result
        return None

    def find_property(name):
        global pm_properties
        r = process.extractOne(name, [a.Name for a in pm_properties], scorer=fuzz.ratio, score_cutoff=threshold)
        if r is None:
            return None
        return pm_properties[r[2]]

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

    samples_not_found = []
    props_not_found = []
    methods_not_found = []
    equipment_not_found = []

    df = pd.read_csv(file_path, sep=";", encoding="utf-8-sig", header=0, dtype=str)
    for row in df.iterrows():
        sample = find_sample(row[1][2], row[1][1], row[1][0])
        if sample is None:
            samples_not_found.append(row[1][2] + " " + row[1][1] + " " + row[1][0])
            continue
        property = find_property(row[1][3])
        if property is None:
            props_not_found.append(row[1][3])
            continue
        method = find_method(row[1][4])
        if method is None:
            methods_not_found.append(row[1][4])
            continue
        if not row[1][5] or (isinstance(row[1][5], str) and row[1][5].strip() not in ("-", "")):
            equipment = find_equipment(row[1][5])
            if equipment is None:
                equipment_not_found.append(row[1][5])
                continue
        else:
            equipment = None
        value = float(row[1][6])
        if PmTaskMethodForSample.get(pm_sample=sample, pm_method=method, pm_performed_task=PmPerformedTask[1]) is None:
            PmTaskMethodForSample(pm_sample=sample, pm_method=method, pm_performed_task=PmPerformedTask[1])
        pm_property_value = PmSamplePropertyValue.get(pm_sample=sample, pm_property=property, pm_test_method=method)
        if pm_property_value is None:
            PmSamplePropertyValue(pm_sample=sample, pm_property=property, pm_test_method=method, Value=value)
        else:
            if pm_property_value.Value != value:
                print(
                    "Обновление значения свойства для образца ",
                    sample.Number,
                    " ",
                    sample.pm_sample_set.Number,
                    " ",
                    sample.pm_sample_set.pm_test_series.Name,
                    " ",
                    property.Name,
                    " ",
                    method.Name,
                    pm_property_value.Value,
                    "->",
                    value,
                )
    if len(samples_not_found) > 0:
        print("Образец не найден:", set(samples_not_found))
    if len(props_not_found) > 0:
        print("Свойство не найдено:", set(props_not_found))
    if len(methods_not_found) > 0:
        print("Метод не найден:", set(methods_not_found))
    if len(equipment_not_found) > 0:
        print("Оборудование не найдено:", set(equipment_not_found))

    if (
        len(samples_not_found) > 0
        or len(props_not_found) > 0
        or len(methods_not_found) > 0
        or len(equipment_not_found) > 0
    ):
        rollback()
        exit(1)
