import wx

from src.database import RBTypicalPreventAction

from .entity_list import EntityList


class RbTypicalReasons(EntityList):
    def __init__(self, parent):
        columns = {"Name": ("Название", lambda: ..., 250), "Comment": ("Комментарий", lambda: ..., 350)}
        super().__init__(parent, columns, RBTypicalPreventAction)
        self.Hide()

    def start(self):
        self.Show()

    def end(self):
        self.Hide()
