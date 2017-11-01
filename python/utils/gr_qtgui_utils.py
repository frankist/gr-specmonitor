#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017 Francisco Paisana.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

from PyQt4 import Qt
from PyQt4.QtCore import QObject, pyqtSlot
import sip
import sys
import ctypes
from gnuradio import qtgui
from gnuradio import gr

# I just created this to remove all the garbage/verbosity of Qt from my python top block script
# Instructions: Make your top_block class a subclass of QtTopBlock and all is good when you call run()
# Not supported yet: calling tb.start()/tb.stop() instead of tb.run()
# Highly untested. Use it only for debug

def init_qt():
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print "Warning: failed to XInitThreads()"

    from distutils.version import StrictVersion
    if StrictVersion(Qt.qVersion()) >= StrictVersion("4.5.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)
    return qapp

def add_widget(qtobj,qqtgraphlock): # receives a child class of Qt.QWidget
    qtobj._time_plot_win = sip.wrapinstance(qqtgraphlock.pyqwidget(), Qt.QWidget)
    qtobj.top_layout.addWidget(qtobj._time_plot_win)

qapp = init_qt()

class QtTopBlock(gr.top_block,Qt.QWidget):
    def __init__(self):
        gr.top_block.__init__(self)
        Qt.QWidget.__init__(self)
        set_layout(self)

    def run(self):
        self.add_qtwidgets() # finds blocks which are qtwidgets and adds them to the layout
        self.start()
        self.show()

        def quitting():
            self.stop()
            self.wait()
        qapp.connect(qapp, Qt.SIGNAL("aboutToQuit()"), quitting)
        qapp.exec_()

    def add_qtwidgets(self):
        members = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]
        for m in members:
            classname = str(type(getattr(self,m)))
            # print 'class name:',classname, classname.find('gnuradio.qtgui.qtgui_swig')
            if classname.find('class')!=-1 and classname.find('gnuradio.qtgui.qtgui_swig')!=-1:
                add_widget(self,getattr(self,m))


def set_layout(qtobj): # receives a child class of Qt.QWidget
    # Qt.QWidget.__init__(qtobj)
    qtobj.setWindowTitle("Top Block")
    try:
        qtobj.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
    except:
        pass
    qtobj.top_scroll_layout = Qt.QVBoxLayout()
    qtobj.setLayout(qtobj.top_scroll_layout)
    qtobj.top_scroll = Qt.QScrollArea()
    qtobj.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
    qtobj.top_scroll_layout.addWidget(qtobj.top_scroll)
    qtobj.top_scroll.setWidgetResizable(True)
    qtobj.top_widget = Qt.QWidget()
    qtobj.top_scroll.setWidget(qtobj.top_widget)
    qtobj.top_layout = Qt.QVBoxLayout(qtobj.top_widget)
    qtobj.top_grid_layout = Qt.QGridLayout()
    qtobj.top_layout.addLayout(qtobj.top_grid_layout)
    qtobj.settings = Qt.QSettings("GNU Radio", "top_block")
    qtobj.restoreGeometry(qtobj.settings.value("geometry").toByteArray())


def make_time_sink_c(size,samp_rate,name,nconnections=1):
    plotobj = qtgui.time_sink_c(size,samp_rate,name,nconnections)
    plotobj.set_update_time(0.10)
    plotobj.set_y_axis(-1, 1)
    plotobj.set_y_label("Amplitude", "")
    plotobj.enable_tags(-1, True)
    plotobj.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
    plotobj.enable_autoscale(False)
    plotobj.enable_grid(False)
    plotobj.enable_control_panel(False)

    labels = ["", "", "", "", "",
                "", "", "", "", ""]
    widths = [1, 1, 1, 1, 1,
                1, 1, 1, 1, 1]
    colors = ["blue", "red", "green", "black", "cyan",
                "magenta", "yellow", "dark red", "dark green", "blue"]
    styles = [1, 1, 1, 1, 1,
                1, 1, 1, 1, 1]
    markers = [-1, -1, -1, -1, -1,
                -1, -1, -1, -1, -1]
    alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                1.0, 1.0, 1.0, 1.0, 1.0]

    for i in xrange(2*1):
        if len(labels[i]) == 0:
            if(i % 2 == 0):
                plotobj.set_line_label(i, "Re{{Data {0}}}".format(i/2))
            else:
                plotobj.set_line_label(i, "Im{{Data {0}}}".format(i/2))
        else:
            plotobj.set_line_label(i, labels[i])
        plotobj.set_line_width(i, widths[i])
        plotobj.set_line_color(i, colors[i])
        plotobj.set_line_style(i, styles[i])
        plotobj.set_line_marker(i, markers[i])
        plotobj.set_line_alpha(i, alphas[i])

    return plotobj

def run_qt_graph(qtgraph,qapp):
    qtgraph.start()
    qtgraph.show()

    def quitting():
        qtgraph.stop()
        qtgraph.wait()
    qapp.connect(qapp, Qt.SIGNAL("aboutToQuit()"), quitting)
    qapp.exec_()

if __name__ == '__main__':
    pass
