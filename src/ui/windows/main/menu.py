import wx

from src.ui.icon import get_icon

from .actions import ID_CHANGE_CREDENTIALS


class MainMenu(wx.MenuBar):
    def __init__(self):
        super().__init__()
        m = wx.Menu()
        m.Append(ID_CHANGE_CREDENTIALS, "Настройки доступа к БД")
        m.AppendSeparator()
        i = m.Append(wx.ID_SAVE, "Сохранить текущую вкладку\tCTRL+S")
        i.SetBitmap(get_icon("save"))
        i.Enable(False)
        i = m.Append(wx.ID_PREVIEW_NEXT, "Следующая вкладка\tCTRL+RIGHT")
        i.SetBitmap(get_icon("next", scale_to=16))
        i.Enable(False)
        i = m.Append(wx.ID_PREVIEW_PREVIOUS, "Предыдущая вкладка\tCTRL+LEFT")
        i.SetBitmap(get_icon("back", scale_to=16))
        i.Enable(False)
        i = m.Append(wx.ID_CLOSE, "Закрыть текущую вкладку\tCTRL+W")
        i.SetBitmap(get_icon("delete"))
        i.Enable(False)
        self.Append(m, "Файл")
        m = wx.Menu()
        self.Append(m, "Правка")
        m = wx.Menu()
        self.Append(m, "Вид")
        m = wx.Menu()
        self.Append(m, "Настройки")
        m = wx.Menu()
        self.Append(m, "Помощь")
