import wx
import wx.grid
import wx.lib.mixins.gridlabelrenderer


class ColLabelRenderer(wx.lib.mixins.gridlabelrenderer.GridDefaultColLabelRenderer):
    def Draw(self, grid, dc, rect, col):
        hAlign, vAlign = grid.GetColLabelAlignment()
        text = grid.GetColLabelValue(col)
        self.DrawBorder(grid, dc, rect)
        _need_hightlight = False
        block: wx.grid.GridBlockCoords
        for block in grid.GetSelectedBlocks():
            if block.GetLeftCol() <= col and block.GetRightCol() >= col:
                _need_hightlight = True
                break
        if grid.GetGridCursorCol() == col or _need_hightlight:
            self.DrawHighlightBorder(grid, dc, rect)
        self.DrawText(grid, dc, rect, text, hAlign, vAlign)

    def DrawBorder(self, grid, dc, rect):
        top = rect.top
        bottom = rect.bottom
        left = rect.left
        right = rect.right
        dc.SetPen(wx.Pen(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DSHADOW)))
        dc.DrawLine(left, top, right, top)
        dc.DrawLine(right, top, right, bottom)
        dc.DrawLine(left, top, left, bottom)
        dc.DrawLine(left, bottom, right, bottom)

    def DrawHighlightBorder(self, grid, dc, rect: wx.Rect):
        top = rect.top
        bottom = rect.bottom
        left = rect.left
        right = rect.right
        dc.SetBackground(wx.Brush(wx.Colour(150, 150, 150)))
        dc.DrawRectangle(rect.x, rect.y, rect.width, rect.height)
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 2))
        dc.DrawLine(left, bottom, right, bottom)
