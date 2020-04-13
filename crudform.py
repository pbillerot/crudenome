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
        'init_widget': (GObject.SIGNAL_RUN_FIRST, None, (str,str,))
    }
    def do_init_widget(self, str_from, str_arg=""):
        """ Traitement du signal """
        # print "do_init_widget %s(%s) -> %s" % (str_from, str_arg, self.__class__)
        for element in self.crud.get_form_elements():
            crudel = self.crud.get_element_prop(element, "crudel")
            crudel.emit("init_widget", self.__class__, "")
        for element in self.crud.get_form_elements():
            crudel = self.crud.get_element_prop(element, "crudel")
            if not crudel.is_hide() and not crudel.is_read_only():
                widget = crudel.get_widget()
                widget.grab_focus()
                break

    def __init__(self, crud, args=None):
        
        GObject.GObject.__init__(self)

        self.crud = crud
        self.app_window = crud.get_window()
        self.crud_portail = crud.get_portail()
        self.crud_view = crud.get_view()
        self.crud.set_form(self)
        self.crudel = crud.get_crudel()
        if args:
            self.args = args
        else:
            self.args = {}

        # print "Form", self.crud.get_table_id(), self.crud.get_view_id(), self.crud.get_form_id(), self.crud.get_key_value()
        # if self.crudel:
        #     print "Form Crudel", self.crudel.element
        # print "Form Args", self.args

        # pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale('crudenome.svg', 24, 24, True) # preserve ratio
        # image = Gtk.Image.new_from_pixbuf(pixbuf)
        # cancel_button = Gtk.Button(label="Cancel", image=image)
        # cancel_button.set_image_position(Gtk.PositionType.LEFT) # LEFT TOP RIGHT BOTTOM
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
        self.box_form.set_border_width(6)
        self.frame = Gtk.Frame()
        self.frame.add(self.box_form)

        self.scroll_window = Gtk.ScrolledWindow()
        self.scroll_window.add(self.frame)
        self.scroll_window.show_all()
        self.crud_portail.box_content.pack_end(self.scroll_window, True, True, 3)

        self.label_error = Gtk.Label()
        self.box_form.pack_end(self.label_error, False, False, 3)

        self.create_fields()

        self.app_window.show_all()

    def create_fields(self):
        """ Création affichage des champs du formulaire """
        # Création des crudel
        for element in self.crud.get_form_elements():
            crudel = Crudel.instantiate(self.crud, element, Crudel.TYPE_PARENT_FORM)
            crudel.init_value()
            self.crud.set_element_prop(element, "crudel", crudel)

        # remplissage des champs avec les colonnes de l'enregistrement
        if self.crud.get_action() in ("read", "update", "delete"):
            rows = self.crud.get_sql_row(Crudel.TYPE_PARENT_FORM)
            for row in rows:
                for element in self.crud.get_form_elements():
                    crudel = self.crud.get_element_prop(element, "crudel")
                    if row.get(element, False):
                        crudel.set_value_sql(row[element])

        # remplissage des champs avec les paramètres du formulaire
        for arg in self.args:
            if self.crud.get_form_elements().get(arg, None):
                crudel = self.crud.get_element_prop(arg, "crudel")
                if crudel.crud.get_action() == "create":
                    crudel.set_value(self.args.get(arg))
                crudel.set_read_only(True)

        # valeur par défaut
        for element in self.crud.get_form_elements():
            crudel = self.crud.get_element_prop(element, "crudel")
            crudel.set_value_default()

        # Calcul sql des crudels
        # Création des widget dans la box de la dialog
        for element in self.crud.get_form_elements():
            crudel = self.crud.get_element_prop(element, "crudel")
            crudel.init_items_sql()
            crudel.init_text_sql()
            # crudel.dump()
            if crudel.is_hide():
                continue
            self.box_form.pack_start(crudel.get_widget_box(), False, False, 5)

    def on_cancel_button_clicked(self, widget):
        """ Cancel """
        if self.crudel:
            self.crud_portail.do_form(self.crudel.crud_view, self.crudel.crud)
        else:
            self.crud_portail.on_button_view_clicked(None, self.crud.get_table_id(), self.crud.get_view_id())

    def on_ok_button_clicked(self, widget):
        """ Validation du formulaire """
        self.label_error.set_text("")
        # remplissage des champs avec les valeurs saisies
        # + mémorisation du type de la clé
        key_type = ""
        for element in self.crud.get_form_elements():
            crudel = self.crud.get_element_prop(element, "crudel")
            if element == self.crud.get_key_id():
                key_type = crudel.get_type()
            if crudel.is_hide() or crudel.is_read_only():
                continue
            crudel.set_value_widget()
            crudel.set_value_default()

        # CONTROLE DE LA SAISIE
        for element in self.crud.get_form_elements():
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
            self.crud_portail.on_button_view_clicked(None, self.crud.get_table_id(), self.crud.get_view_id())
