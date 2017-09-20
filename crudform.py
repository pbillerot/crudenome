# -*- coding:Utf-8 -*-
"""
    Gestion des formulaires
"""
# from crud import Crud

# import sqlite3
# import os
# import urllib2
# import time
# from datetime import datetime
# import re
# import sys
# import itertools
# import crudconst as const

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf

class CrudForm(Gtk.Dialog):
    """ Gestion des Formulaires du CRUD """
    def __init__(self, parent, crud):
        self.crud = crud
        self.parent = parent

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

        self.label_error = Gtk.Label()
        self.label_error.get_style_context().add_class('error')
        self.get_content_area().pack_end(self.label_error, False, False, 3)

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

        # Calcul 
        for element in self.crud.get_form_elements():
            if self.crud.get_key_id() == element:
                self.crud.set_field_prop(element, "required", True)
            if self.crud.get_field_prop(element, "type") == "counter":
                self.crud.set_field_prop(element, "read_only", True)

        # Création des widgets
        box = self.get_content_area()
        # lecture des champs du formulaire form_id
        for element in self.crud.get_form_elements():
            if self.crud.get_field_prop(element, "hide", False):
                continue
            hbox = Gtk.HBox()
            label = Gtk.Label(self.crud.get_field_prop(element, "label_long"))
            label.set_width_chars(20)
            if self.crud.get_field_prop(element, "required", False):
                label.set_text(label.get_text() + " *")
            if self.crud.get_field_prop(element, "type") == "int":
                widget = Gtk.Entry()
                widget.set_text(str(self.crud.get_field_prop(element, "value", "none")))
                widget.set_width_chars(40)
            elif self.crud.get_field_prop(element, "type") == "check":
                widget = Gtk.CheckButton()
                widget.set_label(self.crud.get_field_prop(element, "label_long"))
                widget.set_active(self.crud.get_field_prop(element, "value", "none"))
            elif self.crud.get_field_prop(element, "type") == "jointure":
                # widget = self.crud.create_widget_combo(element)
                # widget = MyCombo(self.crud, element)
                widget = CrudComboBoxText(self.crud, element)
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
            elif self.crud.get_field_prop(element, "type") == "jointure":
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
        self.label_error.set_text("")
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

        # CONTROLE DE LA SAISIE
        errors = []
        # print self.crud.get_form_elements()
        for element in self.crud.get_form_elements():
            if self.crud.get_field_prop(element, "widget", None):
                self.crud.get_field_prop(element, "widget").get_style_context().remove_class('field_invalid')
                if self.crud.get_field_prop(element, "required", False)\
                        and not self.crud.get_field_prop(element, "read_only", False)\
                        and self.crud.get_field_prop(element, "value", "") == "":
                    self.crud.get_field_prop(element, "widget").get_style_context().add_class('field_invalid')
                    errors.append("<b>{}</b> est obligatoire".format(self.crud.get_field_prop(element, "label_long")))
        if errors:
            self.label_error.set_markup("\n".join(errors))
            return
        else:
            if self.crud.get_action() in ("create") :
                if self.crud.sql_exist_key():
                    self.label_error.set_text("Cet enregistrement existe déjà")
                    # dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.WARNING,
                    #     Gtk.ButtonsType.OK, "Cet enregistrement existe déjà")
                    # dialog.run()
                    # dialog.destroy()
                    return
                else:
                    self.crud.sql_insert_record()
            elif self.crud.get_action() in ("update") :
                self.crud.sql_update_record()

            self.response(Gtk.ResponseType.OK)

class CrudComboBoxText(Gtk.ComboBoxText):
    """ Combobox """
    def __init__(self, crud, element):
        Gtk.ComboBoxText.__init__(self)
        self.crud = crud
        self.element = element
        self.text = self.crud.get_field_prop(element, "value")
        # Remplacement des variables
        sql = self.crud.replace_from_dict(self.crud.get_field_prop(element, "combo_select")\
            , self.crud.get_form_values())
        rows = self.crud.sql_to_dict(self.crud.get_table_prop("basename"), sql, {})
        # remplissage du combo
        self.set_entry_text_column(0)
        index = 0
        index_selected = None
        for row in rows:
            # une seule colonne
            for key in row:
                text = str(row[key])
                key = self.crud.get_key_from_bracket(text)
                self.append_text(text)
                if key is None:
                    if text == self.crud.get_field_prop(element, "value"):
                        index_selected = index
                else:
                    if key == self.crud.get_field_prop(element, "value"):
                        index_selected = index

            index += 1

        self.connect('changed', self.on_changed_combo, element)
        if index_selected:
            self.set_active(index_selected)

    def on_changed_combo(self, widget, element):
        """ l'item sélectionné a changé """
        text = widget.get_active_text()
        key = self.crud.get_key_from_bracket(text)
        if text is not None:
            if key:
                self.crud.set_field_prop(element, "value", key)
                self.text = key
            else:
                self.crud.set_field_prop(element, "value", text)
                self.text = text

    def get_text(self):
        """ Fourniture du texte de l'item sélectionné """
        return self.text

class CrudNumberEntry(Gtk.Entry):
    """ Input numéric seulement """
    def __init__(self):
        Gtk.Entry.__init__(self)
        self.connect('changed', self.on_changed_number_entry)

    def on_changed_number_entry(self):
        """ Ctrl de la saisie """
        text = self.get_text().strip()
        self.set_text(''.join([i for i in text if i in '0123456789']))
