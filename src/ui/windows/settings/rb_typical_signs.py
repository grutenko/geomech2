import wx

from src.database import RBTypicalSign

from .entity_list import EntityList


class RcTypicalSigns(EntityList):
    def __init__(self, parent):
        super().__init__(parent, {}, RBTypicalSign)
        self.Hide()

    def start(self):
        self.Show()

    def end(self):
        self.Hide()
