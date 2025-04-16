import wx

from src.ui.icon import get_icon


class FmsImportDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.SetIcon(wx.Icon(get_icon("logo")))
        self.SetTitle("Импорт данных")
        self.SetSize((600, 400))

        sz = wx.BoxSizer(wx.VERTICAL)
        sz_in = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, label="Файл БД ФМС")
        sz_in.Add(label, 0, wx.EXPAND)
        self.file = wx.FilePickerCtrl(self, message="Выберите файл", wildcard="*.xlsx;*.xls")
        sz_in.Add(self.file, 0, wx.EXPAND | wx.BOTTOM, border=10)
        label = wx.StaticText(self, label="Журнал импорта")
        sz_in.Add(label, 0, wx.EXPAND)
        self.log = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_BESTWRAP)
        sz_in.Add(self.log, 1, wx.EXPAND | wx.BOTTOM, border=10)
        sz.Add(sz_in, 1, wx.EXPAND | wx.ALL, 10)
        line = wx.StaticLine(self)
        sz.Add(line, 0, wx.EXPAND)
        sz_btn = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, "Импортировать")
        ok_btn.SetBitmap(get_icon("import"))
        ok_btn.SetDefault()
        sz_btn.Add(ok_btn)
        sz.Add(sz_btn, 0, wx.ALIGN_RIGHT | wx.ALL, border=10)
        self.SetSizer(sz)
        self.Layout()
