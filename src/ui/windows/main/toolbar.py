import wx

from src.ui.icon import get_icon

from .actions import ID_OPEN_DISCHARGE, ID_OPEN_DOCUMENTS, ID_OPEN_FMS_TREE, ID_OPEN_ROCK_BURST_TREE, ID_OPEN_TREE


class MainToolbar(wx.ToolBar):
    def __init__(self, parent):
        super().__init__(parent, style=wx.TB_FLAT | wx.TB_HORZ_TEXT)
        self.AddCheckTool(ID_OPEN_TREE, "Дерево", get_icon("hierarchy"))
        self.AddCheckTool(ID_OPEN_FMS_TREE, "ФМС", get_icon("folder"))
        self.AddCheckTool(ID_OPEN_ROCK_BURST_TREE, "Горные удары", get_icon("folder"))
        self.AddCheckTool(ID_OPEN_DISCHARGE, "Разгрузка", get_icon("folder"))
        self.AddCheckTool(ID_OPEN_DOCUMENTS, "Документы", get_icon("folder"))
        self.Realize()
