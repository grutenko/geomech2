import dataclasses
import typing

import wx
import wx.lib.newevent

from .tree_node import TreeNode

WidgetTreeMenu, EVT_WIDGET_TREE_MENU = wx.lib.newevent.NewEvent()
WidgetTreeActivated, EVT_WIDGET_TREE_ACTIVATED = wx.lib.newevent.NewEvent()
WidgetTreeSelChanged, EVT_WIDGET_TREE_SEL_CHANGED = wx.lib.newevent.NewEvent()


@dataclasses.dataclass
class Context:
    node: TreeNode
    subnodes: typing.List[TreeNode] = dataclasses.field(default_factory=lambda: [])
    is_subnodes_loaded: bool = False


@dataclasses.dataclass
class DeputyContext:
    pass


class TreeWidget(wx.Panel):
    def __init__(self, parent, use_icons=True):
        super().__init__(parent)
        self.SetDoubleBuffered(True)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self._tree = wx.TreeCtrl(self, style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT | wx.BORDER_NONE)
        self._use_icons = use_icons

        if self._use_icons:
            self._icons = {}
            self._image_list = wx.ImageList(16, 16)
            self._tree.AssignImageList(self._image_list)
        main_sizer.Add(self._tree, 1, wx.EXPAND)

        self.SetSizer(main_sizer)

        self._root_node = None

        self.Layout()

        self._synthetic_expand = False

    def bind_all(self):
        self._tree.Bind(wx.EVT_TREE_ITEM_EXPANDED, self._on_native_item_expanded)
        self._tree.Bind(wx.EVT_TREE_SEL_CHANGED, self._on_native_item_selection_changed)
        self._tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self._on_native_item_activated)
        self._tree.Bind(wx.EVT_TREE_ITEM_MENU, self._on_native_item_menu)

    def unbind_all(self):
        self._tree.Unbind(wx.EVT_TREE_ITEM_EXPANDED, handler=self._on_native_item_expanded)
        self._tree.Unbind(wx.EVT_TREE_SEL_CHANGED, handler=self._on_native_item_selection_changed)
        self._tree.Unbind(wx.EVT_TREE_ITEM_ACTIVATED, handler=self._on_native_item_activated)
        self._tree.Unbind(wx.EVT_TREE_ITEM_MENU, handler=self._on_native_item_menu)

    def set_root_node(self, root_node: TreeNode):
        if self._root_node is not None:
            self._tree.DeleteAllItems()
        self._root_node = root_node
        self._tree.AddRoot("Объекты")
        self._tree.SetItemData(self._tree.GetRootItem(), Context(root_node))
        self._load_subnodes(self._tree.GetRootItem())

    def _find_native_item(self, node: TreeNode, root_native_item=None, depth=-1):
        if depth == 0:
            return None

        p = root_native_item if root_native_item is not None else self._tree.GetRootItem()
        p_context = self._tree.GetItemData(p)
        if isinstance(p_context, Context) and p_context.node.__eq__(node):
            return p

        item, _ = self._tree.GetFirstChild(p)

        while item.IsOk():
            context = self._tree.GetItemData(item)
            if isinstance(context, Context) and context.node.__eq__(node):
                return item
            child_item = self._find_native_item(node, item, depth - 1 if depth != -1 else -1)
            if child_item is not None:
                return child_item
            item = self._tree.GetNextSibling(item)

        return None

    def _load_subnodes(self, native_item: wx.TreeItemId):
        context: Context = self._tree.GetItemData(native_item)
        if not context.is_subnodes_loaded and not context.node.is_leaf():
            context.subnodes = context.node.get_subnodes()
            context.is_subnodes_loaded = True
        first_item, cookies = self._tree.GetFirstChild(native_item)
        _item_deputy = None
        if first_item.IsOk():
            deputy_context = self._tree.GetItemData(first_item)
            if isinstance(deputy_context, DeputyContext):
                _item_deputy = first_item
        if len(context.subnodes) > 0:
            if _item_deputy is not None:
                _first_subnode = context.subnodes.pop(0)
                self._append_node(native_item, _first_subnode, native_item=_item_deputy)
            for subnode in context.subnodes:
                self._append_node(native_item, subnode)
            if _item_deputy is not None:
                context.subnodes.insert(0, _first_subnode)
        else:
            if _item_deputy is not None:
                wx.CallAfter(self._tree.Delete, _item_deputy)

    def select_node(self, node: TreeNode):
        if node is None:
            return

        _stack = [node]
        while True:
            _item = self._find_native_item(_stack[0])
            if _item is not None or _stack[0].is_root():
                break
            else:
                _stack.insert(0, _stack[0].get_parent())

        _stack.pop()
        _p_item = None
        for _node in _stack:
            _p_item = self._find_native_item(_node)
            if _p_item is None:
                return
            self._load_subnodes(_p_item)

        _item = self._find_native_item(node)
        if _item is not None:
            self._synthetic_expand = True
            try:
                self._tree.SelectItem(_item)
            finally:
                self._synthetic_expand = False

    def soft_reload_node(self, node: TreeNode):
        item = self._find_native_item(node)
        if item is not None:
            self._soft_reload_native_item(item)

    def get_current_node(self):
        item = self._tree.GetSelection()
        if item.IsOk():
            context = self._tree.GetItemData(item)
            if isinstance(context, Context):
                return context.node
            else:
                return None
        return None

    def _soft_reload_native_item(self, native_item: wx.TreeItemId):
        context = self._tree.GetItemData(native_item)
        if isinstance(context, Context):
            context.node.self_reload()
            self._tree.SetItemText(native_item, context.node.get_name())
            icon = context.node.get_icon()
            if icon is not None:
                self._tree.SetItemImage(native_item, self._apply_icon(icon[0], icon[1]), wx.TreeItemIcon_Normal)
            icon = context.node.get_icon_open()
            if icon is not None:
                self._tree.SetItemImage(native_item, self._apply_icon(icon[0], icon[1]), wx.TreeItemIcon_Expanded)

    def soft_reload_childrens(self, node: TreeNode):
        item = self._find_native_item(node)
        if item is not None:
            self._soft_reload_native_item_childrens(item)

    def _soft_reload_native_item_childrens(self, native_item: wx.TreeItemId):
        context = self._tree.GetItemData(native_item)
        if isinstance(context, Context):
            if not context.is_subnodes_loaded:
                self._load_subnodes(native_item)
            else:
                _subnodes_to_delete = []

                subnodes = context.node.get_subnodes()

                for index, node in enumerate(subnodes):
                    item = self._find_native_item(node, native_item, 1)
                    if item is None:
                        self._append_node(native_item, node, index)

                item, cookie = self._tree.GetFirstChild(native_item)
                i = 0
                while item.IsOk():
                    context: Context = self._tree.GetItemData(item)
                    if context.node not in subnodes:
                        _subnodes_to_delete.append(item)

                    item = self._tree.GetNextSibling(item)
                    i += 1

                for item in _subnodes_to_delete:
                    self._tree.Delete(item)

                context.subnodes = subnodes

    def _apply_icon(self, icon_name, icon):
        if icon_name not in self._icons:
            self._icons[icon_name] = self._image_list.Add(icon)
        return self._icons[icon_name]

    def _append_node(self, parent_native_item: wx.TreeItemId, node: TreeNode, index=-1, native_item=None):
        if native_item is None:
            if index == -1:
                item = self._tree.AppendItem(parent_native_item, node.get_name(), data=Context(node))
            else:
                item = self._tree.InsertItem(parent_native_item, index, node.get_name(), data=Context(node))
        else:
            item = native_item
            self._tree.SetItemText(item, node.get_name())
            self._tree.SetItemData(item, Context(node))

        if self._use_icons:
            icon = node.get_icon()
            if icon is not None:
                self._tree.SetItemImage(item, self._apply_icon(icon[0], icon[1]))
            icon_open = node.get_icon_open()
            if icon_open is not None:
                self._tree.SetItemImage(item, self._apply_icon(icon_open[0], icon_open[1]), wx.TreeItemIcon_Expanded)
        if node.is_name_bold():
            self._tree.SetItemBold(item)
        if not node.is_leaf():
            self._tree.AppendItem(item, "[Загрузка]", data=DeputyContext())

    def _on_native_item_expanded(self, event):
        context: Context = self._tree.GetItemData(event.GetItem())
        if not context.is_subnodes_loaded:
            self._load_subnodes(event.GetItem())

        if self._synthetic_expand:
            return

        item, _ = self._tree.GetFirstChild(event.GetItem())
        i = 0
        self._synthetic_expand = True
        try:
            while item.IsOk() and i < 2:
                self._tree.Expand(item)
                item, _ = self._tree.GetFirstChild(item)
                i += 1
        finally:
            self._synthetic_expand = False

    def _on_native_item_selection_changed(self, event: wx.TreeEvent):
        if not self.__nonzero__():
            return

        wx.PostEvent(self, WidgetTreeSelChanged(node=(self._tree.GetItemData(event.GetItem()).node if self._tree.GetSelection().IsOk() else None)))

        event.Skip()

    def _on_native_item_activated(self, event: wx.TreeEvent):
        wx.PostEvent(self, WidgetTreeActivated(node=self._tree.GetItemData(event.GetItem()).node))

    def _on_native_item_menu(self, event: wx.TreeEvent):
        self._tree.SelectItem(event.GetItem())
        wx.PostEvent(self, WidgetTreeMenu(node=self._tree.GetItemData(event.GetItem()).node, point=event.GetPoint()))

    def get_current_root(self):
        return self._root_node
