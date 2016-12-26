#!/usr/bin/env python
#
#   Copyright (C) 2016 Sean D'Epagnier
#
# This Program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.  

import wx, wx.glcanvas, sys
from OpenGL.GL import *
from scope_ui import SignalKScopeBase
from client import SignalKClientFromArgs
from scope import SignalKPlot

def wxglutkeypress(event, special, key):
    translation = { wx.WXK_UP : GLUT_KEY_UP, wx.WXK_DOWN : GLUT_KEY_DOWN, \
                    wx.WXK_LEFT : GLUT_KEY_LEFT, wx.WXK_RIGHT : GLUT_KEY_RIGHT, \
                    wx.WXK_INSERT : GLUT_KEY_INSERT, wx.WXK_DELETE : GLUT_KEY_DELETE}
    if event.GetKeyCode() in translation:
        special(translation[event.GetKeyCode()], event.GetPosition().x, event.GetPosition().y)
    else:
        k = '%c' % (event.GetKeyCode()&255)
        if not event.GetModifiers() & wx.MOD_SHIFT:
            k = k.lower()
        key(k, event.GetPosition().x, event.GetPosition().y)

class SignalKScope(SignalKScopeBase):
    def __init__(self):
        super(SignalKScope, self).__init__(None)

        self.plot = SignalKPlot()
        self.glContext =  wx.glcanvas.GLContext(self.glArea)
        self.plot.init()

        def on_con():
            for i in range(self.clValues.GetCount()):
                if self.clValues.IsChecked(i):
                    self.client.watch(self.clValues.GetString(i))
            self.plot.reset()

        self.client = SignalKClientFromArgs(sys.argv[:2], on_con)
        self.value_list = self.client.list_values()

        for name in sorted(self.value_list):
            i = self.clValues.Append(name)
            for arg in sys.argv[2:]:
                if arg == name:
                    self.clValues.Check(i, True)

        on_con()

        self.timer = wx.Timer(self, wx.ID_ANY)
        self.timer.Start(50)
        self.Bind(wx.EVT_TIMER, self.receive_messages, id=wx.ID_ANY)

        self.sTime.SetValue(self.plot.disptime)
        self.plot_reshape = False

    def receive_messages(self, event):
        refresh = False
        while True:
            result = self.client.receive_single()
            if not result:
                break
            refresh = True

            self.plot.read_data(result)

        if refresh:
            self.Refresh()

    def onValueSelected( self, event ):
        self.plot.select(self.clValues.GetStringSelection())

    def onValueToggled( self, event ):
        value = self.clValues.IsChecked(event.GetInt())
        self.client.watch(event.GetString(), value)

    def onPaintGL( self, event ):
        dc = wx.PaintDC( self.glArea )
        self.glArea.SetCurrent(self.glContext)
        self.plot.fft_on = self.cbfftw.GetValue()

        if self.plot_reshape:
            apply(self.plot.reshape, self.plot_reshape)
            self.plot_reshape = False

        self.plot.display()
        self.glArea.SwapBuffers()

    def onSizeGL( self, event ):
        self.plot_reshape = (event.GetSize().x, event.GetSize().y)

    def onMouseEvents( self, event ):
        self.glArea.SetFocus()

        pos = event.GetPosition()
        if event.LeftDown():
            self.lastmouse = pos

        if event.RightDown():
            self.plot.curtrace.center()

        if event.Dragging():
            offset = pos[1] - self.lastmouse[1]
            self.plot.adjustoffset(offset, self.glArea.GetSize().y)
            self.lastmouse = pos

        rotation = event.GetWheelRotation() / 60
        if rotation:
            if rotation > 0:
                self.plot.increasescale()
            else:
                self.plot.decreasescale()
            self.glArea.Refresh()

    def onKeyPress( self, event ):
        wxglutkeypress(event, self.plot.special, self.plot.key)
        self.cbfftw.SetValue(self.plot.fft_on)

    def onZero( self, event ):
        if self.plot.curtrace:
            self.plot.curtrace.offset = 0

    def onCenter( self, event ):
        if self.plot.curtrace:
            self.plot.curtrace.center()

    def onScalePlus( self, event ):
        self.plot.increasescale()

    def onScaleMinus( self, event ):
        self.plot.decreasescale()

    def onOffsetPlus( self, event ):
        self.plot.curtrace.offset -= self.plot.scale/10.0

    def onOffsetMinus( self, event ):
        self.plot.curtrace.offset += self.plot.scale/10.0

    def onFreeze( self, event ):
        self.plot.freeze = event.IsChecked()

    def onReset( self, event ):
        self.plot.reset()

    def onTime(self, event):
        self.plot.disptime = self.sTime.GetValue()
	
    def onClose( self, event ):
        self.Close()
	
from OpenGL.GLUT import *
def main():
    glutInit(sys.argv)
    app = wx.App()
    SignalKScope().Show()
    app.MainLoop()

if __name__ == '__main__':
    main()