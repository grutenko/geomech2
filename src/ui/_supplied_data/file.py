import os
from dataclasses import dataclass
from typing import List

import dateutil.parser
import magic
import wx
from pony.orm import commit, db_session, rollback

from src.custom_datetime import date
from src.database import SuppliedData, SuppliedDataPart
from src.datetimeutil import decode_date, encode_date
from src.ui.icon import get_icon
from src.ui.task import Task, TaskJob
from src.ui.validators import DateValidator, TextValidator


@dataclass
class FileFields:
    parent: SuppliedData
    name: str
    filename: str
    mime_type: str
    data_date: date = None
    comment: str = None


class AddFileTask(TaskJob):
    def __init__(self, files: List[FileFields]):
        self.files = files
        super().__init__()

    @db_session
    def run(self):
        for index, file in enumerate(self.files):
            if self.cancel_event.isSet():
                rollback()
                return
            f = open(file.filename, "rb")
            try:
                SuppliedDataPart(
                    parent=SuppliedData[file.parent.RID],
                    Name=file.name,
                    FileName=os.path.basename(file.filename),
                    Comment=file.comment,
                    DataDate=encode_date(file.data_date) if file.data_date is not None else None,
                    DType=file.mime_type,
                    DataContent=f.read(),
                )
            except Exception as e:
                rollback()
                raise e
            finally:
                f.close()

        if self.cancel_event.isSet():
            rollback()
            return

        commit()


class FileDialog(wx.Dialog):
    def __init__(self, parent, is_new=False, o=None, parent_object=None):
        self.is_new = is_new
        self.o = o
        self.parent_object = parent_object
        self.fields = None
        super().__init__(parent)
        if self.is_new:
            self.SetTitle("Добавить файл")
            self.SetIcon(wx.Icon(get_icon("file-add")))
        else:
            self.SetTitle(self.o.Name)
            self.SetIcon(wx.Icon(get_icon("file")))
        sz = wx.BoxSizer(wx.VERTICAL)
        sz = wx.BoxSizer(wx.VERTICAL)
        sz_in = wx.BoxSizer(wx.VERTICAL)
        sz.Add(sz_in, 1, wx.EXPAND | wx.ALL, border=10)

        label = wx.StaticText(self, label="Файл *")
        sz_in.Add(label, 0, wx.EXPAND)
        self.field_file = wx.FilePickerCtrl(self)
        self.field_file.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_file_changed)
        sz_in.Add(self.field_file, 0, wx.EXPAND)

        self.label_file_error = wx.StaticText(self, label="Неверный путь к файлу")
        self.label_file_error.SetForegroundColour(wx.Colour(255, 0, 0))
        self.label_file_error.Hide()
        sz_in.Add(self.label_file_error, 0, wx.EXPAND)

        label = wx.StaticText(self, label="Название *")
        sz_in.Add(label, 0, wx.EXPAND | wx.TOP, border=10)
        self.field_name = wx.TextCtrl(self, size=wx.Size(250, -1))
        self.field_name.SetValidator(TextValidator(lenMin=1, lenMax=128))
        sz_in.Add(self.field_name, 0, wx.EXPAND | wx.BOTTOM, border=10)

        label = wx.StaticText(self, label="Датировка материала")
        sz_in.Add(label, 0, wx.EXPAND)
        self.field_data_date = wx.TextCtrl(self, size=wx.Size(250, -1))
        self.field_data_date.SetValidator(DateValidator())
        sz_in.Add(self.field_data_date, 0, wx.EXPAND | wx.BOTTOM, border=10)

        collpane = wx.CollapsiblePane(self, wx.ID_ANY, "Комментарий")
        sz_in.Add(collpane, 0, wx.GROW)

        comment_pane = collpane.GetPane()
        comment_sizer = wx.BoxSizer(wx.VERTICAL)
        comment_pane.SetSizer(comment_sizer)

        label = wx.StaticText(comment_pane, label="Комментарий")
        comment_sizer.Add(label, 0)
        self.field_comment = wx.TextCtrl(comment_pane, size=wx.Size(250, 100), style=wx.TE_MULTILINE)
        self.field_comment.SetValidator(TextValidator(lenMin=0, lenMax=512))
        comment_sizer.Add(self.field_comment, 0, wx.EXPAND | wx.BOTTOM, border=10)

        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_up)

        line = wx.StaticLine(self)
        sz.Add(line, 0, wx.EXPAND | wx.TOP, border=10)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        if self.is_new:
            label = "Создать"
        else:
            label = "Изменить"
        self.btn_save = wx.Button(self, label=label)
        self.btn_save.Bind(wx.EVT_BUTTON, self.on_save)
        self.btn_save.SetDefault()
        btn_sizer.Add(self.btn_save, 0)
        sz.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, border=10)
        self.SetSizer(sz)
        self.Layout()
        self.Fit()
        self.CenterOnScreen()
        if not self.is_new:
            self.set_fields()
            self.field_file.Disable()

    def set_fields(self):
        self.field_name.SetValue(self.o.Name)
        self.field_comment.SetValue(self.o.Comment if self.o.Comment is not None else "")
        self.field_data_date.SetValue(str(decode_date(self.o.DataDate)) if self.o.DataDate is not None else "")

    def on_key_up(self, event):
        keyCode = event.GetKeyCode()
        if keyCode == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
        else:
            event.Skip()

    @db_session
    def on_save(self, event):
        if not self.Validate():
            return

        if not os.path.exists(self.field_file.GetPath()):
            wx.MessageBox(
                "Неверный путь к файлу: %s" % self.field_file.GetPath(), "ошибка", style=wx.OK | wx.ICON_ERROR
            )
            return
        if self.is_new:
            # Если создаем новый файл то просто набиваем нужные поля и возвращаем их для обработки в AddFileTask
            self.fields = FileFields(
                parent=self.parent_object,
                name=self.field_name.GetValue(),
                comment=self.field_comment.GetValue(),
                filename=self.field_file.GetPath(),
                data_date=(
                    dateutil.parser.parse(self.field_data_date.GetValue(), dayfirst=True)
                    if len(self.field_data_date.GetValue().strip()) > 0
                    else None
                ),
                mime_type=magic.Magic(mime=True).from_file(self.field_file.GetPath()),
            )
            self.EndModal(wx.ID_OK)
        else:
            # Если изменяем то прямо здесь заменяем поля в базе данных
            SuppliedDataPart[self.o.RID].set(
                Name=self.field_name.GetValue(),
                Comment=self.field_comment.GetValue(),
                DataDate=encode_date(
                    self.field_data_date.GetValue() if len(self.field_data_date.GetValue().strip()) > 0 else None
                ),
            )
            commit()
            self.EndModal(wx.ID_OK)

    def on_file_changed(self, event): ...
