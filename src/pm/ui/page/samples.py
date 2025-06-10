import wx
import wx.propgrid
from src.custom_datetime import date
from pony.orm import db_session, select, desc

from src.database import PMSample, PmSamplePropertyValue, OrigSampleSet
from src.ui.icon import get_icon
from src.ui.validators import TextValidator, DateValidator, ChoiceValidator


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


class SampleDialog(wx.Dialog):
    @db_session
    def __init__(self, parent, pm_sample=None, pm_sample_set=None, mode="CREATE"):
        super().__init__(parent, size=wx.Size(300, 550))
        self.mode = mode
        self.pm_sample = pm_sample
        self.pm_sample_set = pm_sample_set
        if mode == "CREATE":
            self.SetTitle("Добавить образец")
        else:
            self.SetTitle("Изменить образец %s" % pm_sample.Number)

        sz = wx.BoxSizer(wx.VERTICAL)
        main_sz = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, label="Номер *")
        main_sz.Add(label, 0)
        self.field_number = wx.TextCtrl(self, size=wx.Size(250, -1))
        self.field_number.SetValidator(TextValidator(lenMin=1, lenMax=256))
        max_pm_sample_number = (
            select(o for o in PMSample if o.pm_sample_set == pm_sample_set).order_by(lambda x: desc(x.Number)).first()
        )
        number = "1"
        if max_pm_sample_number is not None:
            try:
                number = str(int(max_pm_sample_number.Number) + 1)
            except:
                ...
        self.field_number.SetValue(number)
        main_sz.Add(self.field_number, 0, wx.EXPAND | wx.BOTTOM, border=10)

        label = wx.StaticText(self, label="Дата отбора")
        main_sz.Add(label, 0, wx.EXPAND)
        self.field_set_date = wx.TextCtrl(self)
        self.field_set_date.SetValidator(DateValidator())
        self.field_set_date.SetValue(date.today().__str__())
        main_sz.Add(self.field_set_date, 0, wx.EXPAND | wx.BOTTOM, border=10)

        label = wx.StaticText(self, label="Набор образцов *")
        main_sz.Add(label, 0, wx.EXPAND)
        self.orig_sample_sets = []
        self.field_orig_sample_set = wx.Choice(self)
        self.field_orig_sample_set.SetValidator(ChoiceValidator())
        self.field_orig_sample_set.Bind(wx.EVT_CHOICE, self.on_orig_sample_set_updated)
        for o in select(o for o in OrigSampleSet if o.mine_object == pm_sample_set.mine_object):
            if o.bore_hole is None or o.bore_hole.station is None:
                self.orig_sample_sets.append(o)
                self.field_orig_sample_set.Append(o.Name)
        if len(self.orig_sample_sets) > 0:
            self.field_orig_sample_set.SetSelection(0)
        main_sz.Add(self.field_orig_sample_set, 0, wx.EXPAND | wx.BOTTOM, border=10)

        self.core_sz = wx.StaticBoxSizer(wx.VERTICAL, self, label="Параметры керна")
        local_sz = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(self, label="Начальная позиция керна")
        local_sz.Add(label, 0, wx.EXPAND)
        self.field_start_position = wx.SpinCtrlDouble(self, min=0, max=10000)
        self.field_start_position.SetDigits(2)
        local_sz.Add(self.field_start_position, 0, wx.EXPAND | wx.BOTTOM, border=10)

        label = wx.StaticText(self, label="Конечная позиция керна")
        local_sz.Add(label, 0, wx.EXPAND)
        self.field_end_position = wx.SpinCtrlDouble(self, min=0, max=10000)
        self.field_end_position.SetDigits(2)
        local_sz.Add(self.field_end_position, 0, wx.EXPAND | wx.BOTTOM, border=10)

        label = wx.StaticText(self, label="№ ящика")
        local_sz.Add(label, 0, wx.EXPAND)
        self.field_box_number = wx.TextCtrl(self)
        self.field_box_number.SetValidator(TextValidator(lenMin=0, lenMax=32))
        local_sz.Add(self.field_box_number, 0, wx.EXPAND | wx.BOTTOM, border=10)

        self.core_sz.Add(local_sz, 1, wx.EXPAND | wx.ALL, border=10)
        main_sz.Add(self.core_sz, 0, wx.EXPAND | wx.BOTTOM, border=10)

        self.other_sz = wx.StaticBoxSizer(wx.VERTICAL, self, label="Параметры образца")
        local_sz = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, label="Глубина отбора")
        local_sz.Add(label, 0, wx.EXPAND)
        self.field_sample_depth = wx.SpinCtrlDouble(self, min=0, max=10000)
        self.field_sample_depth.SetDigits(2)
        local_sz.Add(self.field_sample_depth, 0, wx.EXPAND | wx.BOTTOM, border=10)
        self.other_sz.Add(local_sz, 1, wx.EXPAND | wx.ALL, border=10)
        main_sz.Add(self.other_sz, 0, wx.EXPAND | wx.BOTTOM, border=10)

        self.core_sz.Hide(0)
        self.other_sz.Hide(0)

        label = wx.StaticText(self, label="Дата завершения испытаний")
        main_sz.Add(label, 0, wx.EXPAND)
        self.field_end_set_date = wx.TextCtrl(self)
        self.field_end_set_date.SetValidator(DateValidator(allow_empty=True))
        main_sz.Add(self.field_end_set_date, 0, wx.EXPAND | wx.BOTTOM, border=10)

        sz.Add(main_sz, 1, wx.EXPAND | wx.ALL, border=10)

        line = wx.StaticLine(self)
        main_sz.Add(line, 0, wx.EXPAND | wx.TOP, border=10)

        btn_sizer = wx.StdDialogButtonSizer()
        self.btn_save = wx.Button(self, label="Создать")
        self.btn_save.Bind(wx.EVT_BUTTON, self.on_save)
        self.btn_save.SetDefault()
        btn_sizer.Add(self.btn_save, 0)
        sz.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, border=10)
        self.SetSizer(sz)
        self.Layout()
        self.on_orig_sample_set_updated()

    def on_orig_sample_set_updated(self, event=None):
        if len(self.orig_sample_sets) > 0:
            if self.orig_sample_sets[self.field_orig_sample_set.GetSelection()].SampleType == "CORE":
                self.use_core()
            else:
                self.use_other()

    def use_core(self):
        self.other_sz.Hide(0)
        self.core_sz.Show(0)
        self.Layout()

    def use_other(self):
        self.other_sz.Show(0)
        self.core_sz.Hide(0)
        self.Layout()

    def on_save(self, event):
        if not self.Validate():
            return


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
        self.toolbar.Bind(wx.EVT_TOOL, self.on_add_sample, id=wx.ID_ADD)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_delete_sample, id=wx.ID_DELETE)
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

    def on_add_sample(self, event):
        dlg = SampleDialog(self, pm_sample_set=self.pm_sample_set, mode="CREATE")
        dlg.ShowModal()

    def on_delete_sample(self, event): ...

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
