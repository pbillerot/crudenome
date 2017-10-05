#!/usr/bin/env python
# -*- coding:Utf-8 -*-
"""
    Fenêtre secondaire
"""
import sys
from gi.repository import Gtk, Gdk, GdkPixbuf, Gio
import gi
gi.require_version('Gtk', '3.0')

class MyWindow(Gtk.Window):
    
    def __init__(self):
        Gtk.Window.__init__(self, title="myWindow")
        # self.connect("destroy", lambda x: Gtk.main_quit())

        self.activate_focus()
        self.set_border_width(10)
        self.set_default_size(800, 600)

        self.add(Gtk.Label("This is another window"))
        self.show_all()