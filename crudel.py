# -*- coding:Utf-8 -*-
"""
    Gestion des éléments
"""
# import re
import importlib
from collections import OrderedDict
import uuid
from datetime import datetime

import gi
from gi.repository import Gtk, GObject
gi.require_version('Gtk', '3.0')

class Crudel(GObject.GObject):
    """ Gestion des Elements """
    TYPE_PARENT_VIEW = 1
    TYPE_PARENT_FORM = 2

    @staticmethod
    def instantiate(crud, element, type_parent):
        """ Instanciation de la classe correspondate au type d'élément """
        if crud.get_element_prop(element, "type", "text") == "batch":
            crudel = CrudelBatch(crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "button":
            crudel = CrudelButton(crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "check":
            crudel = CrudelCheck(crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "counter":
            crudel = CrudelCounter(crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "date":
            crudel = CrudelDate(crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "float":
            crudel = CrudelFloat(crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "form":
            crudel = CrudelForm(crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "graph":
            crudel = CrudelGraph(crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "int":
            crudel = CrudelInt(crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "jointure":
            crudel = CrudelJointure(crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "combo":
            crudel = CrudelCombo(crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "radio":
            crudel = CrudelRadio(crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "uid":
            crudel = CrudelUid(crud, element, type_parent)
        elif crud.get_element_prop(element, "type", "text") == "view":
            crudel = CrudelView(crud, element, type_parent)
        else:
            crudel = CrudelText(crud, element, type_parent)
        return crudel

    __gsignals__ = {
        'init_widget': (GObject.SIGNAL_RUN_FIRST, None, (str, str,))
    }
    def do_init_widget(self, str_from, str_arg=""):
        """ Traitement du signal """
        # print "do_init_widget %s(%s) -> %s" % (str_from, str_arg, self.__class__)
        self.init_widget()

    def __init__(self, crud, element, type_parent=1):

        GObject.GObject.__init__(self)

        self.crud = crud
        self.app_window = crud.get_window()
        self.crud_portail = crud.get_portail()
        self.crud_view = crud.get_view()
        self.crud_form = crud.get_form()
        self.element = element
        self.widget = None
        self.type_parent = type_parent
        self.items = {}
        self.params = None
        self.value = None

        self.init_crudel()

    def init_crudel(self):
        """ initialisation de la valeur """
        if self.crud.get_element_prop(self.element, "items", None):
            self.items = self.crud.get_element_prop(self.element, "items")
        self.params = self.crud.get_element_prop(self.element, "params", None)

    def init_crudel_sql(self):
        """ Initialisation calcul, remplissage des items de liste """
        if self.is_type_jointure():
            if self.get_param("table"):
                sql = "SELECT " + self.get_param("key") + " AS key, "\
                    + self.get_param("display", self.get_param("key")) + " as display "\
                    + "FROM " + self.get_param("table")
                if self.get_param("where"):
                    sql += " WHERE " + self.get_param("where")
                rows = self.crud.sql_to_dict(self.crud.get_table_prop("basename"), sql , {})
                for row in rows:
                    self.items[row["key"]] = row["display"]

    def init_value(self):
        """ Initialisation de la valeur """
        pass

    def set_value(self, value):
        """ Valorisation dans le crud """
        self.value = value

    def set_value_sql(self, value_sql):
        """ Valorisation de l'élément avec le contenu de la colonne de la table """
        if value_sql is None:
            return
        self.value = value_sql if isinstance(value_sql, int) or isinstance(value_sql, float) else value_sql.encode("utf-8")

    def set_value_widget(self):
        """ valorisation à partir de la saisie dans le widget """
        self.value = self.get_widget().get_text()

    def set_value_default(self):
        """ valorisation avec la valeur par défaut si valeur '' """

        if self.get_value() == ""\
            and self.crud.get_field_prop(self.element, "default", "") != "":
            self.value = self.crud.get_field_prop(self.element, "default")


    def get_value(self):
        """ valeur interne de l'élément """
        return self.value

    def get_value_sql(self):
        """ valeur à enregistrer dans la colonne de l'élément """
        return self.value

    def get_type_gdk(self):
        """ Type d'objet du GDK """
        return GObject.TYPE_STRING

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
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            return self.crud.get_column_prop(self.element, "label_long", False)
        else:
            return self.crud.get_field_prop(self.element, "label_long", False)

    def get_label_short(self):
        """ Label de l'élément utilisé dans une vue """
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            return self.crud.get_column_prop(self.element, "label_short", False)
        else:
            return self.crud.get_field_prop(self.element, "label_short", False)

    def get_type(self, type="text"):
        """ type d''élément du crud """
        return self.crud.get_element_prop(self.element, "type", type)

    def is_display(self):
        """ Est-ce que la propriété display est valorisée ? """
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            return self.crud.get_column_prop(self.element, "display", False)
        else:
            return self.crud.get_field_prop(self.element, "display", False)

    def get_display(self):
        """ modèle de présentation de la chaîne
        https://www.tutorialspoint.com/python/python_strings.htm
        "%3.2d €" par exemple pour présenter un montant en 0.00 €
        "%5s" pour représenter une chaîne en remplissant de blancs à gauche si la longueur < 5c
        """
        value = self.get_value()
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            display = self.crud.get_column_prop(self.element, "display", None)
        else:
            display = self.crud.get_field_prop(self.element, "display", None)
        if display:
            if not self.is_read_only() and self.type_parent == Crudel.TYPE_PARENT_FORM:
                pass
            else:
                value = display.encode("utf-8") % (value)
        if self.get_type_gdk() == GObject.TYPE_STRING:
            value = str(value)
        return value

    def get_cell(self):
        """ retourne la cellule dans la vue """
        return self.get_display()

    def get_col_width(self):
        """ largeur de la colonne """
        return self.crud.get_column_prop(self.element, "col_width", None)

    def get_col_align(self):
        """ alignement du texte dans la colonne """
        return self.crud.get_column_prop(self.element, "col_align", "")

    def get_sql_color(self):
        """ Couleur du texte dans la colonne """
        return self.crud.get_element_prop(self.element, "sql_color", "")

    def get_sql_get(self):
        """ l'instruction sql dans le select pour lire la colonne """
        return self.crud.get_element_prop(self.element, "sql_get", "")

    def get_sql_put(self):
        """ l'instruction sql pour écrire la colonne """
        return self.crud.get_element_prop(self.element, "sql_put", "")

    def get_cell_sql_post(self):
        """ l'instruction sql à exécuter suite à la mise à jour de la cellule """
        return self.crud.get_element_prop(self.element, "cell_sql_post", False)

    def get_height(self, default):
        """ Hauteur du widget """
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            return self.crud.get_column_prop(self.element, "height", default)
        else:
            return self.crud.get_field_prop(self.element, "height", default)

    def get_param(self, param, default=None):
        """ Retourne la valeur du paramètre """
        return self.crud.get_element_param(self.element, param, default)

    def get_param_replace(self, param, default=None):
        """ Retourne la valeur du paramètre """
        return self.crud.replace_from_dict(\
            self.crud.get_element_param(self.element, param, default), self.crud.get_table_values())

    def get_args(self):
        """ Retourne les arguments """
        return self.crud.get_element_prop(self.element, "args", None)

    def get_args_replace(self):
        """ remplacement des variables des paramètres """
        args = self.get_args().copy()
        values = self.crud.get_table_values()
        for arg in args:
            args[arg] = self.crud.replace_from_dict(args[arg], values)
        return args

    def is_virtual(self):
        """ Les colonnes préfixées par _ ne sont pas dans la table """
        return self.element.startswith("_")

    def set_hide(self, bool):
        """ hide """
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            return self.crud.set_column_prop(self.element, "hide", bool)
        else:
            return self.crud.set_field_prop(self.element, "hide", bool)
    def is_hide(self):
        """ élément caché """
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            return self.crud.get_column_prop(self.element, "hide", False)
        else:
            return self.crud.get_field_prop(self.element, "hide", False)

    def set_read_only(self, bool):
        """ read_only """
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            return self.crud.set_column_prop(self.element, "read_only", bool)
        else:
            return self.crud.set_field_prop(self.element, "read_only", bool)
    def is_read_only(self):
        """ élément en lecture seule """
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            return self.crud.get_column_prop(self.element, "read_only", False)
        else:
            return self.crud.get_field_prop(self.element, "read_only", False)

    def is_type_jointure(self):
        """ est-ce que la colonne est en lien avec une autre table """
        if self.get_type() in ("combo", "radio", "jointure"):
            if self.get_param("table"):
                return True
            if self.get_param("join"):
                return True
            if self.get_param("column"):
                return True

    def is_searchable(self):
        """ le contenu de la colonne sera lue par le moteur de recharche """
        return self.crud.get_column_prop(self.element, "searchable", False)

    def is_sortable(self):
        """ La colonne pourra être triée en cliquant sur le titre de la colonne """
        return self.crud.get_column_prop(self.element, "sortable", False)

    def set_required(self, bool):
        """ required """
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            return self.crud.set_column_prop(self.element, "required", bool)
        else:
            return self.crud.set_field_prop(self.element, "required", bool)
    def is_required(self):
        """ La saisie du champ est obligatoire """
        if self.is_read_only():
            return False
        return self.crud.get_field_prop(self.element, "required", False)

    def _get_widget_entry(self):
        """ champ de saisie """
        widget = Gtk.Entry()
        widget.set_text(str(self.get_display()))
        widget.set_width_chars(40)
        if self.is_read_only():
            widget.set_sensitive(False)

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
        renderer = self._get_renderer(treeview)
        if self.get_col_align() == "left":
            renderer.set_property('xalign', 0.1)
        elif self.get_col_align() == "right":
            renderer.set_property('xalign', 1.0)
        elif self.get_col_align() == "center":
            renderer.set_property('xalign', 0.5)

        tvc = self._get_tvc(renderer, col_id)

        if self.get_sql_color() != "":
            col_id += 1
            tvc.add_attribute(renderer, "foreground", col_id)
        if self.is_sortable():
            col_id += 1
            tvc.set_sort_column_id(col_id)
        if self.get_col_width():
            tvc.set_fixed_width(self.get_col_width())

        treeview.append_column(tvc)

        # on ajoute les colonnes techniques
        # if self.get_sql_color() != "":
        #     col_id += 1
        # if self.is_sortable():
        #     col_id += 1
        return col_id

    def _get_renderer(self, treeview):
        """ Renderer de la cellule """
        renderer = Gtk.CellRendererText()
        if self.crud.get_column_prop(self.element, "cell_editable", False):
            renderer.set_property('editable', True)
            renderer.connect('edited', self.on_cell_edited)
        return renderer

    def _get_tvc(self, renderer, col_id):
        """ TreeViewColumn de la cellule """
        tvc = Gtk.TreeViewColumn(self.get_label_short(), renderer, text=col_id)
        return tvc

    def check(self):
        """ Contrôle de la saisie """
        if self.is_hide():
            return True
        if self.is_read_only():
            return True
        self.get_widget().get_style_context().remove_class('field_invalid')
        if self.is_required() and self.get_value() == "":
            self.get_widget().get_style_context().add_class('field_invalid')
            self.crud.add_error("<b>{}</b> est obligatoire".format(self.get_label_long()))

    def dump(self):
        """ print des propriétés de l'élément """
        props = {}
        props.update(self.crud.get_table_elements()[self.element])
        if self.type_parent == Crudel.TYPE_PARENT_VIEW:
            props.update(self.crud.get_view_elements()[self.element])
        else:
            props.update(self.crud.get_form_elements()[self.element])
        for prop in props:
            if isinstance(props[prop], int):
                print "%s.%s = %s" % (self.element, prop, props[prop])
            elif isinstance(props[prop], float):
                print "%s.%s = %s" % (self.element, prop, props[prop])
            elif isinstance(props[prop], OrderedDict):
                print "%s.%s = %s" % (self.element, prop, props[prop])                
            elif isinstance(props[prop], Crudel):
                pass
            else:
                print "%s.%s = %s" % (self.element, prop, props[prop].encode("utf-8"))

    def on_cell_edited(self, renderer, path, text):
        """ Edition de la cellule dans la vue """
        key_value = self.crud_view.store_filter_sort[path][self.crud.get_view_prop("key_id")]
        row_id = self.crud_view.store_filter_sort[path][self.crud.get_view_prop("col_row_id")]
        col_id = self.crud.get_column_prop(self.element, "col_id")
        # print "on_cell_edited", row_id, col_id, key_value
        # if self.get_type_gdk() == GObject.TYPE_STRING:
        #     text = text.decode("utf-8")

        self.crud_view.liststore[row_id][col_id] = text

        if self.get_sql_color() != "":
            col_id += 1
        if self.is_sortable():
            col_id += 1
            self.crud_view.liststore[row_id][col_id] = text

        sql = "UPDATE " + self.crud.get_table_id() + " SET "\
        + self.element + " = :text WHERE " + self.crud.get_key_id() + " = :key_value"
        self.crud.exec_sql(self.crud.get_table_prop("basename")\
            , sql, {"key_value": key_value, "text": text})

########################################################
### Classes des crudel en fonction dy type d'élément ####################################################
########################################################

class CrudelButton(Crudel):
    """ Gestion des colonnes et champs de type bouton """

    def __init__(self, crud, element, type_parent):
        Crudel.__init__(self, crud, element, type_parent)

    def get_type_gdk(self):
        return GObject.TYPE_OBJECT

    def get_widget_box(self):
        # todo
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        self.widget = self._get_widget_entry()
        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(self.widget, False, False, 5)
        return hbox

class CrudelCheck(Crudel):
    """ Gestion des colonnes et champs de type boîte à cocher """

    def __init__(self, crud, element, type_parent):
        Crudel.__init__(self, crud, element, type_parent)

    def get_type_gdk(self):
        return GObject.TYPE_BOOLEAN

    def init_value(self):
        self.set_value(False)

    def get_widget_box(self):
        # todo
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        label.set_label("")

        self.widget = Gtk.CheckButton()
        if self.is_read_only():
            self.widget.set_sensitive(False)

        self.widget.set_label(self.get_label_long())
        self.widget.set_active(self.get_value())
        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(self.widget, False, False, 5)
        return hbox

    def _get_renderer(self, treeview):
        renderer = Gtk.CellRendererToggle()
        return renderer

    def _get_tvc(self, renderer, col_id):
        renderer.connect("toggled", self.on_cell_toggle)
        tvc = Gtk.TreeViewColumn(self.get_label_short(), renderer, active=col_id)
        return tvc

    def set_value_widget(self):
        self.value = self.get_widget().get_active()


    def on_cell_toggle(self, renderer, path):
        """ Clic sur la coche """
        key_id = self.crud.get_key_id()
        key_value = self.crud_view.store_filter_sort[path][self.crud.get_view_prop("key_id")]
        row_id = self.crud_view.store_filter_sort[path][self.crud.get_view_prop("col_row_id")]
        col_id = self.crud.get_column_prop(self.element, "col_id")

        self.set_value(not renderer.get_active())
        value_sql = self.get_value_sql()

        sql = "UPDATE " + self.crud.get_table_id() + " SET "\
        + self.element + " = :value_sql WHERE " + key_id + " = :key_value"
        self.crud.exec_sql(self.crud.get_table_prop("basename")\
            , sql, {"key_value": key_value, "value_sql": value_sql})

        if self.get_cell_sql_post():
            sql = " ".join(self.get_cell_sql_post())
            params = {
                key_id: key_value
            }
            row = self.crud.get_sql_row(params)
            sql_post = self.crud.replace_from_dict(sql, row)
            sqls = sql_post.split(";")
            for sql in sqls:
                self.crud.exec_sql(self.crud.get_table_prop("basename"), sql, params)

        # cochage / décochage de la ligne
        self.crud_view.liststore[row_id][col_id] = not renderer.get_active()

    def get_value_sql(self):
        """ valeur à enregistrer dans la colonne de l'élément """
        if self.get_value():
            return 1
        else:
            return 0

    def set_value_sql(self, value_sql):
        """ Valorisation de l'élément avec le contenu de la colonne de la table """
        if value_sql is None:
            self.value = False
        elif value_sql == "True":
            self.value = True
        elif value_sql == "False":
            self.value = False
        elif value_sql == 1:
            self.value = True
        elif value_sql == 0:
            self.value = False
        elif value_sql == "1":
            self.value = True
        elif value_sql == "0":
            self.value = False
        elif value_sql == "":
            self.value = False
        else:
            self.value = True

class CrudelCounter(Crudel):
    """ Gestion des colonnes et champs de type boîte à cocher """

    def __init__(self, crud, element, type_parent):
        Crudel.__init__(self, crud, element, type_parent)

    def get_type_gdk(self):
        return GObject.TYPE_INT

    def init_crudel(self):
        Crudel.init_crudel(self)
        if self.type_parent == Crudel.TYPE_PARENT_FORM:
            self.crud.set_field_prop(self.element, "read_only", True)

    def init_value(self):
        self.set_value(0)

    def get_widget_box(self):
        # todo
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        self.widget = self._get_widget_entry()
        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(self.widget, False, False, 5)
        return hbox

    def _get_renderer(self, treeview):
        """ Renderer de la cellule """
        renderer = Gtk.CellRendererText()
        renderer.set_property('xalign', 1.0)
        return renderer

    def set_value_widget(self):
        pass

class CrudelDate(Crudel):
    """ Gestion des colonnes et champs de type date """

    def __init__(self, crud, element, type_parent):
        Crudel.__init__(self, crud, element, type_parent)

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_value(self):
        self.set_value("")

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

    def __init__(self, crud, element, type_parent):
        Crudel.__init__(self, crud, element, type_parent)

    def get_type_gdk(self):
        return GObject.TYPE_FLOAT

    def init_value(self):
        self.set_value(0.0)

    def get_widget_box(self):
        # todo
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        self.widget = self._get_widget_entry()
        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(self.widget, False, False, 5)
        return hbox

    def _get_renderer(self, treeview):
        """ Renderer de la cellule """
        renderer = Gtk.CellRendererText()
        renderer.set_property('xalign', 1.0)
        if self.crud.get_column_prop(self.element, "cell_editable", False):
            renderer.set_property('editable', True)
            renderer.connect('edited', self.on_cell_edited)
        return renderer

    def set_value_widget(self):
        value = self.widget.get_text()
        if value == '':
            value = 0
        self.value = float(value)

class CrudelForm(Crudel):
    """ Appel d'un formulaire dans une vue
        Affichage d'un sous formulaire
    """

    def __init__(self, crud, element, type_parent):
        Crudel.__init__(self, crud, element, type_parent)

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_value(self):
        self.set_value("")

    def get_widget_box(self):
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        label.set_label("")

        self.widget = Gtk.CheckButton()
        if self.is_read_only():
            self.widget.set_sensitive(False)

        self.widget.set_label(self.get_label_long())
        self.widget.set_active(self.get_value())
        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(self.widget, False, False, 5)
        return hbox

    def _get_renderer(self, treeview):
        renderer = CellRendererClickablePixbuf()
        renderer.connect('clicked', self.on_clicked_in_view)
        return renderer

    def _get_tvc(self, renderer, col_id):
        tvc = Gtk.TreeViewColumn(self.get_label_short(), renderer, icon_name=col_id)
        return tvc

    def set_value_widget(self):
        self.value = self.get_widget().get_active()

    def get_cell(self):
        # la colonne aura pour valeur le nom de l'icone
        # https://specifications.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html#names
        # /usr/share/icons/Adwaita/scalable/actions
        return self.get_param("icon_name", "applications-accessories")

    def on_clicked_in_view(self, cell, path):
        """ Clic sur l'élément dans une vue """
        key_id = self.crud_view.store_filter_sort[path][self.crud.get_view_prop("key_id")]
        row_id = self.crud_view.store_filter_sort[path][self.crud.get_view_prop("col_row_id")]
        self.crud.set_row_id(row_id)
        self.crud.remove_all_selection()
        self.crud.add_selection(key_id)
        self.crud.set_key_value(key_id)
        if self.get_param("plugin"):
            plugin = self.get_param("plugin")
            plugin_class = self.crud.load_class("plugin." + plugin)
            form = plugin_class(self.crud)
        else:
            self.crud.set_action("update")
            self.crud_portail.set_layout(self.crud_portail.LAYOUT_FORM)
            self.crud.set_form_id(self.get_param("form"))
            from crudform import CrudForm
            form = CrudForm(self.crud, None)
        self.app_window.show_all()
        form.emit("init_widget", self.__class__, "on_button_edit_clicked")

class CrudelGraph(CrudelCheck):
    """ Gestion des colonnes et champs de type boîte à cocher """

    def __init__(self, crud, element, type_parent):
        CrudelCheck.__init__(self, crud, element, type_parent)

class CrudelInt(Crudel):
    """ Gestion des colonnes et champs de type entier """

    def __init__(self, crud, element, type_parent):
        Crudel.__init__(self, crud, element, type_parent)
        self.widget = None

    def get_type_gdk(self):
        return GObject.TYPE_INT

    def init_value(self):
        self.set_value(0)

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

    def _get_renderer(self, treeview):
        """ Renderer de la cellule """
        renderer = Gtk.CellRendererText()
        renderer.set_property('xalign', 1.0)
        if self.crud.get_column_prop(self.element, "cell_editable", False):
            renderer.set_property('editable', True)
            renderer.connect('edited', self.on_cell_edited)
        return renderer

    def on_changed_number_entry(self, widget):
        """ Ctrl de la saisie """
        text = widget.get_text().strip()
        widget.set_text(''.join([i for i in text if i in '0123456789']))

    def set_value_widget(self):
        value = self.widget.get_text()
        if value == '':
            value = 0
        self.value = int(value)

class CrudelJointure(Crudel):
    """ Gestion des colonnes et champs de type jointure entre 2 tables """

    def __init__(self, crud, element, type_parent):
        Crudel.__init__(self, crud, element, type_parent)

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def is_read_only(self):
        return True

    def get_cell(self):
        return Crudel.get_display(self)

    def get_display(self):
        value = self.get_value()
        if self.get_param("table"):
            sql = "SELECT " + self.get_param("display", self.get_param("key")) + " as value"\
            + " FROM " + self.get_param("table")\
            + " WHERE " + self.get_param("key") + " = '" + self.get_value() + "'"
            rows = self.crud.sql_to_dict(self.crud.get_table_prop("basename"), sql, {})
            for row in rows:
                value = row["value"]
        return Crudel.get_display(self)

    def get_widget_box(self):
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        self.widget = self._get_widget_entry()
        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(self.widget, False, False, 5)
        return hbox

class CrudelCombo(Crudel):
    """ Gestion des colonnes et champs de type list """

    def __init__(self, crud, element, type_parent):
        Crudel.__init__(self, crud, element, type_parent)

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_value(self):
        self.set_value(False)

    def get_widget_box(self):
        hbox = Gtk.HBox()

        label = self._get_widget_label()

        self.widget = Gtk.ComboBoxText()
        if self.is_read_only():
            self.widget.set_sensitive(False)

        # remplissage du combo
        self.widget.set_entry_text_column(0)
        index = 0
        index_selected = None
        for item in self.items:
            if item == self.get_value():
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
                self.value = key
            else:
                self.value = text

    def set_value_widget(self):
        pass

class CrudelBatch(Crudel):
    """ Plugin """

    def __init__(self, crud, element, type_parent):
        Crudel.__init__(self, crud, element, type_parent)
        self.set_hide(True)

class CrudelRadio(Crudel):
    """ Gestion des colonnes et champs de type Radio """
    items = {}

    def __init__(self, crud, element, type_parent):
        Crudel.__init__(self, crud, element, type_parent)
        self.items = self.crud.get_element_prop(element, "items")

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_value(self):
        self.set_value(False)

    def get_widget_box(self):
        # todo
        hbox = Gtk.HBox()
        label = self._get_widget_label()

        self.widget = Gtk.HBox()
        if self.is_read_only():
            self.widget.set_sensitive(False)
        button_group = None
        for item in self.items:
            button = Gtk.RadioButton.new_with_label_from_widget(button_group, self.items[item])
            button.connect("toggled", self.on_button_toggled, item)
            if item == self.get_value():
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
            self.value = self.items.get(name)

    def set_value_widget(self):
        pass

class CrudelText(Crudel):
    """ Gestion des colonnes et champs de type texte """

    def __init__(self, crud, element, type_parent):
        Crudel.__init__(self, crud, element, type_parent)

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_value(self):
        self.set_value("")

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

    def __init__(self, crud, element, type_parent):
        Crudel.__init__(self, crud, element, type_parent)

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_crudel(self):
        Crudel.init_crudel(self)
        if self.type_parent == Crudel.TYPE_PARENT_FORM:
            self.crud.set_field_prop(self.element, "read_only", True)

    def init_value(self):
        self.set_value(str(uuid.uuid4()))

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

    def __init__(self, crud, element, type_parent):
        Crudel.__init__(self, crud, element, type_parent)
        self.widget_view = None
        self.box_main = None
        self.box_toolbar = None
        self.box_content = None
        self.scroll_window = None

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_value(self):
        self.set_value("")

    def get_widget_box(self):
        from crudview import CrudView

        # clonage du crud et en particulier du contexte
        crud = Crud(self.crud, duplicate=True)
        # set de la table et vue à afficher dans le widget
        crud.set_view_id(self.get_param("view"))
        crud.set_table_id(self.get_param("table"))

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

        crud.set_crudel(self)
        self.widget_view = CrudView(crud, self.box_main, self.box_toolbar, self.scroll_window, self.get_args_replace())
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

class CellRendererClickablePixbuf(Gtk.CellRendererPixbuf):
    __gsignals__ = {
        'clicked': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (GObject.TYPE_STRING,))
    }
    def __init__(self):
        Gtk.CellRendererPixbuf.__init__(self)
        self.set_property('mode', Gtk.CellRendererMode.ACTIVATABLE)
    def do_activate(self, event, widget, path, background_area, cell_area, flags):
        self.emit('clicked', path)
