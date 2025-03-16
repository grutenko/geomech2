import wx
from pony.orm import db_session, select

from src.database import CoordSystem

from .entity_list import EntityList


class CoordSystems(EntityList):
    @db_session
    def __init__(self, parent):
        columns = {"Name": ("Название", lambda: ..., 250), "Comment": ("Комментарий", lambda: ..., 350)}
        query = select(o for o in CoordSystem if o.Level > 0)
        super().__init__(parent, columns, CoordSystem, query=query)
        self.Hide()

    def start(self):
        self.Show()

    def end(self):
        self.Hide()
