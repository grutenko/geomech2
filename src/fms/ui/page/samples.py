import wx
import wx.propgrid
from pony.orm import commit, db_session, select

from src.database import PMSample, PmSamplePropertyValue
from src.ui.icon import get_icon
from src.ui.overlay import Overlay


class PmPropertiesTab(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(self, style=wx.TB_FLAT | wx.TB_HORZ_TEXT)
        self.toolbar.AddTool(wx.ID_ADD, "Добавить свойство", get_icon("file-add"))
        self.toolbar.AddTool(wx.ID_DELETE, "Удалить свойство", get_icon("delete"))
        self.toolbar.EnableTool(wx.ID_ADD, False)
        self.toolbar.EnableTool(wx.ID_DELETE, False)
        self.toolbar.Realize()
        sz.Add(self.toolbar, 0, wx.EXPAND)
        self.propgrid = wx.propgrid.PropertyGridManager(
            self, style=wx.propgrid.PG_DEFAULT_STYLE | wx.propgrid.PG_SPLITTER_AUTO_CENTER
        )
        self.propgrid.SetColumnCount(4)
        self.propgrid.SetColumnProportion(0, 25)
        self.propgrid.SetColumnProportion(1, 10)
        self.propgrid.SetColumnProportion(2, 25)
        self.propgrid.SetColumnProportion(3, 25)
        self.propgrid.Refresh()
        sz.Add(self.propgrid, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.pm_sample: PMSample = None
        self.prop_ids = []
        self.propgrid.Bind(wx.propgrid.EVT_PG_SELECTED, self.on_selection_changed)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_add_property, id=wx.ID_ADD)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_delete_property, id=wx.ID_DELETE)

    @db_session
    def on_add_property(self, event=None):
        """dlg = PmPropertyDialog(self, self.pm_sample)
        if dlg.ShowModal() == wx.ID_OK:
            self.pm_sample = PMSample[self.pm_sample.RID]
            self.remove_properties()
            wx.CallAfter(self.load_properties)"""
        ...

    @db_session
    def on_delete_property(self, event):
        prop = self.propgrid.GetSelectedProperty()
        if prop is not None:
            if prop.GetName() == "Length1":
                PMSample[self.pm_sample.RID].Length1 = None
            elif prop.GetName() == "Length2":
                PMSample[self.pm_sample.RID].Length2 = None
            elif prop.GetName() == "Height":
                PMSample[self.pm_sample.RID].Height = None
            elif prop.GetName() == "MassAirDry":
                PMSample[self.pm_sample.RID].MassAirDry = None
            else:
                o = select(o for o in PmSamplePropertyValue if o.pm_property.Code == prop.GetName()).first()
                if o is not None:
                    o.delete()
                    commit()
        self.pm_sample = PMSample[self.pm_sample.RID]
        self.remove_properties()
        self.load_properties()
        self.update_controls_state()

    def on_selection_changed(self, event):
        self.update_controls_state()

    @db_session
    def set_pm_sample(self, pm_sample):
        self.pm_sample = PMSample[pm_sample.RID]
        self.remove_properties()
        self.load_properties()
        self.update_controls_state()

    @db_session
    def load_properties(self):
        self.prop_ids = []
        header = self.propgrid.Append(wx.propgrid.PropertyCategory("Свойство", name="@header"))
        self.propgrid.SetPropertyCell(header, 1, "Значение")
        self.propgrid.SetPropertyCell(header, 2, "Метод испытаний")
        self.propgrid.SetPropertyCell(header, 3, "Оборудование")
        self.prop_ids.append(header)
        if self.pm_sample.Length1 is not None:
            p = self.propgrid.Append(wx.propgrid.FloatProperty("Сторона 1 (мм)", "Length1", self.pm_sample.Length1))
            self.propgrid.SetPropertyCell(p, 2, "-")
            self.propgrid.SetPropertyCell(p, 3, "-")
            self.prop_ids.append(p)
        if self.pm_sample.Length2 is not None:
            p = self.propgrid.Append(wx.propgrid.FloatProperty("Сторона 2 (мм)", "Length2", self.pm_sample.Length2))
            self.propgrid.SetPropertyCell(p, 2, "-")
            self.propgrid.SetPropertyCell(p, 3, "-")
            self.prop_ids.append(p)
        if self.pm_sample.Height is not None:
            p = self.propgrid.Append(wx.propgrid.FloatProperty("Высота (мм)", "Height", self.pm_sample.Height))
            self.propgrid.SetPropertyCell(p, 2, "-")
            self.propgrid.SetPropertyCell(p, 3, "-")
            self.prop_ids.append(p)
        if self.pm_sample.MassAirDry is not None:
            p = self.propgrid.Append(
                wx.propgrid.FloatProperty(
                    "Масса в воздушно сухом состоянии (г)", "MassAirDry", self.pm_sample.MassAirDry
                )
            )
            self.propgrid.SetPropertyCell(p, 2, "-")
            self.propgrid.SetPropertyCell(p, 3, "-")
            self.prop_ids.append(p)
        for o in select(o for o in PmSamplePropertyValue if o.pm_sample == self.pm_sample):
            prop = o.pm_property
            p = self.propgrid.Append(wx.propgrid.FloatProperty("%s (%s)" % (prop.Name, prop.Unit), prop.Code, o.Value))
            self.propgrid.SetPropertyCell(p, 2, o.pm_test_method.Name)
            self.prop_ids.append(p)
        self.propgrid.Update()
        self.update_controls_state()

    def remove_properties(self):
        if len(self.prop_ids) > 0:
            self.propgrid.DeleteProperty(self.prop_ids[0])
        self.prop_ids = []
        self.propgrid.Refresh()

    def end(self):
        self.pm_sample = None
        self.remove_properties()
        self.update_controls_state()

    def update_controls_state(self):
        self.toolbar.EnableTool(wx.ID_ADD, self.pm_sample is not None)
        self.toolbar.EnableTool(
            wx.ID_DELETE, self.pm_sample != None and self.propgrid.GetSelectedProperty() is not None
        )


ID_PROP_ADD = wx.ID_HIGHEST + 135
ID_PROP_DELETE = ID_PROP_ADD + 1


class SampleDialog(wx.Dialog): ...


class PropertyDialog(wx.Dialog): ...


class SamplesWidget(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.o = None
        sz = wx.BoxSizer(wx.VERTICAL)
        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        p = wx.Panel(self.splitter)
        p_sz = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(p, style=wx.TB_FLAT | wx.TB_HORZ_TEXT)
        self.toolbar.AddTool(ID_PROP_ADD, "Добавить образец", get_icon("file-add"))
        self.toolbar.AddTool(wx.ID_DELETE, "Удалить образец", get_icon("delete"))
        self.toolbar.EnableTool(ID_PROP_ADD, False)
        self.toolbar.EnableTool(wx.ID_DELETE, False)
        self.toolbar.Realize()
        p_sz.Add(self.toolbar, 0, wx.EXPAND)
        self.search = wx.SearchCtrl(p, style=wx.TE_PROCESS_ENTER)
        self.search.SetDescriptiveText("Поиск образца")
        p_sz.Add(self.search, 0, wx.EXPAND)
        self.list = wx.ListCtrl(p, style=wx.LC_REPORT)
        self.list.AppendColumn("№ Образца")
        self.list.AppendColumn("Дата испытания")
        self.list.SetColumnWidth(0, 100)
        self.list.SetColumnWidth(1, 150)
        p_sz.Add(self.list, 1, wx.EXPAND)
        p.SetSizer(p_sz)
        self.properties = PmPropertiesTab(self.splitter)
        self.splitter.SplitVertically(p, self.properties, 250)
        self.splitter.SetMinimumPaneSize(100)
        sz.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.Disable()
        self.list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_list_item_selected)
        self.list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_list_item_deselected)
        self.samples = []

    @db_session
    def on_list_item_selected(self, event):
        self.properties.set_pm_sample(self.samples[event.GetIndex()])

    def on_list_item_deselected(self, event):
        self.properties.end()
        self.toolbar.EnableTool(ID_PROP_ADD, False)
        self.toolbar.EnableTool(wx.ID_DELETE, False)

    @db_session
    def start(self, o):
        self.o = o
        self.Enable()
        self.update_controls_state()
        self.list.DeleteAllItems()
        self.samples = []
        for o in select(o for o in PMSample if o.pm_sample_set == self.o):
            item = self.list.InsertItem(self.list.GetItemCount(), str(o.Number))
            self.list.SetItem(item, 1, str(o.EndTestDate) if o.EndTestDate is not None else "")
            self.samples.append(o)

    def end(self):
        self.o = None
        self.Disable()
        self.update_controls_state()
        self.properties.end()

    def update_controls_state(self): ...
