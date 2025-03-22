import wx
from pony.orm import commit, db_session
from transliterate import translit

from src.database import SuppliedData
from src.datetimeutil import decode_date, encode_date
from src.ui.icon import get_icon
from src.ui.validators import DateValidator, TextValidator


class FolderDialog(wx.Dialog):
    def __init__(self, parent, own_entity, is_new=False, o=None):
        self.is_new = is_new
        self.o = o
        self.own_entity = own_entity
        super().__init__(parent)
        if self.is_new:
            self.SetTitle("Добавить папку")
            self.SetIcon(wx.Icon(get_icon("folder-add")))
        else:
            self.SetTitle(self.o.Name)
            self.SetIcon(wx.Icon(get_icon("folder")))
        sz = wx.BoxSizer(wx.VERTICAL)
        sz_in = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, label="Название *")
        sz_in.Add(label, 0, wx.EXPAND)
        self.field_name = wx.TextCtrl(self, size=wx.Size(250, -1))
        self.field_name.SetValidator(TextValidator(lenMin=1, lenMax=128))
        sz_in.Add(self.field_name, 0, wx.EXPAND | wx.BOTTOM, border=10)
        self.field_name.Bind(wx.EVT_KEY_UP, self.on_name_changed)

        label = wx.StaticText(self, label="Номер")
        sz_in.Add(label, 0, wx.EXPAND)
        self.field_number = wx.TextCtrl(self, size=wx.Size(250, -1))
        self.field_number.SetValidator(TextValidator(lenMin=0, lenMax=32))
        sz_in.Add(self.field_number, 0, wx.EXPAND | wx.BOTTOM, border=10)

        label = wx.StaticText(self, label="Датировка материала")
        sz_in.Add(label, 0, wx.EXPAND)
        self.field_data_date = wx.TextCtrl(self, size=wx.Size(250, -1))
        self.field_data_date.SetValidator(DateValidator(allow_empty=True))
        sz_in.Add(self.field_data_date, 0, wx.EXPAND | wx.BOTTOM, border=10)

        collpane = wx.CollapsiblePane(self, wx.ID_ANY, "Комментарий")
        sz_in.Add(collpane, 0, wx.GROW)

        comment_pane = collpane.GetPane()
        comment_sizer = wx.BoxSizer(wx.VERTICAL)
        comment_pane.SetSizer(comment_sizer)

        label = wx.StaticText(comment_pane, label="Комментарий")
        comment_sizer.Add(label, 0)
        self.field_comment = wx.TextCtrl(comment_pane, size=wx.Size(250, 100), style=wx.TE_MULTILINE)
        self.field_comment.SetValidator(TextValidator(lenMin=0, lenMax=512))
        comment_sizer.Add(self.field_comment, 0, wx.EXPAND | wx.BOTTOM, border=10)

        sz.Add(sz_in, 1, wx.EXPAND | wx.ALL, border=10)

        line = wx.StaticLine(self)
        sz.Add(line, 0, wx.EXPAND | wx.TOP, border=10)

        btn_sizer = wx.StdDialogButtonSizer()
        if self.is_new:
            label = "Создать"
        else:
            label = "Изменить"
            self.set_fields()
        self.btn_save = wx.Button(self, label=label)
        self.btn_save.Bind(wx.EVT_BUTTON, self.on_save)
        self.btn_save.SetDefault()
        btn_sizer.Add(self.btn_save, 0)
        sz.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, border=10)
        self.SetSizer(sz)
        self.Layout()
        self.Fit()
        self.CenterOnScreen()

    def on_name_changed(self, event):
        event.Skip()
        self.field_number.SetValue(translit(self.field_name.GetValue(), "ru", reversed=True))

    def set_fields(self):
        o = self.o
        self.field_name.SetValue(o.Name)
        self.field_comment.SetValue(o.Comment if o.Comment is not None else "")
        self.field_number.SetValue(o.Number if o.Number is not None else "")
        self.field_data_date.SetValue(decode_date().__str__() if o.DataDate else "")

    @db_session
    def on_save(self, event):
        if not self.Validate():
            return

        fields = {"Name": self.field_name.GetValue().strip(), "Comment": self.field_comment.GetValue().strip()}

        if len(self.field_number.GetValue().strip()) > 0:
            fields["Number"] = self.field_number.GetValue().strip()
        if len(self.field_data_date.GetValue().strip()) > 0:
            fields["DataDate"] = encode_date(self.field_data_date.GetValue().strip())

        if self.o is None:
            fields["OwnID"] = self.own_entity.RID
            fields["OwnType"] = self.own_entity.sp_own_type
            o = SuppliedData(**fields)
        else:
            o = SuppliedData[self.o.RID]
            o.set(**fields)
        commit()
        self.o = o
        self.EndModal(wx.ID_OK)
