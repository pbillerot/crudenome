#!/usr/bin/env python
# -*- coding:Utf-8 -*-
# http://python-gtk-3-tutorial.readthedocs.io/en/latest/index.html
import sqlite3
import os
import urllib2
import time
from datetime import datetime
import re
import sys
import itertools
import crudconst as const
from crud import Crud
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gio, GLib

class FormDlg(Gtk.Dialog):
    """ Gestion des Formulaires du CRUD """
    def __init__(self, parent, crud):
        self.crud = Crud(crud)

        Gtk.Dialog.__init__(self, self.crud.get_formulaire_prop("title"), parent, 0, None)
        self.set_default_size(300, 150)

        cancel_button = Gtk.Button(stock=Gtk.STOCK_CANCEL)
        cancel_button.set_always_show_image(True)
        cancel_button.connect("clicked", self.on_cancel_button_clicked)

        ok_button = Gtk.Button(stock=Gtk.STOCK_OK)
        ok_button.set_always_show_image(True)
        ok_button.connect("clicked", self.on_ok_button_clicked)

        hbox_button = Gtk.HBox()
        hbox_button.pack_end(ok_button, False, False, 3)
        hbox_button.pack_end(cancel_button, False, False, 3)
        self.get_content_area().pack_end(hbox_button, False, True, 0)

        self.show_all()

    def on_cancel_button_clicked(self, widget):
        """ Cancel """
        print "on_cancel_button_clicked"
        self.response(Gtk.ResponseType.CANCEL)

    def on_ok_button_clicked(self, widget):
        """ Validation du formulaire """
        print "on_ok_button_clicked"
        self.response(Gtk.ResponseType.OK)
