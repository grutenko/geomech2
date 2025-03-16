import wx

from src.database import PetrotypeStruct

from .entity_list import EntityList


class PetrotypeStruct(EntityList):
    def __init__(self, parent):
        super().__init__(parent, {}, PetrotypeStruct)
        self.Hide()

    def start(self):
        self.Show()

    def end(self):
        self.Hide()
