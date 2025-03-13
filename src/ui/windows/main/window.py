from dataclasses import dataclass, field
from typing import Dict

import wx
import wx.aui
from pony.orm import db_session, select

import src.mine_object.ui.page.mine_object_editor
import src.objects.ui.page.tree
from src.database import MineObject
from src.ui.icon import get_icon
from src.ui.page import EVT_PAGE_HDR_CHANGED

from .menu import MainMenu


@dataclass
class PageCtx:
    type: str
    code: str
    o: object
    kwds: Dict[str, object] = field(default_factory=lambda: {})


class MainWindow(wx.Frame):
    @db_session
    def __init__(self):
        super().__init__(None, title="База данных геомеханики", size=wx.Size(1280, 720))
        self.CenterOnScreen()
        self.SetIcon(wx.Icon(get_icon("logo")))

        self.statusbar = wx.StatusBar(self)
        self.statusbar.SetFieldsCount(4)
        self.menu = MainMenu()
        self.SetMenuBar(self.menu)
        self.SetStatusBar(self.statusbar)
        sz = wx.BoxSizer(wx.HORIZONTAL)
        p = wx.Panel(self)

        self.mgr = wx.aui.AuiManager(p)
        self.notebook = wx.aui.AuiNotebook(p, style=wx.aui.AUI_NB_DEFAULT_STYLE)
        self.notebook.SetSelectedFont(wx.Font(wx.FontInfo(10).Italic()))
        self.mgr.AddPane(self.notebook, wx.aui.AuiPaneInfo().CenterPane())
        self.mgr.Update()

        sz.Add(p, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.Show()

        def mine_object_editor_def(o=None, is_new=False, parent_object=None, tab_index=0):
            return src.mine_object.ui.page.mine_object_editor.MineObjectEditor(self.notebook, o, parent_object, is_new, tab_index)

        self.page_def = {"tree": lambda **kwds: src.objects.ui.page.tree.PageTree(self.notebook), "mine_object_editor": mine_object_editor_def}

        # Функции должны возвращать true если наборы аргументов соответствуют друг другу,
        # то есть если страница выводящая такое же данные уже существует.
        # Вместо этого страница будет сделана текущей
        def mine_object_editor_cmp(args0, args1):
            if args0.keys() != args1.keys():
                return False
            for key in args0.keys():
                if args0[key] != args1[key]:
                    return False
            return True

        self.page_cmp_args = {"tree": lambda args0, args1: True, "mine_object_editor": mine_object_editor_cmp}
        self.pages = []
        self.open("tree")

        self.bind_all()

    def bind_all(self):
        self.notebook.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.on_page_close)
        self.Bind(EVT_PAGE_HDR_CHANGED, self.on_page_header_changed)

    def on_page_header_changed(self, event):
        _index = -1
        for index in range(self.notebook.GetPageCount()):
            _wnd = self.notebook.GetPage(index)
            if event.target == _wnd:
                _index = index
                break
        if _index != -1:
            self.apply_page_header(_index, event.target)

    def apply_page_header(self, index, wnd):
        self.notebook.SetPageText(index, wnd.get_name())
        icon = wnd.get_icon()
        if icon is not None:
            self.notebook.SetPageBitmap(index, icon)

    def on_page_close(self, event):
        page_index = event.GetSelection()
        if page_index == wx.NOT_FOUND:
            return
        wnd = self.notebook.GetPage(page_index)
        # TODO: Добавить отправку события EVT_CLOSE на страницу для возможности Veto()
        for index, ctx in enumerate(self.pages):
            if ctx.o == wnd:
                self.pages.__delitem__(index)
                break
        if event.GetClientData() == True:
            self.notebook.DeletePage(page_index)
        else:
            event.Skip()  # Позволяет закрытию завершиться

    def open(self, code, **kwds):
        """
        открывает новую страницу по ее коду и набору аргументов.
        """
        _finded_page = None
        for page_ctx in self.pages:
            if page_ctx.code == code and self.page_cmp_args[code](page_ctx.kwds, kwds):
                _finded_page = page_ctx
                break
        if _finded_page is not None:
            if _finded_page.type == "notebook":
                index = self.notebook.GetPageIndex(_finded_page.o)
                if index != -1:
                    self.notebook.SetSelection(index)
        else:
            page = self.page_def[code](**kwds)
            self.notebook.AddPage(page, page.get_name(), select=True, bitmap=page.get_icon())
            self.pages.append(PageCtx("notebook", code, page, kwds=kwds))

    def close(self, wnd: wx.Panel):
        _index = -1
        for index in range(self.notebook.GetPageCount()):
            _wnd = self.notebook.GetPage(index)
            if wnd == _wnd:
                _index = index
                break
        if _index != -1:
            close_event = wx.aui.AuiNotebookEvent(wx.aui.wxEVT_AUINOTEBOOK_PAGE_CLOSE, self.notebook.GetId())
            close_event.SetSelection(_index)
            close_event.SetClientData(True)
            wx.PostEvent(self.notebook, close_event)  # Генерируем событие вручную
