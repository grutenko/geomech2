import wx


class MainMenu(wx.MenuBar):
    def __init__(self):
        super().__init__()
        m = wx.Menu()
        self.Append(m, "Файл")
        m = wx.Menu()
        self.Append(m, "Правка")
        m = wx.Menu()
        self.Append(m, "Вид")
        m = wx.Menu()
        self.Append(m, "Настройки")
        m = wx.Menu()
        self.Append(m, "Помощь")
