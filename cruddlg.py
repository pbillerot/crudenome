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

        print self.crud.table_id, self.crud.view_id, self.crud.form_id, self.crud.key_id, self.crud.key_value

        Gtk.Dialog.__init__(self, self.crud.get_form_prop("title"), parent, 0, None)
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

        self.create_fields()

        self.show_all()

    def create_fields(self):
        """ Création affichage des champs du formulaire """
        # lecture des champs dans la base sql
        sql = "SELECT "
        b_first = True
        id_row = 0
        for element in self.crud.get_form_elements():
            if b_first:
                sql += element
                b_first = False
            else:
                sql += ", " + element
            id_row += 1

        sql += " FROM " + self.crud.table_id
        sql += " WHERE " + self.crud.get_table_prop("key") + " = :key_value"
        rows = self.crud.sql_to_dict(self.crud.get_table_prop("basename"), sql, {"key_value": self.crud.key_value})
        # remplissage des champs 
        print sql, self.crud.key_value, rows
        for row in rows:
            print row
            for element in self.crud.get_form_elements():
                self.crud.set_element_prop(element, "value", row[element])


        # Création des champs
        box = self.get_content_area()
        # lecture des champs du formulaire form_id
        print "Field", self.crud.table_id, self.crud.view_id, self.crud.form_id
        for field in self.crud.get_form_elements():
            print field
            hbox = Gtk.HBox()
            label = Gtk.Label(self.crud.get_field_prop(field, "label_long"))
            label.set_width_chars(10)
            if self.crud.get_field_prop(field, "type") == "int":
                entry = Gtk.Entry()
                entry.set_text(str(self.crud.get_field_prop(field, "value", "none")))
            else:
                # text par défaut
                entry = Gtk.Entry()
                entry.set_text(str(self.crud.get_field_prop(field, "value", "none")))

            if field == self.crud.get_table_prop("key"):
                entry.set_editable(False)
                entry.get_style_context().add_class('read_only')
            if self.crud.get_field_prop(field, "read_only", False):
                entry.set_editable(False)
                entry.get_style_context().add_class('read_only')

            hbox.pack_end(entry, False, False, 5)
            hbox.pack_end(label, False, False, 5)
            box.pack_start(hbox, True, True, 5)


    def on_cancel_button_clicked(self, widget):
        """ Cancel """
        print "on_cancel_button_clicked"
        self.response(Gtk.ResponseType.CANCEL)

    def on_ok_button_clicked(self, widget):
        """ Validation du formulaire """
        print "on_ok_button_clicked"
        self.response(Gtk.ResponseType.OK)
