# -*- coding:Utf-8 -*-
"""
    Gestion des formulaires
"""
from crud import Crud
from crudel import Crudel
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GdkPixbuf

class CrudForm(GObject.GObject):
    """ Gestion des Formulaires du CRUD """
    __gsignals__ = {
        'refresh': (GObject.SIGNAL_RUN_FIRST, None, (Crudel,))
    }
    def do_refresh(self, widget):
        """ Rafraichissement du formulaire """
        # remplissage des champs avec les valeurs saisies
        for element in self.elements:
            crudel = self.crud.get_element_prop(element, "crudel")
            if crudel.is_hide() or crudel.is_read_only():
                continue
            crudel.set_value_widget()
            crudel.set_value_default(self.elements)
        # Application des formules
        self.crud.compute_formulas(Crudel.TYPE_PARENT_FORM)
        # ReCréation des widget dans la box de la form
        # Suppression avant
        for children in self.box_form.get_children():
            Gtk.Widget.destroy(children)
        # Création
        for element in self.elements:
            crudel = self.crud.get_element_prop(element, "crudel")
            crudel.init_items_sql()
            crudel.init_text_sql(elements=self.elements)
            # crudel.dump()
            if crudel.is_hide():
                continue
            self.box_form.pack_start(crudel.get_widget_box(), False, False, 5)
        # Dessin
        self.dialog.show_all()

    def __init__(self, crud, args=None):
        GObject.GObject.__init__(self)
        self.dialog = Gtk.Dialog(title=crud.get_form_prop("title"),
            parent=crud.get_window()
        )
        # Gtk.Window.__init__(self, title=crud.get_form_prop("title"))
        self.dialog.set_default_size(1000, 700)

        self.crud = Crud(crud, duplicate=True)
        self.crud_portail = self.crud.get_portail()
        self.crud_view = self.crud.get_view()
        self.crud.set_form(self)
        self.crudel = self.crud.get_crudel()
        self.table_id_from = self.crud.get_table_id_from()
        self.view_id_from = self.crud.get_view_id_from()
        if args:
            self.args = args
        else:
            self.args = {}

        self.box_form = Gtk.VBox()
        self.box_form.set_border_width(6)
        self.label_error = Gtk.Label()
        self.box_form.pack_start(self.label_error, False, False, 3)
        self.elements = self.crud.get_form_elements()
        self.create_fields() # ajout dans box_form

        self.frame_form = Gtk.Frame()
        self.frame_form.add(self.box_form)
        self.scroll_window = Gtk.ScrolledWindow()
        self.scroll_window.add(self.frame_form)
        self.scroll_window.show_all()

        cancel_button = Gtk.Button(stock=Gtk.STOCK_CANCEL)
        cancel_button.set_always_show_image(True)
        cancel_button.connect("clicked", self.on_cancel_button_clicked)

        ok_button = Gtk.Button(stock=Gtk.STOCK_OK)
        ok_button.set_always_show_image(True)
        ok_button.connect("clicked", self.on_ok_button_clicked)

        form_title = Gtk.Label()
        form_title.set_markup("<b>%s</b>" % self.crud.get_form_prop("title"))

        self.box_toolbar = Gtk.HBox(spacing=0)
        self.box_toolbar.set_border_width(6)
        self.box_toolbar.pack_start(form_title, True, True, 3)
        self.box_toolbar.pack_end(ok_button, False, True, 3)
        self.box_toolbar.pack_end(cancel_button, False, True, 3)

        self.box_main = self.dialog.get_content_area()
        self.box_main.pack_start(self.box_toolbar, False, False, 3)
        self.box_main.pack_end(self.scroll_window, True, True, 3)

        self.dialog.show_all()

    def create_fields(self):
        """ Création affichage des champs du formulaire """
        # Création des crudel
        for element in self.elements:
            crudel = Crudel.instantiate(self.crud, element, Crudel.TYPE_PARENT_FORM)
            crudel.init_value()
            self.crud.set_element_prop(element, "crudel", crudel)

        # remplissage des champs avec les colonnes de l'enregistrement
        if self.crud.get_action() in ("read", "update", "delete"):
            rows = self.crud.get_sql_row(Crudel.TYPE_PARENT_FORM)
            for row in rows:
                for element in self.elements:
                    if row.get(element, False):
                        crudel = self.crud.get_element_prop(element, "crudel")
                        crudel.set_value_sql(row[element])

        # remplissage des champs avec les paramètres du formulaire
        for element in self.elements:
            crudel = self.crud.get_element_prop(element, "crudel", None)
            if self.args.get(element, False) : 
                crudel.set_value(self.args.get(element))

        # application des formulas
        self.crud.compute_formulas(Crudel.TYPE_PARENT_FORM)

        # valeur par défaut + vérif si on_change est à traiter
        for element in self.elements:
            crudel = self.crud.get_element_prop(element, "crudel")
            crudel.set_value_default(elements=self.elements)

        # Calcul sql des crudels
        # Création des widget dans la box de la dialog
        for element in self.elements:
            crudel = self.crud.get_element_prop(element, "crudel")
            crudel.init_items_sql(elements=self.elements)
            crudel.init_text_sql(elements=self.elements)
            # crudel.dump()
            if crudel.is_hide():
                continue
            self.box_form.pack_start(crudel.get_widget_box(), False, False, 5)

    def on_cancel_button_clicked(self, widget):
        """ Cancel """
        if self.crudel:
            self.crud_portail.do_form(self.crudel.crud_view, self.crudel.crud)
        else:
            # self.crud_portail.emit("select_view", self.crud.get_table_id_from(), self.crud.get_view_id_from())
            self.dialog.destroy()

    def on_ok_button_clicked(self, widget):
        """ Validation du formulaire """
        self.label_error.set_text("")
        # remplissage des champs avec les valeurs saisies
        # + mémorisation du type de la clé
        key_type = ""
        for element in self.elements:
            crudel = self.crud.get_element_prop(element, "crudel")
            if element == self.crud.get_key_id():
                key_type = crudel.get_type()
            if crudel.is_hide() or crudel.is_read_only():
                continue
            crudel.set_value_widget()
            crudel.set_value_default(self.elements)

        # CONTROLE DE LA SAISIE
        for element in self.elements:
            crudel = self.crud.get_element_prop(element, "crudel")
            if crudel.is_hide() or crudel.is_read_only() or crudel.is_protected():
                continue
            crudel.check()

        if self.crud.get_errors():
            self.label_error.set_markup('\n'.join(self.crud.get_errors()))
            # self.label_error.get_style_context().add_class('error')
            self.crud.remove_all_errors()
            return
        else:
            # OK pour mettre à jour la bd
            # calcul des rubriques avec formule
            self.crud.compute_formulas(Crudel.TYPE_PARENT_FORM)
            if self.crud.get_action() in ("create"):
                if key_type != "counter" and self.crud.sql_exist_key():
                    self.crud.add_error("Cet enregistrement existe déjà")
                    # dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.WARNING,
                    #     Gtk.ButtonsType.OK, "Cet enregistrement existe déjà")
                    # dialog.run()
                    # dialog.destroy()
                else:
                    self.crud.sql_insert_record()
            elif self.crud.get_action() in ("update"):
                self.crud.sql_update_record()

        if self.crud.get_errors():
            self.label_error.set_markup("\n".join(self.crud.get_errors()))
            # self.label_error.get_style_context().add_class('error')
            self.crud.remove_all_errors()
            return

        if self.crudel:
            self.crud_portail.do_form(self.crudel.crud_view, self.crudel.crud)
        else:
            self.crud_portail.emit("select_view", self.table_id_from, self.view_id_from)
            self.dialog.destroy()

