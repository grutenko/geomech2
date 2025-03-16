import wx

from src.database import PmPropertyClass

from .entity_list import EntityList


class PmPropertyClasses(EntityList):
    def __init__(self, parent):
        super().__init__(parent, {}, PmPropertyClass)
        self.Hide()

    def start(self):
        self.Show()

    def end(self):
        self.Hide()
