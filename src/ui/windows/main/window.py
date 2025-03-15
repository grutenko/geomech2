from dataclasses import dataclass, field
from typing import Dict

import wx
import wx.aui
from pony.orm import db_session

import src.bore_hole.ui.page.bore_hole_editor
import src.discharge.ui.page.list
import src.discharge.ui.page.test_series_editor
import src.fms.ui.page.sample_set_editor
import src.fms.ui.page.test_series_editor
import src.fms.ui.page.tree
import src.mine_object.ui.page.mine_object_editor
import src.objects.ui.page.tree
import src.rock_burst.ui.page.editor
import src.rock_burst.ui.page.list
import src.station.ui.page.station_editor
from src.ctx import app_ctx
from src.ui.icon import get_icon
from src.ui.page import EVT_PAGE_HDR_CHANGED
from src.ui.windows.login import LoginDialog
from src.ui.windows.settings.window import SettingsWindow

from .actions import ID_CHANGE_CREDENTIALS, ID_OPEN_DISCHARGE, ID_OPEN_DOCUMENTS, ID_OPEN_FMS_TREE, ID_OPEN_ROCK_BURST_TREE, ID_OPEN_TREE
from .menu import MainMenu
from .page.document_editor import DocumentEditor
from .page.documents import Documents
from .toolbar import MainToolbar


@dataclass
class PageCtx:
    type: str
    code: str
    o: object
    kwds: Dict[str, object] = field(default_factory=lambda: {})


class MainWindow(wx.Frame):
    @db_session
    def __init__(self):
        super().__init__(None, title="База данных геомеханики", size=wx.Size(1280, 550))
        self.CenterOnScreen()
        self.SetIcon(wx.Icon(get_icon("logo")))

        self.toolbar = MainToolbar(self)
        self.SetToolBar(self.toolbar)
        self.statusbar = wx.StatusBar(self)
        self.statusbar.SetFieldsCount(4)
        cfg = app_ctx().config
        status = "Подключено: %s, %s:%d, %s" % (cfg.database, cfg.host, cfg.port, cfg.login)
        self.statusbar.SetStatusText(status)
        self.menu = MainMenu()
        self.SetMenuBar(self.menu)
        self.SetStatusBar(self.statusbar)
        sz = wx.BoxSizer(wx.HORIZONTAL)
        p = wx.Panel(self)

        self.mgr = wx.aui.AuiManager(p)
        self.notebook = wx.aui.AuiNotebook(p, style=wx.aui.AUI_NB_DEFAULT_STYLE | wx.aui.AUI_NB_WINDOWLIST_BUTTON)
        self.notebook.SetSelectedFont(wx.Font(wx.FontInfo(10).Italic()))
        self.mgr.AddPane(self.notebook, wx.aui.AuiPaneInfo().CenterPane())
        self.mgr.Update()

        sz.Add(p, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.Show()

        def mine_object_editor_def(o=None, is_new=False, parent_object=None, tab_index=0):
            return src.mine_object.ui.page.mine_object_editor.MineObjectEditor(self.notebook, o, parent_object, is_new, tab_index)

        def station_editor_def(o=None, is_new=False, parent_object=None):
            return src.station.ui.page.station_editor.StationEditor(self.notebook, is_new=is_new, o=o, parent_object=parent_object)

        def bore_hole_editor_def(o=None, is_new=False, parent_object=None):
            return src.bore_hole.ui.page.bore_hole_editor.BoreHoleEditor(self.notebook, is_new=is_new, o=o, parent_object=parent_object)

        def rock_burst_editor_def(o=None, is_new=False, parent_object=None):
            return src.rock_burst.ui.page.editor.RockBurstEditor(self.notebook, o=o, is_new=is_new, parent_object=parent_object)

        def pm_sample_set_editor_def(o=None, is_new=False, parent_object=None):
            return src.fms.ui.page.sample_set_editor.PmSampleSetEditor(self.notebook, is_new=is_new, o=o, parent_object=parent_object)

        def test_series_editor_def(o=None, is_new=False, parent_object=None):
            return src.discharge.ui.page.test_series_editor.TestSeriesEditor(self.notebook, is_new=is_new, o=o, parent_object=parent_object)

        def pm_test_series_editor_def(o=None, is_new=False, parent_object=None):
            return src.fms.ui.page.test_series_editor.PmTestSeriesEditor(self.notebook, is_new=is_new, o=o, parent_object=parent_object)

        def documents_editor_def(o=None, is_new=False, parent_object=None):
            return DocumentEditor(self.notebook, is_new=is_new, o=o, parent_object=parent_object)

        self.page_def = {
            "tree": lambda **kwds: src.objects.ui.page.tree.PageTree(self.notebook),
            "fms_tree": lambda **kwds: src.fms.ui.page.tree.TreePage(self.notebook),
            "rock_burst_list": lambda **kwds: src.rock_burst.ui.page.list.RockBurstWidget(self.notebook),
            "discharge_list": lambda **kwds: src.discharge.ui.page.list.DischargeList(self.notebook),
            "pm_sample_set_editor": pm_sample_set_editor_def,
            "pm_test_series_editor": pm_test_series_editor_def,
            "rock_burst_editor": rock_burst_editor_def,
            "mine_object_editor": mine_object_editor_def,
            "station_editor": station_editor_def,
            "bore_hole_editor": bore_hole_editor_def,
            "test_series_editor": test_series_editor_def,
            "documents_list": lambda **kwds: Documents(self.notebook),
            "document_editor": documents_editor_def,
        }

        # Функции должны возвращать true если наборы аргументов соответствуют друг другу,
        # то есть если страница выводящая такое же данные уже существует.
        # Вместо этого страница будет сделана текущей
        def base_args_cmp(args0, args1):
            if args0.keys() != args1.keys():
                return False
            for key in args0.keys():
                if args0[key] != args1[key]:
                    return False
            return True

        self.page_cmp_args = {
            "tree": lambda args0, args1: True,
            "fms_tree": lambda args0, args1: True,
            "discharge_list": lambda args0, args1: True,
            "mine_object_editor": base_args_cmp,
            "rock_burst_editor": base_args_cmp,
            "station_editor": base_args_cmp,
            "bore_hole_editor": base_args_cmp,
            "rock_burst_list": lambda args0, args1: True,
            "pm_sample_set_editor": base_args_cmp,
            "test_series_editor": base_args_cmp,
            "pm_test_series_editor": base_args_cmp,
            "documents_list": lambda args0, args1: True,
            "document_editor": base_args_cmp,
        }
        self.pages = []

        self.bind_all()
        self.setttings_wnd = SettingsWindow(self)

    def bind_all(self):
        self.notebook.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.on_page_close)
        self.notebook.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.on_page_changed)
        self.Bind(EVT_PAGE_HDR_CHANGED, self.on_page_header_changed)
        self.Bind(wx.EVT_MENU, self.on_change_credentials, id=ID_CHANGE_CREDENTIALS)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_toggle_tree, id=ID_OPEN_TREE)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_toggle_fms_tree, id=ID_OPEN_FMS_TREE)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_open_rock_bursts, id=ID_OPEN_ROCK_BURST_TREE)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_open_discharge_list, id=ID_OPEN_DISCHARGE)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_open_documents, id=ID_OPEN_DOCUMENTS)
        self.menu.Bind(wx.EVT_MENU, self.on_close_tab, id=wx.ID_CLOSE)
        self.menu.Bind(wx.EVT_MENU, self.on_next_tab, id=wx.ID_PREVIEW_NEXT)
        self.menu.Bind(wx.EVT_MENU, self.on_prev_tab, id=wx.ID_PREVIEW_PREVIOUS)
        self.menu.Bind(wx.EVT_MENU, self.on_open_settings, id=wx.ID_PROPERTIES)

    def on_open_settings(self, event):
        self.setttings_wnd.ShowWindowModal()

    def on_open_discharge_list(self, event):
        _ctx = self.find_ctx_by_code("discharge_list")
        if _ctx is None:
            self.open("discharge_list")
        else:
            self.close(_ctx.o)

    def on_open_rock_bursts(self, event):
        _ctx = self.find_ctx_by_code("rock_burst_list")
        if _ctx is None:
            self.open("rock_burst_list")
        else:
            self.close(_ctx.o)

    def on_toggle_fms_tree(self, event):
        _ctx = self.find_ctx_by_code("fms_tree")
        if _ctx is None:
            self.open("fms_tree")
        else:
            self.close(_ctx.o)

    def on_open_documents(self, event):
        _ctx = self.find_ctx_by_code("documents_list")
        if _ctx is None:
            self.open("documents_list")
        else:
            self.close(_ctx.o)

    def on_page_changed(self, event):
        self.update_controls_state()

    def on_next_tab(self, event):
        if self.notebook.GetSelection() < self.notebook.GetPageCount() - 1:
            self.notebook.SetSelection(self.notebook.GetSelection() + 1)

    def on_prev_tab(self, event):
        if self.notebook.GetSelection() > 0:
            self.notebook.SetSelection(self.notebook.GetSelection() - 1)

    def on_close_tab(self, event):
        index = self.notebook.GetSelection()
        if index != -1:
            self.close(self.notebook.GetPage(index))

    def on_toggle_tree(self, event):
        _ctx = self.find_ctx_by_code("tree")
        if _ctx is None:
            self.open("tree")
        else:
            self.close(_ctx.o)

    def on_change_credentials(self, event):
        dlg = LoginDialog(self, mode="CHANGE_CREDENTIALS")
        if dlg.ShowModal() == wx.ID_OK:
            wx.MessageBox("Изменения вступят в силу после перезагрузки", "Доступы изменены", wx.OK | wx.ICON_INFORMATION)

    def find_ctx_by_code(self, code):
        _ctx = None
        for ctx in self.pages:
            if ctx.code == code:
                _ctx = ctx
                break
        return _ctx

    def find_index_by_instance(self, wnd):
        _index = -1
        for index in range(self.notebook.GetPageCount()):
            _wnd = self.notebook.GetPage(index)
            if wnd == _wnd:
                _index = index
                break
        return _index

    def on_page_header_changed(self, event):
        _index = self.find_index_by_instance(event.target)
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
        if event.GetClientData():
            self.notebook.DeletePage(page_index)
        else:
            event.Skip()  # Позволяет закрытию завершиться
        self.update_controls_state()

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
        self.update_controls_state()

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

    def update_controls_state(self):
        self.toolbar.ToggleTool(ID_OPEN_TREE, self.find_ctx_by_code("tree") is not None)
        self.toolbar.ToggleTool(ID_OPEN_FMS_TREE, self.find_ctx_by_code("fms_tree") is not None)
        self.toolbar.ToggleTool(ID_OPEN_ROCK_BURST_TREE, self.find_ctx_by_code("rock_burst_list") is not None)
        self.toolbar.ToggleTool(ID_OPEN_DISCHARGE, self.find_ctx_by_code("discharge_list") is not None)
        self.toolbar.ToggleTool(ID_OPEN_DOCUMENTS, self.find_ctx_by_code("documents_list") is not None)
        self.menu.Enable(wx.ID_CLOSE, self.notebook.GetPageCount() > 0)
        self.menu.Enable(wx.ID_PREVIEW_NEXT, self.notebook.GetPageCount() > 0 and self.notebook.GetSelection() < self.notebook.GetPageCount() - 1)
        self.menu.Enable(wx.ID_PREVIEW_PREVIOUS, self.notebook.GetPageCount() > 0 and self.notebook.GetSelection() > 0)
        self.toolbar.Realize()
