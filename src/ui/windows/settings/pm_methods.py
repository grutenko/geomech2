import wx

from src.database import PmTestMethod

from .entity_list import EntityList


class PmMethods(EntityList):
    def __init__(self, parent):
        super().__init__(parent, {}, PmTestMethod)
        self.Hide()

    def start(self):
        self.Show()

    def end(self):
        self.Hide()
