import wx

from src.database import RBTypicalCause

from .entity_list import EntityList


class RcTypicalCauses(EntityList):
    def __init__(self, parent):
        super().__init__(parent, {}, RBTypicalCause)
        self.Hide()

    def start(self):
        self.Show()

    def end(self):
        self.Hide()
