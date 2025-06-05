import os

import wx

from src.ui.icon import get_icon


class DoImportDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.SetTitle("Идет импорт...")
        sz = wx.BoxSizer(wx.VERTICAL)
        sz_in = wx.BoxSizer(wx.VERTICAL)
        self.gauge = wx.Gauge(self)
        sz_in.Add(self.gauge, 0, wx.EXPAND | wx.BOTTOM, border=10)
        label = wx.StaticText(self, label="Журнал импорта")
        sz_in.Add(label, 0)
        self.log = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        sz_in.Add(self.log, 1, wx.EXPAND)
        sz.Add(sz_in, 1, wx.EXPAND | wx.ALL, border=10)
        self.SetSizer(sz)
        self.Layout()

    def run(self, filename: str): ...


class FmsImportDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.SetIcon(wx.Icon(get_icon("logo")))
        self.SetTitle("Импорт данных")
        self.SetSize((600, 160))
        sz = wx.BoxSizer(wx.VERTICAL)
        sz_in = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, label="Файл БД ФМС")
        sz_in.Add(label, 0, wx.EXPAND)
        self.file = wx.FilePickerCtrl(self, message="Выберите файл", wildcard="*.xlsx;*.xls")
        self.file.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_file_picker_changed)
        sz_in.Add(self.file, 0, wx.EXPAND | wx.BOTTOM, border=10)
        sz.Add(sz_in, 1, wx.EXPAND | wx.ALL, 10)
        line = wx.StaticLine(self)
        sz.Add(line, 0, wx.EXPAND)
        sz_btn = wx.StdDialogButtonSizer()
        self.ok_btn = wx.Button(self, wx.ID_OK, "Импортировать")
        self.ok_btn.SetBitmap(get_icon("import"))
        self.ok_btn.Disable()
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_import)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        sz_btn.Add(self.ok_btn)
        sz.Add(sz_btn, 0, wx.ALIGN_RIGHT | wx.ALL, border=10)
        self.SetSizer(sz)
        self.Layout()

    def on_close(self, event):
        self.EndModal(wx.ID_CANCEL)

    def on_file_picker_changed(self, event):
        self.ok_btn.Enable(os.path.exists(self.file.GetPath()))

    def on_import(self, event):
        dlg = DoImportDialog(self)
        dlg.run(self.file.GetPath())
