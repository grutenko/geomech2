import wx
from pony.orm import db_session, select

from src.ctx import app_ctx
from src.database import PMSampleSet, PMTestSeries
from src.ui.icon import get_icon
from src.ui.tree import EVT_WIDGET_TREE_ACTIVATED, TreeNode, TreeWidget


class _PmSampleSet_Node(TreeNode):
    def __init__(self, o):
        self.o = o

    def get_name(self):
        return self.o.get_tree_name()

    def get_icon(self):
        return "file", get_icon("file")

    def get_parent(self) -> TreeNode:
        return _PmTestSeries_Node(self.o.pm_test_series)

    def is_leaf(self):
        return True

    def __eq__(self, node):
        return isinstance(node, _PmSampleSet_Node) and self.o.RID == node.o.RID


class _PmTestSeries_Node(TreeNode):
    def __init__(self, o):
        self.o = o

    def get_name(self):
        return self.o.get_tree_name()

    def get_icon(self):
        return "folder", get_icon("folder")

    def get_icon_open(self):
        return "folder-open", get_icon("folder-open")

    def get_parent(self) -> TreeNode:
        return _Root_Node()

    @db_session(optimistic=False)
    def get_subnodes(self):
        nodes = []
        for o in select(o for o in PMSampleSet if o.pm_test_series == self.o):
            nodes.append(_PmSampleSet_Node(o))
        return nodes

    def __eq__(self, node):
        return isinstance(node, _PmTestSeries_Node) and self.o.RID == node.o.RID


class _Root_Node(TreeNode):
    def get_name(self) -> str:
        return "Объекты"

    def get_parent(self) -> TreeNode:
        return _Root_Node()

    @db_session(optimistic=False)
    def get_subnodes(self):
        nodes = []
        for o in select(o for o in PMTestSeries):
            nodes.append(_PmTestSeries_Node(o))
        return nodes

    def is_root(self) -> bool:
        return True

    def __eq__(self, o):
        return isinstance(o, _Root_Node)


class _Tree(TreeWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.bind_all()
        self.set_root_node(_Root_Node())


class TreePage(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(self, style=wx.TB_FLAT | wx.TB_HORZ_TEXT)
        self.toolbar.AddTool(wx.ID_ADD, "Добавить", get_icon("file-add"))
        self.toolbar.Bind(wx.EVT_TOOL, self.on_add, id=wx.ID_ADD)
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(wx.ID_EDIT, "Изменить", get_icon("edit"))
        self.toolbar.Bind(wx.EVT_TOOL, self.on_edit, id=wx.ID_EDIT)
        self.toolbar.AddTool(wx.ID_DELETE, "Удалить", get_icon("delete"))
        self.toolbar.Bind(wx.EVT_TOOL, self.on_delete, id=wx.ID_DELETE)
        self.toolbar.EnableTool(wx.ID_EDIT, False)
        self.toolbar.EnableTool(wx.ID_DELETE, False)
        self.toolbar.Realize()
        self.toolbar.Realize()
        sz.Add(self.toolbar, 0, wx.EXPAND)
        self.tree = _Tree(self)
        sz.Add(self.tree, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.tree.Bind(EVT_WIDGET_TREE_ACTIVATED, self.on_activate)

    def on_activate(self, event):
        if isinstance(event.node, _PmSampleSet_Node):
            app_ctx().main.open("pm_sample_set_editor", is_new=False, o=event.node.o)
        elif isinstance(event.node, _PmTestSeries_Node):
            app_ctx().main.open("pm_test_series_editor", is_new=False, o=event.node.o)

    def get_name(self):
        return "ФМС"

    def get_icon(self):
        return get_icon("folder")

    def on_add(self, event): ...

    def on_edit(self, event): ...

    def on_delete(self, event): ...
