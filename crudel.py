# -*- coding:Utf-8 -*-
"""
    Gestion des éléments
"""
# import sqlite3
# import os
# import urllib2
# import time
# from datetime import datetime
# import re
# import sys
# import itertools
# import crudconst as const
import uuid

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

class Crudel():
    """ Gestion des Elements """

    def __init__(self, parent, crud, element):
        self.crud = crud
        self.parent = parent
        self.element = element
        self.widget = None

        # Cast class
        if crud.get_field_prop(element, "type", "text") == "button":
            self.__class__ = CrudButton
        elif crud.get_field_prop(element, "type", "text") == "check":
            self.__class__ = CrudCheck
        elif crud.get_field_prop(element, "type", "text") == "date":
            self.__class__ = CrudDate
        elif crud.get_field_prop(element, "type", "text") == "float":
            self.__class__ = CrudFloat
        elif crud.get_field_prop(element, "type", "text") == "int":
            self.__class__ = CrudInt
        elif crud.get_field_prop(element, "type", "text") == "jointure":
            self.__class__ = CrudJointure
        elif crud.get_field_prop(element, "type", "text") == "uid":
            self.__class__ = CrudUid
        else:
            self.__class__ = CrudText

        # Initialisation de l'élément
        self.init_value()

    def get_type_gdk(self):
        """ Type d'objet du GDK """
        return GObject.TYPE_STRING

    def get_instance(parent, crud, element):
        """ Création d'une instance d'un élément int, text ou autre"""
        if crud.get_field_prop(element, "type", "text") == "button":
            return CrudText(parent, crud, element)
        elif crud.get_field_prop(element, "type", "text") == "check":
            return CrudCheck(parent, crud, element)
        elif crud.get_field_prop(element, "type", "text") == "date":
            return CrudDate(parent, crud, element)
        elif crud.get_field_prop(element, "type", "text") == "float":
            return CrudFloat(parent, crud, element)
        elif crud.get_field_prop(element, "type", "text") == "int":
            return CrudInt(parent, crud, element)
        elif crud.get_field_prop(element, "type", "text") == "jointure":
            return CrudJointure(parent, crud, element)
        elif crud.get_field_prop(element, "type", "text") == "uid":
            return CrudUid(parent, crud, element)
        else:
            return CrudText(parent, crud, element)

    def init_value(self):
        """ initialisation de la valeur """
        self.crud.set_field_prop(self.element, "value", u"")

    def set_value_sql(self, value_sql):
        """ Valorisation de l'élément avec le contenu de la colonne de la table """
        self.crud.set_field_prop(self.element, "value",\
            str(value_sql) if isinstance(value_sql, int) else value_sql.encode("utf-8"))

    def is_virtual(self):
        """ Les colonnes préfixées par _ ne sont pas dans la table """
        return self.element.startswith("_")

    def get_widget_box(self):
        """ Création du widget dans une hbox """
        return None

    def get_label_long(self):
        """ Label de l'élément utilisé dans un formulaire """
        return self.crud.get_field_prop(self.element, "label_long", "")

    def get_label_short(self):
        """ Label de l'élément utilisé dans une vue """
        return self.crud.get_field_prop(self.element, "label_short", "")

    def get_type(self):
        """ type d''élément du crud """
        return self.crud.get_field_prop(self.element, "type", "text")

    def get_col_width(self):
        """ Label de l'élément utilisé dans une vue """
        return self.crud.get_field_prop(self.element, "col_width", "")

    def get_value(self):
        """ valeur interne de l'élément """
        return self.crud.get_field_prop(self.element, "value", "")

    def get_value_format(self):
        """ valeur formatée de l'élément """
        display = self.crud.get_field_prop(self.element, "format", None)
        if display:
            return display.format(self.get_value())
        else:
            return self.get_value()

    def _get_widget_entry(self):
        """ champ de saisie """
        widget = Gtk.Entry()
        widget.set_text(str(self.get_value()))
        widget.set_width_chars(40)
        if self.is_read_only():
            widget.set_editable(False)
            widget.get_style_context().add_class('read_only')
        return widget

    def _get_widget_label(self):
        """ Label du widget normalement à gauche du champ dans le formulaire """
        label = Gtk.Label(self.get_label_long())
        label.set_width_chars(20)
        if self.is_required:
            label.set_text(label.get_text() + " *")
        return label

    def is_hide(self):
        """ élément caché """
        return self.crud.get_field_prop(self.element, "hide", False)

    def is_read_only(self):
        """ élément en lecture seule """
        return self.crud.get_field_prop(self.element, "read_only", False)

    def is_searchable(self):
        """ le contenu de la colonne sera lue par le moteur de recharche """
        return self.crud.get_field_prop(self.element, "searchable", False)

    def is_sortable(self):
        """ La colonne pourra être triée en cliquant sur le titre de la colonne """
        return self.crud.get_field_prop(self.element, "sortable", False)

    def is_required(self):
        """ La saisie du champ est obligatoire """
        return self.crud.get_field_prop(self.element, "required", False)

class CrudButton(Crudel):
    """ Gestion des colonnes et champs de type bouton """

    def __init__(self, parent, crud, element):
        Crudel.__init__(self, parent, crud, element)

    def get_type_gdk(self):
        return GObject.TYPE_OBJECT

    def init_value(self):
        Crudel.init_value(self)
        if self.crud.get_key_id() == self.element:
            self.crud.set_field_prop(self.element, "required", True)

    def get_widget_box(self):
        # todo
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        widget = self._get_widget_entry()
        # Mémorisation du widget
        self.crud.set_field_prop(self.element, "widget", widget)
        # arrangement
        hbox.pack_end(widget, False, False, 5)
        hbox.pack_end(label, False, False, 5)
        return hbox

class CrudCheck(Crudel):
    """ Gestion des colonnes et champs de type boîte à cocher """

    def __init__(self, parent, crud, element):
        Crudel.__init__(self, parent, crud, element)

    def get_type_gdk(self):
        return GObject.TYPE_BOOLEAN

    def init_value(self):
        Crudel.init_value(self)
        self.crud.set_field_prop(self.element, "value", False)

    def get_widget_box(self):
        # todo
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        label.set_label("")
        widget = Gtk.CheckButton()
        widget.set_label(self.get_label_long())
        widget.set_active(self.get_value())
        # Mémorisation du widget
        self.crud.set_field_prop(self.element, "widget", widget)
        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(widget, False, False, 5)
        return hbox

class CrudCounter(Crudel):
    """ Gestion des colonnes et champs de type boîte à cocher """

    def __init__(self, parent, crud, element):
        Crudel.__init__(self, parent, crud, element)

    def get_type_gdk(self):
        return GObject.TYPE_INT

    def init_value(self):
        Crudel.init_value(self)
        self.crud.set_field_prop(self.element, "value", 0)
        self.crud.set_field_prop(self.element, "read_only", True)

    def get_widget_box(self):
        # todo
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        widget = self._get_widget_entry()
        # Mémorisation du widget
        self.crud.set_field_prop(self.element, "widget", widget)
        # arrangement
        hbox.pack_end(widget, False, False, 5)
        hbox.pack_end(label, False, False, 5)
        return hbox

class CrudDate(Crudel):
    """ Gestion des colonnes et champs de type date """

    def __init__(self, parent, crud, element):
        Crudel.__init__(self, parent, crud, element)

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_value(self):
        Crudel.init_value(self)
        self.crud.set_field_prop(self.element, "value", u"")

    def get_widget_box(self):
        # todo
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        widget = self._get_widget_entry()
        # Mémorisation du widget
        self.crud.set_field_prop(self.element, "widget", widget)
        # arrangement
        hbox.pack_end(widget, False, False, 5)
        hbox.pack_end(label, False, False, 5)
        return hbox

class CrudFloat(Crudel):
    """ Gestion des colonnes et champs de type décimal """

    def __init__(self, parent, crud, element):
        Crudel.__init__(self, parent, crud, element)

    def get_type_gdk(self):
        return GObject.TYPE_FLOAT

    def init_value(self):
        Crudel.init_value(self)
        self.crud.set_field_prop(self.element, "value", 0)

    def get_widget_box(self):
        # todo
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        widget = self._get_widget_entry()
        # Mémorisation du widget
        self.crud.set_field_prop(self.element, "widget", widget)
        # arrangement
        hbox.pack_end(widget, False, False, 5)
        hbox.pack_end(label, False, False, 5)
        return hbox

class CrudInt(Crudel):
    """ Gestion des colonnes et champs de type entier """

    def __init__(self, parent, crud, element):
        Crudel.__init__(self, parent, crud, element)
        self.widget = None

    def get_type_gdk(self):
        return GObject.TYPE_INT

    def init_value(self):
        Crudel.init_value(self)
        self.crud.set_field_prop(self.element, "value", 0)

    def get_widget_box(self):
        # todo
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        self.widget = self._get_widget_entry()
        self.widget.connect('changed', self.on_changed_number_entry)
        # Mémorisation du widget
        self.crud.set_field_prop(self.element, "widget", self.widget)
        # arrangement
        hbox.pack_end(self.widget, False, False, 5)
        hbox.pack_end(label, False, False, 5)
        return hbox

    def on_changed_number_entry(self):
        """ Ctrl de la saisie """
        text = self.widget.get_text().strip()
        self.widget.set_text(''.join([i for i in text if i in '0123456789']))

class CrudJointure(Crudel):
    """ Gestion des colonnes et champs de type jointure entre 2 tables """

    def __init__(self, parent, crud, element):
        Crudel.__init__(self, parent, crud, element)

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_value(self):
        Crudel.init_value(self)
        self.crud.set_field_prop(self.element, "value", u"")

    def get_widget_box(self):
        hbox = Gtk.HBox()
        label = self._get_widget_label()

        widget = Gtk.ComboBoxText()

        # Remplacement des variables
        sql = self.crud.replace_from_dict(self.crud.get_field_prop(self.element, "combo_select")\
            , self.crud.get_form_values())
        rows = self.crud.sql_to_dict(self.crud.get_table_prop("basename"), sql, {})
        # remplissage du combo
        widget.set_entry_text_column(0)
        index = 0
        index_selected = None
        for row in rows:
            # une seule colonne
            for key in row:
                text = str(row[key])
                key = self.crud.get_key_from_bracket(text)
                widget.append_text(text)
                if key is None:
                    if text == self.crud.get_field_prop(self.element, "value"):
                        index_selected = index
                else:
                    if key == self.crud.get_field_prop(self.element, "value"):
                        index_selected = index

            index += 1

        widget.connect('changed', self.on_changed_combo, self.element)
        if index_selected:
            widget.set_active(index_selected)

        # Mémorisation du widget
        self.crud.set_field_prop(self.element, "widget", widget)
        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(widget, False, False, 5)
        return hbox

    def on_changed_combo(self, widget, element):
        """ l'item sélectionné a changé """
        text = widget.get_active_text()
        key = self.crud.get_key_from_bracket(text)
        if text is not None:
            if key:
                self.crud.set_field_prop(element, "value", key)
            else:
                self.crud.set_field_prop(element, "value", text)

class CrudUid(Crudel):
    """ Gestion des colonnes et champs de type Unique IDentifier """

    def __init__(self, parent, crud, element):
        Crudel.__init__(self, parent, crud, element)

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_value(self):
        Crudel.init_value(self)
        self.crud.set_field_prop(self.element, "value", uuid.uuid4())
        self.crud.set_field_prop(self.element, "read_only", True)

    def get_widget_box(self):
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        widget = self._get_widget_entry()
        # Mémorisation du widget
        self.crud.set_field_prop(self.element, "widget", widget)
        # arrangement
        hbox.pack_end(widget, False, False, 5)
        hbox.pack_end(label, False, False, 5)
        return hbox

class CrudText(Crudel):
    """ Gestion des colonnes et champs de type texte """

    def __init__(self, parent, crud, element):
        Crudel.__init__(self, parent, crud, element)

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_value(self):
        Crudel.init_value(self)
        self.crud.set_field_prop(self.element, "value", u"")

    def get_widget_box(self):
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        widget = self._get_widget_entry()
        # Mémorisation du widget
        self.crud.set_field_prop(self.element, "widget", widget)
        # arrangement
        hbox.pack_end(widget, False, False, 5)
        hbox.pack_end(label, False, False, 5)
        return hbox
