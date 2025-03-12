import wx
import wx.aui


class MyFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="AuiNotebook to AuiManager", size=(800, 600))

        self.manager = wx.aui.AuiManager(self)

        # Главная панель
        self.panel = wx.Panel(self)
        self.notebook = wx.aui.AuiNotebook(self.panel)

        # Создаем панель для вкладки
        self.page = wx.Panel(self.notebook)
        self.page.SetBackgroundColour(wx.Colour(200, 200, 255))

        self.notebook.AddPage(self.page, "Page 1")

        # Кнопки управления
        self.button_move_to_manager = wx.Button(self.panel, label="Move to Manager")
        self.button_move_to_notebook = wx.Button(self.panel, label="Move to Notebook")

        self.button_move_to_manager.Bind(wx.EVT_BUTTON, self.move_to_manager)
        self.button_move_to_notebook.Bind(wx.EVT_BUTTON, self.move_to_notebook)

        # Размещение элементов
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.EXPAND)
        sizer.Add(self.button_move_to_manager, 0, wx.ALL | wx.CENTER, 5)
        sizer.Add(self.button_move_to_notebook, 0, wx.ALL | wx.CENTER, 5)
        self.panel.SetSizer(sizer)

        # Добавляем панель в AuiManager
        self.manager.AddPane(self.panel, wx.aui.AuiPaneInfo().CenterPane())
        self.manager.Update()

        self.moved_panel = None  # Панель, которая перемещается
        self.page_title = "Page 1"

    def move_to_manager(self, event):
        if self.notebook.GetPageCount() == 0:
            return

        # Получаем панель
        self.moved_panel = self.notebook.GetPage(0)
        self.page_title = self.notebook.GetPageText(0)

        # Удаляем из AuiNotebook и меняем родителя
        self.notebook.RemovePage(0)
        self.moved_panel.Reparent(self)  # Меняем родителя на главное окно

        # Добавляем в AuiManager как отдельную панель
        self.manager.AddPane(self.moved_panel, wx.aui.AuiPaneInfo().Caption(self.page_title).Float().CloseButton(True))
        self.manager.Update()

    def move_to_notebook(self, event):
        if self.moved_panel is None:
            return

        # Удаляем из AuiManager
        self.manager.DetachPane(self.moved_panel)
        self.manager.Update()

        # Меняем родителя обратно на AuiNotebook
        self.moved_panel.Reparent(self.notebook)
        self.notebook.AddPage(self.moved_panel, self.page_title)

        self.moved_panel = None


if __name__ == "__main__":
    app = wx.App(False)
    frame = MyFrame()
    frame.Show()
    app.MainLoop()
