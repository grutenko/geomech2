from dataclasses import dataclass, field
from typing import Dict

import wx
import wx.aui
from pony.orm import db_session

from src.ctx import app_ctx
from src.database import is_entity
from src.ui.icon import get_icon
from src.ui.page import EVT_PAGE_HDR_CHANGED

from .actions import (
    ID_CHANGE_CREDENTIALS,
    ID_OPEN_CONSOLE,
    ID_OPEN_DISCHARGE,
    ID_OPEN_DOCUMENTS,
    ID_OPEN_FMS,
    ID_OPEN_MAP,
    ID_OPEN_ROCK_BURST_TREE,
    ID_OPEN_TREE,
)
from .menu import MainMenu
from .toolbar import MainToolbar


@dataclass
class PageCtx:
    type: str
    code: str
    o: object
    kwds: Dict[str, object] = field(default_factory=lambda: {})

    def serialize_allowed(self) -> bool:
        return hasattr(self.o, "serialize")

    def serialize(self):
        if not self.serialize_allowed():
            return None
        data = {"code": self.code, "o": self.o.serialize()}
        kwds = {}
        for key, value in self.kwds:
            if is_entity(value):
                kwds[key] = {"type": "entity", "class": value.__class__.__name__, "id": value.RID}
            else:
                kwds[key] = value
        data["kwds"] = kwds
        return data


class MainWindow(wx.Frame):
    @db_session
    def __init__(self):
        super().__init__(None, title="База данных геомеханики", size=wx.Size(900, 580))
        self.SetSizeHints(580, 580, 2580, 2580)
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
        self.notebook.SetSelectedFont(wx.Font(wx.FontInfo(9).Italic()))
        self.mgr.AddPane(self.notebook, wx.aui.AuiPaneInfo().CenterPane())
        self.mgr.Update()

        sz.Add(p, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.Show()

        def mine_object_editor_def(o=None, is_new=False, parent_object=None, tab_index=0):
            from src.mine_object.ui.page.mine_object_editor import MineObjectEditor

            return MineObjectEditor(self.notebook, o, parent_object, is_new, tab_index)

        def station_editor_def(o=None, is_new=False, parent_object=None):
            from src.station.ui.page.station_editor import StationEditor

            return StationEditor(self.notebook, is_new=is_new, o=o, parent_object=parent_object)

        def bore_hole_editor_def(o=None, is_new=False, parent_object=None):
            from src.bore_hole.ui.page.bore_hole_editor import BoreHoleEditor

            return BoreHoleEditor(self.notebook, is_new=is_new, o=o, parent_object=parent_object)

        def rock_burst_editor_def(o=None, is_new=False, parent_object=None):
            from src.rock_burst.ui.page.editor import RockBurstEditor

            return RockBurstEditor(self.notebook, o=o, is_new=is_new, parent_object=parent_object)

        def pm_sample_set_editor_def(o=None, is_new=False, parent_object=None):
            from src.fms.ui.page.sample_set_editor import PmSampleSetEditor

            return PmSampleSetEditor(self.notebook, is_new=is_new, o=o, parent_object=parent_object)

        def test_series_editor_def(o=None, is_new=False, parent_object=None):
            from src.discharge.ui.page.test_series_editor import TestSeriesEditor

            return TestSeriesEditor(self.notebook, is_new=is_new, o=o, parent_object=parent_object)

        def pm_test_series_editor_def(o=None, is_new=False, parent_object=None):

            from src.fms.ui.page.test_series_editor import PmTestSeriesEditor

            return PmTestSeriesEditor(self.notebook, is_new=is_new, o=o, parent_object=parent_object)

        def documents_editor_def(o=None, is_new=False, parent_object=None):
            from src.document.ui.page.document_editor import DocumentEditor

            return DocumentEditor(self.notebook, is_new=is_new, o=o, parent_object=parent_object)

        def documents_list_def():
            from src.document.ui.page.documents import Documents

            return Documents(self.notebook)

        def tree_def():
            from src.objects.ui.page.tree import PageTree

            return PageTree(self.notebook)

        def fms_def():
            from src.fms.ui.page.fms import FmsPage

            return FmsPage(self.notebook)

        def rock_burst_list_def():
            from src.rock_burst.ui.page.list import RockBurstWidget

            return RockBurstWidget(self.notebook)

        def discharge_list_def():
            from src.discharge.ui.page.list import DischargeList

            return DischargeList(self.notebook)

        def stuf_editor_def(o=None, is_new=False, parent_object=None):
            from src.orig_sample_set.ui.page.stuf_editor import StufEditor

            return StufEditor(self.notebook, is_new=is_new, o=o, parent_object=parent_object)

        def disperse_editor_def(o=None, is_new=False, parent_object=None):
            from src.orig_sample_set.ui.page.disperse_editor import DisperseEditor

            return DisperseEditor(self.notebook, is_new=is_new, o=o, parent_object=parent_object)

        self.page_def = {
            "tree": tree_def,
            "fms": fms_def,
            "rock_burst_list": rock_burst_list_def,
            "discharge_list": discharge_list_def,
            "pm_sample_set_editor": pm_sample_set_editor_def,
            "pm_test_series_editor": pm_test_series_editor_def,
            "rock_burst_editor": rock_burst_editor_def,
            "mine_object_editor": mine_object_editor_def,
            "station_editor": station_editor_def,
            "bore_hole_editor": bore_hole_editor_def,
            "test_series_editor": test_series_editor_def,
            "documents_list": documents_list_def,
            "document_editor": documents_editor_def,
            "stuf_editor": stuf_editor_def,
            "disperse_editor": disperse_editor_def,
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
            "map": lambda args0, args1: True,
            "fms_tree": lambda args0, args1: True,
            "discharge_list": lambda args0, args1: True,
            "console_editor": lambda args0, args1: True,
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
            "stuf_editor": base_args_cmp,
            "disperse_editor": base_args_cmp,
        }
        self.pages = []

        self.bind_all()
        self.setttings_wnd = None
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, event):
        cfg = app_ctx().config
        cfg.width = self.GetSize().GetWidth()
        cfg.height = self.GetSize().GetHeight()
        cfg.x = self.GetPosition().Get().__getitem__(0)
        cfg.y = self.GetPosition().Get().__getitem__(1)
        wx.Exit()
        event.Skip()

    def bind_all(self):
        self.notebook.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.on_page_close)
        self.notebook.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.on_page_changed)
        self.Bind(EVT_PAGE_HDR_CHANGED, self.on_page_header_changed)
        self.Bind(wx.EVT_MENU, self.on_change_credentials, id=ID_CHANGE_CREDENTIALS)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_toggle_tree, id=ID_OPEN_TREE)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_toggle_fms, id=ID_OPEN_FMS)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_open_rock_bursts, id=ID_OPEN_ROCK_BURST_TREE)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_open_discharge_list, id=ID_OPEN_DISCHARGE)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_open_documents, id=ID_OPEN_DOCUMENTS)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_open_console, id=ID_OPEN_CONSOLE)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_open_map, id=ID_OPEN_MAP)
        self.menu.Bind(wx.EVT_MENU, self.on_close_tab, id=wx.ID_CLOSE)
        self.menu.Bind(wx.EVT_MENU, self.on_next_tab, id=wx.ID_PREVIEW_NEXT)
        self.menu.Bind(wx.EVT_MENU, self.on_prev_tab, id=wx.ID_PREVIEW_PREVIOUS)
        self.menu.Bind(wx.EVT_MENU, self.on_open_settings, id=wx.ID_PROPERTIES)

    def on_open_map(self, event):
        _ctx = self.find_ctx_by_code("map")
        if _ctx is None:
            self.open("map")
        else:
            self.close(_ctx.o)

    def on_open_console(self, event):
        _ctx = self.find_ctx_by_code("console_editor")
        if _ctx is None:
            self.open("console_editor")
        else:
            self.close(_ctx.o)

    def on_open_settings(self, event):
        from src.ui.windows.settings.window import SettingsWindow

        if self.setttings_wnd is None:
            self.setttings_wnd = SettingsWindow(self)
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

    def on_toggle_fms(self, event):
        _ctx = self.find_ctx_by_code("fms")
        if _ctx is None:
            self.open("fms")
        else:
            self.close(_ctx.o)

    def on_open_documents(self, event):
        _ctx = self.find_ctx_by_code("documents_list")
        if _ctx is None:
            self.open("documents_list")
        else:
            self.close(_ctx.o)

    def on_page_changed(self, event):
        selected_index = event.GetSelection()
        deselected_index = event.GetOldSelection()
        if selected_index != -1:
            new_wnd = self.notebook.GetPage(selected_index)
            if new_wnd is not None:
                if hasattr(new_wnd, "on_select"):
                    new_wnd.on_select()
        self.update_controls_state()
        if deselected_index != -1:
            old_wnd = self.notebook.GetPage(deselected_index)
            if old_wnd is not None:
                if hasattr(old_wnd, "on_deselect"):
                    old_wnd.on_deselect()

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
        from src.ui.windows.login import LoginDialog

        dlg = LoginDialog(self, mode="CHANGE_CREDENTIALS")
        if dlg.ShowModal() == wx.ID_OK:
            wx.MessageBox(
                "Изменения вступят в силу после перезагрузки", "Доступы изменены", wx.OK | wx.ICON_INFORMATION
            )

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
        apply = True
        if hasattr(wnd, "on_close"):
            apply = wnd.on_close()
        if not apply:
            event.Veto()
            return
        if hasattr(wnd, "on_deselect"):
            wnd.on_deselect()
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
        self.toolbar.ToggleTool(ID_OPEN_FMS, self.find_ctx_by_code("fms") is not None)
        self.toolbar.ToggleTool(ID_OPEN_ROCK_BURST_TREE, self.find_ctx_by_code("rock_burst_list") is not None)
        self.toolbar.ToggleTool(ID_OPEN_DISCHARGE, self.find_ctx_by_code("discharge_list") is not None)
        self.toolbar.ToggleTool(ID_OPEN_DOCUMENTS, self.find_ctx_by_code("documents_list") is not None)
        self.toolbar.ToggleTool(ID_OPEN_CONSOLE, self.find_ctx_by_code("console_editor") is not None)
        self.toolbar.ToggleTool(ID_OPEN_MAP, self.find_ctx_by_code("map") is not None)
        self.menu.Enable(wx.ID_CLOSE, self.notebook.GetPageCount() > 0)
        self.menu.Enable(
            wx.ID_PREVIEW_NEXT,
            self.notebook.GetPageCount() > 0 and self.notebook.GetSelection() < self.notebook.GetPageCount() - 1,
        )
        self.menu.Enable(wx.ID_PREVIEW_PREVIOUS, self.notebook.GetPageCount() > 0 and self.notebook.GetSelection() > 0)
        self.toolbar.Realize()
