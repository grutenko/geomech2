import wx

from src.ui.icon import get_icon

from .actions import ID_TOGGLE_FASTVIEW, ID_TOGGLE_OBJECTS, ID_TOGGLE_SUPPLIED_DATA


class LeftToolbar(wx.ToolBar):
    def __init__(self, parent):
        super().__init__(parent, style=wx.TB_FLAT | wx.TB_VERTICAL)
        tool = self.AddCheckTool(ID_TOGGLE_OBJECTS, "Объекты", get_icon("hierarchy"), shortHelp="Показать/Скрыть объекты")
        tool = self.AddCheckTool(ID_TOGGLE_FASTVIEW, "Быстрый просмотр", get_icon("show-property", scale_to=16), shortHelp="Показать/Скрыть быстрый просмотр")
        tool = self.AddCheckTool(ID_TOGGLE_SUPPLIED_DATA, "Сопутствующие материалы", get_icon("versions", scale_to=16), shortHelp="Показать/Скрыть сопутствующие материалы")
        self.Realize()
