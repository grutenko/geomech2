import logging
import os
from pathlib import Path

import wx
from pony.orm import db_session, select
from wx.lib.gizmos.treelistctrl import TreeListCtrl

from src.database import SuppliedData, SuppliedDataPart, is_entity
from src.datetimeutil import decode_date
from src.ui.icon import get_icon
from src.ui.overlay import Overlay
from src.ui.task import Task

from .delete import DeleteTask
from .download import DownloadItem, DownloadTask, sanitize_filename
from .file import AddFileTask, FileDialog
from .folder import FolderDialog


def human_readable_size(num_bytes, precision=2):
    units = ["Б", "КБ", "МБ", "ГБ", "ТБ", "ПБ"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024:
            return f"{size:.{precision}f} {unit}"
        size /= 1024
    return f"{size:.{precision}f} ПБ"


class SuppliedDataWidget(wx.Panel):
    def __init__(self, parent, deputy_text=None):
        self.o = None
        self.items = []
        self.o = None
        self.items = []
        super().__init__(parent)
        self.start_pos = None
        self.end_pos = None
        self.overlay = wx.Overlay()
        self.is_selecting = False
        self.sz = wx.BoxSizer(wx.VERTICAL)
        self.tb = wx.ToolBar(self, style=wx.TB_FLAT)
        self.tb.AddTool(wx.ID_DOWN, "Скачать", get_icon("download"), shortHelp="Скачать")
        self.tb.AddTool(wx.ID_FILE1, "Добавить папку", get_icon("folder-add"), shortHelp="Добавить папку")
        self.tb.AddTool(
            wx.ID_FILE2, "Добавить файл", get_icon("file-add"), kind=wx.ITEM_DROPDOWN, shortHelp="Добавить файл"
        )
        self.tb.AddSeparator()
        self.tb.AddTool(wx.ID_EDIT, "Изменить", get_icon("edit"), shortHelp="Изменить")
        self.tb.AddTool(wx.ID_DELETE, "Удалить", get_icon("delete"), shortHelp="Удалить")
        self.tb.Realize()
        self.sz.Add(self.tb, 0, wx.EXPAND)
        self.image_list = wx.ImageList(16, 16)
        self.icon_book = self.image_list.Add(get_icon("book"))
        self.icon_folder = self.image_list.Add(get_icon("folder"))
        self.icon_folder_open = self.image_list.Add(get_icon("folder-open"))
        self.icon_file = self.image_list.Add(get_icon("file"))
        self.tree = TreeListCtrl(self, agwStyle=wx.TR_DEFAULT_STYLE | wx.TR_MULTIPLE)
        self.tree.AddColumn("Название", width=450)
        self.tree.AddColumn("Тип", width=100)
        self.tree.AddColumn("Размер", width=80)
        self.tree.AddColumn("Датировка", width=150)
        self.tree.AddColumn("Комментарий", width=300)
        self.tree.AssignImageList(self.image_list)
        self.tree.Hide()
        self.start_pos = None
        self.end_pos = None
        self.overlay = wx.Overlay()
        self.is_selecting = False
        self.sz = wx.BoxSizer(wx.VERTICAL)
        self.tb = wx.ToolBar(self, style=wx.TB_FLAT)
        self.tb.AddTool(wx.ID_DOWN, "Скачать", get_icon("download"), shortHelp="Скачать")
        self.tb.AddTool(wx.ID_FILE1, "Добавить папку", get_icon("folder-add"), shortHelp="Добавить папку")
        self.tb.AddTool(
            wx.ID_FILE2, "Добавить файл", get_icon("file-add"), kind=wx.ITEM_DROPDOWN, shortHelp="Добавить файл"
        )
        self.tb.AddSeparator()
        self.tb.AddTool(wx.ID_EDIT, "Изменить", get_icon("edit"), shortHelp="Изменить")
        self.tb.AddTool(wx.ID_DELETE, "Удалить", get_icon("delete"), shortHelp="Удалить")
        self.tb.Realize()
        self.sz.Add(self.tb, 0, wx.EXPAND)
        self.image_list = wx.ImageList(16, 16)
        self.icon_book = self.image_list.Add(get_icon("book"))
        self.icon_folder = self.image_list.Add(get_icon("folder"))
        self.icon_folder_open = self.image_list.Add(get_icon("folder-open"))
        self.icon_file = self.image_list.Add(get_icon("file"))
        self.tree = TreeListCtrl(self, agwStyle=wx.TR_DEFAULT_STYLE | wx.TR_MULTIPLE)
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
            deputy_text = "Недоступно"
        self.deputy = wx.StaticText(self, label=deputy_text)
        self.sz.Add(self.deputy, 1, wx.CENTER | wx.ALL, border=100)
        self.SetSizer(self.sz)
        self.Layout()
        self.bind_all()
        self.update_controls_state()
        self.disable_overlay = Overlay(self, deputy_text)
        self.disable_overlay.Show()

    def bind_all(self):
        self.tb.Bind(wx.EVT_TOOL, self.on_folder_add, id=wx.ID_FILE1)
        self.tb.Bind(wx.EVT_TOOL, self.on_file_add, id=wx.ID_FILE2)
        self.tb.Bind(wx.EVT_TOOL, self.on_edit, id=wx.ID_EDIT)
        self.tb.Bind(wx.EVT_TOOL, self.on_delete, id=wx.ID_DELETE)
        self.tb.Bind(wx.EVT_TOOL, self.on_download, id=wx.ID_DOWN)
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_select)
        self.tree.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.on_menu)
        self.tree.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.tree.Bind(wx.EVT_MOTION, self.on_mouse_move)
        self.tree.Bind(wx.EVT_LEFT_UP, self.on_left_up)

    def on_left_down(self, event):
        self.start_pos = event.GetPosition()
        self.end_pos = self.start_pos
        self.is_selecting = True
        self.tree.CaptureMouse()

    def on_mouse_move(self, event):
        if self.is_selecting and event.Dragging() and event.LeftIsDown():
            self.end_pos = event.GetPosition()
            self.draw_selection()

    def on_left_up(self, event):
        if self.is_selecting:
            if self.tree.HasCapture():
                self.tree.ReleaseMouse()
            self.overlay.Reset()
            self.is_selecting = False
            self.select_items_in_rect(wx.Rect(self.start_pos, self.end_pos))
            self.Refresh()

    def draw_selection(self):
        """Рисует прямоугольник выделения"""
        dc = wx.ClientDC(self.tree)
        odc = wx.DCOverlay(self.overlay, dc)
        odc.Clear()

        rect = wx.Rect(self.start_pos, self.end_pos)
        dc.SetPen(wx.Pen(wx.BLUE, 1, wx.PENSTYLE_DOT))
        dc.SetBrush(wx.Brush(wx.Colour(0, 0, 255, 50)))  # Полупрозрачный синий
        dc.DrawRectangle(rect)

    def select_items_in_rect(self, rect):
        """Выбирает элементы, попавшие в выделенную область"""
        self.tree.UnselectAll()
        item, _ = self.tree.GetFirstChild(self.tree.GetRootItem())
        while item is not None and item.IsOk():
            item_rect = self.tree.GetBoundingRect(item, textOnly=False)
            if item_rect.IsEmpty():
                item, _ = self.tree.GetNextChild(self.tree.GetRootItem(), _)
                continue
            if rect.Intersects(item_rect):
                self.tree.SelectItem(item, True)
                self.tree.SelectAllChildren(item)
            item, _ = self.tree.GetNextChild(self.tree.GetRootItem(), _)

    def on_menu(self, event):
        m = wx.Menu()
        data = self.tree.GetItemPyData(self.tree.GetSelections().__getitem__(0))
        if len(self.tree.GetSelections()) > 1:
            i = m.Append(wx.ID_DELETE, "Удалить")
            i.SetBitmap(get_icon("delete"))
        else:
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

    def on_download(self, event):
        dlg = wx.DirDialog(self, "Выберите место сохранения")
        if dlg.ShowModal() != wx.ID_OK:
            return
        items = []

        # Рекурсивно обходит все элементы дерева добавляя в список элементов на
        # загрузку те - которые выделены пользователем
        def r(p=None, path=None):
            tree_items = []
            if p is None:
                tree_items.append(self.tree.GetRootItem())
            else:
                item, cookie = self.tree.GetFirstChild(p)
                while item is not None:
                    tree_items.append(item)
                    item = self.tree.GetNextSibling(item)

            _once_selected = False
            for item in tree_items:
                if self.tree.IsSelected(item):
                    _once_selected = True
                    break

            for item in tree_items:
                if not self.tree.IsSelected(item) and _once_selected:
                    # пропускаем элементы которые не выделены, но при этом есть хотя бы один выделеный элемент в на у этого родителя
                    # Иначе предполагается что пользователь выбрал все дочерние элементы
                    continue
                data = self.tree.GetItemPyData(item)
                new_path = None
                o = None
                if data is None:
                    new_path = sanitize_filename(self.o.get_tree_name())
                elif isinstance(data, SuppliedData):
                    new_path = os.path.join(path, sanitize_filename(data.Name))
                elif isinstance(data, SuppliedDataPart):
                    _path = Path(data.FileName)
                    new_path = os.path.join(path, sanitize_filename(data.Name + "".join(_path.suffixes)))
                    o = data
                items.append(DownloadItem(new_path, o))
                r(item, new_path)

        r()
        self.download_task = Task(
            "Скачивание файлов", "Идет скачивание файлов", DownloadTask(items, dlg.GetPath()), self
        )
        try:
            self.download_task.then(self.on_download_resolve, self.on_download_reject)
            self.download_task.run()
        except Exception:
            self.download_task.Destroy()

    def on_download_resolve(self, data):
        self.download_task.Destroy()

    def on_download_reject(self, e):
        self.download_task.Destroy()
        raise e

    def on_file_add(self, event):
        data = self.tree.GetItemPyData(self.tree.GetSelections().__getitem__(0))
        dlg = FileDialog(self, is_new=True, parent_object=data)
        if dlg.ShowModal() == wx.ID_OK:
            self.file_add_task = Task(
                "идет добавление файлов...",
                "Добавление файлов",
                AddFileTask([dlg.fields]),
                can_abort=False,
                show_time=False,
            )
            try:
                self.file_add_task.then(self.on_file_add_resolve, self.on_file_add_reject)
                self.file_add_task.run()
            except Exception as e:
                self.file_add_task.Destroy()
                raise e

    def on_file_add_resolve(self, data):
        self.file_add_task.Destroy()
        self.load()
        self.update_controls_state()
            self.file_add_task = Task(
                "идет добавление файлов...",
                "Добавление файлов",
                AddFileTask([dlg.fields]),
                can_abort=False,
                show_time=False,
            )
            try:
                self.file_add_task.then(self.on_file_add_resolve, self.on_file_add_reject)
                self.file_add_task.run()
            except Exception as e:
                self.file_add_task.Destroy()
                raise e

    def on_file_add_resolve(self, data):
        self.file_add_task.Destroy()
        self.load()
        self.update_controls_state()

    def on_file_add_reject(self, e):
        self.file_add_task.Destroy()
        raise e

    def on_edit(self, event):
        data = self.tree.GetItemPyData(self.tree.GetSelections().__getitem__(0))
        if isinstance(data, SuppliedData):
            dlg = FolderDialog(self, own_entity=self.o, is_new=False, o=data)
        elif isinstance(data, SuppliedDataPart):
            dlg = FileDialog(self, is_new=False, o=data)
    def on_file_add_reject(self, e):
        self.file_add_task.Destroy()
        raise e

    def on_edit(self, event):
        data = self.tree.GetItemPyData(self.tree.GetSelections().__getitem__(0))
        if isinstance(data, SuppliedData):
            dlg = FolderDialog(self, own_entity=self.o, is_new=False, o=data)
        elif isinstance(data, SuppliedDataPart):
            dlg = FileDialog(self, is_new=False, o=data)
        if dlg.ShowModal() == wx.ID_OK:
            self.load()
            self.update_controls_state()
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
            self.tree.SetItemText(sp_item, str(decode_date(sp.DataDate)) if sp.DataDate is not None else "", column=3)
            self.tree.SetItemText(sp_item, sp.Comment if sp.Comment is not None else "", column=4)
            self.items.append(sp)
            for sp_part in select(o for o in SuppliedDataPart if o.parent == sp):
                sp_part_item = self.tree.AppendItem(sp_item, sp_part.Name, image=self.icon_file, data=sp_part)
                self.tree.SetItemText(sp_part_item, "Файл", column=1)
                self.tree.SetItemText(sp_part_item, human_readable_size(sp_part.size()), column=2)
                self.tree.SetItemText(
                    sp_part_item, str(decode_date(sp_part.DataDate)) if sp_part.DataDate is not None else "", column=3
                )
                self.tree.SetItemText(sp_part_item, sp_part.Comment if sp_part.Comment is not None else "", column=4)
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
        self.disable_overlay.Hide()

    def end(self):
        self.o = None
        self.sz.Detach(1)
        self.sz.Add(self.deputy, 1, wx.EXPAND)
        self.tree.Hide()
        self.deputy.Show()
        self.tree.DeleteAllItems()
        self.update_controls_state()
        self.disable_overlay.Show()

    def update_controls_state(self):
        valid_item = (
            len(self.tree.GetSelections()) == 1 and self.tree.GetSelections().__getitem__(0) != self.tree.GetRootItem()
        )
        if len(self.tree.GetSelections()) == 1:
            entity = self.tree.GetItemPyData(self.tree.GetSelections().__getitem__(0))
        else:
            entity = None
        self.tb.EnableTool(wx.ID_FILE1, self.o is not None and entity is None)
        self.tb.EnableTool(wx.ID_FILE2, self.o is not None and valid_item and isinstance(entity, SuppliedData))
        self.tb.EnableTool(wx.ID_EDIT, self.o is not None and valid_item)
        self.tb.EnableTool(wx.ID_DELETE, self.o is not None and len(self.tree.GetSelections()) > 0)
        self.tb.EnableTool(wx.ID_DOWN, self.o is not None and len(self.tree.GetSelections()) > 0)
