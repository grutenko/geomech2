import wx
import wx.lib.agw.flatnotebook
import wx.propgrid
from pony.orm import commit, db_session, select

from src.ctx import app_ctx
from src.database import BoreHole, MineObject, OrigSampleSet, Station
from src.datetimeutil import decode_date, encode_date
from src.mine_object.ui.choice import Choice as MineObjectChoice
from src.ui.icon import get_icon
from src.ui.page import PageHdrChangedEvent
from src.ui.supplied_data import SuppliedDataWidget
from src.ui.validators import DateValidator, TextValidator


class BoreHoleEditor(wx.Panel):
    def __init__(self, parent, is_new: bool = False, o=None, parent_object=None):
        super().__init__(parent)
        self.is_new = is_new
        self.o = o
        self.parent_object = parent_object
        sz = wx.BoxSizer(wx.VERTICAL)
        self.splitter = wx.SplitterWindow(self)
        self.left = wx.Panel(self.splitter)
        l_sz = wx.BoxSizer(wx.VERTICAL)
        self.left.SetSizer(l_sz)
        self.right = wx.lib.agw.flatnotebook.FlatNotebookCompatible(
            self.splitter, agwStyle=wx.lib.agw.flatnotebook.FNB_NO_X_BUTTON
        )
        p = wx.Panel(self.right)
        p_sz = wx.BoxSizer(wx.VERTICAL)
        self.props = wx.propgrid.PropertyGrid(p, style=wx.propgrid.PG_SPLITTER_AUTO_CENTER)
        self.props.Append(wx.propgrid.FloatProperty("Азимут (град.)", "Azimuth"))
        self.props.Append(wx.propgrid.FloatProperty("Налон (град.)", "Tilt"))
        self.props.Append(wx.propgrid.FloatProperty("Длина (м)", "Length"))
        self.props.Append(wx.propgrid.FloatProperty("Диаметр (мм)", "Diameter"))
        p_sz.Add(self.props, 1, wx.EXPAND)
        p.SetSizer(p_sz)
        self.right.AddPage(p, "Параметры [*]")
        p = wx.Panel(self.right)
        self.right.AddPage(p, "Координаты [*]")
        p = wx.Panel(self.right)
        p_sz = wx.BoxSizer(wx.VERTICAL)
        n = wx.Notebook(p)
        if is_new:
            deputy_text = "Недоступно для новых объектов. Сначала сохраните."
        else:
            deputy_text = "Набор образов не был добавлен"
        self.core_supplied_data = SuppliedDataWidget(n, deputy_text=deputy_text)
        n.AddPage(self.core_supplied_data, "Сопутствующие материалы")
        p_sz.Add(n, 1, wx.EXPAND)
        p.SetSizer(p_sz)
        self.right.AddPage(p, "Керн")
        self.supplied_data = SuppliedDataWidget(
            self.right, deputy_text="Недоступно для новых объектов. Сначала сохраните."
        )
        self.right.AddPage(self.supplied_data, "Сопуствующие материалы")
        self.splitter.SplitVertically(self.left, self.right, 250)
        self.splitter.SetMinimumPaneSize(250)
        sz.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()

    def get_name(self):
        if self.is_new:
            return "(новый)"
        return self.o.get_tree_name()

    def get_icon(self):
        return get_icon("file")
