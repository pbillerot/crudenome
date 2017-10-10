# -*- coding:Utf-8 -*-
"""
    Gestion des éléments
"""
# import re
import importlib
import uuid
from crud import Crud
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

class Crudel(GObject.GObject):
    """ Gestion des Elements """
    TYPE_PARENT_VIEW = 1
    TYPE_PARENT_FORM = 2

    __gsignals__ = {
        'init_widget': (GObject.SIGNAL_RUN_FIRST, None, (str,str,))
    }
    def do_init_widget(self, str_from, str_arg=""):
        """ Traitement du signal """
        # print "do_init_widget %s(%s) -> %s" % (str_from, str_arg, self.__class__)
        self.init_widget()

    @staticmethod
    def instantiate(app_window, crud_portail, crud_view, crud_form, crud, element, type_parent):
        """ Instanciation de la classe correspondate au type d'élément """
        if crud.get_element_prop(element, "type", "text") == "button":
            crudel = CrudelButton(app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "check":
            crudel = CrudelCheck(app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "counter":
            crudel = CrudelCounter(app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "date":
            crudel = CrudelDate(app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "float":
            crudel = CrudelFloat(app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "int":
            crudel = CrudelInt(app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "jointure":
            crudel = CrudelJointure(app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "list":
            crudel = CrudelList(app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "radio":
            crudel = CrudelRadio(app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "uid":
            crudel = CrudelUid(app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "view":
            crudel = CrudelView(app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)
        else:
            crudel = CrudelText(app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)
        return crudel

    def instantiate_old(app_window, crud_portail, crud_view, crud_form, crud, element, type_parent=1):
        """ Instanciation de la classe correspondate au type d'élément """
        module_ = importlib.import_module("crudel")
        class_name = ""
        try:
            if crud.get_element_prop(element, "type", "text") == "button":
                class_name = "CrudelButton"
            elif crud.get_element_prop(element, "type", "text") == "check":
                class_name = "CrudelCheck"
            elif crud.get_element_prop(element, "type", "text") == "counter":
                class_name = "CrudelCounter"
            elif crud.get_element_prop(element, "type", "text") == "date":
                class_name = "CrudelDate"
            elif crud.get_element_prop(element, "type", "text") == "float":
                class_name = "CrudelFloat"
            elif crud.get_element_prop(element, "type", "text") == "int":
                class_name = "CrudelInt"
            elif crud.get_element_prop(element, "type", "text") == "jointure":
                class_name = "CrudelJointure"
            elif crud.get_element_prop(element, "type", "text") == "uid":
                class_name = "CrudelUid"
            elif crud.get_element_prop(element, "type", "text") == "view":
                class_name = "CrudelView"
            elif crud.get_element_prop(element, "type", "text") == "radio":
                class_name = "CrudelRadio"
            else:
                class_name = "CrudelText"

            class_ = getattr(module_, class_name)(app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)
        except AttributeError:
            print class_name, 'Class does not exist'
        return class_ or None

    def __init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent=1):

        GObject.GObject.__init__(self)

        self.crud = crud
        self.app_window = app_window
        self.crud_portail = crud_portail
        self.crud_view = crud_view
        self.crud_form = crud_form
        self.element = element
        self.widget = None
        self.type_parent = type_parent

        # # Cast class
        # if crud.get_element_prop(element, "type", "text") == "button":
        #     self.__class__ = CrudelButton
        # elif crud.get_element_prop(element, "type", "text") == "check":
        #     self.__class__ = CrudelCheck
        # elif crud.get_element_prop(element, "type", "text") == "counter":
        #     self.__class__ = CrudelCounter
        # elif crud.get_element_prop(element, "type", "text") == "date":
        #     self.__class__ = CrudelDate
        # elif crud.get_element_prop(element, "type", "text") == "float":
        #     self.__class__ = CrudelFloat
        # elif crud.get_element_prop(element, "type", "text") == "int":
        #     self.__class__ = CrudelInt
        # elif crud.get_element_prop(element, "type", "text") == "jointure":
        #     self.__class__ = CrudelJointure
        # elif crud.get_element_prop(element, "type", "text") == "uid":
        #     self.__class__ = CrudelUid
        # elif crud.get_element_prop(element, "type", "text") == "view":
        #     self.__class__ = CrudelView
        # elif crud.get_element_prop(element, "type", "text") == "radio":
        #     self.__class__ = CrudelRadio
        # else:
        #     self.__class__ = CrudelText

    def get_type_gdk(self):
        """ Type d'objet du GDK """
        return GObject.TYPE_STRING

    def init_value(self):
        """ initialisation de la valeur """
        self.set_value_sql(u"")

    def set_value_sql(self, value_sql):
        """ Valorisation de l'élément avec le contenu de la colonne de la table """
        self.crud.set_element_prop(self.element, "value",\
            value_sql if isinstance(value_sql, int) or isinstance(value_sql, float)\
                else value_sql.encode("utf-8"))

    def set_value_widget(self):
        """ valorisation à partir de la saisie dans le widget """
        self.crud.set_element_prop(self.element\
                    ,"value", self.get_widget().get_text())

    def set_value_default(self):
        """ valorisation avec la valeur par défaut si valeur '' """
        if self.crud.get_field_prop(self.element, "value", "") == ""\
            and self.crud.get_field_prop(self.element, "default", "") != "":
            self.crud.set_element_prop(self.element, "value", self.crud.get_field_prop(self.element, "default"))

    def get_value(self):
        """ valeur interne de l'élément """
        return self.crud.get_element_prop(self.element, "value", "")

    def get_value_sql(self):
        """ valeur à enregistrer dans la colonne de l'élément """
        return self.crud.get_element_prop(self.element, "value", "")

    def get_widget(self):
        """ get du widget """
        return self.widget

    def get_widget_box(self):
        """ Création du widget dans une hbox """
        return None

    def init_widget(self):
        """ Initialisation du widget après création """
        pass

    def get_label_long(self):
        """ Label de l'élément utilisé dans un formulaire """
        return self.crud.get_field_prop(self.element, "label_long", "")

    def get_label_short(self):
        """ Label de l'élément utilisé dans une vue """
        return self.crud.get_column_prop(self.element, "label_short", "")

    def get_type(self, type="text"):
        """ type d''élément du crud """
        return self.crud.get_element_prop(self.element, "type", type)

    def get_cell(self):
        """ modèle de présentation de la chaîne
        https://www.tutorialspoint.com/python/python_strings.htm
        "%3.2d €" par exemple pour présenter un montant en 0.00 €
        "%5s" pour représenter une chaîne en remplissant de blancs à gauche si la longueur < 5c
        """
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            display = self.crud.get_column_prop(self.element, "display")
        else:
            display = self.crud.get_field_prop(self.element, "display")
        # print "display", self.element, self.crud.get_column_prop(self.element, "value"), self.get_value()
        if display == "":
            return str(self.get_value())
        else:
            return display % (self.get_value())

    def get_col_width(self):
        """ largeur de la colonne """
        return self.crud.get_column_prop(self.element, "col_width", None)

    def get_col_align(self):
        """ alignement du texte dans la colonne """
        return self.crud.get_column_prop(self.element, "col_align", "")

    def get_sql_color(self):
        """ Couleur du texte dans la colonne """
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            return self.crud.get_column_prop(self.element, "sql_color", "")
        else:
            return self.crud.get_field_prop(self.element, "sql_color", "")

    def get_sql_get(self):
        """ l'instruction sql dans le select pour lire la colonne """
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            return self.crud.get_column_prop(self.element, "sql_get", "")
        else:
            return self.crud.get_field_prop(self.element, "sql_get", "")

    def get_sql_put(self):
        """ l'instruction sql pour écrire la colonne """
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            return self.crud.get_column_prop(self.element, "sql_put", "")
        else:
            return self.crud.get_field_prop(self.element, "sql_put", "")

    def get_sql_where(self):
        """ le where d'une rubrique de type view """
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            return self.crud.get_column_prop(self.element, "sql_where", "")
        else:
            return self.crud.get_field_prop(self.element, "sql_where", "")

    def get_jointure_columns(self):
        """ la partie select de la jointure """
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            return self.crud.get_column_prop(self.element, "jointure_columns", "")
        else:
            return self.crud.get_field_prop(self.element, "jointure_columns", "")

    def get_jointure_join(self):
        """ la partie liaison evec la table principale """
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            return self.crud.get_column_prop(self.element, "jointure_join", "")
        else:
            return self.crud.get_field_prop(self.element, "jointure_join", "")

    def get_view_table(self):
        """ nom de la table de la rubrique view """
        return self.crud.get_field_prop(self.element, "view_table", "")

    def get_view_view(self):
        """ nom de la vue de la rubrique view """
        return self.crud.get_field_prop(self.element, "view_view", "")

    def get_height(self, default):
        """ Hauteur du widget """
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            return self.crud.get_column_prop(self.element, "height", default)
        else:
            return self.crud.get_field_prop(self.element, "height", default)

    def is_virtual(self):
        """ Les colonnes préfixées par _ ne sont pas dans la table """
        return self.element.startswith("_")

    def is_hide(self):
        """ élément caché """
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            return self.crud.get_column_prop(self.element, "hide", False)
        else:
            return self.crud.get_field_prop(self.element, "hide", False)

    def is_read_only(self):
        """ élément en lecture seule """
        return self.crud.get_field_prop(self.element, "read_only", False)

    def is_searchable(self):
        """ le contenu de la colonne sera lue par le moteur de recharche """
        return self.crud.get_column_prop(self.element, "searchable", False)

    def is_sortable(self):
        """ La colonne pourra être triée en cliquant sur le titre de la colonne """
        return self.crud.get_column_prop(self.element, "sortable", False)

    def is_required(self):
        """ La saisie du champ est obligatoire """
        return self.crud.get_field_prop(self.element, "required", False)

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
        label.set_xalign(0.9)
        if self.is_required():
            label.set_text(label.get_text() + " *")
        return label

    def add_tree_view_column(self, treeview, col_id):
        """ Cellule de la colonne dans la vue 
        """
        if not self.is_hide():
            renderer = self._get_renderer()
            if self.get_col_align() == "left":
                renderer.set_property('xalign', 0.1)
            elif self.get_col_align() == "right":
                renderer.set_property('xalign', 1.0)
            elif self.get_col_align() == "center":
                renderer.set_property('xalign', 0.5)

            tvc = self._get_tvc(renderer, col_id)

            if self.get_sql_color() != "":
                tvc.add_attribute(renderer, "foreground", col_id)
            if self.is_sortable():
                tvc.set_sort_column_id(col_id)
            if self.get_col_width():
                tvc.set_fixed_width(self.get_col_width())

            treeview.append_column(tvc)

        # on ajoute les colonnes techniques
        if self.get_sql_color() != "":
            col_id += 1
        if self.is_sortable():
            col_id += 1
        return col_id

    def _get_renderer(self):
        """ Renderer de la cellule """
        renderer = Gtk.CellRendererText()
        return renderer

    def _get_tvc(self, renderer, col_id):
        """ TreeViewColumn de la cellule """
        tvc = Gtk.TreeViewColumn(self.get_label_short(), renderer, text=col_id)
        return tvc

    def check(self):
        """ Contrôle de la saisie """
        self.get_widget().get_style_context().remove_class('field_invalid')
        if self.is_required() and not self.is_read_only() and self.get_value() == "":
            self.get_widget().get_style_context().add_class('field_invalid')
            self.crud.add_error("<b>{}</b> est obligatoire".format(self.get_label_long()))

    def dump(self):
        """ print des propriétés de l'élément """
        prop = {}
        prop.update(self.crud.get_table_elements()[self.element])
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            prop.update(self.crud.get_view_elements()[self.element])
        else:
            prop.update(self.crud.get_form_elements()[self.element])
        for p in prop:
            print "%s.%s = %s" % (self.element, p, prop[p])

class CrudelButton(Crudel):
    """ Gestion des colonnes et champs de type bouton """

    def __init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent):
        Crudel.__init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)

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
        self.widget = self._get_widget_entry()
        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(self.widget, False, False, 5)
        return hbox

    def get_cell(self):
        return self.get_value()

class CrudelCheck(Crudel):
    """ Gestion des colonnes et champs de type boîte à cocher """

    def __init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent):
        Crudel.__init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)

    def get_type_gdk(self):
        return GObject.TYPE_BOOLEAN

    def init_value(self):
        Crudel.init_value(self)
        self.set_value_sql(False)

    def get_cell(self):
        """ représentation en colonne """
        return self.get_value()

    def get_widget_box(self):
        # todo
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        label.set_label("")
        self.widget = Gtk.CheckButton()
        self.widget.set_label(self.get_label_long())
        self.widget.set_active(self.get_value())
        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(self.widget, False, False, 5)
        return hbox

    def _get_renderer(self):
        renderer = Gtk.CellRendererToggle()
        return renderer

    def _get_tvc(self, renderer, col_id):
        tvc = Gtk.TreeViewColumn(self.get_label_short(), renderer, active=col_id)
        return tvc

    def set_value_widget(self):
        self.crud.set_element_prop(self.element\
                    ,"value", self.get_widget().get_active())

    def get_value_sql(self):
        if self.crud.get_element_prop(self.element, "value", False) == True:
            return "1"
        elif self.crud.get_element_prop(self.element, "value", False) == False:
            return "0"
        elif self.crud.get_element_prop(self.element, "value", "") == "1":
            return "1"
        elif self.crud.get_element_prop(self.element, "value", "") == "0":
            return "0"
        elif self.crud.get_element_prop(self.element, "value", "") == "":
            return "0"
        else:
            return "1"

    def set_value_sql(self, value_sql):
        """ Valorisation de l'élément avec le contenu de la colonne de la table """
        if value_sql == "True":
            self.crud.set_element_prop(self.element, "value", True)
        elif value_sql == "False":
            self.crud.set_element_prop(self.element, "value", False)
        elif value_sql == 1:
            self.crud.set_element_prop(self.element, "value", True)
        elif value_sql == 0:
            self.crud.set_element_prop(self.element, "value", False)
        elif value_sql == "1":
            self.crud.set_element_prop(self.element, "value", True)
        elif value_sql == "0":
            self.crud.set_element_prop(self.element, "value", False)
        elif value_sql == "":
            self.crud.set_element_prop(self.element, "value", False)
        else:
            self.crud.set_element_prop(self.element, "value", True)

class CrudelCounter(Crudel):
    """ Gestion des colonnes et champs de type boîte à cocher """

    def __init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent):
        Crudel.__init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)

    def get_type_gdk(self):
        return GObject.TYPE_INT

    def init_value(self):
        Crudel.init_value(self)
        self.set_value_sql(0)
        self.crud.set_field_prop(self.element, "read_only", True)

    def get_widget_box(self):
        # todo
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        self.widget = self._get_widget_entry()
        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(self.widget, False, False, 5)
        return hbox

    def _get_renderer(self):
        """ Renderer de la cellule """
        renderer = Gtk.CellRendererText()
        renderer.set_property('xalign', 1.0)
        return renderer

    def get_cell(self):
        return self.get_value()

    def set_value_widget(self):
        pass

class CrudelDate(Crudel):
    """ Gestion des colonnes et champs de type date """

    def __init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent):
        Crudel.__init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_value(self):
        Crudel.init_value(self)
        self.set_value_sql(u"")

    def get_widget_box(self):
        # todo
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        self.widget = self._get_widget_entry()
        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(self.widget, False, False, 5)
        return hbox

class CrudelFloat(Crudel):
    """ Gestion des colonnes et champs de type décimal """

    def __init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent):
        Crudel.__init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)

    def get_type_gdk(self):
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            display = self.crud.get_column_prop(self.element, "display")
        else:
            display = self.crud.get_field_prop(self.element, "display")
        if display == "":
            return GObject.TYPE_FLOAT
        else:
            return GObject.TYPE_STRING

    def init_value(self):
        Crudel.init_value(self)
        self.set_value_sql(0)

    def get_widget_box(self):
        # todo
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        self.widget = self._get_widget_entry()
        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(self.widget, False, False, 5)
        return hbox

    def _get_renderer(self):
        """ Renderer de la cellule """
        renderer = Gtk.CellRendererText()
        renderer.set_property('xalign', 1.0)
        return renderer

    def get_cell(self):
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            display = self.crud.get_column_prop(self.element, "display")
        else:
            display = self.crud.get_field_prop(self.element, "display")
        if display == "":
            return self.get_value()
        else:
            return display % (self.get_value())

class CrudelInt(Crudel):
    """ Gestion des colonnes et champs de type entier """

    def __init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent):
        Crudel.__init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)
        self.widget = None

    def get_type_gdk(self):
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            display = self.crud.get_column_prop(self.element, "display")
        else:
            display = self.crud.get_field_prop(self.element, "display")
        if display == "":
            return GObject.TYPE_INT
        else:
            return GObject.TYPE_STRING

    def init_value(self):
        Crudel.init_value(self)
        self.set_value_sql(0)

    def get_widget_box(self):
        # todo
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        self.widget = self._get_widget_entry()
        self.widget.connect('changed', self.on_changed_number_entry)
        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(self.widget, False, False, 5)
        return hbox

    def _get_renderer(self):
        """ Renderer de la cellule """
        renderer = Gtk.CellRendererText()
        renderer.set_property('xalign', 1.0)
        return renderer

    def on_changed_number_entry(self):
        """ Ctrl de la saisie """
        text = self.widget.get_text().strip()
        self.widget.set_text(''.join([i for i in text if i in '0123456789']))

    def get_cell(self):
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            display = self.crud.get_column_prop(self.element, "display")
        else:
            display = self.crud.get_field_prop(self.element, "display")
        if display == "":
            return self.get_value()
        else:
            return display % (self.get_value())

    def set_value_widget(self):
        self.crud.set_element_prop(self.element\
                , "value", int(self.widget.get_text()))

class CrudelJointure(Crudel):
    """ Gestion des colonnes et champs de type jointure entre 2 tables """

    def __init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent):
        Crudel.__init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_value(self):
        Crudel.init_value(self)
        self.set_value_sql(u"")

    def get_widget_box(self):
        hbox = Gtk.HBox()
        
        label = self._get_widget_label()

        self.widget = Gtk.ComboBoxText()

        # Remplacement des variables
        params = {}
        sql = self.crud.replace_from_dict(self.crud.get_field_prop(self.element, "combo_select")\
            ,self.crud.get_form_values(params))
        rows = self.crud.sql_to_dict(self.crud.get_table_prop("basename"), sql, {})
        # remplissage du combo
        self.widget.set_entry_text_column(0)
        index = 0
        index_selected = None
        for row in rows:
            key = None
            text = None
            for col in row:
                if key is None:
                    if isinstance(row[col], int) or isinstance(row[col], float):
                        key = str(row[col])
                    else:
                        key = row[col].encode("utf-8")
                if isinstance(row[col], int) or isinstance(row[col], float):
                    text = str(row[col])
                else:
                    text = row[col].encode("utf-8")
            if key is None:
                # une seule colonne
                if text == self.get_value():
                    index_selected = index
                self.widget.append_text("%s" % text)
            else:
                if str(key) == str(self.get_value()):
                    index_selected = index
                self.widget.append_text("%s (%s)" % (text, key))
            # print key, text, self.get_value(), index_selected

            index += 1

        self.widget.connect('changed', self.on_changed_combo, self.element)
        if index_selected is not None:
            self.widget.set_active(index_selected)

        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(self.widget, False, False, 5)
        return hbox

    def on_changed_combo(self, widget, element):
        """ l'item sélectionné a changé """
        text = self.widget.get_active_text()
        key = self.crud.get_key_from_bracket(text)
        if text is not None:
            if key:
                self.crud.set_element_prop(element, "value", key)
            else:
                self.crud.set_element_prop(element, "value", text)

    def set_value_widget(self):
        pass

class CrudelList(Crudel):
    """ Gestion des colonnes et champs de type jointure entre 2 tables """

    def __init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent):
        Crudel.__init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)
        self.items = self.crud.get_element_prop(element, "items")

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_value(self):
        Crudel.init_value(self)
        self.set_value_sql(u"")

    def get_cell(self):
        """ représentation en colonne """
        return self.items.get(self.get_value(), "")

    def get_widget_box(self):
        hbox = Gtk.HBox()
        
        label = self._get_widget_label()

        self.widget = Gtk.ComboBoxText()

        # remplissage du combo
        self.widget.set_entry_text_column(0)
        index = 0
        index_selected = None
        for item in self.items:
            if self.items[item] == self.get_value():
                index_selected = index
            if self.items[item] == item:
                self.widget.append_text("%s" % (item))
            else:
                self.widget.append_text("%s (%s)" % (self.items[item], item))
            index += 1

        self.widget.connect('changed', self.on_changed_combo, self.element)
        if index_selected is not None:
            self.widget.set_active(index_selected)

        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(self.widget, False, False, 5)
        return hbox

    def on_changed_combo(self, widget, element):
        """ l'item sélectionné a changé """
        text = self.widget.get_active_text()
        key = self.crud.get_key_from_bracket(text)
        if text is not None:
            if key:
                self.crud.set_element_prop(element, "value", key)
            else:
                self.crud.set_element_prop(element, "value", text)

    def set_value_widget(self):
        pass

class CrudelRadio(Crudel):
    """ Gestion des colonnes et champs de type Radio """
    items = {}

    def __init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent):
        Crudel.__init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)
        self.items = self.crud.get_element_prop(element, "items")

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_value(self):
        Crudel.init_value(self)
        self.set_value_sql(False)

    def get_cell(self):
        """ représentation en colonne """
        return self.items.get(self.get_value(), "")

    def get_widget_box(self):
        # todo
        hbox = Gtk.HBox()
        label = self._get_widget_label()

        self.widget = Gtk.HBox()
        button_group = None
        for item in self.items:
            button = Gtk.RadioButton.new_with_label_from_widget(button_group, self.items[item])
            button.connect("toggled", self.on_button_toggled, item)
            if self.items[item] == self.get_value():
                button.set_active(True)
            self.widget.pack_start(button, False, False, 0)
            if button_group is None:
                button_group = button

        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(self.widget, False, False, 5)
        return hbox

    def on_button_toggled(self, button, name):
        """ Sélection d'un bouton """
        if button.get_active():
            self.crud.set_element_prop(self.element\
                ,"value", self.items.get(name))

    def set_value_widget(self):
        pass

class CrudelText(Crudel):
    """ Gestion des colonnes et champs de type texte """

    def __init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent):
        Crudel.__init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_value(self):
        Crudel.init_value(self)
        self.set_value_sql(u"")

    def get_widget_box(self):
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        self.widget = self._get_widget_entry()
        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(self.widget, False, False, 5)
        return hbox

class CrudelUid(Crudel):
    """ Gestion des colonnes et champs de type Unique IDentifier """

    def __init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent):
        Crudel.__init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_value(self):
        Crudel.init_value(self)
        self.set_value_sql(str(uuid.uuid4()))
        self.crud.set_field_prop(self.element, "read_only", True)

    def get_widget_box(self):
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        self.widget = self._get_widget_entry()
        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(self.widget, False, False, 5)
        return hbox

    def set_value_widget(self):
        pass

#
#####################################################################################
#
class CrudelView(Crudel):
    """ Gestion d'une vue à l'intérieur d'un formulaire """

    def __init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent):
        Crudel.__init__(self, app_window, crud_portail, crud_view, crud_form, crud, element, type_parent)
        self.widget_view = None
        self.box_main = None
        self.box_toolbar = None
        self.box_content = None
        self.scroll_window = None

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_value(self):
        Crudel.init_value(self)
        self.set_value_sql(str(uuid.uuid4()))

    def get_widget_box(self):
        from crudview import CrudView

        # clonage du crud et en particulier du contexte
        crud = Crud(self.crud, duplicate=True)
        # set de la table et vue à afficher dans le widget
        crud.set_view_id(self.get_view_view())
        crud.set_table_id(self.get_view_table())

        hbox = Gtk.HBox()
        label = self._get_widget_label()
        label.set_yalign(0.3)

        # box_view
        self.box_main = Gtk.VBox(spacing=0)
        self.box_main.set_size_request(-1, self.get_height(150))

        # box_viewbar
        self.box_toolbar = Gtk.HBox(spacing=0)
        self.box_main.pack_start(self.box_toolbar, False, True, 3)

        # box_listview
        self.box_content = Gtk.HBox(spacing=0)
        self.box_main.pack_end(self.box_content, True, True, 3)

        self.scroll_window = Gtk.ScrolledWindow()
        self.scroll_window.set_hexpand(True)
        self.scroll_window.set_vexpand(False)
        self.box_content.pack_end(self.scroll_window, True, True, 3)

        self.widget_view = CrudView(self.app_window, self.crud_portail, crud, self.box_main, self.box_toolbar, self.scroll_window, self)
        self.widget = self.widget_view.get_widget()
        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(self.widget, False, True, 5)

        return hbox

    def init_widget(self):
        """ Initialisation du widget après création """
        self.widget_view.emit("init_widget", self.__class__, "")

    def set_value_widget(self):
        pass
