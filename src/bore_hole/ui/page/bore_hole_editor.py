import wx
import wx.lib.agw.flatnotebook
import wx.propgrid
from pony.orm import commit, db_session, select

from src.ctx import app_ctx
from src.database import BoreHole, MineObject, OrigSampleSet, Station
from src.datetimeutil import decode_date, encode_date
from src.mine_object.ui.choice import Choice as MineObjectChoice
from src.ui.flatnotebook import xFlatNotebook
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
        self.right = xFlatNotebook(self.splitter, agwStyle=wx.lib.agw.flatnotebook.FNB_NO_X_BUTTON)
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
        self.splitter.SplitVertically(self.left, self.right, 270)
        self.splitter.SetMinimumPaneSize(250)
        sz.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        if not self.is_new:
            self.field_mine_object.Disable()
            self.supplied_data.start(self.o)
            orig_sample_set = select(o for o in OrigSampleSet if o.bore_hole == self.o).first()
            if orig_sample_set is not None:
                self.core_supplied_data.start(orig_sample_set)
            self.set_fields()
            app_ctx().recently_used.remember("tree", self.o.__class__.__qualname__, self.o.RID)
        else:
            self.right.enable_tab(2, enable=False)
            self.field_mine_object.SetValue(parent_object)
        self.bind_all()

    def set_fields(self):
        if self.o.station is not None:
            self.field_mine_object.SetValue(self.o.station)
        else:
            self.field_mine_object.SetValue(self.o.mine_object)
        self.field_name.SetValue(self.o.Name)
        self.field_comment.SetValue(self.o.Comment if self.o.Comment is not None else "")
        self.field_start_date.SetValue(str(decode_date(self.o.StartDate)))
        if self.o.EndDate is not None:
            self.field_end_date.SetValue(str(decode_date(self.o.EndDate)))
        self.props.SetPropertyValues(
            {"Azimuth": self.o.Azimuth, "Tilt": self.o.Tilt, "Diameter": self.o.Diameter, "Length": self.o.Length}
        )

    def bind_all(self):
        self.toolbar.Bind(wx.EVT_TOOL, self.on_save_and_close, id=wx.ID_SAVEAS)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_save, id=wx.ID_SAVE)

    @db_session
    def on_orig_no_updated(self, event):
        event.Skip()
        if isinstance(self.parent_object, MineObject):
            parent = MineObject[self.parent_object.RID]
            name = str(self.field_number.GetValue()) + " на"
            number = str(self.field_number.GetValue())
        else:
            station = Station[self.parent_object.RID]
            parent = station.mine_object
            name = station.Number.split("@")[0] + "/" + str(self.field_number.GetValue()) + " на"
            number = str(self.field_number.GetValue()) + "@" + station.Number.split("@")[0]
        while parent.Level > 0:
            name += " " + parent.Name
            number += "@" + (parent.Name if len(parent.Name) < 4 else parent.Name[:4])
            parent = parent.parent

        self.field_name.SetValue(name)
        self.number = number

    def get_name(self):
        if self.is_new:
            return "(новый)"
        return self.o.get_tree_name()

    def get_icon(self):
        return get_icon("file")
