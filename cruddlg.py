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
        # print self.crud.ctx
        Gtk.Dialog.__init__(self, self.crud.get_form_prop("title"), parent, 0, None)
        # self.set_default_size(300, 150)

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
        if self.crud.get_action() == "create":
            # formulaire d'ajout
            for element in self.crud.get_form_elements():
                self.crud.set_field_prop(element, "value", "")
        elif self.crud.get_action() in ("read", "update", "delete"):
            # remplissage des champs avec les colonnes
            self.crud.sql_select_to_form()

        # Création des widgets
        box = self.get_content_area()
        # lecture des champs du formulaire form_id
        for element in self.crud.get_form_elements():
            if self.crud.get_field_prop(element, "hide", False):
                continue
            hbox = Gtk.HBox()
            label = Gtk.Label(self.crud.get_field_prop(element, "label_long"))
            label.set_width_chars(20)
            if self.crud.get_field_prop(element, "type") == "int":
                widget = Gtk.Entry()
                widget.set_text(str(self.crud.get_field_prop(element, "value", "none")))
                widget.set_width_chars(40)
            elif self.crud.get_field_prop(element, "type") == "check":
                widget = Gtk.CheckButton()
                widget.set_label(self.crud.get_field_prop(element, "label_long"))
                widget.set_active(self.crud.get_field_prop(element, "value", "none"))
            else:
                # text par défaut
                widget = Gtk.Entry()
                widget.set_text(str(self.crud.get_field_prop(element, "value", "none")))
                widget.set_width_chars(40)
            if self.crud.get_field_prop(element, "read_only", False):
                widget.set_editable(False)
                widget.get_style_context().add_class('read_only')
            # Mémorisation du widget
            self.crud.set_field_prop(element, "widget", widget)
            # arrangement
            if self.crud.get_field_prop(element, "type") == "check":
                label.set_label("")
                hbox.pack_start(label, False, False, 5)
                hbox.pack_start(widget, False, False, 5)
            else:
                hbox.pack_end(widget, False, False, 5)
                hbox.pack_end(label, False, False, 5)
            box.pack_start(hbox, True, True, 5)

    def on_cancel_button_clicked(self, widget):
        """ Cancel """
        # print "on_cancel_button_clicked"
        self.response(Gtk.ResponseType.CANCEL)

    def on_ok_button_clicked(self, widget):
        """ Validation du formulaire """
        # remplissage des champs avec les valeurs saisies
        for element in self.crud.get_form_elements():
            if self.crud.get_field_prop(element, "hide", False):
                continue
            if self.crud.get_field_prop(element, "type") == "check":
                self.crud.set_field_prop(element\
                    ,"value", self.crud.get_field_prop(element, "widget").get_active())
            else:
                self.crud.set_field_prop(element\
                    ,"value", self.crud.get_field_prop(element, "widget").get_text())
        # valeur par défaut
        for element in self.crud.get_form_elements():
            if self.crud.get_field_prop(element, "value", "") == ""\
                and self.crud.get_field_prop(element, "default", "") != "":
                self.crud.set_field_prop(element, "value", self.crud.get_field_prop(element, "default"))

        if self.crud.get_action() in ("create") :
            self.crud.sql_insert_record()
        elif self.crud.get_action() in ("update") :
            self.crud.sql_update_record()

        self.response(Gtk.ResponseType.OK)
