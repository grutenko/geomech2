import wx
from pony.orm import db_session, select

from src.database import PMSampleSet, PMTestSeries
from src.ui.icon import get_icon
from src.ui.tree import TreeNode, TreeWidget


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
        self.tree = _Tree(self)
        sz.Add(self.tree, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()

    def get_name(self):
        return "ФМС"

    def get_icon(self):
        return get_icon("folder")
