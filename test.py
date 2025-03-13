import wx


class SavePopup(wx.PopupTransientWindow):
    def __init__(self, parent, message):
        super().__init__(parent, wx.BORDER_SIMPLE)
        panel = wx.Panel(self)
        text = wx.StaticText(panel, label=message)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(text, flag=wx.ALL, border=10)
        panel.SetSizer(sizer)
        self.SetSize(panel.GetBestSize())
        self.Layout()
        self.Fit()


class MyFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Save Notification", size=(400, 300))
        panel = wx.Panel(self)

        save_button = wx.Button(panel, label="Save File", pos=(20, 20))
        save_button.Bind(wx.EVT_BUTTON, self.on_save)

    def on_save(self, event):
        # Логика сохранения файла
        popup = SavePopup(self, "File saved successfully!")
        pos = self.ClientToScreen((20, 50))  # Размещение рядом с кнопкой
        popup.Position(pos, (0, 0))
        popup.Popup()


app = wx.App(False)
frame = MyFrame()
frame.Show()
app.MainLoop()
