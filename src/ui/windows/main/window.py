import wx
import wx.aui

import src.objects.ui.page.tree
from src.ui.icon import get_icon

from .left_toolbar import LeftToolbar
from .menu import MainMenu


class MainWindow(wx.Frame):
    def __init__(self):
        super().__init__(None, title="База данных геомеханики", size=wx.Size(1280, 500))
        self.CenterOnScreen()
        self.SetIcon(wx.Icon(get_icon("logo")))

        self.statusbar = wx.StatusBar(self)
        self.statusbar.SetFieldsCount(4)
        self.menu = MainMenu()
        self.SetMenuBar(self.menu)
        self.SetStatusBar(self.statusbar)
        sz = wx.BoxSizer(wx.HORIZONTAL)
        self.left_toolbar = LeftToolbar(self)
        sz.Add(self.left_toolbar, 0, wx.EXPAND)
        p = wx.Panel(self)

        self.mgr = wx.aui.AuiManager(p)
        self.notebook = wx.aui.AuiNotebook(p)
        self.mgr.AddPane(self.notebook, wx.aui.AuiPaneInfo().CenterPane())
        self.mgr.Update()

        sz.Add(p, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.Show()

        self.pages = {"tree": lambda: src.objects.ui.page.tree.PageTree(self.notebook)}
        self.open("tree")

    def open(self, code, *args):
        page = self.pages[code](*args)
        self.notebook.AddPage(page, page.get_name(), select=True, bitmap=page.get_icon())
