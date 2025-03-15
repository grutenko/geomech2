import wx

from src.ui.icon import get_icon


class SettingsWindow(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Настройки", size=wx.Size(700, 350), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.SetIcon(wx.Icon(get_icon("logo")))
        sz = wx.BoxSizer(wx.VERTICAL)
        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.tree = wx.TreeCtrl(self.splitter)
        r = self.tree.AddRoot("Настройки")
        p = self.tree.AppendItem(r, "ФМС")
        self.tree.AppendItem(p, "Методы испытаний")
        self.tree.AppendItem(p, "Оборудование")
        self.tree.AppendItem(p, "Выполняемые задачи")
        self.tree.AppendItem(p, "Классы свойств")
        self.tree.AppendItem(p, "Свойства")
        p = self.tree.AppendItem(r, "Горные удары")
        p = self.tree.AppendItem(r, "Петротипы")
        p = self.tree.AppendItem(r, "Системы координат")
        self.right = wx.Panel(self.splitter)
        self.splitter.SplitVertically(self.tree, self.right, 200)
        self.splitter.SetMinimumPaneSize(200)
        sz.Add(self.splitter)
        self.Layout()
        self.CenterOnScreen()
