import wx
import wx.lib.mixins.listctrl as listmix
import wx.lib.newevent
from pony.orm import db_session, select

from src.config import ClassConfigProvider
from src.ctx import app_ctx
from src.database import RockBurst
from src.datetimeutil import decode_date
from src.ui.icon import get_icon

__CONFIG_VERSION__ = 2

RockBurstSelectedEvent, EVT_ROCK_BURST_SELECTED = wx.lib.newevent.NewEvent()


class RockBurstWidget(wx.Panel, listmix.ColumnSorterMixin):
    def __init__(self, parent):
        super().__init__(parent)
        self.config_provider = ClassConfigProvider(__name__ + "." + self.__class__.__name__, __CONFIG_VERSION__)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.items = {}
        self.itemDataMap = {}
        self.toolbar = wx.ToolBar(self, style=wx.TB_FLAT | wx.TB_HORZ_TEXT)
        self.toolbar.AddTool(wx.ID_ADD, "Добавить", get_icon("file-add"))
        self.toolbar.Bind(wx.EVT_TOOL, self.on_add, id=wx.ID_ADD)
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(wx.ID_EDIT, "Изменить", get_icon("edit"))
        self.toolbar.Bind(wx.EVT_TOOL, self.on_edit, id=wx.ID_EDIT)
        self.toolbar.AddTool(wx.ID_DELETE, "Удалить", get_icon("delete"))
        self.toolbar.Bind(wx.EVT_TOOL, self.on_delete, id=wx.ID_DELETE)
        self.toolbar.EnableTool(wx.ID_EDIT, False)
        self.toolbar.EnableTool(wx.ID_DELETE, False)
        self.toolbar.Realize()
        sz.Add(self.toolbar, 0, wx.EXPAND)
        self.search = wx.SearchCtrl(self)
        sz.Add(self.search, 0, wx.EXPAND)
        self.image_list = wx.ImageList(16, 16)
        self.list = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.list.AppendColumn("№", width=50)
        self.list.AppendColumn("Меторождение", width=80)
        self.list.AppendColumn("Дата", width=100)
        listmix.ColumnSorterMixin.__init__(self, 3)
        self.list.Bind(wx.EVT_RIGHT_DOWN, self.on_right_click)
        self.list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)
        self.list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_item_selected)
        self.list.AssignImageList(self.image_list, wx.IMAGE_LIST_SMALL)
        sz.Add(self.list, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.silence_select = False
        self.load()

    def on_right_click(self, event):
        index, flags = self.list.HitTest(event.GetPosition())
        if index != -1:
            self.list.Select(index)
            menu = wx.Menu()
            item = menu.Append(wx.ID_EDIT, "Изменить")
            item.SetBitmap(get_icon("edit"))
            menu.Bind(wx.EVT_MENU, self.on_edit, item)
            item = menu.Append(wx.ID_DELETE, "Удалить")
            item.SetBitmap(get_icon("delete"))
            menu.Bind(wx.EVT_MENU, self.on_delete, item)
        else:
            menu = wx.Menu()
            item = menu.Append(wx.ID_ADD, "Добавить горный удар")
            menu.Bind(wx.EVT_MENU, self.on_add, item)
            item.SetBitmap(get_icon("file-add"))
        self.PopupMenu(menu, event.GetPosition())

    @db_session
    def load(self):
        self.list.DeleteAllItems()
        self.items = []
        for o in select(o for o in RockBurst):
            self.items.append(o)
        self.itemDataMap = {}
        for index, o in enumerate(self.items):
            row = []
            row.append(o.Number)
            row.append(o.mine_object.Name)
            row.append(decode_date(o.Date))
            self.list.InsertItem(index, row[0].__str__())
            self.list.SetItem(index, 1, row[1])
            self.list.SetItem(index, 2, row[2].__str__())
            self.itemDataMap[o.RID] = row

    def on_add(self, event):
        app_ctx().main.open("rock_burst_editor", is_new=True)

    def on_edit(self, event):
        # dlg = RockBurstDialog(self)
        # dlg.ShowModal()
        ...

    def on_delete(self, event): ...

    def on_item_selected(self, event):
        self.update_controls_state()

    def GetListCtrl(self):
        return self.list

    def save_pane_info(self, info: str):
        self.config_provider["aui_pane_info"] = info
        self.config_provider.flush()

    def get_pane_info(self) -> str | None:
        return self.config_provider["aui_pane_info"]

    def remove_selection(self, silence=False):
        i = self.list.GetFirstSelected()
        self.silence_select = silence
        try:
            while i != -1:
                self.list.Select(i, 0)
                i = self.list.GetNextSelected(i)
        finally:
            self.silence_select = False

    def update_controls_state(self):
        self.toolbar.EnableTool(wx.ID_EDIT, self.list.GetSelectedItemCount() > 0)
        self.toolbar.EnableTool(wx.ID_DELETE, self.list.GetSelectedItemCount() > 0)
        self.toolbar.Realize()

    def get_name(self):
        return "Горные удары"

    def get_icon(self):
        return get_icon("folder")

    def serialize(self):
        return {}
