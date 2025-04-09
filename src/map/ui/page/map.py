import wx
import wx.html2

from src.ui.icon import get_icon

html = """
<!DOCTYPE html>
<html lang="ru">
<head>
<script src="https://mapgl.2gis.com/api/js/v1?callback=initMap" async defer></script>
<script>
    map = null
    function initMap() {
        map = new mapgl.Map('map', {
            center: [33.412423, 67.492623],
            zoom: 9,
            key: 'ed15a9f2-a3fc-4e34-baa4-f612006e55a1',
        });
    }

    window.addEventListener('resize', function () {
        if(map != null) {
            map.invalidateSize();
        }   
    });
</script>
<style>
html, body, #map {
    margin: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
}
</style>
</head>
<body>
<div id="map"></div>
</body>
</html>
"""


class Map(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(self, style=wx.TB_FLAT)
        sz.Add(self.toolbar, 0, wx.EXPAND)
        self.toolbar.Realize()
        self.search = wx.SearchCtrl(self)
        sz.Add(self.search, 0, wx.EXPAND)
        self.browser = wx.html2.WebView.New(self)
        self.browser.SetPage(html, "")
        sz.Add(self.browser, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()

    def get_name(self):
        return "Карта"

    def get_icon(self):
        return get_icon("map")
