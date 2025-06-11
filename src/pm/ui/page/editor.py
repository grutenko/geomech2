from typing import List

import wx
import wx.lib.agw.flatnotebook
from pony.orm import db_session, select

from src.ctx import app_ctx
from src.database import PmSampleSetPropertyValue, PMTestSeries
from src.mine_object.ui.choice import Choice as MineObjectChoice
from src.ui.flatnotebook import xFlatNotebook
from src.ui.grid import (
    EVT_GRID_EDITOR_STATE_CHANGED,
    Column,
    FloatCellType,
    GridEditor,
    Model,
    StringCellType,
    NumberCellType,
)
from src.ui.icon import get_icon
from src.ui.supplied_data import SuppliedDataWidget
from src.ui.validators import DateValidator, TextValidator
from src.datetimeutil import decode_date, encode_date

from .samples import SamplesWidget


class StatsGridModel(Model):
    def __init__(self):
        self.columns = {
            "pm_property": Column(id="pm_property", name_short="Свойство", cell_type=StringCellType()),
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
        self.rows = []
        self.pm_sample_set = None

    def get_columns(self) -> List[Column]:
        return list(self.columns.values())

    def get_value_at(self, col, row) -> str:
        col_id = self.get_columns().__getitem__(col).id
        if col_id in self.rows[row]:
            return self.rows[row][col_id]
        return ""

    def get_rows_count(self) -> int:
        return len(self.rows)

    def is_changed(self) -> bool:
        return False

    def total_rows(self):
        return len(self.rows)

    def set_pm_sample_set(self, pm_sample_set):
        self.pm_sample_set = pm_sample_set
        self.load()

    @db_session
    def load(self):
        self.rows = []
        rows = select(o for o in PmSampleSetPropertyValue if o.pm_sample_set == self.pm_sample_set).order_by(
            PmSampleSetPropertyValue.pm_property
        )[:]
        for row in rows:
            self.rows.append(
                {
                    "pm_property": row.pm_property.Name,
                    "pm_method": row.pm_method.Name,
                    "pm_min_value": str(row.MinValue),
                    "pm_max_value": str(row.MaxValue),
                    "pm_avg_value": str(row.AvgValue),
                    "pm_sample_cnt": str(row.SampleCnt),
                    "pm_root_mean_sqr_dev": str(row.RootMeanSqrDev),
                    "pm_variation_coeff": str(row.VariationCoef),
                }
            )

    def set_value_at(self, col, row, value): ...
    def insert_row(self, row): ...
    def delete_row(self, row): ...
    def get_row_state(self, row): ...
    def validate(self): ...
    def save(self): ...
    def have_changes(self):
        return False


class StatsWidget(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(self, style=wx.TB_FLAT | wx.TB_HORZ_TEXT)
        self.toolbar.AddTool(wx.ID_REFRESH, "Обновить", get_icon("update"))
        tool = self.toolbar.AddTool(wx.ID_COPY, "Копировать", get_icon("copy", scale_to=16), "Копировать")
        tool.Enable(False)
        self.toolbar.AddTool(wx.ID_OPEN, "Открыть в Excell", get_icon("excel"))
        self.toolbar.Bind(wx.EVT_TOOL, self.on_refresh, id=wx.ID_REFRESH)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_copy, id=wx.ID_COPY)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_open_in_excel, id=wx.ID_OPEN)
        self.toolbar.Realize()
        sz.Add(self.toolbar, 0, wx.EXPAND)
        self.model = StatsGridModel()
        self.grid = GridEditor(
            self, self.model, app_ctx().main.menu, self.toolbar, app_ctx().main.statusbar, 35, read_only=True
        )
        self.grid.Bind(EVT_GRID_EDITOR_STATE_CHANGED, self.on_grid_state_changed)
        self.grid.auto_size_columns()
        sz.Add(self.grid, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()

    def on_grid_state_changed(self, event):
        self.update_controls_state()

    def on_refresh(self, event):
        self.model.load()  # перечитываем даные из БД
        self.grid._render()  # перерисовываем грид по новой модели
        self.grid.auto_size_columns()
        self.update_controls_state()

    def on_copy(self, event):
        self.grid.copy()

    def on_open_in_excel(self, event):
        self.grid.open_in_excell()

    def start(self, pm_sample_set):
        self.model.set_pm_sample_set(pm_sample_set)
        self.grid._render()
        self.grid.auto_size_columns()
        self.update_controls_state()

    def update_controls_state(self):
        self.toolbar.EnableTool(wx.ID_COPY, self.grid.can_copy())


class SummaryGridModel(Model):
    def __init__(self):
        self.columns = {"Number": Column("Number", StringCellType(), "№ образца", "№ образца")}
        self.rows = []
        self.pm_sample_set = None

    def set_pm_sample_set(self, pm_sample_set):
        self.pm_sample_set = pm_sample_set

    def get_columns(self) -> List[Column]:
        return list(self.columns.values())

    def get_value_at(self, col, row) -> str:
        col_id = self.get_columns().__getitem__(col).id
        if col_id in self.rows[row]:
            return self.rows[row][col_id]
        return ""

    def get_rows_count(self) -> int:
        return len(self.rows)

    def is_changed(self) -> bool:
        return False

    def total_rows(self):
        return len(self.rows)

    def load(self): ...

    def set_value_at(self, col, row, value): ...
    def insert_row(self, row): ...
    def delete_row(self, row): ...
    def get_row_state(self, row): ...
    def validate(self): ...
    def save(self): ...
    def have_changes(self):
        return False


class SummaryWidget(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(self, style=wx.TB_FLAT | wx.TB_HORZ_TEXT)
        self.toolbar.AddTool(wx.ID_REFRESH, "Обновить", get_icon("update"))
        tool = self.toolbar.AddTool(wx.ID_COPY, "Копировать", get_icon("copy", scale_to=16), "Копировать")
        tool.Enable(False)
        self.toolbar.AddTool(wx.ID_OPEN, "Открыть в Excell", get_icon("excel"))
        self.toolbar.Bind(wx.EVT_TOOL, self.on_refresh, id=wx.ID_REFRESH)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_copy, id=wx.ID_COPY)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_open_in_excel, id=wx.ID_OPEN)
        self.toolbar.Realize()
        sz.Add(self.toolbar, 0, wx.EXPAND)
        self.model = SummaryGridModel()
        self.grid = GridEditor(
            self, self.model, app_ctx().main.menu, self.toolbar, app_ctx().main.statusbar, 35, read_only=True
        )
        self.grid.Bind(EVT_GRID_EDITOR_STATE_CHANGED, self.on_grid_state_changed)
        self.grid.auto_size_columns()
        sz.Add(self.grid, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()

    def on_grid_state_changed(self, event):
        self.update_controls_state()

    def on_refresh(self, event):
        self.model.load()  # перечитываем даные из БД
        self.grid._render()  # перерисовываем грид по новой модели
        self.grid.auto_size_columns()
        self.update_controls_state()

    def on_copy(self, event):
        self.grid.copy()

    def on_open_in_excel(self, event):
        self.grid.open_in_excell()

    def start(self, pm_sample_set):
        self.model.set_pm_sample_set(pm_sample_set)
        self.grid._render()
        self.grid.auto_size_columns()
        self.update_controls_state()

    def update_controls_state(self):
        self.toolbar.EnableTool(wx.ID_COPY, self.grid.can_copy())


class PmSampleSetEditor(wx.Panel):
    @db_session
    def __init__(self, parent, is_new=False, o=None, parent_object=None):
        self.is_new = is_new
        self.o = o
        self.parent_object = parent_object
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.left = wx.ScrolledWindow(self.splitter)
        p_sz = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(self.left, style=wx.TB_FLAT | wx.TB_HORZ_TEXT)
        self.toolbar.AddTool(wx.ID_SAVE, "Сохранить", get_icon("save"))
        self.toolbar.Realize()
        p_sz.Add(self.toolbar, 0, wx.EXPAND)
        p_sz_in = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self.left, label="Месторождение *")
        p_sz_in.Add(label, 0)
        self.field_mine_object = MineObjectChoice(self.left, mode="field")
        p_sz_in.Add(self.field_mine_object, 0, wx.EXPAND | wx.BOTTOM, border=10)
        label = wx.StaticText(self.left, label="Номер *")
        p_sz_in.Add(label, 0, wx.EXPAND)
        self.field_number = wx.TextCtrl(self.left)
        self.field_number.SetValidator(TextValidator(lenMin=1, lenMax=256))
        p_sz_in.Add(self.field_number, 0, wx.EXPAND | wx.BOTTOM, border=10)
        label = wx.StaticText(self.left, label="Комментарий")
        p_sz_in.Add(label, 0, wx.EXPAND)
        self.field_comment = wx.TextCtrl(self.left, style=wx.TE_MULTILINE, size=(-1, 100))
        p_sz_in.Add(self.field_comment, 0, wx.EXPAND | wx.BOTTOM, border=10)
        label = wx.StaticText(self.left, label="Дата отбора")
        p_sz_in.Add(label, 0)
        self.field_set_date = wx.TextCtrl(self.left)
        self.field_set_date.SetValidator(DateValidator())
        p_sz_in.Add(self.field_set_date, 0, wx.EXPAND | wx.BOTTOM, border=10)

        label = wx.StaticText(self.left, label="Дата испытания")
        p_sz_in.Add(label, 0)
        self.field_test_date = wx.TextCtrl(self.left)
        self.field_test_date.SetValidator(DateValidator(allow_empty=True))
        p_sz_in.Add(self.field_test_date, 0, wx.EXPAND | wx.BOTTOM, border=10)

        p_sz.Add(p_sz_in, 1, wx.EXPAND | wx.ALL, border=10)
        self.left.SetSizer(p_sz)
        self.left.SetVirtualSize(self.left.GetBestSize() + (250, 250))
        self.left.SetScrollRate(10, 10)
        self.right = xFlatNotebook(self.splitter, agwStyle=wx.lib.agw.flatnotebook.FNB_NO_X_BUTTON)
        self.samples = SamplesWidget(self.right)
        self.right.AddPage(self.samples, "Образцы")
        self.stats = StatsWidget(self.right)
        self.right.AddPage(self.stats, "Статистика")
        self.summary = SummaryWidget(self.right)
        self.right.AddPage(self.summary, "Сводка")
        self.splitter.SplitVertically(self.left, self.right, 270)
        self.splitter.SetMinimumPaneSize(250)
        sz.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.SetSizer(sz)
        self.Layout()
        self.right.enable_tab(0, enable=False)
        self.right.enable_tab(1, enable=False)
        self.right.enable_tab(2, enable=False)
        if not self.is_new:
            self.samples.start(self.o)
            self.stats.start(self.o)
            self.right.enable_tab(0, enable=True)
            self.right.enable_tab(1, enable=True)
            self.right.enable_tab(2, enable=True)
            self.set_fields()

    def set_fields(self):
        self.field_mine_object.SetValue(self.o.mine_object)
        self.field_number.SetValue(self.o.Number)
        self.field_comment.SetValue(self.o.Comment if self.o.Comment is not None else "")
        self.field_set_date.SetValue(decode_date(self.o.SetDate) if self.o.SetDate is not None else "")
        self.field_test_date.SetValue(decode_date(self.o.TestDate) if self.o.TestDate is not None else "")

    @db_session
    def get_name(self):
        if self.is_new:
            return "(новый)"

        return "%s %s" % (self.o.get_tree_name(), PMTestSeries[self.o.pm_test_series.RID].get_tree_name())

    def get_icon(self):
        return get_icon("file")
