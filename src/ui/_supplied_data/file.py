import wx
from pony.orm import commit, db_session

from src.ui.icon import get_icon
from src.ui.validators import DateValidator, TextValidator


class FileDialog(wx.Dialog):
    def __init__(self, parent, is_new=False, o=None, parent_object=None):
        self.is_new = is_new
        self.o = o
        self.parent_object = parent_object
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

        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyUP)

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
        self.CenterOnScreen()

    @db_session
    def on_save(self, event): ...

    def on_file_changed(self, event): ...
