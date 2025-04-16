from datetime import timedelta

import wx
from pony.orm import db_session

from src.ctx import app_ctx
from src.custom_datetime import datetime
from src.database import db
from src.ui.icon import get_icon


def human_readable_time(dt: datetime) -> str:
    now = datetime.now()
    delta = now - dt

    if delta < timedelta(minutes=1):
        return "только что"
    elif delta < timedelta(hours=1):
        minutes = int(delta.total_seconds() // 60)
        return f"{minutes} мин назад"
    elif dt.date() == now.date():
        return "сегодня в " + dt.strftime("%H:%M")
    elif dt.date() == (now - timedelta(days=1)).date():
        return "вчера в " + dt.strftime("%H:%M")
    elif dt.year == now.year:
        return dt.strftime("%d %B") + " в " + dt.strftime("%H:%M")  # для Linux/macOS
        # return dt.strftime("%#d %B в %H:%M")  # для Windows
    else:
        return dt.strftime("%d.%m.%Y")


class RecentlyUsedMenu(wx.Menu):
    def __init__(self, section: str = None):
        super().__init__()
        self.items = []
        self.section = section
        self.load_id = wx.NewIdRef()
        self.Append(self.load_id, "Загрузка...")
        self.Enable(self.load_id, False)
        self.Bind(wx.EVT_MENU, self.on_menu)

    @db_session
    def rebuild(self):
        for item in self.GetMenuItems():
            self.Delete(item.GetId())
        self.items = []
        k = list(map(lambda a: a.__qualname__, db.entities.values()))
        v = db.entities.values()
        entities = dict(zip(k, v))
        i = 1
        for item in app_ctx().recently_used.section(self.section):
            if item.class_name not in entities:
                continue

            try:
                o = entities[item.class_name][item.id_]
            except Exception:
                continue

            menu_item = self.Append(i, o.get_tree_name() + " (" + human_readable_time(item.use_date) + ")")
            menu_item.SetBitmap(get_icon("file"))
            self.items.append(o)
            i += 1
        self.UpdateUI()

    def on_menu(self, event: wx.MenuEvent):
        id_ = event.GetId()
        if id_ - 1 < len(self.items) and id_ - 1 >= 0:
            app_ctx().main.open_by_object(self.items[id_ - 1])
