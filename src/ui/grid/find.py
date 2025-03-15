import wx

from src.ui.icon import get_icon


class FindDialog(wx.Dialog):
    def __init__(self, parent, q="", strict_mode=True):
        super().__init__(parent, title="Поиск по таблице")
        self.SetIcon(wx.Icon(get_icon("find")))
        self.CenterOnParent()
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyUP)

        top_sizer = wx.BoxSizer(wx.VERTICAL)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer.Add(main_sizer, 1, wx.EXPAND | wx.ALL, border=10)
        self.field_q = wx.TextCtrl(self, value=q, size=wx.Size(300, -1))
        main_sizer.Add(self.field_q, 0, wx.EXPAND | wx.BOTTOM, border=10)
        self.field_range_find = wx.CheckBox(self, label="Строгий поиск")
        if strict_mode:
            mode = wx.CHK_CHECKED
        else:
            mode = wx.CHK_UNCHECKED
        self.field_range_find.Set3StateValue(mode)
        main_sizer.Add(self.field_range_find, 0, wx.EXPAND | wx.BOTTOM, border=10)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_find = wx.Button(self, label="Искать")
        self.btn_find.SetDefault()
        btn_sizer.Add(self.btn_find, 0)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT)
        self.SetSizer(top_sizer)
        self.Layout()
        self.Fit()
        self.btn_find.Bind(wx.EVT_BUTTON, self._on_find)

    def _on_find(self, event):
        self.EndModal(wx.ID_OK)

    def OnKeyUP(self, event):
        keyCode = event.GetKeyCode()
        if keyCode == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
        else:
            event.Skip()

    def get_q(self):
        return self.field_q.GetValue()

    def is_strict_mode(self):
        return self.field_range_find.IsChecked()
