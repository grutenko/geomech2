"""
Создает таблицу свойств близкую к PMSamplePropertyValues из переданого файла БД ФМС
"""

import pandas as pd
import wx

app = wx.App(False)
dlg = wx.FileDialog(
    None,
    "Select the FMS property values file",
    wildcard="Excel files (*.xlsx)|*.xlsx",
    style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
)
if dlg.ShowModal() != wx.ID_OK:
    exit(0)
file_path = dlg.GetPath()
dlg.Destroy()

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
SAMPLE_FIELDS = [("Набор испытаний", 1), ("Проба", 9), ("Образец", 14)]
column_list = []
df_column = pd.read_excel(file_path, 0).columns
for i in df_column:
    column_list.append(i)
converter = {col: str for col in column_list}
df = pd.read_excel(file_path, sheet_name=0, header=0, converters=converter)

rows = []
for index, row in enumerate(df.iterrows()):
    if index == 0:
        continue
    _new_row = []
    _skip = False
    _i = 0
    for name, index in SAMPLE_FIELDS:
        if not row[1][index] or isinstance(row[1][index], str) and row[1][index].strip() in ("", "-"):
            print(_new_row, "skipped")
            _skip = True
            break
        if _i == 0:
            _new_row.append("№" + str(row[1][0]) + " " + ".".join(reversed(str(row[1][1]).split(" ")[0].split("-"))))
        else:
            _new_row.append(row[1][index])
        _i += 1
    if not _skip:
        for name, index in HANDMADE_PROPS:
            if not row[1][index] or isinstance(row[1][index], str) and row[1][index].strip() in ("", "-"):
                continue
            rows.append(_new_row + [name, "Физическая энциклопедия", "", row[1][index]])
        for name, i_value, i_method, i_equipment in PROPS:
            if not row[1][i_value] or isinstance(row[1][i_value], str) and row[1][i_value].strip() in ("", "-"):
                continue
            _props = []
            _props.append(name)
            _props.append(row[1][i_method])
            _props.append(row[1][i_equipment])
            _props.append(row[1][i_value])
            rows.append(_new_row + _props)


column_names = [i[0] for i in SAMPLE_FIELDS] + ["Свойство", "Метод", "Оборудование", "Значение"]
df = pd.DataFrame(rows, columns=column_names, dtype=str)
df.to_csv("output.csv", index=False, encoding="utf-8-sig", sep=";")
