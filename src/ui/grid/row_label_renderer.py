import wx
import wx.grid
import wx.lib.mixins.gridlabelrenderer


class RowLabelRenderer(wx.lib.mixins.gridlabelrenderer.GridDefaultRowLabelRenderer):
    def Draw(self, grid: wx.grid.Grid, dc, rect, row):
        hAlign, vAlign = grid.GetRowLabelAlignment()
        text = grid.GetRowLabelValue(row)
        self.DrawBorder(grid, dc, rect)
        _need_hightlight = False
        block: wx.grid.GridBlockCoords
        for block in grid.GetSelectedBlocks():
            if block.GetBottomRow() >= row and block.GetTopRow() <= row:
                _need_hightlight = True
                break
        if grid.GetGridCursorRow() == row or _need_hightlight:
            self.DrawHighlightBorder(grid, dc, rect)
        self.DrawText(grid, dc, rect, text, hAlign, vAlign)

    def DrawBorder(self, grid, dc, rect):
        top = rect.top
        bottom = rect.bottom
        left = rect.left
        right = rect.right
        dc.SetPen(wx.Pen(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DSHADOW)))
        dc.DrawLine(right, top, right, bottom)
        dc.DrawLine(left, top, left, bottom)
        dc.DrawLine(left, bottom, right, bottom)

    def DrawHighlightBorder(self, grid, dc, rect):
        top = rect.top
        bottom = rect.bottom
        left = rect.left
        right = rect.right
        dc.SetBackground(wx.Brush(wx.Colour(150, 150, 150)))
        dc.DrawRectangle(rect.x, rect.y, rect.width, rect.height)
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 2))
        dc.DrawLine(right, top, right, bottom)
