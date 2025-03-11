import wx

from src.ui.icon import get_icon


class MainWindow(wx.Frame):
    def __init__(self):
        super().__init__(None, title="База данных геомеханики", size=wx.Size(1280, 500))
        self.CenterOnScreen()
        self.SetIcon(wx.Icon(get_icon("logo")))
        self.Layout()
        self.Show()
