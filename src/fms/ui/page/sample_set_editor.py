import wx
from pony.orm import db_session, select

from src.database import Petrotype, PetrotypeStruct
from src.mine_object.ui.choice import Choice as MineObjectChoice
from src.ui.icon import get_icon
from src.ui.supplied_data import SuppliedDataWidget
from src.ui.validators import DateValidator, TextValidator

from .samples import SamplesWidget


class ComboBoxWithSuggesion(wx.ComboBox):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        self._synthetic_text_enter = False
        self.suggested = False

        self.Bind(wx.EVT_CHAR, self._on_char)
        self.Bind(wx.EVT_TEXT, self._on_text)

    def _on_char(self, event: wx.KeyEvent):
        _from, _to = self.GetTextSelection()
        if event.GetKeyCode() == wx.WXK_BACK and abs(_from - _to) > 0:
            self.SetTextSelection(max(_from - 1, 0), _to)
        event.Skip()

    def _on_text(self, event):
        self.suggested = False
        if self._synthetic_text_enter:
            return
        self._synthetic_text_enter = True
        _text = event.GetString()
        _found = False
        if len(_text) == 0:
            self.SetValue("")
            self._synthetic_text_enter = False
            return

        for index, choice in enumerate(self.GetItems()):
            if choice.upper().startswith(_text.upper()):
                self.suggested = True
                self.SetValue(choice)
                self.SetInsertionPoint(len(_text))
                self.SetTextSelection(len(_text), len(choice))
                _found = True
                break
        if _found:
            event.Skip()

        self._synthetic_text_enter = False


class PmSampleSetEditor(wx.Panel):
    @db_session
    def __init__(self, parent, is_new=False, o=None, parent_object=None):
        self.is_new = is_new
        self.o = o
        self.parent_object = parent_object
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(self, style=wx.TB_FLAT | wx.TB_HORZ_TEXT)
        self.toolbar.AddTool(wx.ID_SAVE, "Сохранить", get_icon("save"))
        self.toolbar.Realize()
        sz.Add(self.toolbar, 0, wx.EXPAND)
        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.left = wx.ScrolledWindow(self.splitter)
        p_sz = wx.BoxSizer(wx.VERTICAL)
        p_sz_in = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self.left, label="Месторождение *")
        p_sz_in.Add(label, 0, wx.EXPAND)
        self.field_mine_object = MineObjectChoice(self.left, mode="field")
        p_sz_in.Add(self.field_mine_object, 0, wx.EXPAND | wx.BOTTOM, border=10)
        label = wx.StaticText(self.left, label="Номер *")
        p_sz_in.Add(label, 0, wx.EXPAND)
        self.field_number = wx.TextCtrl(self.left)
        self.field_number.SetValidator(TextValidator(lenMin=1, lenMax=255))
        p_sz_in.Add(self.field_number, 0, wx.EXPAND | wx.BOTTOM, border=10)
        label = wx.StaticText(self.left, label="Комментарий")
        p_sz_in.Add(label, 0)
        self.field_comment = wx.TextCtrl(self.left, size=wx.Size(250, 100), style=wx.TE_MULTILINE)
        self.field_comment.SetValidator(TextValidator(lenMin=0, lenMax=256))
        p_sz_in.Add(self.field_comment, 0, wx.EXPAND | wx.BOTTOM, border=10)
        label = wx.StaticText(self.left, label="Дата отбора *")
        p_sz_in.Add(label, 0)
        self.field_set_date = wx.TextCtrl(self.left, size=wx.Size(250, 25))
        self.field_set_date.SetValidator(DateValidator())
        p_sz_in.Add(self.field_set_date, 0, wx.EXPAND | wx.BOTTOM, border=10)
        label = wx.StaticText(self.left, label="Дата испытания")
        p_sz_in.Add(label, 0)
        self.field_test_date = wx.TextCtrl(self.left, size=wx.Size(250, 25))
        self.field_test_date.SetValidator(DateValidator(allow_empty=True))
        p_sz_in.Add(self.field_test_date, 0, wx.EXPAND | wx.BOTTOM, border=10)
        label = wx.StaticText(self.left, label="Петротип")
        p_sz_in.Add(label, 0)
        self.field_petrotype = ComboBoxWithSuggesion(self.left)
        self.field_petrotype.Bind(wx.EVT_COMBOBOX, self._on_select_petrotype)
        self.field_petrotype.Bind(wx.EVT_TEXT, self._on_select_petrotype)
        p_sz_in.Add(self.field_petrotype, 0, wx.EXPAND | wx.BOTTOM, border=10)

        self._petrotypes = list(select(o for o in Petrotype))
        for _o in self._petrotypes:
            self.field_petrotype.Append(_o.Name.strip())

        label = wx.StaticText(self.left, label="Структура петротипа")
        p_sz_in.Add(label, 0)
        self._petrotype_structs = []
        self.field_petrotype_struct = ComboBoxWithSuggesion(self.left)
        p_sz_in.Add(self.field_petrotype_struct, 0, wx.EXPAND | wx.BOTTOM, border=10)

        if len(self._petrotypes) > 0:
            self.field_petrotype.SetSelection(0)
            self._on_select_petrotype()
        p_sz.Add(p_sz_in, 1, wx.EXPAND | wx.ALL, border=10)
        self.left.SetSizer(p_sz)
        self.left.SetVirtualSize(self.left.GetBestSize() + (250, 250))
        self.left.SetScrollRate(10, 10)
        self.right = wx.Notebook(self.splitter)
        self.samples = SamplesWidget(self.right)
        self.right.AddPage(self.samples, "Образцы")
        self.supplied_data = SuppliedDataWidget(self.right, deputy_text="Недоступно для новых объектов.")
        self.right.AddPage(self.supplied_data, "Сопутствующие материалы")
        self.splitter.SplitVertically(self.left, self.right, 250)
        self.splitter.SetMinimumPaneSize(250)
        sz.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.SetSizer(sz)
        self.Layout()
        if not self.is_new:
            self.supplied_data.start(self.o)
            self.samples.start(self.o)

    @db_session
    def _on_select_petrotype(self, event=None):
        _text = self.field_petrotype.GetValue()
        _petrotype = select(o for o in Petrotype if o.Name.lower() == _text.lower()).first()
        if _petrotype is not None:
            _petrotype_structs = select(o for o in PetrotypeStruct if o.petrotype == _petrotype)
            self._petrotype_structs = _petrotype_structs
            self.field_petrotype_struct.Clear()
            for o in _petrotype_structs:
                self.field_petrotype_struct.Append(o.Name.strip())
            if len(_petrotype_structs) > 0:
                self.field_petrotype_struct.SetSelection(0)
        else:
            self.field_petrotype_struct.Clear()
        if event is not None:
            event.Skip()

    def get_name(self):
        if self.is_new:
            return "(новый) Проба"
        return "[Проба] " + self.o.Name

    def get_icon(self):
        return get_icon("file")
