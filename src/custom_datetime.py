from datetime import date as system_date
from datetime import datetime as system_datetime


class date(system_date):
    def __str__(self):  # similarly for __repr__
        return "%02d.%02d.%04d" % (self.day, self.month, self.year)


class datetime(system_datetime):
    def __str__(self):  # similarly for __repr__
        return "%02d.%02d.%04d %02d:%02d:%02d" % (self.day, self.month, self.year, self.hour, self.minute, self.second)

    def date(self):
        return date(self.year, self.month, self.day)
