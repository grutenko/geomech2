import wx

from src.ui.icon import get_icon

from .coord_systems import CoordSystems
from .petrotype_struct import PetrotypeStructList
from .pm_equipments import PmEquipments
from .pm_methods import PmMethods
from .pm_properties import PmProperties
from .pm_property_classes import PmPropertyClasses
from .pm_tasks import PmTasks
from .rb_types import RbTypes
from .rb_typical_causes import RcTypicalCauses
from .rb_typical_reasons import RbTypicalReasons
from .rb_typical_signs import RcTypicalSigns


class Deputy(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, label="Выберите элемент в панели слева")
        sz.Add(label, 1, wx.EXPAND | wx.ALL, border=100)
        self.SetSizer(sz)
        self.Layout()
        self.Hide()

    def start(self):
        self.Show()

    def end(self):
        self.Hide()


class SettingsWindow(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Настройки", size=wx.Size(700, 350), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.SetIcon(wx.Icon(get_icon("logo")))
        sz = wx.BoxSizer(wx.VERTICAL)
        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.tree = wx.TreeCtrl(self.splitter, style=wx.TR_HIDE_ROOT)
        self.image_list = wx.ImageList(16, 16)
        self.file_icon = self.image_list.Add(get_icon("file"))
        self.tree.SetImageList(self.image_list)
        r = self.tree.AddRoot("Настройки")
        p = self.tree.AppendItem(r, "ФМС")
        self.tree.AppendItem(p, "Методы испытаний", image=self.file_icon, data="pm_methods")
        self.tree.AppendItem(p, "Оборудование", image=self.file_icon, data="pm_equipments")
        self.tree.AppendItem(p, "Выполняемые задачи", image=self.file_icon, data="pm_tasks")
        self.tree.AppendItem(p, "Классы свойств", image=self.file_icon, data="pm_property_classes")
        self.tree.AppendItem(p, "Свойства", image=self.file_icon, data="pm_properties")
        p = self.tree.AppendItem(r, "Горные удары")
        self.tree.AppendItem(p, "Типовые мероприятия", image=self.file_icon, data="rb_typical_causes")
        self.tree.AppendItem(p, "Типовые признаки", image=self.file_icon, data="rb_typical_signs")
        self.tree.AppendItem(p, "Типовые причины", image=self.file_icon, data="rb_typical_causes")
        self.tree.AppendItem(p, "Типовые профилактические мероприятия", image=self.file_icon, data="rb_typical_reasons")
        self.tree.AppendItem(p, "Типы событий", image=self.file_icon, data="rb_types")
        p = self.tree.AppendItem(r, "Петротипы", image=self.file_icon, data="petrotype_struct")
        p = self.tree.AppendItem(r, "Системы координат", image=self.file_icon, data="coord_systems")
        self.tree.ExpandAll()
        self.right = wx.Panel(self.splitter)
        self.right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.deputy = Deputy(self.right)
        self.right_sizer.Add(self.deputy, 1, wx.EXPAND)
        self.deputy.start()
        self.right.SetSizer(self.right_sizer)
        self.splitter.SplitVertically(self.tree, self.right, 200)
        self.splitter.SetMinimumPaneSize(150)
        sz.Add(self.splitter, 1, wx.EXPAND)
        self.Layout()
        self.CenterOnScreen()
        self.panels = {
            "coord_systems": CoordSystems(self.right),
            "petrotype_struct": PetrotypeStructList(self.right),
            "pm_equipments": PmEquipments(self.right),
            "pm_methods": PmMethods(self.right),
            "pm_properties": PmProperties(self.right),
            "pm_property_classes": PmPropertyClasses(self.right),
            "rb_types": RbTypes(self.right),
            "rb_typical_causes": RcTypicalCauses(self.right),
            "rb_typical_reasons": RbTypicalReasons(self.right),
            "rb_typical_signs": RcTypicalSigns(self.right),
            "pm_tasks": PmTasks(self.right),
        }
        self.started = False
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_select)
        self.sash_hack = +1

    def on_select(self, event):
        try:
            item_id = self.tree.GetSelection()
        except Exception:
            return
        if item_id.IsOk():
            data = self.tree.GetItemData(item_id)
            if data is not None:
                self.start(data)
            else:
                self.end()

    def start(self, panel_code):
        wnd = self.right_sizer.GetItem(0).GetWindow()
        self.right_sizer.Detach(0)
        wnd.end()
        new_wnd = self.panels[panel_code]
        self.right_sizer.Add(new_wnd, 1, wx.EXPAND)
        new_wnd.start()
        self.sash_hack *= -1
        self.splitter.SetSashPosition(self.splitter.GetSashPosition() + int(self.sash_hack))
        new_wnd.Layout()
        self.Layout()
        self.Update()

    def end(self):
        wnd = self.right_sizer.GetItem(0).GetWindow()
        self.right_sizer.Detach(0)
        wnd.end()
        self.right_sizer.Add(self.deputy, 1, wx.EXPAND)
        self.deputy.start()
        self.deputy.Layout()
        self.Layout()
