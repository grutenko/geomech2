import wx
import wx.propgrid
from pony.orm import db_session, select

from src.database import PMSample, PmSamplePropertyValue
from src.ui.icon import get_icon


class PropertyValueEditor(wx.Dialog):
    def __init__(self, parent, is_new, o=None, sample=None):
        super().__init__(parent, title="Свойство образца", size=(500, 400))


class PropertiesEditor(wx.Panel):
    class cmdAddProperty(wx.Command): ...

    class cmdDeleteProperty(wx.Command): ...

    class cmdEditProperty(wx.Command): ...

    def __init__(self, parent):
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.pm_sample = None
        self.properties = []
        self.command_processor = wx.CommandProcessor()
        self.toolbar = wx.ToolBar(self, style=wx.TB_FLAT)
        self.toolbar.AddTool(wx.ID_SAVE, "Сохранить", get_icon("save"))
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(wx.ID_ADD, "Добавить свойство", get_icon("file-add"))
        self.toolbar.AddTool(wx.ID_DELETE, "Удалить свойство", get_icon("delete"))
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(wx.ID_UNDO, "Отменить", get_icon("undo"))
        self.toolbar.AddTool(wx.ID_REDO, "Вернуть", get_icon("redo"))
        self.toolbar.Realize()
        sz.Add(self.toolbar, 0, wx.EXPAND)
        self.propgrid = wx.propgrid.PropertyGridManager(
            self, style=wx.propgrid.PG_DEFAULT_STYLE | wx.propgrid.PG_SPLITTER_AUTO_CENTER
        )
        self.section = None
        self.propgrid.SetColumnCount(4)
        self.propgrid.SetColumnProportion(0, 25)
        self.propgrid.SetColumnProportion(1, 10)
        self.propgrid.SetColumnProportion(2, 25)
        self.propgrid.SetColumnProportion(3, 25)
        self.propgrid.Refresh()
        sz.Add(self.propgrid, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.update_controls_state()

    def start(self, sample):
        self.pm_sample = sample
        self.clear()
        self.load()
        self.update_controls_state()

    def clear(self):
        if self.section is not None:
            self.propgrid.DeleteProperty(self.section)
            self.propgrid.Refresh()
            self.section = None
        self.properties = []

    def end(self):
        self.pm_sample = None
        self.clear()

    def need_save(self) -> bool:
        return False

    def save(self): ...

    def update_controls_state(self):
        self.toolbar.EnableTool(wx.ID_ADD, self.pm_sample is not None)
        self.toolbar.EnableTool(
            wx.ID_DELETE, self.pm_sample is not None and self.propgrid.GetSelectedProperty() is not None
        )
        self.toolbar.EnableTool(wx.ID_SAVE, self.pm_sample is not None and self.need_save())
        self.toolbar.EnableTool(wx.ID_UNDO, self.pm_sample is not None and self.command_processor.CanRedo())
        self.toolbar.EnableTool(wx.ID_REDO, self.pm_sample is not None and self.command_processor.CanRedo())

    @db_session
    def load(self):
        self.section = self.propgrid.Append(wx.propgrid.PropertyCategory("Свойство", name="@header"))
        self.propgrid.SetPropertyCell(self.section, 1, "Значение")
        self.propgrid.SetPropertyCell(self.section, 2, "Метод испытаний")
        self.propgrid.SetPropertyCell(self.section, 3, "Оборудование")
        if self.pm_sample.Length1 is not None:
            p = self.propgrid.Append(wx.propgrid.FloatProperty("Сторона 1 (мм)", "Length1", self.pm_sample.Length1))
            self.propgrid.SetPropertyCell(p, 2, "-")
            self.propgrid.SetPropertyCell(p, 3, "-")
            self.properties.append(p)
        if self.pm_sample.Length2 is not None:
            p = self.propgrid.Append(wx.propgrid.FloatProperty("Сторона 2 (мм)", "Length2", self.pm_sample.Length2))
            self.propgrid.SetPropertyCell(p, 2, "-")
            self.propgrid.SetPropertyCell(p, 3, "-")
            self.properties.append(p)
        if self.pm_sample.Height is not None:
            p = self.propgrid.Append(wx.propgrid.FloatProperty("Высота (мм)", "Height", self.pm_sample.Height))
            self.propgrid.SetPropertyCell(p, 2, "-")
            self.propgrid.SetPropertyCell(p, 3, "-")
            self.properties.append(p)
        if self.pm_sample.MassAirDry is not None:
            p = self.propgrid.Append(
                wx.propgrid.FloatProperty(
                    "Масса в воздушно сухом состоянии (г)", "MassAirDry", self.pm_sample.MassAirDry
                )
            )
            self.propgrid.SetPropertyCell(p, 2, "-")
            self.propgrid.SetPropertyCell(p, 3, "-")
            self.properties.append(p)
        for o in select(o for o in PmSamplePropertyValue if o.pm_sample == self.pm_sample):
            prop = o.pm_property
            if prop.Unit is None or prop.Unit.strip() == "":
                name = prop.Name
            else:
                name = "%s (%s)" % (prop.Name, prop.Unit)
            p = self.propgrid.Append(wx.propgrid.FloatProperty(name, prop.Code, o.Value))
            self.propgrid.SetPropertyCell(p, 2, o.pm_test_method.Name)
            self.properties.append(p)


class SamplesList(wx.Panel):
    def __init__(self, parent):
        self.pm_sample_set = None
        self.samples = []
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(self, style=wx.TB_FLAT)
        self.toolbar.AddTool(wx.ID_ADD, "Добавить образец", get_icon("file-add"))
        self.toolbar.AddTool(wx.ID_DELETE, "Удалить образец", get_icon("delete"))
        self.toolbar.Realize()
        sz.Add(self.toolbar, 0, wx.EXPAND)
        self.search = wx.SearchCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.search.SetDescriptiveText("Поиск образца")
        sz.Add(self.search, 0, wx.EXPAND)
        self.list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_SINGLE_SEL)
        self.list.AppendColumn("Номер", width=120)
        self.list.AppendColumn("Дата испытания", width=120)
        sz.Add(self.list, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.update_controls_state()
        self.list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)
        self.list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_item_selected)

    def on_item_selected(self, event):
        self.update_controls_state()
        event.Skip()

    def start(self, pm_sample_set):
        self.pm_sample_set = pm_sample_set
        self.load()
        self.update_controls_state()

    @db_session
    def load(self):
        self.list.DeleteAllItems()
        self.samples = []
        for o in select(o for o in PMSample if o.pm_sample_set == self.pm_sample_set):
            item = self.list.InsertItem(self.list.GetItemCount(), str(o.Number))
            self.list.SetItem(item, 1, str(o.EndTestDate) if o.EndTestDate is not None else "")
            self.samples.append(o)

    def get_current_sample(self):
        if self.list.GetSelectedItemCount() == 0:
            return None
        index = self.list.GetFirstSelected()
        return self.samples[index]

    def update_controls_state(self):
        self.toolbar.EnableTool(wx.ID_ADD, self.pm_sample_set is not None)
        self.toolbar.EnableTool(wx.ID_DELETE, self.pm_sample_set is not None and self.list.GetSelectedItemCount() > 0)


class SampleDialog(wx.Dialog): ...


class SamplesWidget(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.pm_sample_set = None
        sz = wx.BoxSizer(wx.VERTICAL)
        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.list = SamplesList(self.splitter)
        self.properties = PropertiesEditor(self.splitter)
        sz.Add(self.splitter, 1, wx.EXPAND)
        self.splitter.SplitVertically(self.list, self.properties, 250)
        self.splitter.SetMinimumPaneSize(100)
        self.SetSizer(sz)
        self.Layout()
        self.list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_list_item_selected)
        self.list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_list_item_deselected)

    def on_list_item_selected(self, event):
        self.properties.start(self.list.get_current_sample())

    def on_list_item_deselected(self, event):
        self.properties.end()

    def start(self, pm_sample_set):
        self.pm_sample_set = pm_sample_set
        self.list.start(pm_sample_set)
