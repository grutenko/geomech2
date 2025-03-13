import dateutil.parser
import wx

from src.custom_datetime import date as cdate
from src.custom_datetime import datetime as cdatetime


def encode_date(date):
    if isinstance(date, wx.DateTime):
        year = date.GetYear()
        month = date.GetMonth() + 1
        day = date.GetDay()
    elif isinstance(date, cdate):
        year = date.year
        month = date.month
        day = date.day
    elif isinstance(date, str):
        date = dateutil.parser.parse(date, dayfirst=True)
        year = date.year
        month = date.month
        day = date.day
    else:
        raise Exception("Неподдерживаемый класс даты: %s" % str(type(date)))
    return int("%s%s%s000000" % (str(year), str(month).zfill(2), str(day).zfill(2)))


def encode_datetime(date: wx.DateTime, hour, minute, seconds):
    return int(
        "%s%s%s%s%s%s" % (str(date.GetYear()), str(date.GetMonth() + 1).zfill(2), str(date.GetDay()).zfill(2), str(hour).zfill(2), str(minute).zfill(2), str(seconds).zfill(2))
    )


def decode_date(n):
    return cdate(int(str(n)[:4]), int(str(n)[4:6]), int(str(n)[6:8]))


def decode_datetime(n):
    return cdatetime(int(str(n)[:4]), int(str(n)[4:6]), int(str(n)[6:8]), int(str(n)[8:10]), int(str(n)[10:12]), int(str(n)[12:14]))
