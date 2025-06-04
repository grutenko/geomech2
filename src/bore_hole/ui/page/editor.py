import pubsub.pub
import wx
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
    @db_session
    def __init__(self, parent, is_new: bool = False, o=None, parent_object=None):
        super().__init__(parent)
        self.is_new = is_new
        self.o = o
        self.parent_object = parent_object
        sz = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(self, style=wx.TB_HORZ_TEXT)
        self.toolbar.AddTool(wx.ID_SAVE, "Сохранить", get_icon("save"))
        self.toolbar.AddTool(wx.ID_SAVEAS, "Сохранить и закрыть", get_icon("save"))
        self.toolbar.Realize()
        self.number = None
        sz.Add(self.toolbar, 0, wx.EXPAND)
        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.left = wx.ScrolledWindow(self.splitter, style=wx.VSCROLL)
        self.left.SetVirtualSize(self.left.GetBestSize() + (250, 250))
        self.left.SetScrollRate(10, 10)
        l_sz = wx.BoxSizer(wx.VERTICAL)
        l_sz_in = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(self.left, label="Горный объект *")
        l_sz_in.Add(label, 0)
        self.field_mine_object = MineObjectChoice(self.left, mode="all_with_stations")
        l_sz_in.Add(self.field_mine_object, 0, wx.EXPAND | wx.BOTTOM, border=10)

        self.number = None
        if self.is_new:
            label = wx.StaticText(self.left, label="№ скважины *")
            l_sz_in.Add(label, 0)
            self.field_number = wx.TextCtrl(self.left, size=wx.Size(250, 25))
            self.field_number.SetValidator(TextValidator(lenMin=1, lenMax=256))
            l_sz_in.Add(self.field_number, 0, wx.EXPAND | wx.BOTTOM, border=10)
            self.field_number.Bind(wx.EVT_KEY_UP, self.on_orig_no_updated)

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

        label = wx.StaticText(self.left, label="Дата начала")
        l_sz_in.Add(label, 0)
        self.field_start_date = wx.TextCtrl(self.left, size=wx.Size(250, 25))
        self.field_start_date.SetValidator(DateValidator())
        l_sz_in.Add(self.field_start_date, 0, wx.EXPAND | wx.BOTTOM, border=10)

        label = wx.StaticText(self.left, label="Дата окончания")
        l_sz_in.Add(label, 0)
        self.field_end_date = wx.TextCtrl(self.left, size=wx.Size(250, 25))
        self.field_end_date.SetValidator(DateValidator(allow_empty=True))
        l_sz_in.Add(self.field_end_date, 0, wx.EXPAND | wx.BOTTOM, border=10)

        l_sz.Add(l_sz_in, 1, wx.EXPAND | wx.ALL, border=10)
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
        else:
            self.right.enable_tab(3, enable=False)
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
            return "(новый) Скважина"
        return self.o.get_tree_name()

    def get_icon(self):
        return get_icon("file")

    def on_save_and_close(self, event):
        self.on_save(event, need_close=True)

    @db_session
    def on_save(self, event, need_close=False):
        if not self.Validate():
            return

        self.props.CommitChangesFromEditor()
        if self.is_new:
            p = self.field_mine_object.GetValue()
            if isinstance(p, MineObject):
                mine_object = MineObject[p.RID]
                station = None
            else:
                station = Station[p.RID]
                mine_object = station.mine_object
            fields = {
                "mine_object": mine_object,
                "station": station,
                "Number": self.number,
                "Name": self.field_name.GetValue(),
                "Comment": self.field_comment.GetValue(),
                "StartDate": encode_date(self.field_start_date.GetValue()),
                "EndDate": (
                    encode_date(self.field_end_date.GetValue())
                    if len(self.field_end_date.GetValue().strip()) > 0
                    else None
                ),
                "DestroyDate": None,
                "X": 0.0,
                "Y": 0.0,
                "Z": 0.0,
                "Azimuth": self.props.GetPropertyValue("Azimuth"),
                "Tilt": self.props.GetPropertyValue("Tilt"),
                "Diameter": self.props.GetPropertyValue("Diameter"),
                "Length": self.props.GetPropertyValue("Length"),
            }
            o = BoreHole(**fields)
            core_fields = {
                "bore_hole": o,
                "mine_object": mine_object,
                "Number": "Керн:%s" % self.number,
                "Name": "Керн:%s" % self.field_name.GetValue(),
                "Comment": self.field_comment.GetValue(),
                "SampleType": "CORE",
                "X": 0.0,
                "Y": 0.0,
                "Z": 0.0,
                "StartSetDate": fields["StartDate"],
                "EndSetDate": fields["EndDate"],
            }
            core = OrigSampleSet(**core_fields)
        else:
            fields = {
                "Name": self.field_name.GetValue(),
                "Comment": self.field_comment.GetValue(),
                "StartDate": encode_date(self.field_start_date.GetValue()),
                "EndDate": (
                    encode_date(self.field_end_date.GetValue())
                    if len(self.field_end_date.GetValue().strip()) > 0
                    else None
                ),
                "Azimuth": self.props.GetPropertyValue("Azimuth"),
                "Tilt": self.props.GetPropertyValue("Tilt"),
                "Diameter": self.props.GetPropertyValue("Diameter"),
                "Length": self.props.GetPropertyValue("Length"),
            }
            print(self.props.GetPropertyValue("Diameter"))
            o = BoreHole[self.o.RID]
            o.set(**fields)
            core = select(core for core in OrigSampleSet if core.bore_hole == o).first()
            if core is not None:
                core.set(Name="Керн:%s" % fields["Name"], Comment=fields["Comment"])
        commit()
        self.o = o
        if self.is_new:
            pubsub.pub.sendMessage("object.added", o=o)
            if not need_close:
                app_ctx().main.open("bore_hole_editor", is_new=False, o=o)
            app_ctx().main.close(self)
        else:
            pubsub.pub.sendMessage("object.updated", o=o)
            wx.PostEvent(app_ctx().main, PageHdrChangedEvent(target=self))
            if need_close:
                app_ctx().main.close(self)
