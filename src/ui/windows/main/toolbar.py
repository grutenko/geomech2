import wx

from src.ui.icon import get_icon

from .actions import (
    ID_OPEN_DISCHARGE,
    ID_OPEN_DOCUMENTS,
    ID_OPEN_FMS_TREE,
    ID_OPEN_MAP,
    ID_OPEN_ROCK_BURST_TREE,
    ID_OPEN_TREE,
)


class MainToolbar(wx.ToolBar):
    def __init__(self, parent):
        super().__init__(parent, style=wx.TB_FLAT | wx.TB_HORZ_TEXT)
        i = self.AddTool(ID_OPEN_TREE, "Дерево", get_icon("hierarchy"), kind=wx.ITEM_DROPDOWN)
        m = wx.Menu()
        m.Append(1, "Скважины")
        m.Append(2, "Станции")
        self.SetDropdownMenu(ID_OPEN_TREE, m)
        self.AddCheckTool(ID_OPEN_FMS_TREE, "ФМС", get_icon("folder"))
        self.AddCheckTool(ID_OPEN_ROCK_BURST_TREE, "Горные удары", get_icon("folder"))
        self.AddCheckTool(ID_OPEN_DISCHARGE, "Разгрузка", get_icon("folder"))
        self.AddCheckTool(ID_OPEN_DOCUMENTS, "Документы", get_icon("folder"))
        self.AddSeparator()
        # self.AddCheckTool(ID_OPEN_CONSOLE, "Консоль", get_icon("console"))
        self.AddCheckTool(ID_OPEN_MAP, "Карта", get_icon("map"))
        self.Realize()
