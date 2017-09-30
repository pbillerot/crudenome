# -*- coding:Utf-8 -*-
"""
    Gestion des formulaires
"""
from crud import Crud
from crudel import Crudel

from gi.repository import Gtk
import gi
gi.require_version('Gtk', '3.0')


class CrudForm(Gtk.Dialog):
    """ Gestion des Formulaires du CRUD """
    def __init__(self, parent, crud):
        self.crud = crud
        self.crud.__class__ = Crud
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

        # Initialisation des widgets
        for element in self.crud.get_form_elements():
            crudel = self.crud.get_field_prop(element, "crudel")
            crudel.init_widget()
        for element in self.crud.get_form_elements():
            crudel = self.crud.get_field_prop(element, "crudel")
            if not crudel.is_hide() and not crudel.is_read_only():
                widget = self.crud.get_field_prop(element, "widget")
                widget.grab_focus()
                break

    def create_fields(self):
        """ Création affichage des champs du formulaire """
        # Création des crudel
        for element in self.crud.get_form_elements():
            crudel = Crudel(self.parent, self.crud, element, Crudel.CRUD_PARENT_FORM)
            crudel.init_value()
            self.crud.set_field_prop(element, "crudel", crudel)

        # remplissage des champs avec les colonnes
        if self.crud.get_action() in ("read", "update", "delete"):
            self.crud.sql_select_to_form()

        # Création des widget dans la box de la dialog
        box = self.get_content_area()
        for element in self.crud.get_form_elements():
            crudel = self.crud.get_field_prop(element, "crudel")
            if crudel.is_hide():
                continue
            # crudel.dump()
            box.pack_start(crudel.get_widget_box(), True, True, 5)

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
