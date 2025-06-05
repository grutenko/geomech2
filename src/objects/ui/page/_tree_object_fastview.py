import wx
import wx.lib.newevent
import wx.propgrid
from pony.orm import db_session
from pubsub import pub
from wx.lib.agw.flatnotebook import EVT_FLATNOTEBOOK_PAGE_CLOSING, FNB_NO_NAV_BUTTONS, FlatNotebookCompatible

from src.database import BoreHole, CoordSystem, MineObject, Station
from src.datetimeutil import decode_date


class FastviewPropgrid(wx.propgrid.PropertyGridManager):
    def __init__(self, parent):
        super().__init__(parent, style=wx.propgrid.PG_SPLITTER_AUTO_CENTER | wx.propgrid.PG_TOOLBAR)
        self.AddPage("Параметры")

    def start(self, fields): ...

    def stop(self): ...


class BoreHoleFastview(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(main_sizer)

        self.propgrid = FastviewPropgrid(self)
        self.propgrid.SetSplitterPosition(150)
        prop = self.propgrid.Append(wx.propgrid.IntProperty("ID", "RID"))
        self.propgrid.SetPropertyReadOnly(prop)
        prop = self.propgrid.Append(wx.propgrid.StringProperty("№", "Number"))
        self.propgrid.SetPropertyReadOnly(prop)
        prop = self.propgrid.Append(wx.propgrid.StringProperty("Название", "Name"))
        self.propgrid.SetPropertyReadOnly(prop)
        prop = self.propgrid.Append(wx.propgrid.LongStringProperty("Комментарий", "Comment"))
        self.propgrid.SetPropertyReadOnly(prop)
        category = self.propgrid.Append(wx.propgrid.PropertyCategory("Координаты", "Coords"))
        prop = self.propgrid.AppendIn(category, wx.propgrid.FloatProperty("X (м)", "X"))
        self.propgrid.SetPropertyReadOnly(prop)
        prop = self.propgrid.AppendIn(category, wx.propgrid.FloatProperty("Y (м)", "Y"))
        self.propgrid.SetPropertyReadOnly(prop)
        prop = self.propgrid.AppendIn(category, wx.propgrid.FloatProperty("Z (м)", "Z"))
        self.propgrid.SetPropertyReadOnly(prop)
        category = self.propgrid.Append(wx.propgrid.PropertyCategory("Параметры", "Params"))
        prop = self.propgrid.AppendIn(category, wx.propgrid.FloatProperty("Азимут (град.)", "Azimuth"))
        self.propgrid.SetPropertyReadOnly(prop)
        prop = self.propgrid.AppendIn(category, wx.propgrid.FloatProperty("Наклон (град.)", "Tilt"))
        self.propgrid.SetPropertyReadOnly(prop)
        prop = self.propgrid.AppendIn(category, wx.propgrid.FloatProperty("Диаметр (мм)", "Diameter"))
        self.propgrid.SetPropertyReadOnly(prop)
        prop = self.propgrid.AppendIn(category, wx.propgrid.FloatProperty("Длина (м)", "Length"))
        self.propgrid.SetPropertyReadOnly(prop)
        prop = self.propgrid.AppendIn(category, wx.propgrid.DateProperty("Дата закладки", "StartDate"))
        prop.SetFormat("%d.%m.%Y")
        self.propgrid.SetPropertyReadOnly(prop)
        prop = self.propgrid.AppendIn(category, wx.propgrid.DateProperty("Дата завершения", "EndDate"))
        prop.SetFormat("%d.%m.%Y")
        self.propgrid.SetPropertyReadOnly(prop)
        prop = self.propgrid.AppendIn(category, wx.propgrid.DateProperty("Дата ликвидации", "DestroyDate"))
        prop.SetFormat("%d.%m.%Y")
        self.propgrid.SetPropertyReadOnly(prop)
        main_sizer.Add(self.propgrid, 1, wx.EXPAND)

        self.Layout()
        self.Hide()

    def start(self, o, bounds=None):
        start_date = decode_date(o.StartDate)
        fields = {
            "RID": o.RID,
            "Number": o.Number,
            "Name": o.Name,
            "Comment": o.Comment,
            "X": o.X,
            "Y": o.Y,
            "Z": o.Z,
            "Azimuth": o.Azimuth,
            "Tilt": o.Tilt,
            "Diameter": o.Diameter,
            "Length": o.Length,
            "StartDate": wx.DateTime(start_date.day, start_date.month - 1, start_date.year),
        }
        if o.EndDate is not None:
            date = decode_date(o.EndDate)
            fields["EndDate"] = wx.DateTime(date.day, date.month - 1, date.year)
        else:
            fields["EndDate"] = None
        if o.DestroyDate is not None:
            date = decode_date(o.DestroyDate)
            fields["DestroyDate"] = wx.DateTime(date.day, date.month - 1, date.year)
        else:
            fields["DestroyDate"] = None
        self.propgrid.SetPropertyValues(fields)
        self.Update()
        self.Show()

    def end(self):
        self.Hide()


class _deputy(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, label="Недоступен для этого объекта")
        main_sizer.Add(label, 1, wx.EXPAND | wx.ALL, border=20)
        self.SetSizer(main_sizer)
        self.Layout()
        self.Hide()

    def start(self, o):
        self.Show()

    def end(self):
        self.Hide()


class MineObjectFastview(FastviewPropgrid):
    def __init__(self, parent):
        super().__init__(parent)

        prop = self.Append(wx.propgrid.IntProperty("ID", "RID"))
        self.SetPropertyReadOnly(prop)
        prop = self.Append(wx.propgrid.StringProperty("Название", "Name"))
        self.SetPropertyReadOnly(prop)
        prop = self.Append(wx.propgrid.LongStringProperty("Комментарий", "Comment"))
        self.SetPropertyReadOnly(prop)
        prop = self.Append(wx.propgrid.StringProperty("Система координат", "coord_system"))
        self.SetPropertyReadOnly(prop)
        category = self.Append(wx.propgrid.PropertyCategory("Ограничения координат", "Coords"))
        prop = self.AppendIn(category, wx.propgrid.FloatProperty("X Мин. (м)", "X_Min"))
        self.SetPropertyReadOnly(prop)
        prop = self.AppendIn(category, wx.propgrid.FloatProperty("Y Мин. (м)", "Y_Min"))
        self.SetPropertyReadOnly(prop)
        prop = self.AppendIn(category, wx.propgrid.FloatProperty("Z Мин. (м)", "Z_Min"))
        self.SetPropertyReadOnly(prop)
        prop = self.AppendIn(category, wx.propgrid.FloatProperty("X Макс. (м)", "X_Max"))
        self.SetPropertyReadOnly(prop)
        prop = self.AppendIn(category, wx.propgrid.FloatProperty("Y Макс. (м)", "Y_Max"))
        self.SetPropertyReadOnly(prop)
        prop = self.AppendIn(category, wx.propgrid.FloatProperty("Z Макс. (м)", "Z_Max"))
        self.SetPropertyReadOnly(prop)

        self.Layout()
        self.Hide()

    @db_session
    def start(self, o, bounds=None):
        _fields = {
            "RID": o.RID,
            "Name": o.Name,
            "Comment": o.Comment,
            "coord_system": CoordSystem[o.coord_system.RID].Name,
            "X_Min": o.X_Min,
            "Y_Min": o.Y_Min,
            "Z_Min": o.Z_Min,
            "X_Max": o.X_Max,
            "Y_Max": o.Y_Max,
            "Z_Max": o.Z_Max,
        }
        self.SetPropertyValues(_fields)
        self.Update()
        self.Show()

    def end(self):
        self.Hide()


class StationFastview(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(main_sizer)

        self.propgrid = FastviewPropgrid(self)
        self.propgrid.SetSplitterPosition(150)
        prop = self.propgrid.Append(wx.propgrid.IntProperty("ID", "RID"))
        self.propgrid.SetPropertyReadOnly(prop)
        prop = self.propgrid.Append(wx.propgrid.StringProperty("№", "Number"))
        self.propgrid.SetPropertyReadOnly(prop)
        prop = self.propgrid.Append(wx.propgrid.StringProperty("Название", "Name"))
        self.propgrid.SetPropertyReadOnly(prop)
        prop = self.propgrid.Append(wx.propgrid.LongStringProperty("Комментарий", "Comment"))
        self.propgrid.SetPropertyReadOnly(prop)
        category = self.propgrid.Append(wx.propgrid.PropertyCategory("Координаты", "Coords"))
        prop = self.propgrid.AppendIn(category, wx.propgrid.FloatProperty("X (м)", "X"))
        self.propgrid.SetPropertyReadOnly(prop)
        prop = self.propgrid.AppendIn(category, wx.propgrid.FloatProperty("Y (м)", "Y"))
        self.propgrid.SetPropertyReadOnly(prop)
        prop = self.propgrid.AppendIn(category, wx.propgrid.FloatProperty("Z (м)", "Z"))
        self.propgrid.SetPropertyReadOnly(prop)
        category = self.propgrid.Append(wx.propgrid.PropertyCategory("Параметры", "Params"))
        prop = self.propgrid.AppendIn(category, wx.propgrid.DateProperty("Дата закладки", "StartDate"))
        prop.SetFormat("%d.%m.%Y")
        self.propgrid.SetPropertyReadOnly(prop)
        prop = self.propgrid.AppendIn(category, wx.propgrid.DateProperty("Дата завершения", "EndDate"))
        prop.SetFormat("%d.%m.%Y")
        self.propgrid.SetPropertyReadOnly(prop)
        main_sizer.Add(self.propgrid, 1, wx.EXPAND)

        self.Layout()
        self.Hide()

    def start(self, o, bounds=None):
        start_date = decode_date(o.StartDate)
        fields = {
            "RID": o.RID,
            "Number": o.Number,
            "Name": o.Name,
            "Comment": o.Comment,
            "X": o.X,
            "Y": o.Y,
            "Z": o.Z,
            "StartDate": wx.DateTime(start_date.day, start_date.month - 1, start_date.year),
        }
        if o.EndDate is not None:
            date = decode_date(o.EndDate)
            fields["EndDate"] = wx.DateTime(date.day, date.month - 1, date.year)
        else:
            fields["EndDate"] = None
        self.propgrid.SetPropertyValues(fields)
        self.Update()
        self.Show()

    def end(self):
        self.Hide()


FwCloseEvent, EVT_FW_CLOSE = wx.lib.newevent.NewEvent()


class TreeObjectFastView(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.notebooktab = FlatNotebookCompatible(self, style=FNB_NO_NAV_BUTTONS)
        sz.Add(self.notebooktab, 1, wx.EXPAND | wx.ALL, 0)
        self.notebooktab.Bind(EVT_FLATNOTEBOOK_PAGE_CLOSING, self.on_close)
        self.p = wx.Panel(self.notebooktab)
        self._deputy = _deputy(self.p)
        self._bore_hole = BoreHoleFastview(self.p)
        self._mine_object = MineObjectFastview(self.p)
        self._station = StationFastview(self.p)

        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self.p.SetSizer(self._sizer)
        self.statusbar = wx.StatusBar(self.p, style=0)
        self._sizer.Add(self.statusbar, 0, wx.EXPAND)
        self._sizer.Add(self._deputy, 1, wx.EXPAND)
        self.Layout()
        self.notebooktab.AddPage(self.p, "Объект", True)
        self.SetSizer(sz)
        self.Hide()
        self.current = None

    def on_close(self, event):
        wx.PostEvent(self, FwCloseEvent())
        event.Veto()

    def start(self, o):
        if isinstance(o, MineObject):
            new_win = self._mine_object
        elif isinstance(o, Station):
            new_win = self._station
        elif isinstance(o, BoreHole):
            new_win = self._bore_hole
        else:
            self.stop()
            return
        win = self._sizer.GetItem(1).GetWindow()
        win.end()
        self._sizer.Detach(1)
        self._sizer.Insert(1, new_win, 1, wx.EXPAND)
        new_win.start(o)
        self.current = new_win
        self.o = o
        self.Layout()
        self.Show()
        pub.subscribe(self.on_object_updated, "object.updated")

    def on_object_updated(self, o):
        if isinstance(o, type(self.o)) and o.RID == self.o.RID and self.current is not None:
            self.o = o
            self.current.start(o)

    def stop(self):
        if self.current is None:
            return
        win = self._sizer.GetItem(1).GetWindow()
        win.end()
        self._sizer.Detach(1)
        self._sizer.Add(self._deputy, 1, wx.EXPAND)
        self.Layout()
        self.Hide()
        self.current = None
        pub.unsubscribe(self.on_object_updated, "object.updated")
