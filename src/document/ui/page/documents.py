import pubsub.pub
import wx
import wx.lib.mixins.listctrl as listmix
from pony.orm import db_session, desc, select

from src.ctx import app_ctx
from src.database import FoundationDocument
from src.delete_object import delete_object
from src.ui.icon import get_icon


class Documents(wx.Panel, listmix.ColumnSorterMixin):
    def __init__(self, parent):
        super().__init__(parent)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(main_sizer)

        self.toolbar = wx.ToolBar(self, style=wx.TB_HORIZONTAL | wx.TB_FLAT | wx.TB_HORZ_TEXT)
        item = self.toolbar.AddTool(wx.ID_ADD, "Добавить", get_icon("file-add"))
        self.toolbar.Bind(wx.EVT_TOOL, self._on_create, id=wx.ID_ADD)
        self.toolbar.AddSeparator()
        item = self.toolbar.AddTool(wx.ID_EDIT, "Изменить", get_icon("edit"))
        item.Enable(False)
        item = self.toolbar.AddTool(wx.ID_DELETE, "Удалить", get_icon("delete"))
        item.Enable(False)
        self.toolbar.Realize()
        main_sizer.Add(self.toolbar, 0, wx.EXPAND)
        self.tree_search = wx.SearchCtrl(self, size=wx.Size(-1, 25))
        main_sizer.Add(self.tree_search, 0, wx.EXPAND)
        self._items = []
        self.itemDataMap = {}

        self._image_list = wx.ImageList(16, 16)
        self._book_stack_icon = self._image_list.Add(get_icon("file"))
        self._list = wx.ListCtrl(self, style=wx.LC_REPORT)
        self._list.AppendColumn("Тип", width=100)
        self._list.AppendColumn("Номер", width=100)
        self._list.AppendColumn("ID", format=wx.LIST_FORMAT_RIGHT, width=70)
        self._list.AssignImageList(self._image_list, wx.IMAGE_LIST_SMALL)
        listmix.ColumnSorterMixin.__init__(self, 3)
        main_sizer.Add(self._list, 1, wx.EXPAND)

        self.Bind(wx.EVT_CLOSE, self._on_close)
        self._list.Bind(wx.EVT_RIGHT_DOWN, self._on_right_click)
        self._list.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_item_sel_changed)
        self._list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self._on_item_sel_changed)
        self._list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_activated)
        pubsub.pub.subscribe(self.on_objects_changed, "object.added")
        pubsub.pub.subscribe(self.on_objects_changed, "object.updated")
        self._load()

    def on_close(self):
        pubsub.pub.unsubscribe(self.on_objects_changed, "object.added")
        pubsub.pub.unsubscribe(self.on_objects_changed, "object.updated")
        return True

    def on_objects_changed(self, o):
        if isinstance(o, FoundationDocument):
            self._load()

    def on_activated(self, event):
        self._on_edit(event)

    def _on_item_sel_changed(self, event):
        self._update_controls_state()

    def GetListCtrl(self):
        return self._list

    @db_session
    def _load(self):
        self._list.DeleteAllItems()
        self._items = []
        self.itemDataMap = {}
        data = select(o for o in FoundationDocument).order_by(lambda x: desc(x.RID))

        for index, o in enumerate(data):
            _row = []
            _row.append(o.Type)
            _row.append(o.Number)
            _row.append(o.RID)
            item = self._list.InsertItem(index, _row[0], self._book_stack_icon)
            self._list.SetItem(item, 1, _row[1].__str__())
            self._list.SetItem(item, 2, _row[2].__str__())
            self._list.SetItemData(item, o.RID)
            self._items.append(o)
            self.itemDataMap[o.RID] = _row

    def _on_right_click(self, event):
        menu = wx.Menu()
        index, flags = self._list.HitTest(event.GetPosition())
        if index != -1:
            self._list.Select(index)
            item = menu.Append(wx.ID_EDIT, "Изменить")
            item.SetBitmap(get_icon("edit"))
            menu.Bind(wx.EVT_MENU, self._on_edit, item)
            item = menu.Append(wx.ID_DELETE, "Удалить")
            item.SetBitmap(get_icon("delete"))
            menu.Bind(wx.EVT_MENU, self._on_delete, item)
            menu.AppendSeparator()
            item = menu.Append(wx.ID_ADD, "Добавить документ")
            menu.Bind(wx.EVT_MENU, self._on_create, item)
            item.SetBitmap(get_icon("file-add"))
        else:
            menu = wx.Menu()
            item = menu.Append(wx.ID_ADD, "Добавить документ")
            menu.Bind(wx.EVT_MENU, self._on_create, item)
            item.SetBitmap(get_icon("file-add"))
        self.PopupMenu(menu)

    def _on_close(self, event):
        self.Hide()

    def _on_node_selection_changed(self, event):
        self._menu_bar.Enable(wx.ID_EDIT, event.node is not None)
        self._menu_bar.Enable(wx.ID_DELETE, event.node is not None)

    def _on_create(self, event):
        app_ctx().main.open("document_editor", is_new=True)

    def _on_edit(self, event):
        index = self._list.GetFirstSelected()
        if index == -1:
            return

        app_ctx().main.open("document_editor", is_new=False, o=self._items[index])

    def _on_delete(self, event):
        index = self._list.GetFirstSelected()
        if index == -1:
            return

        o = self._items[index]

        if delete_object(o, ["discharge_series", "pm_test_series"]):
            self._load()

    def _update_controls_state(self):
        self.toolbar.EnableTool(wx.ID_EDIT, self._list.GetFirstSelected() != -1)
        self.toolbar.EnableTool(wx.ID_DELETE, self._list.GetFirstSelected() != -1)

    def get_name(self):
        return "Документы"

    def get_icon(self):
        return get_icon("folder")
