# -*- coding:Utf-8 -*-
"""
    Gestion des formulaires
"""
from crud import Crud
from crudel import Crudel
from gi.repository import Gtk
import gi
gi.require_version('Gtk', '3.0')


class CrudForm():
    """ Gestion des Formulaires du CRUD """
    def __init__(self, app_window, crud_portail, crud):
        self.crud = crud
        self.crud.__class__ = Crud
        self.app_window = app_window
        self.crud_portail = crud_portail

        cancel_button = Gtk.Button(stock=Gtk.STOCK_CANCEL)
        cancel_button.set_always_show_image(True)
        cancel_button.connect("clicked", self.on_cancel_button_clicked)

        ok_button = Gtk.Button(stock=Gtk.STOCK_OK)
        ok_button.set_always_show_image(True)
        ok_button.connect("clicked", self.on_ok_button_clicked)

        form_title = Gtk.Label()
        form_title.set_markup("<b>%s</b>" % self.crud.get_form_prop("title"))

        self.crud_portail.box_toolbar.pack_start(form_title, True, True, 3)
        self.crud_portail.box_toolbar.pack_end(ok_button, False, True, 3)
        self.crud_portail.box_toolbar.pack_end(cancel_button, False, True, 3)

        self.box_form = Gtk.VBox()
        # self.crud_portail.box_content.pack_start(self.box_form, False, True, 3)
        self.crud_portail.scroll_window.add(self.box_form)

        self.label_error = Gtk.Label()
        self.label_error.get_style_context().add_class('error')
        self.box_form.pack_end(self.label_error, False, False, 3)

        self.create_fields()

        self.app_window.show_all()

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
            crudel = Crudel(self.app_window, self, self.crud, element, Crudel.CRUD_PARENT_FORM)
            crudel.init_value()
            self.crud.set_field_prop(element, "crudel", crudel)

        # remplissage des champs avec les colonnes
        if self.crud.get_action() in ("read", "update", "delete"):
            self.crud.sql_select_to_form()

        # Création des widget dans la box de la dialog
        for element in self.crud.get_form_elements():
            crudel = self.crud.get_field_prop(element, "crudel")
            if crudel.is_hide():
                continue
            # crudel.dump()
            self.box_form.pack_start(crudel.get_widget_box(), False, False, 5)

    def on_cancel_button_clicked(self, widget):
        """ Cancel """
        # print "on_cancel_button_clicked"
        # self.response(Gtk.ResponseType.CANCEL)
        self.crud_portail.on_button_view_clicked(None, self.crud.get_table_id(), self.crud.get_view_id())

    def on_ok_button_clicked(self, widget):
        """ Validation du formulaire """
        self.label_error.set_text("")
        # remplissage des champs avec les valeurs saisies
        for element in self.crud.get_form_elements():
            crudel = self.crud.get_field_prop(element, "crudel")
            if crudel.is_hide():
                continue
            crudel.set_value_widget()
            crudel.set_value_default()

        # CONTROLE DE LA SAISIE
        for element in self.crud.get_form_elements():
            crudel = self.crud.get_field_prop(element, "crudel")
            crudel.check()

        if self.crud.get_errors():
            self.label_error.set_markup("\n".join(self.crud.get_errors()))
            self.crud.remove_all_errors()
            return
        else:
            if self.crud.get_action() in ("create") :
                if self.crud.sql_exist_key():
                    self.crud.add_error("Cet enregistrement existe déjà")
                    # dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.WARNING,
                    #     Gtk.ButtonsType.OK, "Cet enregistrement existe déjà")
                    # dialog.run()
                    # dialog.destroy()
                else:
                    self.crud.sql_insert_record()
            elif self.crud.get_action() in ("update") :
                self.crud.sql_update_record()

        if self.crud.get_errors():
            self.label_error.set_markup("\n".join(self.crud.get_errors()))
            self.crud.remove_all_errors()
            return

        self.crud_portail.on_button_view_clicked(None, self.crud.get_table_id(), self.crud.get_view_id())
