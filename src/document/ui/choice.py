import wx
from pony.orm import db_session, select

from src.ctx import app_ctx
from src.database import FoundationDocument


class Choice(wx.Panel):
    @db_session
    def __init__(self, parent):
        super().__init__(parent)
        self.items = []
        self.selection = None
        sz = wx.BoxSizer(wx.VERTICAL)
        self.choice = wx.Choice(self)
        sz.Add(self.choice, 0, wx.EXPAND)
        hsz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(hsz, 0, wx.EXPAND)
        self.btn_open = wx.StaticText(self, label="Окрыть")
        font = wx.Font().Underlined()
        self.btn_open.SetFont(font)
        self.btn_open.SetForegroundColour(wx.Colour(100, 100, 255))
        self.btn_open.Bind(wx.EVT_LEFT_DOWN, self.on_open)
        self.btn_open.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        hsz.Add(self.btn_open, 0, wx.RIGHT, border=5)
        self.btn_open.Disable()
        self.btn_refresh = wx.StaticText(self, label="Обновить")
        font = wx.Font().Underlined()
        self.btn_refresh.SetFont(font)
        self.btn_refresh.SetForegroundColour(wx.Colour(100, 100, 255))
        self.btn_refresh.Bind(wx.EVT_LEFT_DOWN, self.on_refresh)
        self.btn_refresh.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        hsz.Add(self.btn_refresh, 0, wx.RIGHT, border=5)
        self.SetSizer(sz)
        self.Layout()
        self.load()
        self.choice.Bind(wx.EVT_CHOICE, self.on_choice)

    def on_choice(self, event):
        _index = self.choice.GetSelection()
        if _index > 0:
            self.selection = self.items[_index - 1]
        else:
            self.selection = None
        self.update_controls_state()

    def on_open(self, event):
        app_ctx().main.open("document_editor", is_new=False, o=self.selection)

    def on_refresh(self, event):
        self.load()

    def select(self):
        _index = 0
        _doc = None
        if self.selection is not None:
            _doc = FoundationDocument[self.selection.RID]
            for index, o in enumerate(self.items):
                if o.RID == _doc.RID:
                    _index = index + 1
                    break
        self.choice.SetSelection(_index)

    @db_session
    def load(self):
        self.items = []
        self.choice.Clear()
        self.choice.Append("Без документа")
        for o in select(o for o in FoundationDocument):
            self.items.append(o)
            self.choice.Append(o.Name)
        if self.choice.GetCount() > 0:
            self.choice.SetSelection(0)
        if self.selection is not None:
            for index, _o in enumerate(self.items):
                if _o.RID == self.selection.RID:
                    self.selection = _o
                    break
            self.select()

    def SetValue(self, foundation_doc: FoundationDocument):
        self.selection = foundation_doc
        self.select()

    def GetValue(self) -> FoundationDocument:
        return self.selection

    def update_controls_state(self):
        self.btn_open.Enable(self.selection is not None)
