#!/usr/bin/env python
# -*- coding:Utf-8 -*-
# http://python-gtk-3-tutorial.readthedocs.io/en/latest/index.html
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gio, GLib
import sqlite3
import os
import urllib2
import time
from datetime import datetime
import re
import sys
import itertools
import constants as const

class FormDlg(Gtk.Dialog):
    
    def __init__(self, parent):
        self.config = parent.config
        self.crud = parent.crud
        Gtk.Dialog.__init__(self, self.crud, parent, 0, None)
        self.set_default_size(300, 150)

        self.cancel_button = Gtk.Button(stock=Gtk.STOCK_CANCEL)
        self.cancel_button.set_always_show_image(True)
        self.cancel_button.connect("clicked", self.on_cancel_button_clicked)

        self.ok_button = Gtk.Button(stock=Gtk.STOCK_OK)
        self.ok_button.set_always_show_image(True)
        self.ok_button.connect("clicked", self.on_ok_button_clicked)

        self.action_area.pack_start(self.cancel_button, True, True, 0)
        self.action_area.pack_start(self.ok_button, True, True, 0)


        # Formulaire
        hbox_inptf = Gtk.HBox()
        label_inptf = Gtk.Label("<b>{}</b>".format(parent.liststore[istore][const.COL_NAME]))
        label_inptf.set_use_markup(True)
        label_inptf.set_width_chars(10)
        self.ptf_inptf = Gtk.CheckButton()
        self.ptf_inptf.set_label("En portefeuille")
        self.ptf_inptf.set_active(parent.liststore[istore][const.COL_INPTF_BOOL])
        hbox_inptf.pack_end(self.ptf_inptf, False, False, 5)
        hbox_inptf.pack_end(label_inptf, False, False, 5)

        hbox_quantity = Gtk.HBox()
        label_quantity = Gtk.Label("Nombre d'actions :")
        label_quantity.set_width_chars(10)
        self.ptf_quantity = Gtk.Entry()
        entry = ''.join([i for i in str(parent.liststore[istore][const.COL_QUANTITY]) if i in '0123456789'])
        self.ptf_quantity.set_text(str(entry))
        hbox_quantity.pack_end(self.ptf_quantity, False, False, 5)
        hbox_quantity.pack_end(label_quantity, False, False, 5)

        hbox_cost = Gtk.HBox()
        label_cost = Gtk.Label("Prix de revient :")
        label_cost.set_width_chars(10)
        self.ptf_cost = Gtk.Entry()
        entry = ''.join([i for i in str(parent.liststore[istore][const.COL_COST]) if i in '0123456789.'])
        self.ptf_cost.set_text(str(entry))
        hbox_cost.pack_end(self.ptf_cost, False, False, 5)
        hbox_cost.pack_end(label_cost, False, False, 5)

        hbox_date = Gtk.HBox()
        label_date = Gtk.Label("Date d'achat :")
        label_date.set_width_chars(10)
        self.ptf_date = Gtk.Entry()
        entry = str(parent.liststore[istore][const.COL_DATE])
        self.ptf_date.set_text(str(entry))
        hbox_date.pack_end(self.ptf_date, False, False, 5)
        hbox_date.pack_end(label_date, False, False, 5)

        hbox_error = Gtk.HBox()
        self.label_error = Gtk.Label("")
        self.label_error.hide()
        hbox_error.pack_start(self.label_error, False, False, 5)

        self.vbox.pack_start(hbox_inptf, True, False, 5)
        self.vbox.pack_start(hbox_date, True, False, 5)
        self.vbox.pack_start(hbox_quantity, True, False, 5)
        self.vbox.pack_start(hbox_cost, True, False, 5)
        self.vbox.pack_start(hbox_error, True, False, 5)

        self.show_all()

    def on_cancel_button_clicked(self, widget):
        self.response(Gtk.ResponseType.CANCEL)

    def error(self, msg):
        pattern = '<span foreground="red">{}</span>'
        if len(msg) > 0:
            text = self.label_error.get_text()
            if len(text) > 0:
                text = text + "\n" + msg  
            else:
                text = msg
            self.label_error.set_markup(pattern.format(text))
        else:
            self.label_error.set_text("")

    def on_ok_button_clicked(self, widget):
        self.error("")
        bret = True
        # ctrl des données
        try:
            val = int(self.ptf_quantity.get_text())
            self.ptf_quantity.set_text(str(val))
        except ValueError:
            self.error("Le Nombre d'actions est incorrect")
            bret = False

        try:
            val = float(self.ptf_cost.get_text())
            self.ptf_cost.set_text(str(val))
        except ValueError:
            self.error("Le Prix de revient est incorrect")
            bret = False

        if bret: 
            # self.parent.liststore[self.istore][const.COL_QUANTITY] = int(self.ptf_quantity.get_text())
            # self.parent.liststore[self.istore][const.COL_COST] = self.ptf_cost.get_text()
            if self.ptf_inptf.get_active():
                ptf_inptf = "PPP"
                ptf_quantity = self.ptf_quantity.get_text()
                ptf_cost = self.ptf_cost.get_text()
                ptf_date = self.ptf_date.get_text()
            else:
                ptf_inptf = ""
                ptf_quantity = "0"
                ptf_cost = "0.0"
                ptf_date = ""

            self.crud.exec_sql("""UPDATE PTF 
            SET ptf_quantity = :ptf_quantity
            ,ptf_cost = :ptf_cost 
            ,ptf_inptf = :ptf_inptf 
            ,ptf_date = :ptf_date 
            WHERE ptf_id = :ptf_id
            """, {"ptf_id": self.parent.liststore[self.istore][const.COL_ID] \
            ,"ptf_quantity": self.ptf_quantity.get_text()\
            ,"ptf_cost": self.ptf_cost.get_text()\
            ,"ptf_inptf": ptf_inptf\
            ,"ptf_date": ptf_date\
            })
            self.response(Gtk.ResponseType.OK)
