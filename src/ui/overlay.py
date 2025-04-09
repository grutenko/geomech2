import wx


class Overlay(wx.Panel):
    def __init__(self, parent, text=None):
        super().__init__(parent, style=wx.TRANSPARENT_WINDOW)
        self.SetDoubleBuffered(True)
        self.SetBackgroundColour(wx.Colour(128, 128, 128, 80))  # полупрозрачный чёрный
        self.Hide()  # скрыт по умолчанию

        if text is None:
            text = "Панель недоступна"
        self.text = text

        # Пример: сообщение по центру
        sizer = wx.BoxSizer(wx.VERTICAL)
        text = wx.StaticText(self, label=self.text)
        text.SetForegroundColour(wx.Colour(255, 255, 255))
        font = text.GetFont()
        font.PointSize += 4
        font = font.Bold()
        text.SetFont(font)
        sizer.AddStretchSpacer()
        sizer.Add(text, 0, wx.ALIGN_CENTER)
        sizer.AddStretchSpacer()
        self.SetSizer(sizer)

        self.Bind(wx.EVT_LEFT_DOWN, lambda e: None)
        parent.Bind(wx.EVT_SIZE, self.resize_to_parent)

    def resize_to_parent(self, event):
        event.Skip()
        self.SetSize(self.GetParent().GetSize())
