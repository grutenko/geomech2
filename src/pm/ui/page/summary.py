import textwrap
import time
from dataclasses import dataclass
from typing import List

import wx
import wx.adv
import wx.dataview
import wx.lib.agw.flatnotebook
import wx.lib.newevent
from pony.orm import db_session, exists, select

from src.ctx import app_ctx
from src.database import (
    MineObject,
    Petrotype,
    PetrotypeStruct,
    PmProperty,
    PmPropertyClass,
    PMSample,
    PmSamplePropertyValue,
    PMSampleSet,
    PMTestSeries,
)
from src.datetimeutil import encode_date
from src.ui.grid import (
    EVT_GRID_EDITOR_STATE_CHANGED,
    Column,
    FloatCellType,
    GridEditor,
    Model,
    NumberCellType,
    StringCellType,
)
from src.ui.icon import get_icon


@dataclass
class Filter:
    use_filter: bool = True
    test_series: List[PMTestSeries] = None
    fields: List[MineObject] = None
    petrotypes: List[Petrotype] = None
    test_date_from: wx.DateTime = None
    test_date_to: wx.DateTime = None
    exclude_none_test_date: bool = False
    properties: List[PmProperty] = None
    properties_hide_no_values_samples: bool = False


FilterChangedEvent, EVT_FILTER_CHANGED = wx.lib.newevent.NewEvent()


class FilterPanel(wx.ScrolledWindow):
    def __init__(self, parent, filter):
        super().__init__(parent, style=wx.VSCROLL)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.filter: Filter = filter
        self.fields_items = []
        self.petrotypes_items = []
        self.test_series_items = []
        sz = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(self, style=wx.TB_FLAT | wx.TB_HORZ_TEXT)
        self.toolbar.AddTool(wx.ID_APPLY, "Применить", get_icon("filter"))
        self.toolbar.AddTool(wx.ID_CLEAR, "Сбросить", get_icon("filter-clear"))
        self.toolbar.Bind(wx.EVT_TOOL, self.on_apply, id=wx.ID_APPLY)
        self.toolbar.Realize()
        sz.Add(self.toolbar, 0, wx.EXPAND)
        sz_in = wx.BoxSizer(wx.VERTICAL)
        self.use_filter_checkbox = wx.CheckBox(self)
        self.use_filter_checkbox.Bind(wx.EVT_CHECKBOX, self.on_use_filter)
        sz_in.Add(self.use_filter_checkbox, 0, wx.EXPAND | wx.BOTTOM, border=10)
        self.use_filter_checkbox.SetValue(True)
        self.use_filter_checkbox.Hide()

        self.notebook = wx.Notebook(self, style=wx.NB_LEFT | wx.NB_MULTILINE | wx.NB_NOPAGETHEME)

        p = wx.Panel(self.notebook)
        p_sz = wx.BoxSizer(wx.VERTICAL)
        btn_sz = wx.StdDialogButtonSizer()
        self.properties_select_all = wx.Button(p, label="Выбрать все")
        btn_sz.Add(self.properties_select_all, 0)
        self.properties_remove_selection = wx.Button(p, label="Снять выделение")
        self.properties_select_all.Bind(wx.EVT_BUTTON, self.on_properties_select_all)
        self.properties_remove_selection.Bind(wx.EVT_BUTTON, self.on_properties_remove_selection)
        btn_sz.Add(self.properties_remove_selection)
        p_sz.Add(btn_sz, 0, wx.EXPAND)
        self.properties_hide_no_values_samples = wx.CheckBox(p, label="Скрыть образцы без значений свойств")
        p_sz.Add(self.properties_hide_no_values_samples, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, border=10)
        self.properties_items = []
        self.props_image_list = wx.ImageList(16, 16)
        self.checked_icon = self.props_image_list.Add(get_icon("checkbox-checked"))
        self.unchecked_icon = self.props_image_list.Add(get_icon("checkbox-unchecked"))
        self.properties = wx.TreeCtrl(
            p, style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT | wx.TR_MULTIPLE | wx.TR_HAS_BUTTONS
        )
        self.properties.Bind(wx.EVT_TREE_STATE_IMAGE_CLICK, self.on_properties_checked)
        self.properties.SetStateImageList(self.props_image_list)
        p_sz.Add(self.properties, 1, wx.EXPAND)
        p.SetSizer(p_sz)
        self.notebook.AddPage(p, "Свойства", select=True)

        self.contracts_colpane = wx.Panel(self.notebook)
        p = self.contracts_colpane
        p_sz = wx.BoxSizer(wx.VERTICAL)
        btn_sz = wx.StdDialogButtonSizer()
        self.test_series_select_all = wx.Button(p, label="Выбрать все")
        btn_sz.Add(self.test_series_select_all, 0)
        self.test_series_remove_selection = wx.Button(p, label="Снять выделение")
        self.test_series_select_all.Bind(wx.EVT_BUTTON, self.on_test_series_select_all)
        self.test_series_remove_selection.Bind(wx.EVT_BUTTON, self.on_test_series_remove_selection)
        btn_sz.Add(self.test_series_remove_selection)
        p_sz.Add(btn_sz, 0, wx.EXPAND)
        self.test_series = wx.CheckListBox(p)
        p_sz.Add(self.test_series, 1, wx.EXPAND)
        p.SetSizer(p_sz)
        self.notebook.AddPage(self.contracts_colpane, "Договоры", select=False)

        self.fields_colpane = wx.Panel(self.notebook)
        p = self.fields_colpane
        p_sz = wx.BoxSizer(wx.VERTICAL)
        btn_sz = wx.StdDialogButtonSizer()
        self.field_select_all = wx.Button(p, label="Выбрать все")
        btn_sz.Add(self.field_select_all, 0)
        self.field_remove_selection = wx.Button(p, label="Снять выделение")
        self.field_select_all.Bind(wx.EVT_BUTTON, self.on_field_select_all)
        self.field_remove_selection.Bind(wx.EVT_BUTTON, self.on_field_remove_selection)
        btn_sz.Add(self.field_remove_selection)
        p_sz.Add(btn_sz, 0, wx.EXPAND)
        self.fields = wx.CheckListBox(p)
        p_sz.Add(self.fields, 1, wx.EXPAND)
        p.SetSizer(p_sz)
        self.notebook.AddPage(self.fields_colpane, "Меторождения", select=False)

        self.date_colpane = wx.Panel(self.notebook)
        p = self.date_colpane
        p_sz = wx.BoxSizer(wx.VERTICAL)
        self.test_date_checkbox = wx.CheckBox(p, label="Ограничить по дате")
        self.test_date_checkbox.Bind(wx.EVT_CHECKBOX, self.on_enable_date)
        p_sz.Add(self.test_date_checkbox)
        h_sz = wx.BoxSizer(wx.HORIZONTAL)
        self.field_test_date_from = wx.adv.DatePickerCtrl(p)
        self.field_test_date_to = wx.adv.DatePickerCtrl(p, style=wx.adv.DP_ALLOWNONE)
        self.field_test_date_from.Disable()
        self.field_test_date_to.Disable()
        h_sz.Add(self.field_test_date_from, 1)
        label = wx.StaticText(p, label="-")
        h_sz.Add(label, 0, wx.ALIGN_CENTER_VERTICAL)
        h_sz.Add(self.field_test_date_to, 1)
        p_sz.Add(h_sz, 0, wx.EXPAND)
        self.checkbox_exclude_none_test_date = wx.CheckBox(p, label="Исключить пробы без даты испытания")
        p_sz.Add(self.checkbox_exclude_none_test_date, 0, wx.EXPAND | wx.BOTTOM, border=10)
        p.SetSizer(p_sz)
        self.notebook.AddPage(self.date_colpane, "Дата испытания", select=False)

        self.petrotype_colpane = wx.Panel(self.notebook)
        p = self.petrotype_colpane
        p_sz = wx.BoxSizer(wx.VERTICAL)
        btn_sz = wx.StdDialogButtonSizer()
        self.petrotype_select_all = wx.Button(p, label="Выбрать все")
        btn_sz.Add(self.petrotype_select_all, 0)
        self.petrotype_remove_selection = wx.Button(p, label="Снять выделение")
        self.petrotype_select_all.Bind(wx.EVT_BUTTON, self.on_petrotype_select_all)
        self.petrotype_remove_selection.Bind(wx.EVT_BUTTON, self.on_petrotype_remove_selection)
        btn_sz.Add(self.petrotype_remove_selection)
        p_sz.Add(btn_sz)
        self.field_petrotypes = wx.CheckListBox(p)
        p_sz.Add(self.field_petrotypes, 1, wx.EXPAND)
        p.SetSizer(p_sz)
        self.notebook.AddPage(self.petrotype_colpane, "Литотипы", select=False)

        sz_in.Add(self.notebook, 1, wx.EXPAND)

        sz.Add(sz_in, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.load()
        self.set_filter_fields()
        self.SetMinSize((250, 250))
        self.SetScrollRate(10, 10)
        self.FitInside()

    def on_test_series_select_all(self, event):
        for i in range(self.test_series.GetCount()):
            self.test_series.Check(i)

    def on_test_series_remove_selection(self, event):
        for i in range(self.test_series.GetCount()):
            self.test_series.Check(i, check=False)

    def set_filter_fields(self):
        self.use_filter_checkbox.SetValue(self.filter.use_filter)
        if self.filter.fields is None:
            for i in range(self.fields.GetCount()):
                self.fields.Check(i)
        else:
            for i in range(self.fields.GetCount()):
                for field in self.filter.fields:
                    if self.fields_items[i].RID == field.RID:
                        self.fields.Check(i)
        if self.filter.petrotypes is None:
            for i in range(self.field_petrotypes.GetCount()):
                self.field_petrotypes.Check(i)
        else:
            for i in range(self.field_petrotypes.GetCount()):
                for petrotype in self.filter.petrotypes:
                    if self.petrotypes_items[i].RID == petrotype.RID:
                        self.field_petrotypes.Check(i)
        if self.filter.test_series is None:
            for i in range(self.test_series.GetCount()):
                self.test_series.Check(i)
        else:
            for i in range(self.test_series.GetCount()):
                for test_series in self.filter.test_series:
                    if self.test_series_items[i].RID == test_series.RID:
                        self.test_series.Check(i)
        if self.filter.test_date_from is not None:
            self.test_date_checkbox.SetValue(True)
            self.field_test_date_from.SetValue(self.filter.test_date_from)
        if self.filter.test_date_to is not None:
            self.field_test_date_to.SetValue(self.filter.test_date_to)
        self.checkbox_exclude_none_test_date.SetValue(self.filter.exclude_none_test_date)
        self.update_controls_state()

    def on_use_filter(self, event):
        self.enable_controls(self.use_filter_checkbox.IsChecked())

    def on_enable_date(self, event):
        self.field_test_date_from.Enable(self.test_date_checkbox.IsChecked())
        self.field_test_date_to.Enable(self.test_date_checkbox.IsChecked())

    def on_field_select_all(self, event):
        for i in range(self.fields.GetCount()):
            self.fields.Check(i)

    def on_field_remove_selection(self, event):
        for i in range(self.fields.GetCount()):
            self.fields.Check(i, check=False)

    def on_petrotype_select_all(self, event):
        for i in range(self.field_petrotypes.GetCount()):
            self.field_petrotypes.Check(i)

    def on_petrotype_remove_selection(self, event):
        for i in range(self.field_petrotypes.GetCount()):
            self.field_petrotypes.Check(i, check=False)

    @dataclass
    class PropertyState:
        prop: PmProperty
        checked: bool

    def on_properties_checked(self, event):
        print(event)
        item = event.GetItem()
        if not item.IsOk():
            return
        state = self.properties.GetItemData(item)
        if isinstance(state.prop, PmPropertyClass):
            # Toggle all properties in the class
            item, item_cookie = self.properties.GetFirstChild(item)
            while item.IsOk():
                self.properties.GetItemData(item).checked = not state.checked
                item, item_cookie = self.properties.GetNextChild(item, item_cookie)
            state.checked = not state.checked
        else:
            # Toggle single property
            self.properties.GetItemData(item).checked = not state.checked
        self.apply_property_check()

    def on_properties_select_all(self, event):
        class_, cookie = self.properties.GetFirstChild(self.properties.GetRootItem())
        while class_.IsOk():
            item, item_cookie = self.properties.GetFirstChild(class_)
            class_state = self.properties.GetItemData(class_)
            while item.IsOk():
                self.properties.GetItemData(item).checked = True
                item, item_cookie = self.properties.GetNextChild(class_, item_cookie)
            class_state.checked = True
            class_, cookie = self.properties.GetNextChild(class_, cookie)
        self.apply_property_check()

    def on_properties_remove_selection(self, event):
        class_, cookie = self.properties.GetFirstChild(self.properties.GetRootItem())
        while class_.IsOk():
            item, item_cookie = self.properties.GetFirstChild(class_)
            class_state = self.properties.GetItemData(class_)
            while item.IsOk():
                self.properties.GetItemData(item).checked = False
                item, item_cookie = self.properties.GetNextChild(class_, item_cookie)
            class_state.checked = False
            class_, cookie = self.properties.GetNextChild(class_, cookie)
        self.apply_property_check()

    def apply_property_check(self):
        class_, cookie = self.properties.GetFirstChild(self.properties.GetRootItem())
        while class_.IsOk():
            item, item_cookie = self.properties.GetFirstChild(class_)
            class_state = self.properties.GetItemData(class_)
            while item.IsOk():
                state = self.properties.GetItemData(item)
                if state.checked:
                    self.properties.SetItemState(item, self.checked_icon)
                else:
                    self.properties.SetItemState(item, self.unchecked_icon)
                item, item_cookie = self.properties.GetNextChild(class_, item_cookie)
            if class_state.checked:
                self.properties.SetItemState(class_, self.checked_icon)
            else:
                self.properties.SetItemState(class_, self.unchecked_icon)
            class_, cookie = self.properties.GetNextChild(class_, cookie)
        self.update_controls_state()

    @db_session
    def load(self):
        self.properties.DeleteAllItems()
        self.properties_items = []
        root = self.properties.AddRoot("Свойства")
        for o in select(o for o in PmPropertyClass):
            item = self.properties.AppendItem(root, o.Name)
            self.properties.SetItemData(item, self.PropertyState(o, True))
            for p in o.pm_properties:
                child = self.properties.AppendItem(item, p.Name)
                self.properties.SetItemData(child, self.PropertyState(p, True))
                self.properties_items.append(p)
        self.apply_property_check()
        self.fields_items = []
        self.fields.Clear()
        for o in select(o for o in MineObject if o.Type == "FIELD"):
            self.fields.Append(o.Name)
            self.fields_items.append(o)
        self.field_petrotypes.Clear()
        self.petrotypes_items = []
        for o in select(o for o in Petrotype):
            self.field_petrotypes.Append(o.Name)
            self.petrotypes_items.append(o)
        self.test_series_items = []
        for o in select(o for o in PMTestSeries):
            self.test_series.Append(o.Name)
            self.test_series_items.append(o)

    def update_controls_state(self):
        self.enable_controls(self.use_filter_checkbox.GetValue())
        self.enable_date_fields(self.test_date_checkbox.GetValue())

    def enable_date_fields(self, enable=True):
        self.field_test_date_from.Enable(enable)
        self.field_test_date_to.Enable(enable)

    def enable_controls(self, enable=True):
        self.test_series_select_all.Enable(enable)
        self.test_series_remove_selection.Enable(enable)
        self.test_series.Enable(enable)
        self.field_select_all.Enable(enable)
        self.field_remove_selection.Enable(enable)
        self.fields.Enable(enable)
        self.test_date_checkbox.Enable(enable)
        self.field_test_date_from.Enable(enable and self.test_date_checkbox.IsChecked())
        self.field_test_date_to.Enable(enable and self.test_date_checkbox.IsChecked())
        self.petrotype_select_all.Enable(enable)
        self.petrotype_remove_selection.Enable(enable)
        self.field_petrotypes.Enable(enable)
        self.checkbox_exclude_none_test_date.Enable(enable)

    def on_apply(self, event):
        if not self.use_filter_checkbox.IsChecked():
            self.filter.use_filter = False
            wx.PostEvent(self, FilterChangedEvent())
            return
        self.filter.use_filter = True
        self.filter.fields = []
        for index in range(self.fields.GetCount()):
            if self.fields.IsChecked(index):
                self.filter.fields.append(self.fields_items[index])
        self.filter.petrotypes = []
        for index in range(self.field_petrotypes.GetCount()):
            if self.field_petrotypes.IsChecked(index):
                self.filter.petrotypes.append(self.petrotypes_items[index])
        if self.test_date_checkbox.IsChecked():
            self.filter.test_date_from = self.field_test_date_from.GetValue()
            date: wx.DateTime = self.field_test_date_to.GetValue()
            if date.IsValid():
                self.filter.test_date_to = date
            else:
                self.filter.test_date_to = None
        else:
            self.filter.test_date_from = None
            self.filter.test_date_to = None
        self.filter.test_series = []
        for index in range(self.test_series.GetCount()):
            if self.test_series.IsChecked(index):
                self.filter.test_series.append(self.test_series_items[index])
        class_, cookie = self.properties.GetFirstChild(self.properties.GetRootItem())
        properties = []
        while class_.IsOk():
            item, item_cookie = self.properties.GetFirstChild(class_)
            while item.IsOk():
                state = self.properties.GetItemData(item)
                if state.checked:
                    properties.append(state.prop)
                item, item_cookie = self.properties.GetNextChild(class_, item_cookie)
            class_, cookie = self.properties.GetNextChild(class_, cookie)
        self.filter.properties = properties
        self.filter.properties_hide_no_values_samples = self.properties_hide_no_values_samples.GetValue()
        wx.PostEvent(self, FilterChangedEvent())


def make_filter(filter):
    query = (
        select(o for o in PMSample)
        .order_by(lambda a: (a.pm_sample_set.pm_test_series.Number, a.pm_sample_set.Number, a.Number))
        .prefetch(
            PMSample.pm_sample_property_values,
            PMSample.pm_sample_set,
            PMSampleSet.mine_object,
            PMSampleSet.petrotype_struct,
            PetrotypeStruct.petrotype,
        )  # сразу подгружаем связаную таблицу знчений свойств (чтобы в цикле не загружать по отдельности)
    )
    date_from = encode_date(filter.test_date_from) if filter.test_date_from is not None else None
    date_to = encode_date(filter.test_date_to) if filter.test_date_to is not None else None

    if filter.use_filter and filter.petrotypes is not None:
        query = query.filter(lambda a: a.pm_sample_set.petrotype_struct.petrotype in filter.petrotypes)
    if filter.use_filter and filter.fields is not None:
        query = query.filter(lambda a: a.pm_sample_set.mine_object in filter.fields)
    if filter.use_filter and date_from is not None:
        query = query.filter(lambda a: a.pm_sample_set.TestDate >= date_from)
    if filter.use_filter and date_to is not None:
        query = query.filter(lambda a: a.pm_sample_set.TestDate <= date_to)
    if filter.use_filter and filter.exclude_none_test_date:
        query = query.filter(lambda a: a.pm_sample_set.TestDate != None)  # noqa: E711
    if filter.use_filter and filter.test_series is not None:
        query = query.filter(lambda a: a.pm_sample_set.pm_test_series in filter.test_series)

    return query


class PmGridModel(Model):
    def __init__(self):
        super().__init__()
        self.mode = "compact"
        self.compact_columns = {
            "mine_object": Column("mine_object", StringCellType(), "Месторождение", "Месторождение"),
            "sample": Column("sample", StringCellType(), "Образец", "Образец"),
            "petrotype": Column("petrotype", StringCellType(), "Петротип", "Петротип"),
            "mass_air_dry": Column(
                "mass_air_dry",
                FloatCellType(),
                "Масса в воздушно-\nсухом состоянии, г",
                "Масса в воздушно-сухом состоянии, г",
            ),
        }
        self.extended_columns = {
            "test_series": Column("test_series", StringCellType(), "Набор испытаний", "Набор испытаний"),
            "mine_object": Column("mine_object", StringCellType(), "Месторождение", "Месторождение"),
            "sample_set": Column("sample_set", StringCellType(), "Проба", "Проба"),
            "sample": Column("sample", StringCellType(), "Образец", "Образец"),
            "test_date": Column("test_date", StringCellType(), "Дата испытания", "Дата испытания"),
            "bore_hole": Column("bore_hole", StringCellType(), "Скважина", "Скважина"),
            "petrotype": Column("petrotype", StringCellType(), "Петротип", "Петротип"),
            "length_1": Column("length_1", FloatCellType(), "Диаметр/ Сторона 1", "Диаметр/ Сторона 1"),
            "length_2": Column("length_2", FloatCellType(), "Сторона 2", "Сторона 2"),
            "height": Column("height", FloatCellType(), "Высота", "Высота"),
            "mass_air_dry": Column(
                "mass_air_dry",
                FloatCellType(),
                "Масса в воздушно-\nсухом состоянии, г",
                "Масса в воздушно-сухом состоянии, г",
            ),
        }
        self.property_columns = {}
        self.columns_cache = list(self.compact_columns.values()) + list(self.property_columns.values())
        self.rows = []
        self.filter = Filter()

    def make_columns_cache(self):
        if self.mode == "compact":
            self.columns_cache = list(self.compact_columns.values()) + list(self.property_columns.values())
        else:
            self.columns_cache = list(self.extended_columns.values()) + list(self.property_columns.values())

    def get_columns(self):
        return self.columns_cache

    def get_value_at(self, col, row) -> str:
        col_id = self.columns_cache.__getitem__(col).id
        if col_id in self.rows[row]:
            return self.rows[row][col_id]
        return ""

    def get_rows_count(self) -> int:
        return len(self.rows)

    def is_changed(self) -> bool:
        return False

    def total_rows(self):
        return len(self.rows)

    def set_value_at(self, col, row, value): ...
    def insert_row(self, row): ...
    def delete_row(self, row): ...
    def get_row_state(self, row): ...
    def validate(self): ...
    def save(self): ...
    def have_changes(self):
        return False

    def set_filter(self, filter):
        self.filter = filter
        self.load()

    def change_mode(self, mode="compact"):
        self.mode = mode
        self.load()

    @db_session
    def load(self):
        start_time = time.perf_counter()
        self.rows = []
        query = make_filter(self.filter)
        samples = query[:]
        # Выбираем все свойства - значения которых записны для выбранных образцов

        if self.filter.use_filter and self.filter.properties is not None:
            properties = select(o for o in PmProperty if o in self.filter.properties)
        else:
            properties = select(
                o
                for o in PmProperty
                if exists(v for v in PmSamplePropertyValue if v.pm_property == o and v.pm_sample in samples)
            )

        properties = properties[:]

        is_compact = self.mode == "compact"

        # Добавляем столбцы свойств для выбраных образцов
        self.property_columns = {}
        for property in properties:
            name = property.Name + (", " + property.Unit if property.Unit is not None else "")
            name = textwrap.fill(name, width=20)
            self.property_columns[property.Code] = Column(
                property.Code, FloatCellType(), name_short=name, name_long=name
            )
            if not is_compact:
                # Если расширенный режим - добавляем метод испытания с кодом "<код_свойства>_method"
                self.property_columns[property.Code + "_method"] = Column(
                    "%s_method" % property.Code, StringCellType(), name_short="Метод", name_long="Метод"
                )

        # Добавляем все образцы в строки таблицы
        for sample in query:
            if self.filter.properties_hide_no_values_samples:
                if not any(
                    [value.pm_property for value in sample.pm_sample_property_values if value.pm_property in properties]
                ):
                    continue

            # Набиваем все для обоих режимов, дальше исходя из заголовка таблица заберет то что нужно
            row = {
                "test_series": sample.pm_sample_set.pm_test_series.Name,
                "mine_object": sample.pm_sample_set.mine_object.Name,
                "sample_set": str(sample.pm_sample_set.Number),
                "sample": str(sample.Number),
                "test_date": str(sample.pm_sample_set.TestDate) if sample.pm_sample_set.TestDate is not None else "",
                "petrotype": sample.pm_sample_set.petrotype_struct.petrotype.Name,
                "mass_air_dry": str(sample.MassAirDry) if sample.MassAirDry is not None else "",
                "length_1": str(sample.Length1) if sample.Length1 is not None else "",
                "length_2": str(sample.Length2) if sample.Length2 is not None else "",
                "height": str(sample.Height) if sample.Height is not None else "",
            }
            if sample.orig_sample_set.SampleType == "CORE":
                row["bore_hole"] = sample.orig_sample_set.bore_hole.get_number()
            value = [o for o in sample.pm_sample_property_values if o.pm_property in properties]
            for value in value:
                row[value.pm_property.Code] = str(value.Value)
                row["%s_method" % value.pm_property.Code] = str(value.pm_test_method.Name)
            self.rows.append(row)

        self.make_columns_cache()
        end_time = time.perf_counter()
        app_ctx().main.statusbar.SetStatusText("Время генерации: %f с." % (end_time - start_time), 3)


class PmStartGridModel(Model):
    def __init__(self):
        super().__init__()
        self.columns = {
            "pm_property": Column(id="pm_property", name_short="Свойство", cell_type=StringCellType()),
            "litotype": Column(id="litotype", name_short="Литотип", cell_type=StringCellType()),
            "pm_root_mean_sqr_dev": Column(
                id="pm_root_mean_sqr_dev", name_short="Среднеквадратичное\nотклонение", cell_type=FloatCellType()
            ),
            "pm_variation_coeff": Column(
                id="pm_variation_coeff", name_short="Коэффициент\nвариации", cell_type=FloatCellType()
            ),
            "pm_avg_value": Column(id="pm_avg_value", name_short="Среднее\nзначение", cell_type=FloatCellType()),
            "pm_min_value": Column(id="pm_min_value", name_short="Мин.\nзначение", cell_type=FloatCellType()),
            "pm_max_value": Column(id="pm_max_value", name_short="Макс.\nзначение", cell_type=FloatCellType()),
            "pm_sample_cnt": Column(id="pm_sample_cnt", name_short="Количество\nобразцов", cell_type=NumberCellType()),
            "pm_method": Column(id="pm_method", name_short="Метод испытаний", cell_type=StringCellType()),
        }
        self.filter = Filter()
        self.rows = []

    def get_columns(self):
        return list(self.columns.values())

    def get_value_at(self, col, row) -> str:
        col_id = list(self.columns.values())[col].id
        if col_id in self.rows[row]:
            return self.rows[row][col_id]
        return ""

    def get_rows_count(self) -> int:
        return len(self.rows)

    def is_changed(self) -> bool:
        return False

    def total_rows(self):
        return len(self.rows)

    def set_value_at(self, col, row, value): ...
    def insert_row(self, row): ...
    def delete_row(self, row): ...
    def get_row_state(self, row): ...
    def validate(self): ...
    def save(self): ...
    def have_changes(self):
        return False

    def set_filter(self, filter):
        self.filter = filter
        self.load()

    @db_session
    def load(self):
        self.rows = []

        from collections import defaultdict

        data = defaultdict(list)
        query = make_filter(self.filter)
        samples = query[:]
        # Выбираем все свойства - значения которых записны для выбранных обраsзцов
        properties = select(
            o
            for o in PmProperty
            if exists(v for v in PmSamplePropertyValue if v.pm_property == o and v.pm_sample in samples)
        )

        if self.filter.use_filter and self.filter.properties is not None:
            properties = properties.filter(lambda a: a in self.filter.properties)

        properties = properties[:]

        property_values = select(
            v for v in PmSamplePropertyValue if v.pm_sample in samples and v.pm_property in properties
        )[:]

        for value in property_values:
            # Аггрегируем значения по свойствам, литотипам и методам испытаний
            data[
                (value.pm_property, value.pm_sample.pm_sample_set.petrotype_struct.petrotype, value.pm_test_method)
            ].append(value.Value)

        for (property, petrotype, method), values in data.items():
            # Считаем статистику по свойству
            avg_value = sum(values) / len(values)
            min_value = min(values)
            max_value = max(values)
            root_mean_sqr_dev = (sum((v - avg_value) ** 2 for v in values) / len(values)) ** 0.5
            variation_coeff = root_mean_sqr_dev / avg_value if avg_value != 0 else 0

            # Считаем количество образцов с этим свойством
            sample_cnt = len(values)

            # Считаем литотипы для этого свойства
            litotype = petrotype.Name if petrotype else ""

            self.rows.append(
                {
                    "pm_property": property.Name,
                    "litotype": litotype,
                    "pm_root_mean_sqr_dev": str(root_mean_sqr_dev),
                    "pm_variation_coeff": str(variation_coeff),
                    "pm_avg_value": str(avg_value),
                    "pm_min_value": str(min_value),
                    "pm_max_value": str(max_value),
                    "pm_sample_cnt": str(sample_cnt),
                    "pm_method": method.Name if method else "",
                }
            )

        self.rows.sort(key=lambda x: (x["pm_property"], x["litotype"], x["pm_method"]))


class PmSummaryTable(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.filter = Filter()
        self.started = False
        self.model = PmGridModel()
        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        right = wx.Notebook(self.splitter, style=wx.NB_LEFT)
        p = wx.Panel(right)
        p_sz = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(p, style=wx.TB_FLAT | wx.TB_HORZ_TEXT)
        tool = self.toolbar.AddTool(wx.ID_COPY, "Копировать", get_icon("copy", scale_to=16), "Копировать")
        tool.Enable(False)
        self.toolbar.AddTool(wx.ID_OPEN, "Открыть в Excell", get_icon("excel"))
        self.toolbar.Realize()
        p_sz.Add(self.toolbar, 0, wx.EXPAND)
        self.table = GridEditor(
            p, self.model, app_ctx().main.menu, self.toolbar, app_ctx().main.statusbar, header_height=70, read_only=True
        )
        p_sz.Add(self.table, 1, wx.EXPAND)
        p.SetSizer(p_sz)
        right.AddPage(p, "Таблица")
        p_stats = wx.Panel(right)
        self.stats_model = PmStartGridModel()
        p_stats_sz = wx.BoxSizer(wx.VERTICAL)
        self.stats_table = GridEditor(
            p_stats,
            self.stats_model,
            app_ctx().main.menu,
            self.toolbar,
            app_ctx().main.statusbar,
            header_height=40,
            read_only=True,
        )
        self.stats_table.auto_size_columns()
        p_stats_sz.Add(self.stats_table, 1, wx.EXPAND)
        p_stats.SetSizer(p_stats_sz)
        right.AddPage(p_stats, "Статистика")
        self.left = wx.ScrolledWindow(self.splitter)
        self.left_notebook = wx.lib.agw.flatnotebook.FlatNotebookCompatible(
            self.left, agwStyle=wx.lib.agw.flatnotebook.FNB_NO_X_BUTTON
        )
        l_sz = wx.BoxSizer(wx.VERTICAL)
        self.filter_panel = FilterPanel(self.left, filter=self.filter)
        self.left_notebook.AddPage(self.filter_panel, "Фильтр")
        l_sz.Add(self.left_notebook, 1, wx.EXPAND)
        self.left.SetSizer(l_sz)
        self.splitter.SplitVertically(self.left, right, 320)
        self.splitter.SetMinimumPaneSize(250)
        self.splitter.SetSashGravity(0)
        sz.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.bind_all()

    def bind_all(self):
        self.toolbar.Bind(wx.EVT_TOOL, self.on_refresh, id=wx.ID_REFRESH)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_toggle_extended_mode, id=wx.ID_PREVIEW)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_copy, id=wx.ID_COPY)
        self.filter_panel.Bind(EVT_FILTER_CHANGED, self.on_filter_changed)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_open_in_excell, id=wx.ID_OPEN)
        self.table.Bind(EVT_GRID_EDITOR_STATE_CHANGED, self.on_editor_state_changed)

    def on_open_in_excell(self, event):
        self.table.open_in_excell(only_selection=False)

    def on_copy(self, event):
        self.table.copy()

    def switch_to_extended_mode(self):
        self.model.change_mode("extended")
        self.table._render()

    def switch_to_compact_mode(self):
        self.model.change_mode("compact")
        self.table._render()

    def on_editor_state_changed(self, event):
        self.update_controls_state()

    def on_filter_changed(self, event):
        self.filter = self.filter_panel.filter
        self.model.set_filter(self.filter)
        self.model.load()
        self.table._render()
        self.table.auto_size_columns()
        self.stats_model.set_filter(self.filter)
        self.stats_model.load()
        self.stats_table._render()
        self.stats_table.auto_size_columns()

    def on_toggle_extended_mode(self, event=None):
        if self.toolbar.GetToolState(wx.ID_PREVIEW):
            self.switch_to_extended_mode()
        else:
            self.switch_to_compact_mode()
        app_ctx().config.pm_extended_mode = self.toolbar.GetToolState(wx.ID_PREVIEW)

    def on_refresh(self, event):
        self.model.load()
        self.table._render()
        self.table.auto_size_columns()
        self.stats_model.load()
        self.stats_table._render()
        self.stats_table.auto_size_columns()

    def start(self):
        if not self.started:
            if app_ctx().config.pm_extended_mode:
                self.toolbar.ToggleTool(wx.ID_PREVIEW, True)
                self.toolbar.Realize()
                self.switch_to_extended_mode()
            self.model.load()
            self.table._render()
            self.stats_model.load()
            self.stats_table._render()
            self.started = True
            self.table.apply_controls()
            self.table.auto_size_columns()

    def end(self):
        self.table.remove_controls()

    def update_controls_state(self):
        self.toolbar.EnableTool(wx.ID_COPY, self.table.can_copy())
