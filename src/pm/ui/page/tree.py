import re

import wx
from pony.orm import db_session, select

from src.ctx import app_ctx
from src.database import PMSampleSet, PMTestSeries
from src.ui.icon import get_icon
from src.ui.tree import (
    EVT_WIDGET_TREE_ACTIVATED,
    EVT_WIDGET_TREE_MENU,
    EVT_WIDGET_TREE_SEL_CHANGED,
    TreeNode,
    TreeWidget,
)

from ..db_import import FmsImportDialog


class _PmSampleSet_Node(TreeNode):
    def __init__(self, o):
        self.o = o

    @db_session
    def self_reload(self):
        self.o = PMSampleSet[self.o.RID]

    @db_session
    def get_name(self):
        samples_count = len(PMSampleSet[self.o.RID].pm_samples)
        return self.o.get_tree_name() + (" (образцов: %d)" % samples_count)

    def get_icon(self):
        if self.o.RealDetails:
            return "file", get_icon("file")
        else:
            return "file-search", get_icon("file-search")

    def get_parent(self) -> TreeNode:
        return _PmTestSeries_Node(self.o.pm_test_series)

    def is_leaf(self):
        return True

    def __eq__(self, node):
        return isinstance(node, _PmSampleSet_Node) and self.o.RID == node.o.RID


class _PmTestSeries_Node(TreeNode):
    def __init__(self, o):
        self.o = o

    @db_session
    def self_reload(self):
        self.o = PMTestSeries[self.o.RID]

    @db_session
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
        samples_sets = select(o for o in PMSampleSet if o.pm_test_series == self.o)[:]
        samples_sets = sorted(
            samples_sets, key=lambda p: (float(p.Number) if re.match(r"^\d+(\.\d+)?$", p.Number) else float("inf"))
        )
        for o in samples_sets:
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
        self.toolbar.AddTool(wx.ID_EDIT, "Изменить", get_icon("edit"))
        self.toolbar.Bind(wx.EVT_TOOL, self.on_edit, id=wx.ID_EDIT)
        self.toolbar.AddTool(wx.ID_DELETE, "Удалить", get_icon("delete"))
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(wx.ID_CONVERT, "Импорт", get_icon("import"))
        self.toolbar.Bind(wx.EVT_TOOL, self.on_import, id=wx.ID_CONVERT)
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
        self.tree.Bind(EVT_WIDGET_TREE_MENU, self.on_menu)
        self.tree.Bind(EVT_WIDGET_TREE_SEL_CHANGED, self.on_sel_changed)
        self.current_node = None

    def on_sel_changed(self, event):
        self.update_controls_state()

    def on_import(self, event):
        dlg = FmsImportDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            # Перезагрузит список Договоров из БД и мягко обновит дерево
            # добавит то, чего нет, обновит то что изменилось, удалит то чего больше нет в бд все остальное трогать не будет
            self.tree.soft_reload_childrens(_Root_Node())
            for node in _Root_Node().get_subnodes():
                self.tree.soft_reload_childrens(node)

        dlg.Destroy()

    def on_activate(self, event):
        if isinstance(event.node, _PmSampleSet_Node):
            app_ctx().main.open("pm_sample_set_editor", is_new=False, o=event.node.o)
        elif isinstance(event.node, _PmTestSeries_Node):
            app_ctx().main.open("pm_test_series_editor", is_new=False, o=event.node.o)

    def on_edit(self, event):
        node = self.tree.get_current_node()
        if node is None:
            return
        if isinstance(node, _PmSampleSet_Node):
            app_ctx().main.open("pm_sample_set_editor", is_new=False, o=node.o)
        elif isinstance(node, _PmTestSeries_Node):
            app_ctx().main.open("pm_test_series_editor", is_new=False, o=node.o)

    def on_delete(self, event):
        node = self.tree.get_current_node()
        if node is None:
            return
        if isinstance(node, _PmSampleSet_Node) and node.o.RealDetails:
            ...
        elif isinstance(node, _PmSampleSet_Node) and not node.o.RealDetails:
            ...
        elif isinstance(node, _PmTestSeries_Node):
            ...

    def on_add_sample_set(self, event): ...

    def on_add_approx_sample_set(self, event): ...

    def on_menu(self, event):
        self.current_node = event.node
        m = wx.Menu()
        if isinstance(event.node, _PmSampleSet_Node):
            i = m.Append(wx.ID_EDIT, "Изменить")
            i.SetBitmap(get_icon("edit"))
            m.Bind(wx.EVT_MENU, self.on_edit, i)
            i = m.Append(wx.ID_DELETE, "Удалить")
            i.SetBitmap(get_icon("delete"))
            m.Bind(wx.EVT_MENU, self.on_delete, i)
        elif isinstance(event.node, _PmTestSeries_Node):
            i = m.Append(wx.ID_FILE1, "Добавить пробу")
            i.SetBitmap(get_icon("file"))
            m.Bind(wx.EVT_MENU, self.on_add_sample_set, i)
            i = m.Append(wx.ID_FILE2, "Добавить примерную пробу")
            m.Bind(wx.EVT_MENU, self.on_add_approx_sample_set, i)
            i.SetBitmap(get_icon("file-search"))
            i = m.Append(wx.ID_EDIT, "Изменить")
            m.Bind(wx.EVT_MENU, self.on_edit, i)
            i.SetBitmap(get_icon("edit"))
            i = m.Append(wx.ID_DELETE, "Удалить")
            m.Bind(wx.EVT_MENU, self.on_delete, i)
            i.SetBitmap(get_icon("delete"))
        self.PopupMenu(m, event.point)

    def update_controls_state(self):
        self.toolbar.EnableTool(wx.ID_EDIT, self.tree.get_current_node() is not None)
        self.toolbar.EnableTool(wx.ID_DELETE, self.tree.get_current_node() is not None)
