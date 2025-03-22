import pubsub.pub
import wx
import wx.propgrid
from pony.orm import commit, db_session, select

from src.ctx import app_ctx
from src.database import CoordSystem, MineObject
from src.mine_object.ui.choice import Choice as MineObjectChoice
from src.ui._supplied_data import SuppliedDataWidget
from src.ui.icon import get_icon
from src.ui.validators import TextValidator


class MineObjectEditor(wx.Panel):
    def __init__(
        self, parent, o: MineObject = None, parent_object: MineObject = None, is_new: bool = False, tab_index=0
    ):
        super().__init__(parent)
        self.is_new = is_new
        self.o = o
        self.parent_object = parent_object
        self.mine_objects = []
        self.coord_systems = []
        sz = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(self, style=wx.TB_HORZ_TEXT | wx.BORDER_DEFAULT)
        self.toolbar.AddTool(wx.ID_SAVE, "Сохранить", get_icon("save"))
        self.toolbar.Realize()
        sz.Add(self.toolbar, 0, wx.EXPAND)
        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.left = wx.ScrolledWindow(self.splitter, style=wx.VSCROLL)
        left_sz = wx.BoxSizer(wx.VERTICAL)
        left_sz_in = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(self.left, label="Родительский объект *")
        left_sz_in.Add(label, 0)
        self.field_mine_object = MineObjectChoice(self.left, mode="all_without_excavation")
        left_sz_in.Add(self.field_mine_object, 0, wx.EXPAND | wx.BOTTOM, border=10)

        label = wx.StaticText(self.left, label="Система координат *")
        left_sz_in.Add(label, 0)
        self.field_coord_system = wx.Choice(self.left)
        left_sz_in.Add(self.field_coord_system, 0, wx.EXPAND | wx.BOTTOM, border=10)

        label = wx.StaticText(self.left, label="Название *")
        left_sz_in.Add(label, 0)
        self.field_name = wx.TextCtrl(self.left, size=wx.Size(250, 25))
        self.field_name.SetValidator(TextValidator(lenMin=1, lenMax=256))
        left_sz_in.Add(self.field_name, 0, wx.EXPAND | wx.BOTTOM, border=10)

        label = wx.StaticText(self.left, label="Комментарий")
        left_sz_in.Add(label, 0)
        self.field_comment = wx.TextCtrl(self.left, size=wx.Size(250, 100), style=wx.TE_MULTILINE)
        self.field_comment.SetValidator(TextValidator(lenMin=0, lenMax=256))
        left_sz_in.Add(self.field_comment, 0, wx.EXPAND | wx.BOTTOM, border=10)

        left_sz.Add(left_sz_in, 1, wx.EXPAND | wx.ALL, border=10)
        self.left.SetSizer(left_sz)
        self.left.SetVirtualSize(self.left.GetBestSize() + (250, 250))
        self.left.SetScrollRate(10, 10)

        self.image_list = wx.ImageList(16, 16)
        self.file_icon = self.image_list.Add(get_icon("file"))
        self.right = wx.Notebook(self.splitter)
        self.right.AssignImageList(self.image_list)
        self.supplied_data = SuppliedDataWidget(
            self.right, deputy_text="Недоступно для новых объектов. Сначала сохраните."
        )
        self.coords = wx.propgrid.PropertyGrid(self.right, style=wx.propgrid.PG_SPLITTER_AUTO_CENTER)
        self.coords.Append(wx.propgrid.FloatProperty("X Мин.", "X_Min"))
        self.coords.Append(wx.propgrid.FloatProperty("Y Мин.", "Y_Min"))
        self.coords.Append(wx.propgrid.FloatProperty("Z Мин.", "Z_Min"))
        self.coords.Append(wx.propgrid.FloatProperty("X Макс.", "X_Max"))
        self.coords.Append(wx.propgrid.FloatProperty("Y Макс.", "Y_Max"))
        self.coords.Append(wx.propgrid.FloatProperty("Z Макс.", "Z_Max"))
        self.coords.SetSplitterPosition(350)
        self.coords.Update()
        self.right.AddPage(self.coords, "Координаты")
        self.right.AddPage(self.supplied_data, "Сопуствующие материалы", imageId=self.file_icon)
        self.splitter.SplitVertically(self.left, self.right, 250)
        self.splitter.SetMinimumPaneSize(250)
        self.right.SetSelection(tab_index)
        sz.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()

        self.load_choices()
        if not self.is_new:
            self.supplied_data.start(self.o)
        self.bind_all()
        if not self.is_new:
            self.field_mine_object.Disable()
            self.field_coord_system.Disable()
            self.set_fields()
        else:
            self.field_mine_object.SetValue(self.parent_object)

    def set_fields(self):
        self.field_mine_object.SetValue(self.o.parent)
        _index = 0
        for index, o in enumerate(self.coord_systems):
            if o.RID == self.o.coord_system.RID:
                _index = index
        self.field_coord_system.SetSelection(_index)
        self.field_name.SetValue(self.o.Name)
        self.field_comment.SetValue(self.o.Comment if self.o.Comment is not None else "")
        self.coords.SetPropertyValues(
            {
                "X_Min": self.o.X_Min,
                "Y_Min": self.o.Y_Min,
                "Z_Min": self.o.Z_Min,
                "X_Max": self.o.X_Max,
                "Y_Max": self.o.Y_Max,
                "Z_Max": self.o.Z_Max,
            }
        )

    @db_session
    def load_choices(self):
        def _coord_system_r(p=None):
            if p is not None:
                objects = select(o for o in CoordSystem if o.parent == p)
            else:
                objects = select(o for o in CoordSystem if o.Level == 0)
            for index, o in enumerate(objects):
                self.coord_systems.append(o)
                self.field_coord_system.Append((" . " * o.Level) + o.Name)
                _coord_system_r(o)

        _coord_system_r()

        if self.field_coord_system.GetCount() > 0:
            self.field_coord_system.SetSelection(0)

    def bind_all(self):
        self.toolbar.Bind(wx.EVT_TOOL, self.on_save, id=wx.ID_SAVE)

    @db_session
    def on_save(self, event):
        if not self.Validate():
            return
        if self.parent_object is not None:
            m = {
                "REGION": "Регион",
                "ROCKS": "Горный массив",
                "FIELD": "Месторождение",
                "HORIZON": "Горизонт",
                "EXCAVATION": "Выработка",
            }
            child_mine_object_type = list(m.keys()).__getitem__(list(m.keys()).index(self.parent_object.Type) + 1)
        else:
            child_mine_object_type = "REGION"
        if self.is_new:
            fields = {
                "Type": child_mine_object_type,
                "Name": self.field_name.GetValue(),
                "Comment": self.field_comment.GetValue(),
                "parent": MineObject[self.mine_objects[self.field_mine_object.GetSelection()].RID],
                "coord_system": CoordSystem[self.coord_systems[self.field_coord_system.GetSelection()].RID],
                "X_Min": self.coords.GetPropertyValue("X_Min"),
                "Y_Min": self.coords.GetPropertyValue("Y_Min"),
                "Z_Min": self.coords.GetPropertyValue("Z_Min"),
                "X_Max": self.coords.GetPropertyValue("X_Max"),
                "Y_Max": self.coords.GetPropertyValue("Y_Max"),
                "Z_Max": self.coords.GetPropertyValue("Z_Max"),
            }
            o = MineObject(**fields)
        else:
            fields = {
                "Name": self.field_name.GetValue(),
                "Comment": self.field_comment.GetValue(),
                "X_Min": self.coords.GetPropertyValue("X_Min"),
                "Y_Min": self.coords.GetPropertyValue("Y_Min"),
                "Z_Min": self.coords.GetPropertyValue("Z_Min"),
                "X_Max": self.coords.GetPropertyValue("X_Max"),
                "Y_Max": self.coords.GetPropertyValue("Y_Max"),
                "Z_Max": self.coords.GetPropertyValue("Z_Max"),
            }
            o = MineObject[self.o.RID]
            o.set(**fields)
        commit()
        if self.is_new:
            pubsub.pub.sendMessage("object.added", o=o)
            app_ctx().main.open(
                "mine_object_editor", is_new=False, o=o, parent_object=None, tab_index=self.right.GetSelection()
            )
            app_ctx().main.close(self)

    def get_name(self):
        if self.is_new:
            return "(новый)"
        return self.o.get_tree_name()

    def get_icon(self):
        return get_icon("file")
