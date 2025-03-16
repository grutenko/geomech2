import wx

from src.database import PmProperty

from .entity_list import EntityList


class PmProperties(EntityList):
    def __init__(self, parent):
        super().__init__(parent, {}, PmProperty)
        self.Hide()

    def start(self):
        self.Show()

    def end(self):
        self.Hide()
