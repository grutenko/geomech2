import re

import dateutil
import dateutil.parser
import wx


class Validator(wx.Validator):
    msg: str

    def __init__(self, msg: str = None):
        super().__init__()
        self.msg = msg

    def Validate(self, parent): ...


class TextValidator(Validator):
    lenMin: int
    lenMax: int
    pattern: str

    def __init__(self, msg: str = None, lenMin=None, lenMax=None, pattern=None):
        super().__init__(msg)
        self.lenMin = lenMin
        self.lenMax = lenMax
        self.pattern = pattern

    def Validate(self, ctrl: wx.TextCtrl):
        ok = True
        if not ctrl.IsEnabled():
            return True
        if self.lenMin != None:
            ok = ok and len(ctrl.GetValue()) >= self.lenMin
        if self.lenMax != None:
            ok = ok and len(ctrl.GetValue()) <= self.lenMax
        if self.pattern != None:
            ok = ok and re.match(self.pattern, ctrl.GetValue())
        if not ok:
            ctrl.SetBackgroundColour("red")
            ctrl.Refresh()
        else:
            ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
            ctrl.Refresh()
        return ok

    def TransferFromWindow(self):
        return True

    def TransferToWindow(self):
        return True

    def Clone(self):
        c = TextValidator()
        c.__dict__.update(self.__dict__)
        return c


class DateValidator(Validator):
    def __init__(self, msg: str = None, allow_empty=False):
        super().__init__(msg)
        self.allow_empty = allow_empty

    def Validate(self, ctrl: wx.TextCtrl):
        ok = True
        if self.allow_empty and len(ctrl.GetValue()) == 0:
            ok = True
        else:
            try:
                date = dateutil.parser.parse(ctrl.GetValue(), dayfirst=True)
            except:
                ok = False
            else:
                ok = True
        if not ok:
            ctrl.SetBackgroundColour("red")
            ctrl.Refresh()
        else:
            ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
            ctrl.Refresh()
        return ok

    def TransferFromWindow(self):
        return True

    def TransferToWindow(self):
        return True

    def Clone(self):
        c = DateValidator()
        c.__dict__.update(self.__dict__)
        return c


class ChoiceValidator(Validator):
    def __init__(self, msg: str = None, required=True):
        super().__init__(msg)
        self.required = required

    def Validate(self, ctrl: wx.Choice):
        ok = True
        if not ctrl.IsEnabled():
            return True
        if ctrl.GetSelection() > -1 or not self.required:
            ok = True
        if not ok:
            ctrl.SetBackgroundColour("red")
            ctrl.Refresh()
        else:
            ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
            ctrl.Refresh()
        return ok

    def TransferFromWindow(self):
        return True

    def TransferToWindow(self):
        return True

    def Clone(self):
        c = ChoiceValidator()
        c.__dict__.update(self.__dict__)
        return c
