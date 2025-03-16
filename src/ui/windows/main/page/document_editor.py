import pubsub.pub
import wx
from pony.orm import commit, db_session, select

from src.ctx import app_ctx
from src.database import FoundationDocument
from src.datetimeutil import decode_date, encode_date
from src.ui.icon import get_icon
from src.ui.supplied_data import SuppliedDataWidget
from src.ui.validators import DateValidator, TextValidator


class DocumentEditor(wx.Panel):
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
        self.left = wx.Panel(self.splitter)
        p_sz = wx.BoxSizer(wx.VERTICAL)
        p_sz_in = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self.left, label="Тип *")
        p_sz_in.Add(label, 0, wx.EXPAND)
        self.field_type = wx.TextCtrl(self.left)
        self.field_type.SetValidator(TextValidator(lenMin=1, lenMax=255))
        p_sz_in.Add(self.field_type, 0, wx.EXPAND | wx.BOTTOM, border=10)
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
        label = wx.StaticText(self.left, label="Датировка")
        p_sz_in.Add(label, 0)
        self.field_date = wx.TextCtrl(self.left)
        self.field_date.SetValidator(DateValidator(allow_empty=False))
        p_sz_in.Add(self.field_date, 0, wx.EXPAND | wx.BOTTOM, border=10)
        p_sz.Add(p_sz_in, 1, wx.EXPAND | wx.ALL, border=10)
        self.left.SetSizer(p_sz)
        self.right = wx.Notebook(self.splitter)
        self.supplied_data = SuppliedDataWidget(self.right, deputy_text="Недоступно для новых объектов.")
        self.right.AddPage(self.supplied_data, "Сопутствующие материалы")
        self.splitter.SplitVertically(self.left, self.right, 250)
        self.splitter.SetMinimumPaneSize(250)
        sz.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        if not self.is_new:
            self.supplied_data.start(self.o, _type="FOUNDATION_DOC")
            self.set_fields()
        self.toolbar.Bind(wx.EVT_TOOL, self.save, id=wx.ID_SAVE)

    def set_fields(self):
        self.field_type.SetValue(self.o.Type)
        self.field_number.SetValue(self.o.Number)
        self.field_comment.SetValue(self.o.Comment if self.o.Comment is not None else "")
        if self.o.DocDate is not None:
            self.field_date.SetValue(str(decode_date(self.o.DocDate)))

    @db_session
    def save(self, event):
        fields = {"Type": self.field_type.GetValue().strip(), "Number": self.field_number.GetValue().strip(), "Comment": self.field_comment.GetValue().strip()}
        if len(self.field_date.GetValue().strip()) > 0:
            fields["DocDate"] = encode_date(self.field_date.GetValue().strip())
        if self.is_new:
            o = FoundationDocument(**fields)
        else:
            o = FoundationDocument[self.o.RID]
            o.set(**fields)

        commit()
        if self.is_new:
            pubsub.pub.sendMessage("object.added", o=o)
            app_ctx().main.open("document_editor", is_new=False, o=o, parent_object=None)
            app_ctx().main.close(self)
        else:
            pubsub.pub.sendMessage("object.updated", o=o)

    def get_name(self):
        if self.is_new:
            return "(новый)"
        return self.o.Name

    def get_icon(self):
        return get_icon("file")
