import wx

from src.ui.icon import get_icon


class SettingsWindow(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Настройки", size=wx.Size(700, 350), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.SetIcon(wx.Icon(get_icon("logo")))
        sz = wx.BoxSizer(wx.VERTICAL)
        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.tree = wx.TreeCtrl(self.splitter, style=wx.TR_HIDE_ROOT)
        self.image_list = wx.ImageList(16, 16)
        self.file_icon = self.image_list.Add(get_icon("file"))
        self.tree.SetImageList(self.image_list)
        r = self.tree.AddRoot("Настройки")
        p = self.tree.AppendItem(r, "ФМС")
        self.tree.AppendItem(p, "Методы испытаний", image=self.file_icon)
        self.tree.AppendItem(p, "Оборудование", image=self.file_icon)
        self.tree.AppendItem(p, "Выполняемые задачи", image=self.file_icon)
        self.tree.AppendItem(p, "Классы свойств", image=self.file_icon)
        self.tree.AppendItem(p, "Свойства", image=self.file_icon)
        p = self.tree.AppendItem(r, "Горные удары")
        self.tree.AppendItem(p, "Типовые мероприятия", image=self.file_icon)
        self.tree.AppendItem(p, "Типовые признаки", image=self.file_icon)
        self.tree.AppendItem(p, "Типовые причины", image=self.file_icon)
        self.tree.AppendItem(p, "Типовые профилактические мероприятия", image=self.file_icon)
        self.tree.AppendItem(p, "Типы событий", image=self.file_icon)
        p = self.tree.AppendItem(r, "Петротипы", image=self.file_icon)
        p = self.tree.AppendItem(r, "Системы координат", image=self.file_icon)
        self.right = wx.Panel(self.splitter)
        self.splitter.SplitVertically(self.tree, self.right, 200)
        self.splitter.SetMinimumPaneSize(200)
        sz.Add(self.splitter)
        self.Layout()
        self.CenterOnScreen()
