import wx

from src.database import PetrotypeStruct

from .entity_list import EntityList


class PetrotypeStructList(EntityList):
    def __init__(self, parent):
        columns = {"Name": ("Название", lambda: ..., 250), "Comment": ("Комментарий", lambda: ..., 350)}
        super().__init__(parent, columns, PetrotypeStruct)
        self.Hide()

    def start(self):
        self.Show()

    def end(self):
        self.Hide()
