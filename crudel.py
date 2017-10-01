# -*- coding:Utf-8 -*-
"""
    Gestion des éléments
"""
from crud import Crud
# from crudform import CrudForm
# import sqlite3
# import os
# import urllib2
# import time
# from datetime import datetime
import re
# import sys
# import itertools

import uuid

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

class Crudel():
    """ Gestion des Elements """
    CRUD_PARENT_VIEW = 1
    CRUD_PARENT_FORM = 2

    def __init__(self, app_window, parent, crud, element, crud_parent=1):
        self.crud = crud
        self.app_window = app_window
        self.parent = parent
        self.element = element
        self.widget = None
        self.crud_parent = crud_parent

        # Cast class
        if crud.get_element_prop(element, "type", "text") == "button":
            self.__class__ = CrudButton
        elif crud.get_element_prop(element, "type", "text") == "check":
            self.__class__ = CrudCheck
        elif crud.get_element_prop(element, "type", "text") == "counter":
            self.__class__ = CrudCounter
        elif crud.get_element_prop(element, "type", "text") == "date":
            self.__class__ = CrudDate
        elif crud.get_element_prop(element, "type", "text") == "float":
            self.__class__ = CrudFloat
        elif crud.get_element_prop(element, "type", "text") == "int":
            self.__class__ = CrudInt
        elif crud.get_element_prop(element, "type", "text") == "jointure":
            self.__class__ = CrudJointure
        elif crud.get_element_prop(element, "type", "text") == "uid":
            self.__class__ = CrudUid
        elif crud.get_element_prop(element, "type", "text") == "view":
            self.__class__ = CrudView
        else:
            self.__class__ = CrudText

    def get_type_gdk(self):
        """ Type d'objet du GDK """
        return GObject.TYPE_STRING

    def init_value(self):
        """ initialisation de la valeur """
        self.set_value_sql(u"")

    def set_value_sql(self, value_sql):
        """ Valorisation de l'élément avec le contenu de la colonne de la table """
        self.crud.set_element_prop(self.element, "value",\
            value_sql if isinstance(value_sql, int) or isinstance(value_sql, float) else value_sql.encode("utf-8"))
        # print "set_value_sql", self.element, value_sql, self.crud.get_element_prop(self.element, "value")

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
        return self.crud.get_column_prop(self.element, "label_short", "")

    def get_type(self, type="text"):
        """ type d''élément du crud """
        return self.crud.get_element_prop(self.element, "type", type)

    def get_display(self):
        """ modèle de présentation de la chaîne
        https://www.tutorialspoint.com/python/python_strings.htm
        "%3.2d €" par exemple pour présenter un montant en 0.00 €
        "%5s" pour représenter une chaîne en remplissant de blancs à gauche si la longueur < 5c
        """
        if self.crud_parent == Crudel.CRUD_PARENT_VIEW:
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
        if self.crud_parent == Crudel.CRUD_PARENT_VIEW:
            return self.crud.get_column_prop(self.element, "sql_color", "")
        else:
            return self.crud.get_field_prop(self.element, "sql_color", "")

    def get_sql_get(self):
        """ l'instruction sql dans le select pour lire la colonne """
        if self.crud_parent == Crudel.CRUD_PARENT_VIEW:
            return self.crud.get_column_prop(self.element, "sql_get", "")
        else:
            return self.crud.get_field_prop(self.element, "sql_get", "")

    def get_sql_put(self):
        """ l'instruction sql pour écrire la colonne """
        if self.crud_parent == Crudel.CRUD_PARENT_VIEW:
            return self.crud.get_column_prop(self.element, "sql_put", "")
        else:
            return self.crud.get_field_prop(self.element, "sql_put", "")

    def get_sql_where(self):
        """ le where d'une rubrique de type view """
        if self.crud_parent == Crudel.CRUD_PARENT_VIEW:
            return self.crud.get_column_prop(self.element, "sql_where", "")
        else:
            return self.crud.get_field_prop(self.element, "sql_where", "")

    def get_value(self):
        """ valeur interne de l'élément """
        return self.crud.get_element_prop(self.element, "value", "")

    def get_jointure_columns(self):
        """ la partie selecct de la jointure """
        if self.crud_parent == Crudel.CRUD_PARENT_VIEW:
            return self.crud.get_column_prop(self.element, "jointure_columns", "")
        else:
            return self.crud.get_field_prop(self.element, "jointure_columns", "")

    def get_jointure_join(self):
        """ la partie liaison evec la table principale """
        if self.crud_parent == Crudel.CRUD_PARENT_VIEW:
            return self.crud.get_column_prop(self.element, "jointure_join", "")
        else:
            return self.crud.get_field_prop(self.element, "jointure_join", "")

    def get_view_table(self):
        """ nom de la table de la rubrique view """
        return self.crud.get_field_prop(self.element, "view_table", "")

    def get_view_view(self):
        """ nom de la vue de la rubrique view """
        return self.crud.get_field_prop(self.element, "view_view", "")

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

    def get_height(self):
        """ Hauteur du widget """
        if self.crud_parent == Crudel.CRUD_PARENT_VIEW:
            return self.crud.get_column_prop(self.element, "height", -1)
        else:
            return self.crud.get_field_prop(self.element, "height", -1)

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

    def init_widget(self):
        """ Pour afficher ou cacher des objets graphiques """
        pass

    def is_hide(self):
        """ élément caché """
        if self.crud_parent == Crudel.CRUD_PARENT_VIEW:
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

    def dump(self):
        """ print des propriétés de l'élément """
        prop = {}
        prop.update(self.crud.get_table_elements()[self.element])
        if self.crud_parent == Crudel.CRUD_PARENT_VIEW:
            prop.update(self.crud.get_view_elements()[self.element])
        else:
            prop.update(self.crud.get_form_elements()[self.element])
        for p in prop:
            print "%s.%s = %s" % (self.element, p, prop[p])


class CrudButton(Crudel):
    """ Gestion des colonnes et champs de type bouton """

    def __init__(self, parent, crud, element):
        Crudel.__init__(self.app_window, self, parent, crud, element)

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
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(widget, False, False, 5)
        return hbox

    def get_display(self):
        return self.get_value()

class CrudCheck(Crudel):
    """ Gestion des colonnes et champs de type boîte à cocher """

    def __init__(self, parent, crud, element):
        Crudel.__init__(self.app_window, self, parent, crud, element)

    def get_type_gdk(self):
        return GObject.TYPE_BOOLEAN

    def init_value(self):
        Crudel.init_value(self)
        self.set_value_sql(False)

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

    def _get_renderer(self):
        renderer = Gtk.CellRendererToggle()
        return renderer

    def _get_tvc(self, renderer, col_id):
        tvc = Gtk.TreeViewColumn(self.get_label_short(), renderer, active=col_id)
        return tvc

class CrudCounter(Crudel):
    """ Gestion des colonnes et champs de type boîte à cocher """

    def __init__(self, parent, crud, element):
        Crudel.__init__(self.app_window, self, parent, crud, element)

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
        widget = self._get_widget_entry()
        # Mémorisation du widget
        self.crud.set_field_prop(self.element, "widget", widget)
        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(widget, False, False, 5)
        return hbox

    def _get_renderer(self):
        """ Renderer de la cellule """
        renderer = Gtk.CellRendererText()
        renderer.set_property('xalign', 1.0)
        return renderer

    def get_display(self):
        return self.get_value()

class CrudDate(Crudel):
    """ Gestion des colonnes et champs de type date """

    def __init__(self, parent, crud, element):
        Crudel.__init__(self.app_window, self, parent, crud, element)

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_value(self):
        Crudel.init_value(self)
        self.set_value_sql(u"")

    def get_widget_box(self):
        # todo
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        widget = self._get_widget_entry()
        # Mémorisation du widget
        self.crud.set_field_prop(self.element, "widget", widget)
        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(widget, False, False, 5)
        return hbox

class CrudFloat(Crudel):
    """ Gestion des colonnes et champs de type décimal """

    def __init__(self, parent, crud, element):
        Crudel.__init__(self.app_window, self, parent, crud, element)

    def get_type_gdk(self):
        if self.crud_parent == Crudel.CRUD_PARENT_VIEW:
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
        widget = self._get_widget_entry()
        # Mémorisation du widget
        self.crud.set_field_prop(self.element, "widget", widget)
        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(widget, False, False, 5)
        return hbox

    def _get_renderer(self):
        """ Renderer de la cellule """
        renderer = Gtk.CellRendererText()
        renderer.set_property('xalign', 1.0)
        return renderer

    def get_display(self):
        if self.crud_parent == Crudel.CRUD_PARENT_VIEW:
            display = self.crud.get_column_prop(self.element, "display")
        else:
            display = self.crud.get_field_prop(self.element, "display")
        if display == "":
            return self.get_value()
        else:
            return display % (self.get_value())

class CrudInt(Crudel):
    """ Gestion des colonnes et champs de type entier """

    def __init__(self, parent, crud, element):
        Crudel.__init__(self.app_window, self, parent, crud, element)
        self.widget = None

    def get_type_gdk(self):
        if self.crud_parent == Crudel.CRUD_PARENT_VIEW:
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
        # Mémorisation du widget
        self.crud.set_field_prop(self.element, "widget", self.widget)
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

    def get_display(self):
        if self.crud_parent == Crudel.CRUD_PARENT_VIEW:
            display = self.crud.get_column_prop(self.element, "display")
        else:
            display = self.crud.get_field_prop(self.element, "display")
        if display == "":
            return self.get_value()
        else:
            return display % (self.get_value())

class CrudJointure(Crudel):
    """ Gestion des colonnes et champs de type jointure entre 2 tables """

    def __init__(self, parent, crud, element):
        Crudel.__init__(self.app_window, self, parent, crud, element)

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_value(self):
        Crudel.init_value(self)
        self.set_value_sql(u"")

    def get_widget_box(self):
        hbox = Gtk.HBox()
        
        label = self._get_widget_label()

        widget = Gtk.ComboBoxText()

        # Remplacement des variables
        params = {}
        sql = self.crud.replace_from_dict(self.crud.get_field_prop(self.element, "combo_select")\
            ,self.crud.get_form_values(params))
        rows = self.crud.sql_to_dict(self.crud.get_table_prop("basename"), sql, {})
        # remplissage du combo
        widget.set_entry_text_column(0)
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
                widget.append_text("%s" % text)
            else:
                if str(key) == str(self.get_value()):
                    index_selected = index
                widget.append_text("%s (%s)" % (text, key))
            # print key, text, self.get_value(), index_selected

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
        Crudel.__init__(self.app_window, self, parent, crud, element)

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_value(self):
        Crudel.init_value(self)
        self.set_value_sql(str(uuid.uuid4()))
        self.crud.set_field_prop(self.element, "read_only", True)

    def get_widget_box(self):
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        widget = self._get_widget_entry()
        # Mémorisation du widget
        self.crud.set_field_prop(self.element, "widget", widget)
        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(widget, False, False, 5)
        return hbox

class CrudText(Crudel):
    """ Gestion des colonnes et champs de type texte """

    def __init__(self, parent, crud, element):
        Crudel.__init__(self.app_window, self, parent, crud, element)

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_value(self):
        Crudel.init_value(self)
        self.set_value_sql(u"")

    def get_widget_box(self):
        hbox = Gtk.HBox()
        label = self._get_widget_label()
        widget = self._get_widget_entry()
        # Mémorisation du widget
        self.crud.set_field_prop(self.element, "widget", widget)
        # arrangement
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(widget, False, False, 5)
        return hbox

#
#####################################################################################
#
class CrudView(Crudel):
    """ Gestion d'une vue à l'intérieur d'un formulaire """

    def __init__(self, parent, crud, element):
        Crudel.__init__(self.app_window, self, parent, crud, element)
        self.widget_view = None

    def get_type_gdk(self):
        return GObject.TYPE_STRING

    def init_value(self):
        Crudel.init_value(self)
        self.set_value_sql(str(uuid.uuid4()))

    def get_widget_box(self):
        hbox = Gtk.VBox()
        label = self._get_widget_label()

        self.widget_view = WidgetView(self.app_window, self, self)
        widget = self.widget_view.get_widget()
        # Mémorisation du widget
        self.crud.set_field_prop(self.element, "widget", widget)
        # arrangement
        # hbox.pack_start(label, False, False, 5)
        hbox.pack_end(widget, False, False, 5)
        return hbox

    def init_widget(self):
        self.widget_view.init_widget()


class WidgetView():
    """ Création d'une ListView """

    def __init__(self, app_window, parent, crudel):
        self.parent = parent
        self.crudel = crudel
        self.app_window = app_window

        # clonage du crud et en particulier du contexte
        self.crud = Crud(self.crudel.crud, duplicate=True)
        # set de la table et vue à afficher dans le widget
        self.crud.set_view_id(self.crudel.get_view_view())
        self.crud.set_table_id(self.crudel.get_view_table())

        # Déclaration des variables globales
        self.treeview = None
        self.liststore = None
        self.current_filter = None
        self.store_filter = None
        self.store_filter_sort = None
        self.search_entry = None
        self.scroll_window = None
        self.select = None
        self.button_add = None
        self.button_edit = None
        self.button_delete = None
        self.label_select = None

        # box_view
        self.box_view = Gtk.VBox(spacing=0) # box_viewbar box_listview
        if self.crudel.get_height():
            self.box_view.set_size_request(-1, self.crudel.get_height())

        # box_viewbar
        self.box_view_toolbar = Gtk.HBox(spacing=0)
        self.box_view.pack_start(self.box_view_toolbar, False, True, 3)

        # box_listview
        self.box_view_list = Gtk.HBox(spacing=0)
        self.box_view.pack_end(self.box_view_list, True, True, 3)

        # self.create_view_toolbar()
        self.create_view_list()

    def get_widget(self):
        """ retourne le contaiener de la vue toolbar + list """
        return self.box_view

    def init_widget(self):
        """ Initialisation des objets """
        # self.label_select.hide()
        # self.button_edit.hide()
        # self.button_delete.hide()
        # self.crud.remove_all_selection()
        # self.search_entry.hide()

    def create_view_toolbar(self):
        """ Footer pour afficher des infos et le bouton pour ajouter des éléments """
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.connect("search-changed", self.on_search_changed)
        self.box_view_toolbar.pack_start(self.search_entry, False, True, 3)
        if self.crud.get_view_prop("filter", "") != "":
            self.search_entry.set_text(self.crud.get_view_prop("filter"))
        self.search_entry.grab_focus()

        self.box_view_toolbar_select = Gtk.HBox()
        self.button_delete = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_REMOVE))
        self.button_delete.connect("clicked", self.on_button_delete_clicked)
        self.button_delete.set_tooltip_text("Supprimer la sélection")
        self.box_view_toolbar_select.pack_end(self.button_delete, False, True, 3)
        self.button_edit = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_EDIT))
        self.button_edit.connect("clicked", self.on_button_edit_clicked)
        self.button_edit.set_tooltip_text("Editer le sélection...")
        self.box_view_toolbar_select.pack_end(self.button_edit, False, True, 3)
        self.label_select = Gtk.Label("0 sélection")
        self.box_view_toolbar_select.pack_end(self.label_select, False, True, 3)
        self.label_select.hide()
        self.button_edit.hide()
        self.button_delete.hide()

        if self.crud.get_view_prop("form_add", "") != "":
            # Affichage du bouton d'ajout si formulaire d'ajout présent
            self.button_add = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_ADD))
            self.button_add.connect("clicked", self.on_button_add_clicked)
            self.button_add.set_tooltip_text("Créer un nouvel enregistrement...")
            self.box_view_toolbar.pack_end(self.button_add, False, True, 3)

        self.box_view_toolbar.pack_end(self.box_view_toolbar_select, False, True, 3)

    def create_view_list(self):
        """ Création de la vue """
        self.scroll_window = Gtk.ScrolledWindow() # La scrollwindow va contenir la treeview
        self.scroll_window.set_hexpand(True)
        self.scroll_window.set_vexpand(True)
        self.box_view_list.pack_end(self.scroll_window, True, True, 3)

        self.create_liststore()
        self.create_treeview()

    def create_treeview(self):
        """ Création/mise à jour de la treeview associée au liststore """
        # Treview sort and filter
        self.current_filter = None
        #Creating the filter, feeding it with the liststore model
        self.store_filter = self.liststore.filter_new()
        #setting the filter function, note that we're not using the
        self.store_filter.set_visible_func(self.filter_func)
        self.store_filter_sort = Gtk.TreeModelSort(self.store_filter)

        self.treeview = Gtk.TreeView.new_with_model(self.store_filter_sort)

        col_id = 0
        # la 1ére colonne contiendra le n° de ligne row_id
        self.crud.set_view_prop("col_row_id", col_id)
        col_id += 1
        for element in self.crud.get_view_elements():
            crudel = self.crud.get_column_prop(element, "crudel")

            # colonnes crudel
            col_id = crudel.add_tree_view_column(self.treeview, col_id)

            # mémorisation de la clé dans le crud
            if element == self.crud.get_table_prop("key"):
                self.crud.set_view_prop("key_id", col_id)
            # mémorisation du n° de la ligne
            self.crud.set_column_prop(element, "col_id", col_id)

            col_id += 1

        # ajout de la colonne action
        if self.crud.get_view_prop("deletable", False)\
            or self.crud.get_view_prop("form_edit", None) is not None :
            self.crud.set_view_prop("col_action_id", col_id)
            renderer_action_id = Gtk.CellRendererToggle()
            renderer_action_id.connect("toggled", self.on_action_toggle)
            tvc = Gtk.TreeViewColumn("Action", renderer_action_id, active=col_id)
            self.treeview.append_column(tvc)
            col_id += 1
        # ajout d'une dernière colonne
        # afin que la dernière colonne ne prenne pas tous le reste de la largeur
        # tvc = Gtk.TreeViewColumn("", Gtk.CellRendererText(), text=col_id)
        # self.treeview.append_column(tvc)
        # Connection aux événement changement de ligne sélectionnée
        self.select = self.treeview.get_selection()
        self.select.connect("changed", self.on_tree_selection_changed)

        # Connection au double-clic sur une ligne
        self.treeview.connect("row-activated", self.on_row_actived)

        self.scroll_window.add(self.treeview)
        self.scroll_window.show_all()

    def create_liststore(self):
        """ Création de la structure du liststore à partir du dictionnaire des données """
        col_store_types = []
        # 1ère colonne row_id
        col_store_types.append(GObject.TYPE_INT)
        for element in self.crud.get_view_elements():
            # Création du crudel
            crudel = Crudel(self.app_window, self.parent, self.crud, element, Crudel.CRUD_PARENT_VIEW)
            self.crud.set_column_prop(element, "crudel", crudel)

            # colonnes techniques color et sortable
            if crudel.get_sql_color() != "":
                col_store_types.append(GObject.TYPE_STRING)
            if crudel.is_sortable():
                col_store_types.append(crudel.get_type_gdk())
            # colonnes crudel
            col_store_types.append(crudel.get_type_gdk())

        # col_action_id
        if self.crud.get_view_prop("deletable", False)\
            or self.crud.get_view_prop("form_edit", None) is not None :
            col_store_types.append(GObject.TYPE_BOOLEAN)
        # dernière colonne vide
        col_store_types.append(GObject.TYPE_STRING)

        self.liststore = Gtk.ListStore(*col_store_types)
        # print "col_store_types", col_store_types

        self.update_liststore()

    def update_liststore(self):
        """ Mise à jour du liststore en relisant la table """
        # Génération du select de la table

        sql = "SELECT "
        b_first = True
        for element in self.crud.get_view_elements():
            crudel = self.crud.get_column_prop(element, "crudel")
            if crudel.is_virtual():
                continue
            if crudel.get_type() == "jointure":
                continue
            if b_first:
                b_first = False
            else:
                sql += ", "
            # colonnes techniques
            if crudel.get_sql_color() != "":
                sql += crudel.get_sql_color() + " as " + element + "_color"
                sql += ", "
            # colonnes affichées
            if crudel.get_sql_get() == "":
                sql += self.crud.get_table_id() + "." + element
            else:
                sql += crudel.get_sql_get() + " as " + element
        # ajout des colonnes de jointure
        for element in self.crud.get_view_elements():
            crudel = self.crud.get_column_prop(element, "crudel")
            if crudel.get_type() == "jointure":
                sql += ", " + crudel.get_jointure_columns()
        sql += " FROM " + self.crud.get_table_id()
        # ajout des tables de jointure
        for element in self.crud.get_view_elements():
            crudel = self.crud.get_column_prop(element, "crudel")
            if crudel.get_type() == "jointure":
                sql += " " + crudel.get_jointure_join()

        # ajout du where
        where = ""
        if self.crud.get_view_prop("sql_where") != "":
            where = self.crud.get_view_prop("sql_where")

        # Ajout du sql_where de la rubrique
        # chargement des paramètres avec les éléments du formulaire appelant
        params = {}
        params = self.crudel.crud.get_form_values(params)
        # remplacement des variables de l'ordre sql_where de la rubrique appelante
        sql_where = ""
        if self.crudel.get_sql_where() != "":
            sql_where = self.crud.replace_from_dict(self.crudel.get_sql_where(), params)
        if sql_where != "":
            if where != "":
                where = "(" + where + ") AND (" + sql_where + ")"
            else:
                where = sql_where

        sql += " WHERE " + where
        sql += " LIMIT 2000"

        # print sql
        rows = self.crud.sql_to_dict(self.crud.get_table_prop("basename"), sql, {})
        # print rows
        self.liststore.clear()
        row_id = 0
        for row in rows:
            store = []
            # print row
            # 1ère colonne col_row_id
            store.append(row_id)
            for element in self.crud.get_view_elements():
                crudel = self.crud.get_column_prop(element, "crudel")
                if crudel.is_virtual():
                    continue
                # Mémorisation dans crudel value
                crudel.set_value_sql(row[element])
                # colonnes techniques
                if crudel.get_sql_color() != "":
                    store.append(row[element + "_color"])
                if crudel.is_sortable():
                    store.append(crudel.get_value())
                # colonnes crudel
                display = crudel.get_display()
                # print element, display
                store.append(display)
            # col_action_id
            if self.crud.get_view_prop("deletable", False)\
                or self.crud.get_view_prop("form_edit", None) is not None:
                store.append(False)
            # dernière colonne vide
            store.append("")
            # print "store", store
            self.liststore.append(store)
            row_id += 1

        # suppression de la sélection
        # self.label_select.hide()
        # self.button_edit.hide()
        # self.button_delete.hide()

    def filter_func(self, model, iter, data):
        """Tests if the text in the row is the one in the filter"""
        if self.current_filter is None or self.current_filter == "":
            return True
        else:
            bret = False
            for element in self.crud.get_view_elements():
                crudel = self.crud.get_column_prop(element, "crudel")
                if crudel.is_searchable():
                    if re.search(self.current_filter,\
                                 model[iter][self.crud.get_column_prop(element, "col_id")],\
                                 re.IGNORECASE):
                        bret = True
            return bret

    def on_button_add_clicked(self, widget):
        """ Ajout d'un élément """
        self.crud.set_form_id(self.crud.get_view_prop("form_add"))
        self.crud.set_key_value(None)
        self.crud.set_action("create")
        # dialog = CrudForm(self.parent, self.crud)
        # response = dialog.run()
        # if response == Gtk.ResponseType.OK:
        #     # print("The Ok button was clicked")
        #     # les données ont été modifiées, il faut actualiser la vue
        #     self.update_liststore()
        # elif response == Gtk.ResponseType.CANCEL:
        #     # print("The Cancel button was clicked")
        #     pass
        # dialog.destroy()

    def on_button_edit_clicked(self, widget):
        """ Edition de l'élément sélectionné"""
        print "Edition de", self.crud.get_selection()[0]
        self.crud.set_key_value(self.crud.get_selection()[0])
        self.crud.set_form_id(self.crud.get_view_prop("form_edit"))
        self.crud.set_action("update")
        # dialog = CrudForm(self.parent, self.crud)
        # response = dialog.run()
        # if response == Gtk.ResponseType.OK:
        #     # print("The Ok button was clicked")
        #     self.update_liststore()
        # elif response == Gtk.ResponseType.CANCEL:
        #     # print("The Cancel button was clicked")
        #     pass
        # dialog.destroy()

    def on_button_delete_clicked(self, widget):
        """ Suppression des éléments sélectionnés """
        print "Suppression de ", self.crud.get_selection()
        dialog = Gtk.MessageDialog(parent=self.parent,\
            flags=Gtk.DialogFlags.MODAL,\
            type=Gtk.MessageType.WARNING,\
            buttons=Gtk.ButtonsType.OK_CANCEL,\
            message_format="Confirmez-vous la suppression de\n{}".format(" ".join(str(self.crud.get_selection()))))

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            for key_value in self.crud.get_selection():
                self.crud.sql_delete_record(key_value)

            self.update_liststore()

        dialog.destroy()

    def on_search_changed(self, widget):
        """ Recherche d'éléments dans la vue """
        if len(self.search_entry.get_text()) == 1:
            return
        self.current_filter = self.search_entry.get_text()
        # mémorisation du filtre dans la vue
        self.crud.set_view_prop("filter", self.current_filter)
        self.store_filter.refilter()

    def on_action_toggle(self, cell, path):
        """ Clic sur coche d'action"""
        # print "Action sur", self.store_filter_sort[path][self.crud.get_view_prop("key_id")]
        key_id = self.store_filter_sort[path][self.crud.get_view_prop("key_id")]
        row_id = self.store_filter_sort[path][self.crud.get_view_prop("col_row_id")]
        if self.liststore[row_id][self.crud.get_view_prop("col_action_id")]:
            self.crud.remove_selection(key_id)
        else:
            self.crud.add_selection(key_id)
        qselect = len(self.crud.get_selection())
        if qselect > 1:
            self.label_select.set_markup("({}) sélections".format(qselect))
            self.label_select.show()
            self.button_edit.hide()
            if self.crud.get_view_prop("deletable", False):
                self.button_delete.show()
        elif qselect == 1:
            self.label_select.set_markup("{}".format(key_id))
            self.label_select.show()
            if self.crud.get_view_prop("form_edit", None) is not None:
                self.button_edit.show()
            if self.crud.get_view_prop("deletable", False):
                self.button_delete.show()
        else:
            self.label_select.hide()
            self.button_edit.hide()
            self.button_delete.hide()

        self.liststore[row_id][self.crud.get_view_prop("col_action_id")]\
            = not self.liststore[row_id][self.crud.get_view_prop("col_action_id")]

    def on_tree_selection_changed(self, selection):
        """ Sélection d'une ligne """
        model, self.treeiter_selected = selection.get_selected()
        # if self.treeiter_selected:
        #     print "Select", self.store_filter_sort[self.treeiter_selected][self.crud.get_view_prop("key_id")]

    def on_row_actived(self, widget, row, col):
        """ Double clic sur une ligne """
        # print "Activation", widget.get_model()[row][self.crud.get_view_prop("key_id")]
        self.crud.set_key_value(widget.get_model()[row][self.crud.get_view_prop("key_id")])
        if self.crud.get_view_prop("form_edit", None) is not None:
            self.crud.set_form_id(self.crud.get_view_prop("form_edit"))
            self.crud.set_action("update")
            dialog = CrudForm(self.parent, self.crud)
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                # print("The Ok button was clicked")
                self.update_liststore()
            elif response == Gtk.ResponseType.CANCEL:
                # print("The Cancel button was clicked")
                pass
            dialog.destroy()
