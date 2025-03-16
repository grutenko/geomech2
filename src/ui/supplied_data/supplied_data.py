import mimetypes
import os
import threading
from datetime import datetime

import wx
import wx.dataview
from pony.orm import *
from transliterate import translit

from src.database import *
from src.datetimeutil import *
from src.delete_object import delete_object
from src.resourcelocation import resource_path
from src.ui.icon import get_art, get_icon
from src.ui.validators import *


class FolderEditor(wx.Dialog):
    def __init__(self, parent, own_id=None, own_type=None, o=None):
        super().__init__(parent)
        self.CenterOnScreen()

        if o == None:
            self.own_id = own_id
            self.own_type = own_type
            self.SetTitle("Добавить раздел")
        else:
            self.SetTitle("Изменить раздел: %s" % o.Name)

        self.SetIcon(wx.Icon(get_icon("folder-add")))

        self.o = o

        top_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer.Add(main_sizer, 1, wx.EXPAND | wx.ALL, border=10)

        label = wx.StaticText(self, label="Название *")
        main_sizer.Add(label, 0, wx.EXPAND)
        self.field_name = wx.TextCtrl(self, size=wx.Size(250, -1))
        self.field_name.SetValidator(TextValidator(lenMin=1, lenMax=128))
        main_sizer.Add(self.field_name, 0, wx.EXPAND | wx.BOTTOM, border=10)
        self.field_name.Bind(wx.EVT_KEY_UP, self._on_name_changed)

        label = wx.StaticText(self, label="Номер")
        main_sizer.Add(label, 0, wx.EXPAND)
        self.field_number = wx.TextCtrl(self, size=wx.Size(250, -1))
        self.field_number.SetValidator(TextValidator(lenMin=0, lenMax=32))
        main_sizer.Add(self.field_number, 0, wx.EXPAND | wx.BOTTOM, border=10)

        label = wx.StaticText(self, label="Датировка материала")
        main_sizer.Add(label, 0, wx.EXPAND)
        self.field_data_date = wx.TextCtrl(self, size=wx.Size(250, -1))
        self.field_data_date.SetValidator(DateValidator(allow_empty=True))
        main_sizer.Add(self.field_data_date, 0, wx.EXPAND | wx.BOTTOM, border=10)

        collpane = wx.CollapsiblePane(self, wx.ID_ANY, "Комментарий")
        main_sizer.Add(collpane, 0, wx.GROW)

        comment_pane = collpane.GetPane()
        comment_sizer = wx.BoxSizer(wx.VERTICAL)
        comment_pane.SetSizer(comment_sizer)

        label = wx.StaticText(comment_pane, label="Комментарий")
        comment_sizer.Add(label, 0)
        self.field_comment = wx.TextCtrl(comment_pane, size=wx.Size(250, 100), style=wx.TE_MULTILINE)
        self.field_comment.SetValidator(TextValidator(lenMin=0, lenMax=512))
        comment_sizer.Add(self.field_comment, 0, wx.EXPAND | wx.BOTTOM, border=10)

        line = wx.StaticLine(self)
        top_sizer.Add(line, 0, wx.EXPAND | wx.TOP, border=10)

        btn_sizer = wx.StdDialogButtonSizer()
        if o == None:
            label = "Создать"
        else:
            label = "Изменить"
        self.btn_save = wx.Button(self, label=label)
        self.btn_save.Bind(wx.EVT_BUTTON, self._on_save)
        self.btn_save.SetDefault()
        btn_sizer.Add(self.btn_save, 0)
        top_sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, border=10)

        self.SetSizer(top_sizer)

        self.Layout()
        self.Fit()

        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyUP)

    def _on_name_changed(self, event):
        event.Skip()
        self.field_number.SetValue(translit(self.field_name.GetValue(), "ru", reversed=True))

    def OnKeyUP(self, event):
        keyCode = event.GetKeyCode()
        if keyCode == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
        else:
            event.Skip()

    def _apply_fields(self):
        self.field_name.SetValue(self.o.Name)
        self.field_comment.SetValue(self.o.Comment if self.o.Comment != None else "")
        self.field_number.SetValue(self.o.Number if self.o.Number != None else "")
        self.field_data_date.SetValue(str(decode_date(self.o.DataDate)) if self.o.DataDate != None else "")

    @db_session
    def _on_save(self, event):
        if not self.Validate():
            return

        fields = {"Name": self.field_name.GetValue().strip(), "Comment": self.field_comment.GetValue().strip()}

        if len(self.field_number.GetValue().strip()) > 0:
            fields["Number"] = self.field_number.GetValue().strip()
        if len(self.field_data_date.GetValue().strip()) > 0:
            fields["DataDate"] = encode_date(self.field_data_date.GetValue().strip())

        if self.o == None:
            fields["OwnID"] = self.own_id
            fields["OwnType"] = self.own_type
            o = SuppliedData(**fields)
        else:
            o = SuppliedData[self.o.RID]
            o.set(**fields)
        commit()
        self.o = o
        self.EndModal(wx.ID_OK)


class CreateFileWorker(threading.Thread):
    def __init__(self, gauge, fields, on_resolve, on_reject):
        super().__init__()
        self.gauge = gauge
        self.fields = fields
        self.on_resolve = on_resolve
        self.on_reject = on_reject

    @db_session
    def run(self):
        try:
            _fields = {"Name": self.fields["name"], "Comment": self.fields["comment"], "FileName": self.fields["file_name"], "DType": self.fields["mime_type"]}
            _fields["parent"] = SuppliedData[self.fields["parent"].RID]
            if "data_date" in self.fields:
                _fields["DataDate"] = self.fields["data_date"]

            with open(self.fields["path"], "rb") as f:
                _fields["DataContent"] = f.read()

            o = SuppliedDataPart(**_fields)
            commit()
        except Exception as e:
            self.on_reject(e)
        else:
            self.on_resolve(o)


class FileEditor(wx.Dialog):
    def __init__(self, parent, p=None, o=None):
        super().__init__(parent)
        self.CenterOnScreen()
        self.o = None
        self.p = None
        if o == None:
            self.p = p
            self.SetTitle("Добавить файл")
        else:
            self.o = o
            self.SetTitle("Изменить: %s" % o.Name)

        self.SetIcon(wx.Icon(get_icon("file-add")))

        top_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer.Add(main_sizer, 1, wx.EXPAND | wx.ALL, border=10)

        label = wx.StaticText(self, label="Файл *")
        main_sizer.Add(label, 0, wx.EXPAND)
        self.field_file = wx.FilePickerCtrl(self)
        self.field_file.Bind(wx.EVT_FILEPICKER_CHANGED, self._on_file_changed)
        main_sizer.Add(self.field_file, 0, wx.EXPAND)

        self.label_file_error = wx.StaticText(self, label="Неверный путь к файлу")
        self.label_file_error.SetForegroundColour(wx.Colour(255, 0, 0))
        self.label_file_error.Hide()
        main_sizer.Add(self.label_file_error, 0, wx.EXPAND)

        label = wx.StaticText(self, label="Название *")
        main_sizer.Add(label, 0, wx.EXPAND | wx.TOP, border=10)
        self.field_name = wx.TextCtrl(self, size=wx.Size(250, -1))
        self.field_name.SetValidator(TextValidator(lenMin=1, lenMax=128))
        main_sizer.Add(self.field_name, 0, wx.EXPAND | wx.BOTTOM, border=10)

        label = wx.StaticText(self, label="Датировка материала")
        main_sizer.Add(label, 0, wx.EXPAND)
        self.field_data_date = wx.TextCtrl(self, size=wx.Size(250, -1))
        self.field_data_date.SetValidator(DateValidator())
        main_sizer.Add(self.field_data_date, 0, wx.EXPAND | wx.BOTTOM, border=10)

        collpane = wx.CollapsiblePane(self, wx.ID_ANY, "Комментарий")
        main_sizer.Add(collpane, 0, wx.GROW)

        comment_pane = collpane.GetPane()
        comment_sizer = wx.BoxSizer(wx.VERTICAL)
        comment_pane.SetSizer(comment_sizer)

        label = wx.StaticText(comment_pane, label="Комментарий")
        comment_sizer.Add(label, 0)
        self.field_comment = wx.TextCtrl(comment_pane, size=wx.Size(250, 100), style=wx.TE_MULTILINE)
        self.field_comment.SetValidator(TextValidator(lenMin=0, lenMax=512))
        comment_sizer.Add(self.field_comment, 0, wx.EXPAND | wx.BOTTOM, border=10)

        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyUP)

        line = wx.StaticLine(self)
        top_sizer.Add(line, 0, wx.EXPAND | wx.TOP, border=10)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.progress_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_tick_gauge)
        self.progress = wx.Gauge(self)
        btn_sizer.Add(self.progress, 1, wx.CENTER | wx.RIGHT, border=10)

        if o == None:
            label = "Создать"
        else:
            label = "Изменить"
        self.btn_save = wx.Button(self, label=label)
        self.btn_save.Bind(wx.EVT_BUTTON, self._on_save)
        self.btn_save.SetDefault()
        btn_sizer.Add(self.btn_save, 0)
        top_sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, border=10)

        self.SetSizer(top_sizer)

        self.Layout()
        self.Fit()

        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyUP)

        self._save_worker = None

    def _on_tick_gauge(self, event):
        self.progress.Pulse()

    def _on_file_changed(self, event):
        path = self.field_file.GetPath()
        if len(path) == 0:
            return

        if os.path.exists(path):
            self.field_name.SetValue(os.path.basename(path))
            ctime = os.path.getctime(path)
            ctime = datetime.fromtimestamp(ctime).strftime("%d.%m.%Y")
            self.field_data_date.SetValue(ctime)
            self.label_file_error.Hide()
        else:
            self.label_file_error.Show()

        self.Layout()
        self.Fit()

    def _start_save(self):
        path = self.field_file.GetPath()
        _fields = {
            "parent": self.p,
            "path": path,
            "name": self.field_name.GetValue(),
            "comment": self.field_comment.GetValue(),
            "file_name": os.path.basename(path),
            "data_date": encode_date(self.field_data_date.GetValue()),
        }
        mime_type, _ = mimetypes.guess_type(path)
        if mime_type != None:
            _fields["mime_type"] = mime_type
        else:
            _fields["mime_type"] = "application/octet-stream"
        self._save_worker = CreateFileWorker(self.progress, _fields, self._on_resolve, self._on_reject)
        self._save_worker.start()

        self.progress_timer.Start(10)
        self.field_file.Disable()
        self.field_name.Disable()
        self.field_comment.Disable()
        self.field_data_date.Disable()
        self.btn_save.Disable()

    def _end_save(self):
        self.field_file.Enable()
        self.field_name.Enable()
        self.field_comment.Enable()
        self.field_data_date.Enable()
        self.btn_save.Enable()
        self.progress_timer.Stop()
        self.progress.SetValue(0)

    def _on_resolve(self, o):
        wx.CallAfter(self._end_save)
        self.o = o
        wx.CallAfter(self.EndModal, wx.ID_OK)

    def _on_reject(self, reason):
        wx.CallAfter(self._end_save)
        wx.MessageBox("Ошибка: %s" % str(reason), "Ошибка сохранения", wx.OK | wx.ICON_ERROR)

    def _on_save(self, event):
        if not self.Validate():
            return

        path = self.field_file.GetPath()
        if len(path) == 0 or not os.path.exists(path):
            wx.MessageBox("Файл не выбран", "Ошибка заполнения", style=wx.OK | wx.ICON_ERROR)
            return

        self._start_save()

    def OnKeyUP(self, event):
        keyCode = event.GetKeyCode()
        if keyCode == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
        else:
            event.Skip()


class SuppliedDataWidget(wx.Panel):
    def __init__(self, parent, deputy_text=None):
        super().__init__(parent)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.toolbar = wx.ToolBar(self, style=wx.TB_FLAT)
        item = self.toolbar.AddTool(wx.ID_ADD, "Добавить раздел", get_icon("folder-add"))
        self.toolbar.EnableTool(wx.ID_ADD, False)
        self.toolbar.Bind(wx.EVT_TOOL, self._on_create_folder, item)
        item = self.toolbar.AddTool(wx.ID_FILE, "Добавить файл", get_icon("file-add"))
        self.toolbar.AddStretchableSpace()
        item = self.toolbar.AddTool(wx.ID_DOWN, "Скачать", get_icon("download"), kind=wx.ITEM_DROPDOWN)
        self.toolbar.EnableTool(wx.ID_FILE, False)
        self.toolbar.Realize()
        main_sizer.Add(self.toolbar, 0, wx.EXPAND)

        self.statusbar = wx.StatusBar(self, style=0)
        main_sizer.Add(self.statusbar, 0, wx.EXPAND)

        self._deputy = wx.Panel(self)
        deputy_sizer = wx.BoxSizer(wx.VERTICAL)
        if deputy_text is None:
            deputy_text = "Недоступны для этого объекта"
        label = wx.StaticText(self._deputy, label=deputy_text, style=wx.ST_ELLIPSIZE_MIDDLE)
        deputy_sizer.Add(label, 1, wx.CENTER | wx.ALL, border=20)
        self._deputy.SetSizer(deputy_sizer)
        main_sizer.Add(self._deputy, 1, wx.EXPAND)

        self._image_list = wx.ImageList(16, 16)
        self._icons = {}
        self.list = wx.dataview.TreeListCtrl(self, style=wx.dataview.TL_DEFAULT_STYLE | wx.BORDER_NONE)
        self.list.AssignImageList(self._image_list)
        self._icon_folder = self._image_list.Add(get_icon("folder"))
        self._icon_folder_open = self._image_list.Add(get_icon("folder-open"))
        self._icon_file = self._image_list.Add(get_art(wx.ART_NORMAL_FILE, scale_to=16))
        self.list.AppendColumn("Название", 250)
        self.list.AppendColumn("Тип", 50)
        self.list.AppendColumn("Размер", 50)
        self.list.AppendColumn("Датировка", 80)
        self.list.Hide()

        self.SetSizer(main_sizer)
        self._main_sizer = main_sizer

        self.list.Bind(wx.dataview.EVT_TREELIST_SELECTION_CHANGED, self._on_selection_changed)
        self.list.Bind(wx.dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self._on_item_contenxt_menu)

        self.Layout()

    def hide_target_name(self, hide=True):
        if hide:
            self.statusbar.Hide()
        else:
            self.statusbar.Show()
        self.Layout()

    def _on_selection_changed(self, event):
        self._update_controls_state()

    def _on_create_folder(self, event):
        dlg = FolderEditor(self, self.o.RID, self._type)
        if dlg.ShowModal() == wx.ID_OK:
            self._render()

    def _on_create_file(self, event):
        item = self.list.GetSelection()
        o = self.list.GetItemData(item)
        dlg = FileEditor(self, p=o)
        if dlg.ShowModal() == wx.ID_OK:
            self._render()

    def _on_delete(self, event):
        item = self.list.GetSelection()
        o = self.list.GetItemData(item)
        if isinstance(o, SuppliedData):
            rel = ["parts"]
        elif isinstance(o, SuppliedDataPart):
            rel = []
        else:
            return
        if delete_object(o, rel):
            self._render()

    def _on_item_contenxt_menu(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()
        menu = wx.Menu()
        if not item.IsOk():
            item = menu.Append(wx.ID_ADD, "Добавить раздел")
            item.SetBitmap(get_icon("folder-add"))
            menu.Bind(wx.EVT_MENU, self._on_create_folder, item)
        else:
            item = self.list.GetSelection()
            if isinstance(self.list.GetItemData(item), SuppliedData):
                item = menu.Append(wx.ID_EDIT, "Изменить раздел")
            else:
                item = menu.Append(wx.ID_EDIT, "Изменить файл")
            menu.AppendSeparator()
            item = menu.Append(wx.ID_ADD, "Добавить файл")
            item.SetBitmap(get_icon("file-add"))
            menu.Bind(wx.EVT_MENU, self._on_create_file, item)
            item = menu.Append(wx.ID_DELETE, "Удалить")
            menu.Bind(wx.EVT_MENU, self._on_delete, item)
            item.SetBitmap(get_icon("delete"))

        self.PopupMenu(menu, event.GetPosition())

    def _apply_icon(self, icon_name, icon):
        if icon_name not in self._icons:
            self._icons[icon_name] = self._image_list.Add(icon)
        return self._icons[icon_name]

    @db_session
    def _render(self):
        self.list.DeleteAllItems()
        for o in select(o for o in SuppliedData if o.OwnID == self.o.RID and o.OwnType == self._type):
            folder = self.list.AppendItem(self.list.GetRootItem(), o.Name, self._icon_folder, self._icon_folder_open, o)
            self.list.SetItemText(folder, 1, "Папка")
            self.list.SetItemText(folder, 2, "---")
            for child in o.parts:
                ext = child.FileName.split(".")[-1]
                if ext == "xlsx":
                    ext = "xls"
                icon_path = resource_path("icons/%s.png" % ext)
                if os.path.exists(icon_path):
                    _icon = self._apply_icon(ext, wx.Bitmap(icon_path))
                else:
                    _icon = self._icon_file
                file = self.list.AppendItem(folder, child.Name, _icon, _icon, child)
                self.list.SetItemText(file, 1, child.FileName.split(".")[-1])
                self.list.SetItemText(file, 2, "---")
            self.list.Expand(folder)

    def _update_controls_state(self):
        self.toolbar.EnableTool(wx.ID_ADD, self.o != None)
        item = self.list.GetSelection()
        item_selected = False
        folder_selected = False
        if item.IsOk():
            item_selected = True
            folder_selected = isinstance(self.list.GetItemData(item), SuppliedData)
        self.toolbar.EnableTool(wx.ID_FILE, folder_selected)

    def start(self, o, _type):
        self.o = o
        self._type = _type
        self._main_sizer.Detach(2)
        self._deputy.Hide()
        self._main_sizer.Add(self.list, 1, wx.EXPAND)
        self.list.Show()
        self._render()
        self.statusbar.SetStatusText(o.get_tree_name())
        self.toolbar.EnableTool(wx.ID_ADD, True)
        self.Layout()

    def end(self):
        self.o = None
        self._type = None
        self.list.DeleteAllItems()
        self._main_sizer.Detach(2)
        self.list.Hide()
        self._main_sizer.Add(self._deputy, 1, wx.CENTER)
        self._deputy.Show()
        self.statusbar.SetStatusText("")
        self.Layout()
