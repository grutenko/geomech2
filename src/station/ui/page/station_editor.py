import pubsub.pub
import wx
import wx.lib.agw.flatnotebook
import wx.propgrid
from pony.orm import commit, db_session, select

from src.ctx import app_ctx
from src.database import MineObject, Station
from src.datetimeutil import decode_date, encode_date
from src.mine_object.ui.choice import Choice as MineObjectChoice
from src.ui.flatnotebook import xFlatNotebook
from src.ui.icon import get_icon
from src.ui.page import PageHdrChangedEvent
from src.ui.supplied_data import SuppliedDataWidget
from src.ui.validators import DateValidator, TextValidator


class StationEditor(wx.Panel):
    def __init__(self, parent, is_new=False, o=None, parent_object=None):
        super().__init__(parent)
        self.is_new = is_new
        self.o = o
        self.parent_object = parent_object
        self.mine_objects = []
        self.coord_systems = []
        sz = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(self, style=wx.TB_HORZ_TEXT)
        self.toolbar.AddTool(wx.ID_SAVE, "Сохранить", get_icon("save"))
        self.toolbar.Realize()
        sz.Add(self.toolbar, 0, wx.EXPAND)
        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.left = wx.ScrolledWindow(self.splitter)
        left_sz = wx.BoxSizer(wx.VERTICAL)
        left_sz_in = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(self.left, label="Горный объект *")
        left_sz_in.Add(label, 0)
        self.field_mine_object = MineObjectChoice(self.left)
        left_sz_in.Add(self.field_mine_object, 0, wx.EXPAND | wx.BOTTOM, border=10)

        label = wx.StaticText(self.left, label="Название *")
        left_sz_in.Add(label, 0)
        self.field_name = wx.TextCtrl(self.left, size=wx.Size(250, 25))
        self.field_name.SetValidator(TextValidator(lenMin=1, lenMax=256))
        left_sz_in.Add(self.field_name, 0, wx.EXPAND | wx.BOTTOM, border=10)

        label = wx.StaticText(self.left, label="Комментарий")
        left_sz_in.Add(label, 0)
        self.field_comment = wx.TextCtrl(self.left, size=wx.Size(250, 100), style=wx.TE_MULTILINE)
        self.field_comment.SetValidator(TextValidator(lenMin=0, lenMax=256))
        left_sz_in.Add(self.field_comment, 0, wx.EXPAND | wx.BOTTOM, border=10)

        label = wx.StaticText(self.left, label="Дата начала")
        left_sz_in.Add(label, 0)
        self.field_start_date = wx.TextCtrl(self.left, size=wx.Size(250, 25))
        self.field_start_date.SetValidator(DateValidator())
        left_sz_in.Add(self.field_start_date, 0, wx.EXPAND | wx.BOTTOM, border=10)

        label = wx.StaticText(self.left, label="Дата окончания")
        left_sz_in.Add(label, 0)
        self.field_end_date = wx.TextCtrl(self.left, size=wx.Size(250, 25))
        self.field_end_date.SetValidator(DateValidator(allow_empty=True))
        left_sz_in.Add(self.field_end_date, 0, wx.EXPAND | wx.BOTTOM, border=10)

        left_sz.Add(left_sz_in, 1, wx.EXPAND | wx.ALL, border=10)
        self.left.SetSizer(left_sz)
        self.left.SetVirtualSize(self.left.GetBestSize() + (250, 250))
        self.left.SetScrollRate(10, 10)

        self.right = xFlatNotebook(self.splitter, agwStyle=wx.lib.agw.flatnotebook.FNB_NO_X_BUTTON)
        self.supplied_data = SuppliedDataWidget(
            self.right, deputy_text="Недоступно для новых объектов. Сначала сохраните."
        )
        self.coords = wx.propgrid.PropertyGrid(self.right, style=wx.propgrid.PG_SPLITTER_AUTO_CENTER)
        self.coords.Append(wx.propgrid.FloatProperty("X Мин.", "X_Min"))
        self.coords.Append(wx.propgrid.FloatProperty("Y Мин.", "Y_Min"))
        self.coords.Append(wx.propgrid.FloatProperty("Z Мин.", "Z_Min"))
        self.coords.Append(wx.propgrid.FloatProperty("X Макс.", "X_Max"))
        self.coords.Append(wx.propgrid.FloatProperty("Y Макс.", "Y_Max"))
        self.coords.Append(wx.propgrid.FloatProperty("Z Макс.", "Z_Max"))
        self.right.AddPage(self.coords, "Координаты")
        self.right.AddPage(self.supplied_data, "Сопуствующие материалы")
        self.splitter.SplitVertically(self.left, self.right, 270)
        self.splitter.SetMinimumPaneSize(250)
        sz.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.bind_all()
        if not self.is_new:
            self.set_fields()
            self.field_mine_object.Disable()
            self.supplied_data.start(self.o)
        else:
            self.right.enable_tab(1, enable=False)

        if parent_object is not None:
            self.field_mine_object.SetValue(parent_object)

    @db_session
    def on_orig_no_updated(self, event):
        event.Skip()
        parent = MineObject[self.parent_object.RID]
        name = str(self.field_number.GetValue()) + " на"
        number = str(self.field_number.GetValue())
        while parent is not None:
            name += " " + parent.Name
            number += "@" + (parent.Name if len(parent.Name) < 4 else parent.Name[:4])
            parent = parent.parent
        self.field_name.SetValue(name)
        self.number = number

    def bind_all(self):
        self.toolbar.Bind(wx.EVT_TOOL, self.on_save, id=wx.ID_SAVE)

    @db_session
    def set_fields(self):
        self.field_mine_object.SetValue(self.o.mine_object)
        self.field_name.SetValue(self.o.Name)
        self.field_comment.SetValue(self.o.Comment if self.o.Comment is not None else "")
        self.field_start_date.SetValue(str(decode_date(self.o.StartDate)))
        if self.o.EndDate is not None:
            self.field_end_date.SetValue(str(decode_date(self.o.EndDate)))

    def get_name(self):
        if self.is_new:
            return "(новый)"
        return self.o.get_tree_name()

    def get_icon(self):
        return get_icon("file")

    def on_save(self, event):
        if not self.Validate():
            return
