import wx

from src.database import RBTypicalCause

from .entity_list import EntityList


class RcTypicalCauses(EntityList):
    def __init__(self, parent):
        columns = {"Name": ("Название", lambda: ..., 250), "Comment": ("Комментарий", lambda: ..., 350)}
        super().__init__(parent, columns, RBTypicalCause)
        self.Hide()

    def start(self):
        self.Show()

    def end(self):
        self.Hide()
