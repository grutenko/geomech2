import wx

from src.resourcelocation import resource_path

__default_ext__ = "png"


def icon_set_extesion_by_default(ext):
    global __default_ext__
    __default_ext__ = ext


def get_icon(name, scale_to=None):
    global __default_ext__
    icon = wx.Bitmap(resource_path("icons/" + name + "." + __default_ext__))
    if scale_to != None:
        image = icon.ConvertToImage()
        image = image.Scale(scale_to, scale_to, wx.IMAGE_QUALITY_HIGH)
        icon = image.ConvertToBitmap()
    return icon


def get_art(id, scale_to=None):
    icon = wx.ArtProvider.GetBitmap(id, wx.ART_MENU)
    if scale_to != None:
        image = icon.ConvertToImage()
        image = image.Scale(scale_to, scale_to, wx.IMAGE_QUALITY_HIGH)
        icon = image.ConvertToBitmap()
    return icon
