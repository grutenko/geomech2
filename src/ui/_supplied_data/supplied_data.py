import logging
from dataclasses import dataclass
from datetime import date
from time import sleep
from typing import List

import wx
from pony.orm import db_session, rollback, select
from wx.lib.gizmos.treelistctrl import TreeListCtrl

from src.database import SuppliedData, SuppliedDataPart, is_entity
from src.datetimeutil import decode_date
from src.ui.icon import get_icon
from src.ui.task import Task, TaskJob

from .file import FileDialog
from .folder import FolderDialog


class DeleteTask(TaskJob):
    def __init__(self, entities):
        self.entities = entities
        super().__init__()

    @db_session
    def run(self):
        self.set_progress(0, len(self.entities))
        for index, o in enumerate(self.entities):
            if self.cancel_event.isSet():
                rollback()
                return
            if isinstance(o, SuppliedData):
                _o = SuppliedData[o.RID]
            elif isinstance(o, SuppliedDataPart):
                _o = SuppliedDataPart[o.RID]
            else:
                rollback()
                raise RuntimeError("Unexpected object type: %s", str(type(o)))
            _o.delete()
            self.set_progress(index + 1, len(self.entities))


@dataclass
class FileFields:
    name: str
    comment: str
    data_date: date
    filename: str


class AddFileTask(TaskJob):
    def __init__(self, files: List[FileFields]):
        self.files = files
        super().__init__()

    @db_session
    def run(self):
        self.set_progress(0, len(self.files))
        for index, o in enumerate(self.files):
            if self.cancel_event.isSet():
                rollback()
                return

            self.set_progress(index + 1, len(self.files))


class SuppliedDataWidget(wx.Panel):
    def __init__(self, parent, deputy_text=None):
        self.o = None
        self.items = []
        super().__init__(parent)
        self.sz = wx.BoxSizer(wx.VERTICAL)
        self.tb = wx.ToolBar(self, style=wx.TB_FLAT)
        self.tb.AddTool(wx.ID_FILE1, "Добавить папку", get_icon("folder-add"))
        self.tb.AddTool(wx.ID_FILE2, "Добавить файл", get_icon("file-add"), kind=wx.ITEM_DROPDOWN)
        self.tb.AddSeparator()
        self.tb.AddTool(wx.ID_EDIT, "Изменить", get_icon("edit"))
        self.tb.AddTool(wx.ID_DELETE, "Удалить", get_icon("delete"))
        self.sz.Add(self.tb, 0, wx.EXPAND)
        self.image_list = wx.ImageList(16, 16)
        self.icon_book = self.image_list.Add(get_icon("book"))
        self.icon_folder = self.image_list.Add(get_icon("folder"))
        self.icon_folder_open = self.image_list.Add(get_icon("folder-open"))
        self.icon_file = self.image_list.Add(get_icon("file"))
        self.tree = TreeListCtrl(self, style=wx.TR_HIDE_ROOT)
        self.tree.AddColumn("Название", width=450)
        self.tree.AddColumn("Тип", width=100)
        self.tree.AddColumn("Размер", width=80)
        self.tree.AddColumn("Датировка", width=150)
        self.tree.AddColumn("Комментарий", width=300)
        self.tree.AssignImageList(self.image_list)
        self.tree.Hide()
        if deputy_text is None:
            deputy_text = "Недоступно"
        self.deputy = wx.StaticText(self, label=deputy_text)
        self.sz.Add(self.deputy, 1, wx.CENTER | wx.ALL, border=100)
        self.SetSizer(self.sz)
        self.Layout()
        self.bind_all()

    def bind_all(self):
        self.tb.Bind(wx.EVT_TOOL, self.on_folder_add, id=wx.ID_FILE1)
        self.tb.Bind(wx.EVT_TOOL, self.on_file_add, id=wx.ID_FILE2)
        self.tb.Bind(wx.EVT_TOOL, self.on_edit, id=wx.ID_EDIT)
        self.tb.Bind(wx.EVT_TOOL, self.on_delete, id=wx.ID_DELETE)
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_select)
        self.tree.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.on_menu)

    def on_menu(self, event):
        m = wx.Menu()
        data = self.tree.GetItemPyData(self.tree.GetSelections().__getitem__(0))
        if data is None:
            # RootItem
            i = m.Append(wx.ID_FILE1, "Добавить папку")
            i.SetBitmap(get_icon("folder-add"))
        elif isinstance(data, SuppliedData):
            i = m.Append(wx.ID_FILE2, "Добавить файл")
            i.SetBitmap(get_icon("file-add"))
            i = m.Append(wx.ID_EDIT, "Изменить")
            i.SetBitmap(get_icon("edit"))
            i = m.Append(wx.ID_DELETE, "Удалить")
            i.SetBitmap(get_icon("delete"))
        elif isinstance(data, SuppliedDataPart):
            i = m.Append(wx.ID_EDIT, "Изменить")
            i.SetBitmap(get_icon("edit"))
            i = m.Append(wx.ID_DELETE, "Удалить")
            i.SetBitmap(get_icon("delete"))
        m.Bind(wx.EVT_MENU, self.on_folder_add, id=wx.ID_FILE1)
        m.Bind(wx.EVT_MENU, self.on_file_add, id=wx.ID_FILE2)
        m.Bind(wx.EVT_MENU, self.on_edit, id=wx.ID_EDIT)
        m.Bind(wx.EVT_MENU, self.on_delete, id=wx.ID_DELETE)
        self.PopupMenu(m, event.GetPoint())

    def on_folder_add(self, event):
        dlg = FolderDialog(self, own_entity=self.o, is_new=True)
        if dlg.ShowModal() == wx.ID_OK:
            self.load()
            self.update_controls_state()

    def on_file_add(self, event):
        data = self.tree.GetItemPyData(self.tree.GetSelections().__getitem__(0))
        dlg = FileDialog(self, is_new=True, parent_object=data)
        if dlg.ShowModal() == wx.ID_OK:
            self.file_add_task = Task("идет добавление файлов...", "Добавление файлов", AddFileTask())

    def on_file_add_resolve(self, data):
        self.file_add_task.Destroy()
        self.load()
        self.update_controls_state()

    def on_file_add_reject(self, e):
        self.file_add_task.Destroy()

    def on_edit(self, event):
        data = self.tree.GetItemPyData(self.tree.GetSelections().__getitem__(0))
        if isinstance(data, SuppliedData):
            dlg = FolderDialog(self, own_entity=self.o, is_new=False, o=data)
        elif isinstance(data, SuppliedDataPart):
            dlg = FileDialog(self, is_new=False, o=data)
        if dlg.ShowModal() == wx.ID_OK:
            self.load()
            self.update_controls_state()

    @db_session
    def on_delete(self, event):
        if (
            wx.MessageBox(
                "Вы действительно хотите удалить сопутствующие материалы?",
                "Подтвердите удаление",
                style=wx.YES | wx.NO | wx.CANCEL | wx.NO_DEFAULT | wx.ICON_INFORMATION,
            )
            != wx.YES
        ):
            return
        entities = set()
        for item in self.tree.GetSelections():
            data = self.tree.GetItemPyData(item)
            if isinstance(data, SuppliedData):
                sp = SuppliedData[data.RID]
                entities.add(sp)
                for o in sp.parts:
                    entities.add(o)
            else:
                entities.add(SuppliedDataPart[data.RID])

        self.delete_task = Task(
            "Удаление", "идет удаление сопутствующих материалов...", DeleteTask(entities), self, can_abort=True
        )
        try:
            self.delete_task.then(self.on_delete_resolve, self.on_delete_reject)
            self.delete_task.run()
        except Exception as e:
            self.delete_task.Destroy()
            raise e

    def on_delete_resolve(self, data):
        self.delete_task.Destroy()
        self.load()
        self.update_controls_state()

    def on_delete_reject(self, e):
        self.delete_task.Destroy()

    def on_select(self, event):
        self.update_controls_state()

    @db_session
    def load(self):
        self.tree.DeleteAllItems()
        self.items = []
        self.tree_root = self.tree.AddRoot(self.o.get_tree_name(), image=self.icon_book, selImage=self.icon_book)
        for sp in select(o for o in SuppliedData if o.OwnID == self.o.RID and o.OwnType == self.o.sp_own_type):
            sp_item = self.tree.AppendItem(
                self.tree_root, sp.Name, image=self.icon_folder, selImage=self.icon_folder_open, data=sp
            )
            self.tree.SetItemText(sp_item, "Папка", column=1)
            self.tree.SetItemText(sp_item, "---", column=2)
            self.tree.SetItemText(sp_item, decode_date(sp.DataDate) if sp.DataDate is not None else "", column=3)
            self.tree.SetItemText(sp_item, sp.Comment if sp.Comment is not None else "", column=4)
            self.items.append(sp)
            for sp_part in sp.parts:
                sp_part_item = self.tree.AppendItem(sp_item, sp.Name, image=self.icon_file, data=sp_part)
                self.tree.SetItemText(sp_part_item, "Файл", column=1)
                self.tree.SetItemText(sp_part_item, "---", column=2)
                self.tree.SetItemText(
                    sp_part_item, decode_date(sp.DataDate) if sp.DataDate is not None else "", column=3
                )
                self.tree.SetItemText(sp_part_item, sp.Comment if sp.Comment is not None else "", column=4)
                self.items.append(sp_part)
        self.tree.ExpandAll()

    def start(self, o: object):
        if not is_entity(o) or o.sp_own_type is None:
            logging.warning("Unsupported object for supplied data: %s" % type(o))
        self.o = o
        self.sz.Detach(1)
        self.sz.Add(self.tree, 1, wx.EXPAND)
        self.deputy.Hide()
        self.tree.Show()
        self.load()
        self.update_controls_state()

    def end(self):
        self.o = None
        self.sz.Detach(1)
        self.sz.Add(self.deputy, 1, wx.EXPAND)
        self.tree.Hide()
        self.deputy.Show()
        self.tree.DeleteAllItems()
        self.update_controls_state()

    def update_controls_state(self):
        valid_item = (
            len(self.tree.GetSelections()) == 1 and self.tree.GetSelections().__getitem__(0) != self.tree.GetRootItem()
        )
        entity = self.tree.GetItemPyData(self.tree.GetSelections().__getitem__(0))
        self.tb.EnableTool(wx.ID_FILE1, self.o is not None and entity is None)
        self.tb.EnableTool(wx.ID_FILE2, self.o is not None and valid_item and isinstance(entity, SuppliedData))
        self.tb.EnableTool(wx.ID_EDIT, self.o is not None and valid_item)
        self.tb.EnableTool(wx.ID_DELETE, self.o is not None and valid_item)
