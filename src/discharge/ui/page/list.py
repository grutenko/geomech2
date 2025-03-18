import pubsub
import pubsub.pub
import wx
import wx.lib.mixins.listctrl as listmix
from pony.orm import db_session, desc, select

from src.ctx import app_ctx
from src.database import DischargeSeries, OrigSampleSet
from src.datetimeutil import decode_date
from src.delete_object import delete_object
from src.identity import Identity
from src.ui.icon import get_icon


class DischargeList(wx.Panel, listmix.ColumnSorterMixin):
    def __init__(self, parent):
        super().__init__(parent)

        self._items = {}
        self.itemDataMap = {}

        main_sizer = wx.BoxSizer(wx.VERTICAL)
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
        self.toolbar.AddStretchableSpace()
        self.toolbar.AddTool(wx.ID_REFRESH, "Обновить", get_icon("update"))
        self.toolbar.Bind(wx.EVT_TOOL, self.on_refresh, id=wx.ID_REFRESH)
        self.toolbar.Realize()
        main_sizer.Add(self.toolbar, 0, wx.EXPAND)
        self.tree_search = wx.SearchCtrl(self, size=wx.Size(-1, 25))
        main_sizer.Add(self.tree_search, 0, wx.EXPAND)
        self._image_list = wx.ImageList(16, 16)
        self._book_stack_icon = self._image_list.Add(get_icon("read"))
        self._list = wx.ListCtrl(self, style=wx.LC_REPORT)
        self._list.AppendColumn("Скважина", width=50)
        self._list.AppendColumn("Кол.во. замеров", width=50)
        self._list.AppendColumn("Дата начала", width=100)
        self._list.AppendColumn("Дата окончания", width=100)
        self._list.AppendColumn("Договор", width=150)
        self._list.AppendColumn("Месторождение", width=150)
        self._list.AssignImageList(self._image_list, wx.IMAGE_LIST_SMALL)
        listmix.ColumnSorterMixin.__init__(self, 6)
        main_sizer.Add(self._list, 1, wx.EXPAND)
        self.SetSizer(main_sizer)
        self.Layout()
        self._load()
        self._bind_all()
        self._silence_select = False

    def on_refresh(self, event):
        self._load()

    def on_add(self, event): ...

    def on_edit(self, event): ...

    def on_delete(self, event): ...

    def _bind_all(self):
        self._list.Bind(wx.EVT_RIGHT_DOWN, self._on_right_click)
        self._list.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_item_selected)
        self._list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self._on_item_selected)
        self._list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_activate)

    def on_activate(self, event):
        self._on_edit(event)

    def _on_item_selected(self, event):
        if not self._silence_select:
            event.Skip()

    def _on_right_click(self, event: wx.MouseEvent):
        index, flags = self._list.HitTest(event.GetPosition())
        if index != -1:
            self._list.Select(index)
            menu = wx.Menu()
            item = menu.Append(wx.ID_EDIT, "Изменить")
            item.SetBitmap(get_icon("edit"))
            menu.Bind(wx.EVT_MENU, self._on_edit, item)
            item = menu.Append(wx.ID_DELETE, "Удалить")
            item.SetBitmap(get_icon("delete"))
            menu.Bind(wx.EVT_MENU, self._on_delete, item)
            menu.AppendSeparator()
            sub = wx.Menu()
            item = sub.Append(wx.ID_ANY, 'Показать в "Объектах"')
            sub.Bind(wx.EVT_MENU, self._on_select_core, item)
            item.SetBitmap(get_icon("share"))
            menu.AppendSubMenu(sub, "[Керн]")
            menu.AppendSeparator()
            item = menu.Append(wx.ID_ADD, "Добавить разгрузку")
            menu.Bind(wx.EVT_MENU, self._on_add, item)
            item.SetBitmap(get_icon("wand"))
        else:
            menu = wx.Menu()
            item = menu.Append(wx.ID_ADD, "Добавить разгрузку")
            menu.Bind(wx.EVT_MENU, self._on_add, item)
            item.SetBitmap(get_icon("wand"))
        self.PopupMenu(menu, event.GetPosition())

    @db_session
    def _on_delete(self, event=None):
        if self._list.GetFirstSelected() == -1:
            return None
        ds = self._items[self._list.GetItemData(self._list.GetFirstSelected())]
        core = OrigSampleSet[ds.orig_sample_set.RID]
        if len(core.discharge_measurements) == 0:
            if delete_object(ds):
                self._load()
        else:
            wx.MessageBox("Запрещено удалять объекты к которым есть связаные данные.", "Удаление запрещено", wx.OK | wx.CENTRE | wx.ICON_ERROR)

    def _on_edit(self, event):
        if self._list.GetFirstSelected() == -1:
            return None
        ds = self._items[self._list.GetItemData(self._list.GetFirstSelected())]
        app_ctx().main.open("test_series_editor", is_new=False, o=ds)

    @db_session
    def _on_select_core(self, event):
        if self._list.GetFirstSelected() == -1:
            return None
        ds = self._items[self._list.GetItemData(self._list.GetFirstSelected())]
        core = OrigSampleSet[ds.orig_sample_set.RID]
        pubsub.pub.sendMessage("cmd.object.select", target=self, identity=Identity(core, core, None))

    @db_session
    def _load(self):
        self._list.DeleteAllItems()
        discharges = select(o for o in DischargeSeries).order_by(lambda x: desc(x.RID))
        self._items = {}
        for o in discharges:
            self._items[o.RID] = o
        m = ["REGION", "ROCKS", "FIELD", "HORIZON", "EXCAVATION"]
        self.itemDataMap = {}
        for index, o in enumerate(discharges):
            _row = []
            _row.append(o.orig_sample_set.bore_hole.Number.split("@", 1).__getitem__(0))
            _row.append(len(o.orig_sample_set.discharge_measurements))
            _row.append(decode_date(o.StartMeasure))
            if o.EndMeasure is not None:
                _end_measure = decode_date(o.EndMeasure)
            else:
                _end_measure = ""
            _row.append(_end_measure)
            if o.foundation_document is not None:
                _doc = o.foundation_document.Name
            else:
                _doc = ""
            _row.append(_doc)
            mine_object = o.orig_sample_set.mine_object
            _target_index = m.index("FIELD")
            if mine_object.Type in m:
                while m.index(mine_object.Type) > _target_index:
                    mine_object = mine_object.parent
            _row.append(mine_object.Name)
            _row.append(o.RID)

            item = self._list.InsertItem(index, _row[0], self._book_stack_icon)
            self._list.SetItem(item, 1, _row[1].__str__())
            self._list.SetItem(item, 2, _row[2].__str__())
            self._list.SetItem(item, 3, _row[3].__str__())
            self._list.SetItem(item, 4, _row[4])
            self._list.SetItem(item, 5, _row[5].__str__())
            self._list.SetItemData(item, o.RID)
            self.itemDataMap[o.RID] = _row

    def get_current_o(self):
        if self._list.GetFirstSelected() == -1:
            return None
        return self._items[self._list.GetItemData(self._list.GetFirstSelected())]

    def GetListCtrl(self):
        return self._list

    def _on_add(self, event):
        # dlg = DialogCreateDischargeSeries(self)
        # if dlg.ShowModal() == wx.ID_OK:
        #    self._load()
        ...

    def get_items(self):
        return self._items

    def start(self):
        self.Show()

    def end(self):
        self.Hide()

    def remove_selection(self, silence=False):
        i = self._list.GetFirstSelected()
        self._silence_select = silence
        try:
            while i != -1:
                self._list.Select(i, 0)
                i = self._list.GetNextSelected(i)
        finally:
            self._silence_select = False

    @db_session
    def select_by_identity(self, identity):
        if not isinstance(identity.rel_data_o, OrigSampleSet):
            return
        ds = select(o for o in DischargeSeries if o.orig_sample_set == identity.rel_data_o).first()
        if ds is None:
            return
        for idx in range(self._list.GetItemCount()):
            if self._list.GetItemData(idx) == ds.RID:
                self._list.Select(idx)
                return

    def get_name(self):
        return "Разгрузка"

    def get_icon(self):
        return get_icon("folder")

    def serialize(self):
        return {}
