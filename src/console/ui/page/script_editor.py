import importlib
import io
import re
import sys

import wx
import wx.lib.agw.flatnotebook
import wx.lib.newevent
import wx.stc as stc
from pony.orm import commit, db_session, rollback, select, show

from src.ctx import app_ctx
from src.database import (
    BoreHole,
    CoordSystem,
    CoreBoxStorage,
    DischargeMeasurement,
    DischargeSeries,
    FoundationDocument,
    MineObject,
    OrigSampleSet,
    Petrotype,
    PetrotypeStruct,
    PmPerformedTask,
    PmProperty,
    PmPropertyClass,
    PMSample,
    PmSamplePropertyValue,
    PMSampleSet,
    PmSampleSetUsedProperties,
    PmTestEquipment,
    PmTestMethod,
    PMTestSeries,
    RBASKSMEvent,
    RBCause,
    RBGSRASEvent,
    RBPreventAction,
    RBSign,
    RBType,
    RBTypicalCause,
    RBTypicalPreventAction,
    RBTypicalSign,
    RockBurst,
    Station,
    SuppliedData,
    SuppliedDataPart,
)
from src.ui.grid import Column, FloatCellType, GridEditor, Model, NumberCellType, StringCellType
from src.ui.icon import get_icon
from src.ui.tree import (
    EVT_WIDGET_TREE_ACTIVATED,
    EVT_WIDGET_TREE_MENU,
    EVT_WIDGET_TREE_SEL_CHANGED,
    TreeNode,
    TreeWidget,
)

from ...database import File, Folder


def main_wnd():
    return app_ctx().main


globals = {
    "BoreHole": BoreHole,
    "CoordSystem": CoordSystem,
    "CoreBoxStorage": CoreBoxStorage,
    "DischargeMeasurement": DischargeMeasurement,
    "DischargeSeries": DischargeSeries,
    "FoundationDocument": FoundationDocument,
    "MineObject": MineObject,
    "OrigSampleSet": OrigSampleSet,
    "Petrotype": Petrotype,
    "PetrotypeStruct": PetrotypeStruct,
    "PmPerformedTask": PmPerformedTask,
    "PmProperty": PmProperty,
    "PmPropertyClass": PmPropertyClass,
    "PMSample": PMSample,
    "PmSamplePropertyValue": PmSamplePropertyValue,
    "PMSampleSet": PMSampleSet,
    "PmSampleSetUsedProperties": PmSampleSetUsedProperties,
    "PmTestEquipment": PmTestEquipment,
    "PmTestMethod": PmTestMethod,
    "PMTestSeries": PMTestSeries,
    "RBASKSMEvent": RBASKSMEvent,
    "RBCause": RBCause,
    "RBGSRASEvent": RBGSRASEvent,
    "RBPreventAction": RBPreventAction,
    "RBSign": RBSign,
    "RBType": RBType,
    "RBTypicalCause": RBTypicalCause,
    "RBTypicalPreventAction": RBTypicalPreventAction,
    "RBTypicalSign": RBTypicalSign,
    "RockBurst": RockBurst,
    "Station": Station,
    "SuppliedData": SuppliedData,
    "SuppliedDataPart": SuppliedDataPart,
    "db_session": db_session,
    "select": select,
    "show": show,
    "rollback": rollback,
    "main_wnd": main_wnd,
}


def lazy_import(module_name):
    if module_name in sys.modules:
        return sys.modules[module_name]
    module = importlib.import_module(module_name)
    sys.modules[module_name] = module  # Кешируем
    return module


class _CommonDbSectionNode(TreeNode):
    def get_name(self):
        return "База данных"

    def get_icon(self):
        return "folder", get_icon("folder")

    def get_icon_open(self):
        return "folder-open", get_icon("folder-open")

    def __eq__(self, node):
        return isinstance(node, _CommonDbSectionNode)


class _LocalFileNode(TreeNode):
    def __init__(self, o):
        self.o = o

    @db_session
    def get_parent(self):
        if self.o.folder is not None:
            return _LocalFolderNode(Folder[self.o.folder.id])
        return _LocalSectionNode()

    def get_name(self):
        return self.o.name

    def get_icon(self):
        return "file", get_icon("file")

    def is_leaf(self):
        return True

    def __eq__(self, o):
        return isinstance(o, _LocalFileNode) and o.o.id == self.o.id


class _LocalFolderNode(TreeNode):
    def __init__(self, o):
        self.o = o

    def get_name(self):
        return self.o.name

    @db_session
    def get_parent(self):
        if self.o.parent is not None:
            return _LocalFolderNode(Folder[self.o.parent.id])
        return _LocalSectionNode()

    def get_icon(self):
        return "folder", get_icon("folder")

    def get_icon_open(self):
        return "folder-open", get_icon("folder-open")

    @db_session
    def get_subnodes(self):
        nodes = []
        o = Folder[self.o.id]
        for folder in o.folders:
            nodes.append(_LocalFolderNode(folder))
        for file in o.files:
            nodes.append(_LocalFileNode(file))
        return nodes

    @db_session()
    def is_leaf(self):
        o = Folder[self.o.id]
        return len(o.files) == 0 and len(o.folders) == 0

    def __eq__(self, o):
        return isinstance(o, _LocalFolderNode) and o.o.id == self.o.id


class _LocalSectionNode(TreeNode):
    def get_name(self):
        return "Локальные"

    def get_parent(self):
        return _LocalSectionNode()

    def get_icon(self):
        return "folder", get_icon("folder")

    def get_icon_open(self):
        return "folder-open", get_icon("folder-open")

    @db_session()
    def get_subnodes(self):
        nodes = []
        for folder in select(o for o in Folder if o.parent == None):
            nodes.append(_LocalFolderNode(folder))
        for file in select(o for o in File if o.folder == None):
            nodes.append(_LocalFileNode(file))
        return nodes

    def __eq__(self, node):
        return isinstance(node, _LocalSectionNode)


class _RootNode(TreeNode):
    def is_root(self):
        return True

    def get_name(self):
        return "Объекты"

    def get_subnodes(self):
        return [_CommonDbSectionNode(), _LocalSectionNode()]

    def __eq__(self, node):
        return isinstance(node, _RootNode)


import wx.lib.newevent

FileSelectEvent, EVT_FILE_SELECT = wx.lib.newevent.NewEvent()
FileDeleteEvent, EVT_FILE_DELETE = wx.lib.newevent.NewEvent()


class ScriptsTree(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.notebook = wx.lib.agw.flatnotebook.FlatNotebook(
            self, style=wx.lib.agw.flatnotebook.FNB_NAV_BUTTONS_WHEN_NEEDED
        )
        p = wx.Panel(self.notebook)
        p_sz = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(p)
        self.toolbar.AddTool(wx.ID_FILE1, "Добавить папку", get_icon("folder-add"))
        self.toolbar.AddTool(wx.ID_FILE2, "Добавить файл", get_icon("file-add"))
        self.toolbar.EnableTool(wx.ID_FILE1, False)
        self.toolbar.EnableTool(wx.ID_FILE2, False)
        self.toolbar.Realize()
        self.toolbar.Bind(wx.EVT_TOOL, self.on_add_folder, id=wx.ID_FILE1)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_add_file, id=wx.ID_FILE2)
        p_sz.Add(self.toolbar, 0, wx.EXPAND)
        self.tree = TreeWidget(p)
        self.tree.bind_all()
        self.tree.set_root_node(_RootNode())
        p_sz.Add(self.tree, 1, wx.EXPAND)
        p.SetSizer(p_sz)
        self.notebook.AddPage(p, "Скрипты")
        sz.Add(self.notebook, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.tree.Bind(EVT_WIDGET_TREE_ACTIVATED, self.on_tree_activate)
        self.tree.Bind(EVT_WIDGET_TREE_MENU, self.on_tree_menu)
        self.tree.Bind(EVT_WIDGET_TREE_SEL_CHANGED, self.on_tree_sel_changed)

    def on_tree_activate(self, event):
        if isinstance(event.node, _LocalFileNode):
            wx.PostEvent(self, FileSelectEvent(file=event.node.o))

    def on_tree_menu(self, event):
        m = wx.Menu()
        if isinstance(event.node, _LocalSectionNode):
            i = m.Append(wx.ID_FILE1, "Добавить папку")
            i.SetBitmap(get_icon("folder-add"))
            m.Bind(wx.EVT_MENU, self.on_add_folder, id=wx.ID_FILE1)
            i = m.Append(wx.ID_FILE2, "Добавить файл")
            i.SetBitmap(get_icon("file-add"))
            m.Bind(wx.EVT_MENU, self.on_add_file, id=wx.ID_FILE2)
        elif isinstance(event.node, _LocalFolderNode):
            i = m.Append(wx.ID_FILE1, "Добавить папку")
            i.SetBitmap(get_icon("folder-add"))
            m.Bind(wx.EVT_MENU, self.on_add_folder, id=wx.ID_FILE1)
            i = m.Append(wx.ID_FILE2, "Добавить файл")
            i.SetBitmap(get_icon("file-add"))
            m.Bind(wx.EVT_MENU, self.on_add_file, id=wx.ID_FILE2)
            m.AppendSeparator()
            i = m.Append(wx.ID_DELETE, "Удалить")
            i.SetBitmap(get_icon("delete"))
            m.Bind(wx.EVT_MENU, self.on_delete, id=wx.ID_DELETE)
        elif isinstance(event.node, _LocalFileNode):
            i = m.Append(wx.ID_OPEN, "ОТкрыть")
            i = m.Append(wx.ID_DELETE, "Удалить")
            i.SetBitmap(get_icon("delete"))
            m.Bind(wx.EVT_MENU, self.on_delete, id=wx.ID_DELETE)
            i.SetBitmap(get_icon("delete"))
        self.PopupMenu(m, event.point)

    def on_add_folder(self, event):
        self.add_folder(self.tree.get_current_node())

    def on_add_file(self, event):
        self.add_file(self.tree.get_current_node())

    def on_tree_sel_changed(self, event):
        self.update_controls_state()

    @db_session
    def add_folder(self, parent_node):
        dlg = wx.TextEntryDialog(self, "Введите название папки", "Создание папки")
        dlg.SetIcon(wx.Icon(get_icon("folder-add")))
        if dlg.ShowModal() == wx.ID_OK:
            name = dlg.GetValue()
            if isinstance(parent_node, _LocalSectionNode):
                parent = None
            elif isinstance(parent_node, _LocalFolderNode):
                parent = Folder[parent_node.o.id]
            if (
                select(o for o in Folder if o.name == name and o.parent == parent).count() > 0
                or select(o for o in File if o.name == name and o.folder == parent).count() > 0
            ):
                raise RuntimeError("Элемент с таким названием уже существует в этом расположении.")
            o = Folder(name=name, parent=parent)
            commit()
            self.tree.soft_reload_childrens(parent_node)
            self.tree.select_node(_LocalFolderNode(o))

    @db_session
    def add_file(self, parent_node):
        dlg = wx.TextEntryDialog(self, "Введите название файла", "Создание файла")
        dlg.SetIcon(wx.Icon(get_icon("file-add")))
        if dlg.ShowModal() == wx.ID_OK:
            name = dlg.GetValue()
            if isinstance(parent_node, _LocalSectionNode):
                parent = None
            elif isinstance(parent_node, _LocalFolderNode):
                parent = Folder[parent_node.o.id]
            if (
                select(o for o in Folder if o.name == name and o.parent == parent).count() > 0
                or select(o for o in File if o.name == name and o.folder == parent).count() > 0
            ):
                raise RuntimeError("Элемент с таким названием уже существует в этом расположении.")
            o = File(name=name, folder=parent, content="# script file")
            commit()
            self.tree.soft_reload_childrens(parent_node)
            self.tree.select_node(_LocalFileNode(o))

    def on_delete(self, event):
        self.delete(self.tree.get_current_node())

    @db_session
    def delete(self, node):
        if isinstance(node, _LocalFolderNode):

            def r(p):
                for o in p.folders:
                    r(o)
                for o in p.files:
                    o.delete()
                    wx.PostEvent(self, FileDeleteEvent(file=o))
                p.delete()

            r(Folder[node.o.id])
        elif isinstance(node, _LocalFileNode):
            File[node.o.id].delete()
            wx.PostEvent(self, FileDeleteEvent(file=node.o))
        self.tree.soft_reload_childrens(node.get_parent())

    def update_controls_state(self):
        node = self.tree.get_current_node()
        self.toolbar.EnableTool(
            wx.ID_FILE1, node is not None and isinstance(node, (_LocalSectionNode, _LocalFolderNode))
        )
        self.toolbar.EnableTool(
            wx.ID_FILE2, node is not None and isinstance(node, (_LocalSectionNode, _LocalFolderNode))
        )
        self.toolbar.Realize()


import logging


class CodeEditor(stc.StyledTextCtrl):
    def __init__(self, parent):
        super().__init__(parent, style=wx.TE_MULTILINE | wx.TE_WORDWRAP)
        # Устанавливаем 3 бита стиля (важно!)
        self.SetStyleBits(7)
        self.SetIndent(4)
        self.SetUseTabs(False)
        self.SetTabWidth(4)
        self.SetIndentationGuides(stc.STC_IV_LOOKBOTH)  # Включаем направляющие отступов
        self.AutoCompSetIgnoreCase(True)  # Игнорируем регистр
        self.AutoCompSetAutoHide(True)  # Авто-скрытие списка
        self.AutoCompSetDropRestOfWord(True)  # Заменяет текущее слово при выборе
        self.SetCodePage(stc.STC_CP_UTF8)

        # 📌 Включаем боковую панель с номерами строк и маркерами сворачивания
        self.SetMarginType(0, stc.STC_MARGIN_NUMBER)  # Номера строк
        self.SetMarginWidth(0, 40)  # Ширина панели номеров строк
        self.SetMarginType(1, stc.STC_MARGIN_SYMBOL)  # Маркеры сворачивания
        self.SetMarginMask(1, stc.STC_MASK_FOLDERS)  # Маска для сворачивания
        self.SetMarginWidth(1, 20)  # Ширина панели сворачивания
        self.SetMarginSensitive(1, True)  # Позволяет кликать по маркерам

        self.StyleSetFont(
            stc.STC_STYLE_DEFAULT,
            wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Source Code Pro"),
        )

        self.StyleClearAll()

        # 🏗️ Включаем сворачивание блоков
        self.SetProperty("fold", "1")

        # 🎨 Настраиваем значки сворачивания (плюсы и минусы)
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN, stc.STC_MARK_MINUS, "black", "white")  # Открытый блок
        self.MarkerDefine(stc.STC_MARKNUM_FOLDER, stc.STC_MARK_PLUS, "black", "white")  # Закрытый блок
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB, stc.STC_MARK_EMPTY, "black", "white")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL, stc.STC_MARK_EMPTY, "black", "white")

        # Устанавливаем цвет фона и текста по умолчанию
        self.StyleSetBackground(stc.STC_STYLE_DEFAULT, "#FFFFFF")
        self.StyleSetForeground(stc.STC_STYLE_DEFAULT, "#000000")

        # Устанавливаем лексер для Python
        self.SetLexer(stc.STC_LEX_PYTHON)

        self.StyleSetForeground(5, wx.Colour(0, 0, 255))  # Синие ключевые слова
        self.StyleSetForeground(1, wx.Colour(0, 127, 0))  # Зелёные комментарии
        self.StyleSetForeground(3, wx.Colour(127, 0, 127))  # Фиолетовые строки
        self.StyleSetForeground(2, wx.Colour(0, 127, 127))  # Голубые числа

        # Добавляем ключевые слова
        self.SetKeyWords(0, "def class return import from as if else elif while for in is and or not None True False")

        # Включаем сворачивание кода (опционально)
        self.SetProperty("fold", "1")
        self.SetMarginType(2, stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(2, stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(2, True)
        self.Bind(stc.EVT_STC_CHARADDED, self.on_char)
        self.Bind(stc.EVT_STC_AUTOCOMP_SELECTION, self.on_autocomplete)

    def on_char(self, event):
        char = chr(event.GetKey())
        if (
            char.isalpha() and "A" <= char.upper() <= "Z" or (char >= "0" and char <= "9") or char == "."
        ):  # Автодополнение при вводе букв или точки
            try:
                self.show_autocomplete()
            except Exception as e:
                logging.exception(e)
        event.Skip()

    def show_autocomplete(self):
        global globals
        jedi = lazy_import("jedi")
        _code = self.GetText()
        cursor_pos = self.GetCurrentPos()
        line = self.LineFromPosition(cursor_pos) + 1
        column = cursor_pos - self.PositionFromLine(line - 1)
        script = jedi.Interpreter(_code, [globals])  # Используем фиктивный файл
        completions = script.complete(line=line, column=column)

        if completions:
            word_start = self.find_word_start(cursor_pos)  # Определяем начало слова

            if word_start is not None:
                start_pos = cursor_pos - word_start  # Смещение от курсора
                words = "\n".join([c.name for c in completions])  # Создаем список слов для автодополнения
                self.AutoCompShow(start_pos, words)

    def find_word_start(self, cursor_pos):
        """
        Определяет начальную позицию слова перед курсором.
        """
        text = self.GetText()
        match = re.search(r"\b\w+$", text[:cursor_pos])  # Ищем последнее слово перед курсором
        return match.start() if match else None

    def on_autocomplete(self, event):
        """
        Корректно вставляет выбранное слово, чтобы не дублировать весь список.
        """
        selected_text = event.GetText()  # Получаем выбранное слово
        self.ReplaceSelection(selected_text)  # Вставляем его в текущее место ввода


class ResultsTableModel(Model):
    def __init__(self):
        super().__init__()
        self.columns = []
        self.rows = []

    def get_columns(self):
        return self.columns

    def get_value_at(self, col, row):
        if len(self.rows) <= row or len(self.rows[row]) <= col:
            return ""
        return self.rows[row][col]

    def get_rows_count(self):
        return len(self.rows)

    def total_rows(self):
        return len(self.rows)

    def push_column(self, name, celltype="str"):
        self.columns.append(Column(name, StringCellType(), name, name))

    def push_row(self, cells=[]):
        self.rows.append(cells)


class ResultsTable(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.menu = wx.MenuBar()
        m = wx.Menu()
        self.menu.Append(m, "Файл")
        m = wx.Menu()
        self.menu.Append(m, "Правка")
        m = wx.Menu()
        self.menu.Append(m, "Вид")
        self.toolbar = wx.ToolBar(self)
        self.toolbar.Hide()
        self.statusbar = wx.StatusBar(self)
        self.statusbar.SetFieldsCount(4)
        self.statusbar.Hide()
        self.model = ResultsTableModel()
        self.grid = GridEditor(
            self, self.model, self.menu, self.toolbar, self.statusbar, header_height=25, read_only=True
        )
        sz.Add(self.grid, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()

    def push_column(self, name, celltype="str"):
        self.model.push_column(name, celltype)
        self.grid._render()

    def push_row(self, cells):
        self.model.push_row(cells)
        self.grid._render()

    def clear(self):
        self.model.columns = []
        self.model.rows = []
        self.grid._render()


import os


class ScriptEditor(wx.Panel):
    def __init__(self, parent):
        global globals
        super().__init__(parent)
        self.file = None
        # Подключаемся к локальной sqlite базе данных скриптов
        sz = wx.BoxSizer(wx.VERTICAL)
        self.horsplitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.tree = ScriptsTree(self.horsplitter)
        self.splitter = wx.SplitterWindow(self.horsplitter, style=wx.SP_LIVE_UPDATE)
        p = wx.Panel(self.splitter)
        p_sz = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(p, style=wx.TB_FLAT | wx.TB_HORZ_TEXT)
        self.toolbar.AddTool(wx.ID_EXECUTE, "Запустить", get_icon("run"))
        self.toolbar.AddTool(wx.ID_SAVE, "Сохранить", get_icon("save"))
        self.toolbar.EnableTool(wx.ID_SAVE, False)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_run, id=wx.ID_EXECUTE)
        self.toolbar.Realize()
        p_sz.Add(self.toolbar, 0, wx.EXPAND)
        self.editor = CodeEditor(p)
        if os.path.exists(app_ctx().datadir + "/console_cache.txt"):
            with open(app_ctx().datadir + "/console_cache.txt", "r") as f:
                self.editor.SetValue(f.read())
        p_sz.Add(self.editor, 1, wx.EXPAND)
        p.SetSizer(p_sz)
        self.result = wx.lib.agw.flatnotebook.FlatNotebook(self.splitter)
        self.stdout_text = wx.TextCtrl(self.result, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.result.AddPage(self.stdout_text, "Выходные данные")
        self.result_table = ResultsTable(self.result)
        self.result.AddPage(self.result_table, "Таблица")
        self.splitter.SetMinimumPaneSize(150)
        self.splitter.SetSashGravity(1)
        self.splitter.SplitHorizontally(p, self.result, -150)
        self.horsplitter.SplitVertically(self.tree, self.splitter, 200)
        self.horsplitter.SetMinimumPaneSize(150)
        self.horsplitter.SetSashGravity(0)
        sz.Add(self.horsplitter, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.tree.Bind(EVT_FILE_SELECT, self.on_file_select)
        self.tree.Bind(EVT_FILE_DELETE, self.on_file_delete)

        self.stdout = ""

    def on_file_delete(self, event):
        if self.file is not None and self.file.id == event.file.id:
            self.file = None
            self.editor.SetValue("")
            self.update_controls_state()

    def on_file_select(self, event):
        if self.file is not None and self.file.id == self.file.id:
            return
        if self.file is not None or len(self.editor.GetValue()) > 0:
            ret = wx.MessageBox(
                "Текущиие изменения будут отменены.", "Подтеердите открытие", style=wx.OK | wx.ICON_ASTERISK
            )
            if ret != wx.OK:
                return
        self.file = event.file
        self.editor.SetValue(event.file.content)
        self.update_controls_state()

    def on_run(self, event):
        self.run()

    def push_column(self, name, celltype="str"):
        self.result_table.push_column(name, celltype)

    def push_row(self, cells=[]):
        self.result_table.push_row(cells)

    def go_to_table(self):
        self.result.SetSelection(1)

    def go_to_stdout(self):
        self.result.SetSelection(0)

    def run(self):
        self.result_table.clear()
        global globals
        buffer = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buffer  # Перехватываем вывод
        source = "\n".join("  " + line for line in self.editor.GetValue().splitlines())
        if len(source.strip("\t\n\r ")) == 0:
            source = "  pass"
        grid_fn = {
            "push_column": self.push_column,
            "push_row": self.push_row,
            "go_to_table": self.go_to_table,
            "go_to_stdout": self.go_to_stdout,
        }
        # добавляет весь код в сессю ponyorm в конце добавляется rollback чтобы отменить все возможные изменения
        # важно чтобы после \n были пробелы чтобы rollback был ОБЗАТЕЛЬНО внутри with иначе изменения сработают, что нежелательно
        # Для скриптов с wx.Dialog могут быть проблемы с долгим удержанием сессии.
        # Возможно обернуть db_session() чтобы он всегда делал rollback и дать пользователю запускать сессии. Либо вобще сделать свою реализацию
        source = "with db_session:\n" + source + "\n  rollback()"
        exec(source, globals | grid_fn, globals | grid_fn)
        sys.stdout = old_stdout
        self.stdout = buffer.getvalue()
        self.stdout_text.SetValue(self.stdout)

    def get_name(self):
        return "Консоль"

    def get_icon(self):
        return get_icon("console")

    def on_close(self):
        if len(self.editor.GetText()) > 0:
            ret = wx.MessageBox("Закрыть?", "Подтвердите закрытие", style=wx.OK | wx.CANCEL | wx.ICON_ASTERISK)
            if ret != wx.OK:
                return False
        with open(app_ctx().datadir + "/console_cache.txt", "w+") as f:
            f.write(self.editor.GetValue())
        return True

    def update_controls_state(self):
        self.toolbar.EnableTool(wx.ID_SAVE, self.file is not None)
        self.toolbar.Realize()
