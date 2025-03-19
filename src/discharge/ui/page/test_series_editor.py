import re
from dataclasses import dataclass, field
from typing import Dict, Iterable

import wx
from pony.orm import commit, count, db_session, select
from wx.grid import GridCellAutoWrapStringEditor, GridCellEditor, GridCellRenderer, GridCellStringRenderer

from src.bore_hole.ui.choice import Choice as BoreHoleChoice
from src.ctx import app_ctx
from src.database import BoreHole, DischargeMeasurement, DischargeSeries, FoundationDocument, OrigSampleSet
from src.datetimeutil import decode_date, encode_date
from src.document.ui.choice import Choice as FoundationChoice
from src.ui.grid import (
    EVT_GRID_EDITOR_STATE_CHANGED,
    CellType,
    Column,
    FloatCellType,
    GridEditor,
    Model,
    NumberCellType,
    StringCellType,
)
from src.ui.icon import get_icon
from src.ui.validators import DateValidator, TextValidator


@dataclass
class _Row:
    o: any
    fields: Dict = field(default_factory=lambda: {})
    changed_fields: Dict = field(default_factory=lambda: {})


class VecCellType(CellType):
    def __init__(self, item_type: CellType, min_count=0, max_count=-1):
        self._item_type = item_type

    def get_type_name(self) -> str:
        return "vec<%s>" % self._item_type.get_type_name()

    def get_type_descr(self) -> str:
        return "[Список] %s" % self._item_type.get_type_descr()

    def test_repr(self, value) -> bool:
        for item in re.split("[,;]\s*", value.strip()):
            if not self._item_type.test_repr(item):
                return False
        return True

    def to_string(self, value) -> str:
        if value is None:
            return ""
        return "; ".join(map(lambda x: self._item_type.to_string(x), value))

    def from_string(self, value: str):
        value = value.strip()
        if value is None or value.strip() == "":
            return []
        values = []
        for item in re.split("[,;]\s*", value.strip()):
            values.append(self._item_type.from_string(item))
        return values

    def get_grid_renderer(self) -> GridCellRenderer:
        return GridCellStringRenderer()

    def get_grid_editor(self) -> GridCellEditor:
        return GridCellAutoWrapStringEditor()

    def __eq__(self, o):
        return isinstance(o, VecCellType)


class DMModel(Model):
    def __init__(self, core=None, config_provider=None) -> None:
        super().__init__()
        self._core = core
        self._config_provider = config_provider
        self._rows = []
        self._columns = self._build_columns()
        self._changed_columns = 0
        self._deleted_rows = []
        self.load()

    def _prepare_o(self, o):
        r = _Row(o)
        fields = {
            "SampleNumber": str(o.SampleNumber),
            "Diameter": str(o.Diameter),
            "Length": str(o.Length),
            "Weight": str(int(o.Weight)),
            "CoreDepth": str(o.CoreDepth),
        }
        e = []
        e.append(str(int(o.E1)))
        e.append(str(int(o.E2)))
        e.append(str(int(o.E3)))
        e.append(str(int(o.E4)))
        fields["E"] = "; ".join(e)
        fields["Rotate"] = str(o.Rotate)
        fields["PartNumber"] = o.PartNumber
        fields["RTens"] = str(o.RTens)
        fields["Sensitivity"] = str(o.Sensitivity)
        fields["RockType"] = str(o.RockType) if o.RockType is not None else ""
        tp1 = []
        if o.TP1_1 is not None:
            tp1.append(str(float(o.TP1_1)))
        if o.TP1_2 is not None:
            tp1.append(str(float(o.TP1_2)))
        fields["TP1"] = "; ".join(tp1)
        tp2 = []
        if o.TP2_1 is not None:
            tp2.append(str(float(o.TP2_1)))
        if o.TP2_2 is not None:
            tp2.append(str(float(o.TP2_2)))
        fields["TP2"] = "; ".join(tp2)
        tr = []
        if o.TR_1 is not None:
            tr.append(str(float(o.TR_1)))
        if o.TR_2 is not None:
            tr.append(str(float(o.TR_2)))
        fields["TR"] = "; ".join(tr)
        ts = []
        if o.TS_1 is not None:
            ts.append(str(float(o.TS_1)))
        if o.TS_2 is not None:
            ts.append(str(float(o.TS_2)))
        fields["TS"] = "; ".join(ts)
        fields["PWSpeed"] = str(int(o.PWSpeed)) if o.PWSpeed is not None else ""
        fields["RWSpeed"] = str(int(o.RWSpeed)) if o.RWSpeed is not None else ""
        fields["SWSpeed"] = str(int(o.SWSpeed)) if o.SWSpeed is not None else ""
        fields["PuassonStatic"] = str(o.PuassonStatic) if o.PuassonStatic is not None else ""
        fields["YungStatic"] = str(o.YungStatic) if o.YungStatic is not None else ""
        r.fields = fields
        return r

    @db_session
    def load(self):
        if self._core is not None:
            self._rows = []
            dm = select(o for o in DischargeMeasurement if o.orig_sample_set == self._core).order_by(
                lambda p: int(p.DschNumber)
            )
            o: DischargeMeasurement
            for o in dm:
                self._rows.append(self._prepare_o(o))

    def _get_column_width(self, name):
        if self._config_provider is not None:
            column_width = self._config_provider["column_width"]
            if column_width != None and name in column_width:
                return column_width[name]
        return -1

    def _build_columns(self):
        return {
            "SampleNumber": Column(
                "SampleNumber",
                StringCellType(),
                "* № Образца",
                "Регистрационный номер образца керна",
                self._get_column_width("SampleNumber"),
            ),
            "Diameter": Column(
                "Diameter",
                FloatCellType(prec=1),
                "* Диаметр\n(мм)",
                "Диаметр образца керна",
                self._get_column_width("Diameter"),
            ),
            "Length": Column(
                "Length",
                FloatCellType(prec=1),
                "* Длина\n(см)",
                "Длина образца керна",
                self._get_column_width("Length"),
            ),
            "Weight": Column(
                "Weight", NumberCellType(), "* Вес\n(г)", "Вес образца\nкерна", self._get_column_width("Weight")
            ),
            "CoreDepth": Column(
                "CoreDepth",
                FloatCellType(),
                "* Глубина\nвзятия (м)",
                "Глубина взятия образца керна",
                self._get_column_width("CoreDepth"),
            ),
            "RockType": Column(
                "RockType", StringCellType(), "* Тип породы", "Тип породы", self._get_column_width("RockType")
            ),
            "E": Column(
                "E",
                VecCellType(NumberCellType(), min_count=1, max_count=4),
                "* Относит.\nдеформ. (усл. ед.)",
                "Относительная деформация образца (усл. ед.)",
                self._get_column_width("E"),
            ),
            "Rotate": Column(
                "Rotate",
                FloatCellType(),
                "* Угол корр.\nнапряж.\n(град.)",
                "Угол коррекции направления напряжений",
                self._get_column_width("Rotate"),
            ),
            "PartNumber": Column(
                "PartNumber",
                StringCellType(),
                "* № партии\nтензодат",
                "Номер партии тензодатчиков",
                self._get_column_width("PartNumber"),
            ),
            "RTens": Column(
                "RTens",
                FloatCellType(prec=1),
                "* Сопрот.\nТезодат. (Ом)",
                "Сопротивление тензодатчиков",
                self._get_column_width("RTens"),
            ),
            "Sensitivity": Column(
                "Sensitivity",
                FloatCellType(),
                "* Чувств.\nТезодат.",
                "Коэффициент чувствительности тензодатчиков",
                self._get_column_width("Sensitivity"),
            ),
            "TP1": Column(
                "TP1",
                VecCellType(FloatCellType(prec=1), 0, 2),
                "Время\nпродоль.\n(мс)",
                "Замер времени прохождения продольных волн (ультразвуковое профилирование или др.)",
                self._get_column_width("TP1"),
                optional=True,
            ),
            "TP2": Column(
                "TP2",
                VecCellType(FloatCellType(prec=1), 0, 2),
                "Время продоль.\n(торц.) (мс)",
                "Замер времени прохождения продольных волн (торц.)",
                self._get_column_width("TP2"),
                optional=True,
            ),
            "PWSpeed": Column(
                "PWSpeed",
                NumberCellType(),
                "Скорость\nпродоль.\n(м/с)",
                "Коэффициент чувствительности тензодатчиков",
                self._get_column_width("PWSpeed"),
                optional=True,
            ),
            "TR": Column(
                "TR",
                VecCellType(FloatCellType(prec=2), 0, 2),
                "Время\nповерхност.\n(мс)",
                "Замер времени прохождения поверхностных волн",
                self._get_column_width("TR"),
                optional=True,
            ),
            "RWSpeed": Column(
                "RWSpeed",
                NumberCellType(),
                "Скорость\nповерхност.\n(м/с)",
                "Скорость поверхностны волн",
                self._get_column_width("RWSpeed"),
                optional=True,
            ),
            "TS": Column(
                "TS",
                VecCellType(NumberCellType(), 0, 2),
                "t попереч.\n(мс)",
                "Замер времени прохождения поперечных волн",
                self._get_column_width("TS"),
                optional=True,
            ),
            "SWSpeed": Column(
                "SWSpeed",
                NumberCellType(),
                "Скорость\nпопереч.\n(м/с)",
                "Скорость поперечных волн",
                self._get_column_width("SWSpeed"),
                optional=True,
            ),
            "PuassonStatic": Column(
                "PuassonStatic",
                FloatCellType(),
                "Пуассон\nдинамич.",
                "Динамический коэффициент Пуассона",
                self._get_column_width("PuassonStatic"),
                optional=True,
            ),
            "YungStatic": Column(
                "YungStatic",
                FloatCellType(),
                "Юнг\nдинамич.",
                "Динамический модуль Юнга",
                self._get_column_width("YungStatic"),
                optional=True,
            ),
        }

    def get_columns(self) -> Iterable[Column]:
        return list(self._columns.values())

    def get_row_state(self, row: int):
        return self._rows[row]

    def get_value_at(self, col: int, row: int) -> str:
        _id = list(self._columns.keys()).__getitem__(col)
        row = self._rows[row]
        return row.fields[_id] if _id not in row.changed_fields else row.changed_fields[_id]

    def set_value_at(self, col: int, row: int, value: str):
        if self.get_value_at(col, row) != value:
            _id = list(self._columns.keys()).__getitem__(col)
            self._rows[row].changed_fields[_id] = value

    def insert_row(self, row: int):
        fields = {
            "Diameter": "0.0",
            "Length": "0.0",
            "Weight": "0",
            "CoreDepth": "0.0",
            "E": "0, 0, 0, 0",
            "Rotate": "0.0",
            "PartNumber": "",
            "RTens": "0.0",
            "Sensitivity": "0.0",
            "TP1": "",
            "TP2": "",
            "PWSpeed": "",
            "TR": "",
            "RWSpeed": "",
            "TS": "",
            "SWSpeed": "",
            "PuassonStatic": "",
            "YungStatic": "",
            "SampleNumber": "",
            "RockType": "",
        }
        self._rows.insert(row, _Row(None, fields, fields))

    def restore_row(self, row, state):
        if state.o is not None:
            self._deleted_rows.remove(state.o.RID)
        self._rows.insert(row, state)

    def delete_row(self, row: int):
        if self._rows[row].o is not None:
            self._deleted_rows.append(self._rows[row].o.RID)
        self._rows.__delitem__(row)

    def total_rows(self) -> int:
        return len(self._rows)

    def have_changes(self) -> bool:
        for row in self._rows:
            if row.changed_fields:
                return True
        return len(self._deleted_rows) > 0

    def validate(self):
        errors = []
        for col in self._columns.values():
            for row_index, row in enumerate(self._rows):
                if col.id in row.changed_fields:
                    value = row.changed_fields[col.id]
                else:
                    value = row.fields[col.id]
                if len(value) == 0:
                    if col.optional:
                        continue
                    else:
                        _msg = "Значение не должно быть пустым."
                        errors.append((col, row_index, _msg))
                if len(value) > 0 and not col.cell_type.test_repr(value):
                    _msg = 'Неподходящее значение для ячейки типа "%s"' % col.cell_type.get_type_descr()
                    errors.append((col, row_index, _msg))

        duplicates = {}
        for index, row in enumerate(self._rows):
            if "SampleNumber" in row.changed_fields:
                _v = row.changed_fields["SampleNumber"]
            else:
                _v = row.fields["SampleNumber"]
            if len(_v) == 0:
                continue
            if _v not in duplicates:
                duplicates[_v] = []
            duplicates[_v].append(index)
        col = self._columns["SampleNumber"]
        for indexes in duplicates.values():
            if len(indexes) > 1:
                errors.append((col, indexes[0], "Номер замера должен быть уникален"))

        return errors

    @db_session
    def save(self):
        if len(self.validate()) > 0:
            wx.MessageBox(
                "В таблице обнаружены ошибки. Сохранение невозможно.", "Ошибка сохранения.", style=wx.OK | wx.ICON_ERROR
            )
            return False

        for _id in self._deleted_rows:
            DischargeMeasurement[_id].delete()

        self._deleted_rows = []
        columns = self._columns
        sample_set = OrigSampleSet[self._core.RID]
        new_rows = []
        max_dsch_number = 0
        for row in self._rows:
            if row.o is not None and max_dsch_number < int(row.o.DschNumber):
                max_dsch_number = int(row.o.DschNumber)
        for index, row in enumerate(self._rows):
            f = {**row.fields, **row.changed_fields}
            fields = {}
            fields["orig_sample_set"] = sample_set
            fields["SampleNumber"] = f["SampleNumber"]
            fields["Diameter"] = columns["Diameter"].cell_type.from_string(f["Diameter"])
            fields["Length"] = columns["Length"].cell_type.from_string(f["Length"])
            fields["Weight"] = columns["Weight"].cell_type.from_string(f["Weight"])
            fields["RockType"] = f["RockType"]
            fields["PartNumber"] = f["PartNumber"]
            fields["RTens"] = columns["RTens"].cell_type.from_string(f["RTens"])
            fields["Sensitivity"] = columns["Sensitivity"].cell_type.from_string(f["Sensitivity"])
            tp = [None, None]
            d = columns["TP1"].cell_type.from_string(f["TP1"])
            tp[: len(d)] = d
            fields["TP1_1"] = tp[0]
            fields["TP1_2"] = tp[1]
            tp = [None, None]
            d = columns["TP2"].cell_type.from_string(f["TP2"])
            tp[: len(d)] = d
            fields["TP2_1"] = tp[0]
            fields["TP2_2"] = tp[1]
            tr = [None, None]
            d = columns["TR"].cell_type.from_string(f["TR"])
            tr[: len(d)] = d
            fields["TR_1"] = tr[0]
            fields["TR_2"] = tr[1]
            ts = [None, None]
            d = columns["TS"].cell_type.from_string(f["TS"])
            ts[: len(d)] = d
            fields["TS_1"] = ts[0]
            fields["TS_2"] = ts[1]
            fields["PWSpeed"] = columns["PWSpeed"].cell_type.from_string(f["PWSpeed"])
            fields["RWSpeed"] = columns["RWSpeed"].cell_type.from_string(f["RWSpeed"])
            fields["SWSpeed"] = columns["SWSpeed"].cell_type.from_string(f["SWSpeed"])
            fields["PuassonStatic"] = columns["PuassonStatic"].cell_type.from_string(f["PuassonStatic"])
            fields["YungStatic"] = columns["YungStatic"].cell_type.from_string(f["YungStatic"])
            fields["CoreDepth"] = columns["CoreDepth"].cell_type.from_string(f["CoreDepth"])
            e0 = [0.0, None, None, None]
            e = columns["E"].cell_type.from_string(f["E"])
            for i, v in enumerate(e):
                e0[i] = float(v)
            fields["E1"] = e0[0]
            fields["E2"] = e0[1]
            fields["E3"] = e0[2]
            fields["E4"] = e0[3]
            fields["Rotate"] = columns["Rotate"].cell_type.from_string(f["Rotate"])
            if row.o is not None:
                o = DischargeMeasurement[row.o.RID]
                o.set(**fields)
                new_rows.append(self._prepare_o(o))
            else:
                max_dsch_number += 1
                fields["DschNumber"] = str(max_dsch_number)
                o = DischargeMeasurement(**fields)
                new_rows.append(self._prepare_o(o))
        self._rows = new_rows
        commit()
        return True


class TestSeriesEditor(wx.Panel):
    @db_session
    def __init__(self, parent, is_new=False, o=None, parent_object=None):
        self.is_new = is_new
        self.o = o
        self.parent_object = parent_object
        self.selected = False
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(self, style=wx.TB_FLAT | wx.TB_HORZ_TEXT)
        self.toolbar.AddTool(wx.ID_SAVE, "Сохранить", get_icon("save"))
        self.toolbar.AddStretchableSpace()
        self.toolbar.AddTool(wx.ID_REFRESH, "Обновить", get_icon("update"))
        self.toolbar.Realize()
        sz.Add(self.toolbar, 0, wx.EXPAND)
        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.left = wx.ScrolledWindow(self.splitter)
        l_sz = wx.BoxSizer(wx.VERTICAL)
        l_sz_in = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self.left, label="Скважина *")
        l_sz_in.Add(label, 0, wx.EXPAND)
        self.field_bore_hole = BoreHoleChoice(self.left)
        l_sz_in.Add(self.field_bore_hole, 0, wx.EXPAND | wx.BOTTOM, border=10)
        label = wx.StaticText(self.left, label="Название *")
        l_sz_in.Add(label, 0)
        self.field_name = wx.TextCtrl(self.left, size=wx.Size(250, 25))
        self.field_name.SetValidator(TextValidator(lenMin=1, lenMax=256))
        l_sz_in.Add(self.field_name, 0, wx.EXPAND | wx.BOTTOM, border=10)

        label = wx.StaticText(self.left, label="Комментарий")
        l_sz_in.Add(label, 0)
        self.field_comment = wx.TextCtrl(self.left, size=wx.Size(250, 100), style=wx.TE_MULTILINE)
        self.field_comment.SetValidator(TextValidator(lenMin=0, lenMax=256))
        l_sz_in.Add(self.field_comment, 0, wx.EXPAND | wx.BOTTOM, border=10)
        label = wx.StaticText(self.left, label="Начало испытаний *")
        l_sz_in.Add(label, 0)
        self.field_start_date = wx.TextCtrl(self.left, size=wx.Size(250, 25))
        self.field_start_date.SetValidator(DateValidator())
        l_sz_in.Add(self.field_start_date, 0, wx.EXPAND | wx.BOTTOM, border=10)
        label = wx.StaticText(self.left, label="Конец испытаний")
        l_sz_in.Add(label, 0)
        self.field_end_date = wx.TextCtrl(self.left, size=wx.Size(250, 25))
        self.field_end_date.SetValidator(DateValidator(allow_empty=True))
        l_sz_in.Add(self.field_end_date, 0, wx.EXPAND | wx.BOTTOM, border=10)
        l_sz.Add(l_sz_in, 1, wx.EXPAND | wx.ALL, border=10)
        label = wx.StaticText(self.left, label="Документ обоснование *")
        l_sz_in.Add(label, 0)
        self.field_foundation_doc = FoundationChoice(self.left)
        l_sz_in.Add(self.field_foundation_doc, 0, wx.EXPAND | wx.BOTTOM, border=10)
        self.left.SetSizer(l_sz)
        self.left.SetVirtualSize(self.left.GetBestSize() + (250, 250))
        self.left.SetScrollRate(10, 10)

        self.image_list = wx.ImageList(16, 16)
        self.table_icon = self.image_list.Add(get_icon("table"))
        self.right = wx.Notebook(self.splitter)
        self.right.AssignImageList(self.image_list)
        p = wx.Panel(self.right)
        p_sz = wx.BoxSizer(wx.VERTICAL)
        self.grid_toolbar = wx.ToolBar(p, style=wx.TB_FLAT | wx.TB_HORZ_TEXT)
        tool = self.grid_toolbar.AddTool(wx.ID_COPY, "Копировать", get_icon("copy", scale_to=16), "Копировать")
        tool.Enable(False)
        tool = self.grid_toolbar.AddTool(wx.ID_CUT, "Вырезать", get_icon("cut", scale_to=16), "Вырезать")
        tool.Enable(False)
        tool = self.grid_toolbar.AddTool(wx.ID_PASTE, "Вставить", get_icon("paste", scale_to=16), "Вставить")
        tool.Enable(False)
        self.grid_toolbar.AddSeparator()
        tool = self.grid_toolbar.AddTool(wx.ID_UNDO, "Отменить", get_icon("undo", scale_to=16), "Отменить")
        tool.Enable(False)
        tool = self.grid_toolbar.AddTool(wx.ID_REDO, "Вернуть", get_icon("redo", scale_to=16), "Вернуть")
        tool.Enable(False)
        self.grid_toolbar.Realize()
        self.grid_menubar = wx.MenuBar()
        p_sz.Add(self.grid_toolbar, 0, wx.EXPAND)
        if not self.is_new:
            orig_sample_set = o.orig_sample_set
        else:
            orig_sample_set = None
        self.grid = GridEditor(
            p,
            DMModel(orig_sample_set),
            app_ctx().main.menu,
            self.grid_toolbar,
            app_ctx().main.statusbar,
            header_height=45,
        )
        p_sz.Add(self.grid, 1, wx.EXPAND)
        p.SetSizer(p_sz)
        self.right.AddPage(p, "Замеры", imageId=self.table_icon)
        self.splitter.SplitVertically(self.left, self.right, 280)
        self.splitter.SetMinimumPaneSize(250)
        sz.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.update_controls_state()
        self.bind_all()
        self.bore_holes = []
        if not self.is_new:
            self.field_bore_hole.Disable()
            self.set_fields()
        self.on_select()

    @db_session
    def set_fields(self):
        self.field_name.SetValue(self.o.Name)
        self.field_comment.SetValue(self.o.Comment if self.o.Comment is not None else "")
        self.field_start_date.SetValue(str(decode_date(self.o.StartMeasure)))
        if self.o.EndMeasure is not None:
            self.field_end_date.SetValue(str(decode_date(self.o.EndMeasure)))
        self.field_foundation_doc.SetValue(self.o.foundation_document)
        self.field_bore_hole.SetValue(self.o.orig_sample_set.bore_hole)

    def bind_all(self):
        self.grid.Bind(EVT_GRID_EDITOR_STATE_CHANGED, self.on_editor_state_changed)
        t = self.grid_toolbar
        t.Bind(wx.EVT_TOOL, self.on_copy, id=wx.ID_COPY)
        t.Bind(wx.EVT_TOOL, self.on_cut, id=wx.ID_CUT)
        t.Bind(wx.EVT_TOOL, self.on_paste, id=wx.ID_PASTE)
        t.Bind(wx.EVT_TOOL, self.on_undo, id=wx.ID_UNDO)
        t.Bind(wx.EVT_TOOL, self.on_redo, id=wx.ID_REDO)

    def on_copy(self, event):
        self.grid.copy()

    def on_cut(self, event):
        self.grid.cut()

    def on_paste(self, event):
        self.grid.paste()

    def on_undo(self, event):
        self.grid.undo()

    def on_redo(self, event):
        self.grid.redo()

    def on_editor_state_changed(self, event):
        self.update_controls_state()

    def on_select(self):
        if not self.selected:
            self.selected = True
            menu = app_ctx().main.menu.GetMenu(1)
            item = menu.Append(wx.ID_COPY, "Копировать\tCTRL+C")
            item.SetBitmap(get_icon("copy", scale_to=16))
            item.Enable(False)
            self.menu_copy = item
            item = menu.Append(wx.ID_CUT, "Вырезать\tCTRL+X")
            item.SetBitmap(get_icon("cut", scale_to=16))
            item.Enable(False)
            self.menu_cut = item
            item = menu.Append(wx.ID_PASTE, "Вставить\tCTRL+V")
            item.SetBitmap(get_icon("paste", scale_to=16))
            item.Enable(False)
            self.menu_paste = item
            item = menu.AppendSeparator()
            self.menu_sep = item
            item = menu.Append(wx.ID_UNDO, "Отменить\tCTRL+Z")
            item.SetBitmap(get_icon("undo", scale_to=16))
            item.Enable(False)
            self.menu_undo = item
            item = menu.Append(wx.ID_REDO, "Вернуть\tCTRL+Y")
            item.SetBitmap(get_icon("redo", scale_to=16))
            item.Enable(False)
            self.menu_redo = item
            menu.Bind(wx.EVT_MENU, self.on_copy, id=wx.ID_COPY)
            menu.Bind(wx.EVT_MENU, self.on_cut, id=wx.ID_CUT)
            menu.Bind(wx.EVT_MENU, self.on_paste, id=wx.ID_PASTE)
            menu.Bind(wx.EVT_MENU, self.on_undo, id=wx.ID_UNDO)
            menu.Bind(wx.EVT_MENU, self.on_redo, id=wx.ID_REDO)
            self.grid.apply_controls()
            self.update_controls_state()

    def on_deselect(self):
        menu = app_ctx().main.menu.GetMenu(1)
        if self.selected:
            menu.Delete(self.menu_copy)
            menu.Delete(self.menu_cut)
            menu.Delete(self.menu_paste)
            menu.Delete(self.menu_sep)
            menu.Delete(self.menu_undo)
            menu.Delete(self.menu_redo)
            self.grid.remove_controls()
            self.selected = False

    def get_name(self):
        if self.is_new:
            return "(новый)"
        return self.o.get_tree_name().strip()

    def get_icon(self):
        return get_icon("file")

    def update_controls_state(self):
        t = self.grid_toolbar
        t.EnableTool(wx.ID_COPY, self.grid.can_copy())
        t.EnableTool(wx.ID_CUT, self.grid.can_cut())
        t.EnableTool(wx.ID_PASTE, self.grid.can_paste())
        t.EnableTool(wx.ID_UNDO, self.grid.can_undo())
        t.EnableTool(wx.ID_REDO, self.grid.can_redo())
        menu = app_ctx().main.menu
        if self.selected:
            menu.Enable(wx.ID_COPY, self.grid.can_copy())
            menu.Enable(wx.ID_CUT, self.grid.can_cut())
            menu.Enable(wx.ID_PASTE, self.grid.can_paste())
            menu.Enable(wx.ID_UNDO, self.grid.can_undo())
            menu.Enable(wx.ID_REDO, self.grid.can_redo())
        t.Realize()
