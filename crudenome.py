#!/usr/bin/env python
# -*- coding:Utf-8 -*-
# http://python-gtk-3-tutorial.readthedocs.io/en/latest/index.html
# https://gtk.developpez.com/doc/fr/gtk/gtk-Stock-Items.html
# from __future__ import unicode_literals
import sys
from crud import Crud
from crudform import CrudForm
from crudview import CrudView
import crudconst as const
import re

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, Gio, GObject

class AppWindow(Gtk.ApplicationWindow):
    """ La fenêtre principale du Gtk """
    def __init__(self, app, crud):
        Gtk.Window.__init__(self, title="Welcome to CRUDENOME", application=app)

        # Chargement des paramètres
        self.crud = Crud(crud)

        # Initialisation des variables globales
        self.treeview = None
        self.liststore = None
        self.current_filter = None
        self.store_filter = None
        self.store_filter_sort = None
        self.footerbar = None
        self.search_entry = None
        self.scroll_window = None
        self.select = None
        self.box_view_toolbar_select = None
        self.button_home = None
        self.button_add = None
        self.button_edit = None
        self.button_delete = None
        self.label_select = None

        self.set_title(self.crud.config["name"])
        self.activate_focus()
        self.set_border_width(10)
        self.set_default_size(1200, 600)
        self.set_icon_from_file(self.crud.config["logo"])

        # layout
        self.layout_type = const.LAYOUT_MENU
        self.box_one = Gtk.VBox(spacing=0) # box_application footerbar

        # box_application
        self.box_application = Gtk.HBox(spacing=0) # box_application_menu ou box_sidebar box_view
        self.box_one.pack_start(self.box_application, False, True, 0)

        # box_footerbar
        self.footerbar = Gtk.HBox(spacing=0)
        self.box_one.pack_end(self.footerbar, False, True, 3)

        # box_menu
        self.box_application_menu = Gtk.HBox(spacing=0)
        self.box_application.pack_start(self.box_application_menu, False, True, 0)

        # box_toolbar_home
        self.box_toolbar_home = Gtk.HBox(spacing=0)

        # box_toolbar_sidebar
        self.box_toolbar_view = Gtk.HBox(spacing=0)

        # box_toolbar_right
        self.box_toolbar_right = Gtk.HBox(spacing=0)

        # box_view_sidebar
        self.box_view_sidebar = Gtk.VBox(spacing=0)
        self.box_application.pack_start(self.box_view_sidebar, False, True, 0)

        # box_view
        self.box_view = Gtk.VBox(spacing=0) # box_viewbar box_listview
        self.box_application.pack_end(self.box_view, False, True, 3)

        # box_viewbar
        self.box_view_toolbar = Gtk.HBox(spacing=0)
        self.box_view.pack_start(self.box_view_toolbar, False, True, 3)
        # box_listview
        self.box_view_list = Gtk.HBox(spacing=0)
        self.box_view.pack_end(self.box_view_list, True, True, 3)

        self.add(self.box_one)

        self.create_application_menu()
        self.create_toolbar()
        self.create_footerbar()

        self.display_layout()

        self.show_all()

    def display_layout(self):
        """ Affichage du layout """
        if self.layout_type == const.LAYOUT_MENU:
            for widget in self.box_toolbar_view.get_children():
                Gtk.Widget.destroy(widget)
            for widget in self.box_view_sidebar.get_children():
                Gtk.Widget.destroy(widget)
            for widget in self.box_view_toolbar.get_children():
                Gtk.Widget.destroy(widget)
            for widget in self.box_view_list.get_children():
                Gtk.Widget.destroy(widget)
            self.headerbar.props.title = self.crud.config["title"]
        elif self.layout_type == const.LAYOUT_VIEW_H:
            for widget in self.box_application_menu.get_children():
                Gtk.Widget.destroy(widget)
            for widget in self.box_view_sidebar.get_children():
                Gtk.Widget.destroy(widget)
            self.box_view.show()
            self.headerbar.props.title = self.crud.get_application_prop("title")
            self.box_toolbar_right.show()
        elif self.layout_type == const.LAYOUT_VIEW_V:
            for widget in self.box_application_menu.get_children():
                Gtk.Widget.destroy(widget)
            for widget in self.box_view_toolbar.get_children():
                Gtk.Widget.destroy(widget)
            self.headerbar.props.title = self.crud.get_application_prop("title")

    def display(self, msg):
        """ Affichage de message dans la fenêtre des traces """
        print msg

    def create_application_menu(self):
        """ menu des applications """
        file_list = self.crud.directory_list(self.crud.config["application_directory"])
        for application_file in file_list:
            application = self.crud.get_json_content(self.crud.config["application_directory"] + "/" + application_file)
            self.crud.set_application(application)
            button = Gtk.Button(self.crud.get_application_prop("title"))
            button.connect("clicked", self.on_button_application_clicked, application_file)
            self.box_application_menu.pack_start(button, True, True, 3)

    def create_toolbar(self):
        """ Toolbar avec la recherche et les boutons pour afficher les vues """
        self.headerbar = Gtk.HeaderBar()
        self.headerbar.set_show_close_button(True)
        self.headerbar.props.title = self.crud.config["title"]
        self.set_titlebar(self.headerbar)

        self.button_home = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_HOME))
        self.button_home.set_tooltip_text("Retour au menu général")
        self.button_home.connect("clicked", self.on_button_home_clicked)
        self.headerbar.pack_start(self.button_home)

        self.headerbar.pack_start(self.box_toolbar_view)

    def create_footerbar(self):
        """ Footer pour afficher des infos et le bouton pour ajouter des éléments """
        footer_label = Gtk.Label()
        footer_label.set_markup("<sub>Développé avec {} {} {}</sub>".format(self.crud.config["title"],
                                self.crud.config["version"], self.crud.config["copyright"]))
        self.footerbar.pack_start(footer_label, False, True, 3)

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

    def create_view_sidebar(self):
        """ Création des boutons d'activation des vues de l'application """
        table_first = None
        view_first = None
        for table_id in self.crud.get_application_tables():
            self.crud.set_table_id(table_id)
            if table_first is None:
                table_first = table_id
            for view_id in self.crud.get_table_views():
                self.crud.set_view_id(view_id)
                if view_first is None:
                    view_first = view_id
                # les boutons sont ajoutés dans le dictionnaire de la vue
                self.crud.set_view_prop("button", Gtk.Button(self.crud.get_view_prop("title")))
                self.crud.get_view_prop("button").connect("clicked",
                                                          self.on_button_view_clicked,
                                                          table_id, view_id)
                if self.crud.get_application_prop("menu_orientation") == "horizontal":
                    self.box_toolbar_view.pack_start(self.crud.get_view_prop("button"),
                                                     False, False, 3)
                if self.crud.get_application_prop("menu_orientation") == "vertical":
                    self.box_view_sidebar.pack_start(self.crud.get_view_prop("button"),
                                                     False, False, 3)

        # mise en relief du bouton vue courante
        self.crud.set_table_id(table_first)
        self.crud.set_view_id(view_first)
        self.crud.set_key_id(self.crud.get_table_prop("key"))
        self.crud.get_view_prop("button").get_style_context().add_class('button_selected')

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
        # la colonne qui contiendra le n° de ligne row_id
        self.crud.set_view_prop("col_row_id", col_id)
        renderer_col_id = Gtk.CellRendererText()
        renderer_col_id.set_property('xalign', 1.0)
        tvc = Gtk.TreeViewColumn("id", renderer_col_id, text=col_id)
        tvc.set_visible(False)
        self.treeview.append_column(tvc)
        col_id += 1
        for element in self.crud.get_view_elements():
            # renderer
            renderer = None
            if self.crud.get_column_prop(element, "type") == "check":
                renderer = Gtk.CellRendererToggle()
            elif self.crud.get_column_prop(element, "type") == "int":
                renderer = Gtk.CellRendererText()
                renderer.set_property('xalign', 1.0)
            else:
                renderer = Gtk.CellRendererText()
            # alignement
            if self.crud.get_column_prop(element, "col_align") == "left":
                renderer.set_property('xalign', 0.1)
            elif self.crud.get_column_prop(element, "col_align") == "right":
                renderer.set_property('xalign', 1.0)
            elif self.crud.get_column_prop(element, "col_align") == "center":
                renderer.set_property('xalign', 0.5)
            # colonnes techniques
            col_sortable_id = None
            col_color_id = None
            if self.crud.get_column_prop(element, "sql_color", "") != "":
                tvc = Gtk.TreeViewColumn(element + "_color", Gtk.CellRendererText(), text=col_id)
                tvc.set_visible(False)
                self.treeview.append_column(tvc)
                col_color_id = col_id
                col_id += 1
            if self.crud.get_column_prop(element, "sortable", "") != "":
                tvc = Gtk.TreeViewColumn(element + "_sortable", Gtk.CellRendererText(), text=col_id)
                tvc.set_visible(False)
                self.treeview.append_column(tvc)
                col_sortable_id = col_id
                col_id += 1

            # colonnes affichées
            if self.crud.get_column_prop(element, "type") == "check":
                tvc = Gtk.TreeViewColumn(self.crud.get_column_prop(element, "label_short")\
                    , renderer, active=col_id)
            else:
                tvc = Gtk.TreeViewColumn(self.crud.get_column_prop(element, "label_short")\
                    , renderer, text=col_id)
            if col_sortable_id:
                tvc.set_sort_column_id(col_sortable_id)
            if col_color_id:
                tvc.add_attribute(renderer, "foreground", col_color_id)
            # comportement
            if self.crud.get_column_prop(element, "col_width", 0) > 0:
                tvc.set_min_width(self.crud.get_column_prop(element, "col_width"))
            # mémorisation
            if element == self.crud.get_table_prop("key"):
                self.crud.set_view_prop("key_id", col_id)
            self.crud.set_column_prop(element, "col_id", col_id)

            self.treeview.append_column(tvc)
            col_id += 1

        # colonne action
        if self.crud.get_view_prop("deletable", False) or self.crud.get_view_prop("form_edit", None) :
            self.crud.set_view_prop("col_action_id", col_id)
            renderer_action_id = Gtk.CellRendererToggle()
            renderer_action_id.connect("toggled", self.on_action_toggle)
            tvc = Gtk.TreeViewColumn("Action", renderer_action_id, active=col_id)
            self.treeview.append_column(tvc)
            col_id += 1
        # dernière colonne vide
        tvc = Gtk.TreeViewColumn("", Gtk.CellRendererText(), text=col_id)
        self.treeview.append_column(tvc)

        self.select = self.treeview.get_selection()
        self.select.connect("changed", self.on_tree_selection_changed)

        self.treeview.connect("row-activated", self.on_row_actived)

        self.scroll_window.add(self.treeview)
        self.scroll_window.show_all()

    def create_liststore(self):
        """ Création de la structure du liststore à partir du dictionnaire des données """
        col_store_types = []
        # col_row_id
        col_store_types.append(const.GOBJECT_TYPE["int"])

        for element in self.crud.get_view_elements():
            # colonnes techniques non affichées
            if self.crud.get_column_prop(element, "sql_color", "") != "":
                col_store_types.append(GObject.TYPE_STRING)
            if self.crud.get_column_prop(element, "sortable", "") != "":
                col_store_types.append(const.GOBJECT_TYPE[self.crud.get_element_prop(element, "type")])
            # colonnes affichées
            if self.crud.get_column_prop(element, "format", "") == "":
                col_store_types.append(const.GOBJECT_TYPE[self.crud.get_element_prop(element, "type")])
            else:
                col_store_types.append(GObject.TYPE_STRING)

        # col_action_id
        if self.crud.get_view_prop("deletable", False) or self.crud.get_view_prop("form_edit", None) :
            col_store_types.append(const.GOBJECT_TYPE["check"])
        # dernière colonne vide
        col_store_types.append(const.GOBJECT_TYPE["text"])
        self.liststore = Gtk.ListStore(*col_store_types)

        self.update_liststore()

    def update_liststore(self):
        """ Mise à jour du liststore en relisant la table """
        # Génération du select de la table

        sql = "SELECT "
        b_first = True
        for element in self.crud.get_view_elements():
            if element.startswith("_"):
                continue
            if self.crud.get_column_prop(element, "type") == "jointure":
                continue
            if b_first:
                b_first = False
            else:
                sql += ", "
            # colonnes techniques
            if self.crud.get_column_prop(element, "sql_color", "") != "":
                sql += self.crud.get_column_prop(element, "sql_color") + " as " + element + "_color"
                sql += ", "
            if self.crud.get_column_prop(element, "sortable", "") != "":
                sql += self.crud.get_table_id() + "." + element + " as " + element + "_sortable"
                sql += ", "
            # colonnes affichées
            if self.crud.get_column_prop(element, "sql_get", "") == "":
                sql += self.crud.get_table_id() + "." + element
            else:
                sql += self.crud.get_column_prop(element, "sql_get", "") + " as " + element
        # ajout des colonnes de jointure
        for element in self.crud.get_view_elements():
            if self.crud.get_column_prop(element, "type") == "jointure":
                sql += ", " + self.crud.get_column_prop(element, "jointure_columns")
        sql += " FROM " + self.crud.get_table_id()
        # ajout des tables de jointure
        for element in self.crud.get_view_elements():
            if self.crud.get_column_prop(element, "type") == "jointure":
                sql += " " + self.crud.get_column_prop(element, "jointure_join")
        if self.crud.get_view_prop("sql_where"):
            sql += " WHERE " + self.crud.get_view_prop("sql_where")
        sql += " LIMIT 2000"
        # print sql
        rows = self.crud.sql_to_dict(self.crud.get_table_prop("basename"), sql, self.crud.ctx)
        # print rows
        self.liststore.clear()
        row_id = 0
        for row in rows:
            store = []
            # col_row_id
            store.append(row_id)
            for element in self.crud.get_view_elements():
                # print element, row
                # colonnes techniques
                if self.crud.get_column_prop(element, "sql_color", "") != "":
                    store.append(row[element + "_color"])
                if self.crud.get_column_prop(element, "sortable", "") != "":
                    store.append(row[element + "_sortable"])
                # colonnes affichées
                display = self.crud.get_column_prop(element, "format", "")
                if display == "":
                    if self.crud.get_column_prop(element, "type", "text") in ("text", "date", "jointure"):
                        store.append(str(row[element].encode("utf-8")))
                    else:
                        store.append(row[element])
                else:
                    store.append(display.format(row[element]))
            # col_action_id
            if self.crud.get_view_prop("deletable", False) or self.crud.get_view_prop("form_edit", None):
                store.append(False)
            # dernière colonne vide
            store.append("")
            self.liststore.append(store)
            row_id += 1
        # suppression de la sélection
        self.label_select.hide()
        self.button_edit.hide()
        self.button_delete.hide()
        

    def filter_func(self, model, iter, data):
        """Tests if the text in the row is the one in the filter"""
        if self.current_filter is None or self.current_filter == "":
            return True
        else:
            bret = False
            for element in self.crud.get_view_elements():
                if self.crud.get_column_prop(element, "searchable", False):
                    if re.search(self.current_filter,\
                                 model[iter][self.crud.get_column_prop(element, "col_id")],\
                                 re.IGNORECASE):
                        bret = True
            return bret

    def on_button_application_clicked(self, widget, application_file):
        """ Activation d'une application """
        application = self.crud.get_json_content(
            self.crud.config["application_directory"] + "/" + application_file)
        self.crud.set_application(application)
        if self.crud.get_application_prop("menu_orientation", "horizontal") == "horizontal":
            self.layout_type = const.LAYOUT_VIEW_H
        else:
            self.layout_type = const.LAYOUT_VIEW_V
        self.display_layout()

        self.create_view_sidebar()
        self.create_view_toolbar()
        self.create_view_list()

        self.show_all()
        self.label_select.hide()
        self.button_edit.hide()
        self.button_delete.hide()
        self.crud.remove_all_selection()

    def on_button_home_clicked(self, widget):
        """ Retour au menu général """
        self.layout_type = const.LAYOUT_MENU
        self.create_application_menu()
        self.display_layout()
        self.show_all()

    def on_button_view_clicked(self, widget, table_id, view_id):
        """ Activation d'une vue """
        self.crud.get_view_prop("button").get_style_context().remove_class('button_selected')

        self.crud.set_table_id(table_id)
        self.crud.set_view_id(view_id)
        self.crud.set_key_id(self.crud.get_table_prop("key"))
        self.crud.get_view_prop("button").get_style_context().add_class('button_selected')
        for widget in self.box_view_toolbar.get_children():
            Gtk.Widget.destroy(widget)
        for widget in self.box_view_list.get_children():
            Gtk.Widget.destroy(widget)
        self.display_layout()

        self.create_view_toolbar()
        self.create_view_list()
        self.show_all()
        self.label_select.hide()
        self.button_edit.hide()
        self.button_delete.hide()
        self.crud.remove_all_selection()

    def on_button_add_clicked(self, widget):
        """ Ajout d'un élément """
        self.crud.set_form_id(self.crud.get_view_prop("form_add"))
        self.crud.set_key_value(None)
        self.crud.set_action("create")
        dialog = CrudForm(self, self.crud)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            # print("The Ok button was clicked")
            # les données ont été modifiées, il faut actualiser la vue
            self.update_liststore()
        elif response == Gtk.ResponseType.CANCEL:
            # print("The Cancel button was clicked")
            pass
        dialog.destroy()

    def on_button_edit_clicked(self, widget):
        """ Edition de l'élément sélectionné"""
        print "Edition de", self.crud.get_selection()[0]
        self.crud.set_key_value(self.crud.get_selection()[0])
        self.crud.set_form_id(self.crud.get_view_prop("form_edit"))
        self.crud.set_action("update")
        dialog = CrudForm(self, self.crud)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            # print("The Ok button was clicked")
            self.update_liststore()
        elif response == Gtk.ResponseType.CANCEL:
            # print("The Cancel button was clicked")
            pass
        dialog.destroy()

    def on_button_delete_clicked(self, widget):
        """ Suppression des éléments sélectionnés """
        # print "Suppression de ", self.crud.get_selection()
        dialog = Gtk.MessageDialog(parent=self,\
            flags=Gtk.DialogFlags.MODAL,\
            type=Gtk.MessageType.WARNING,\
            buttons=Gtk.ButtonsType.OK_CANCEL,\
            message_format="Confirmez-vous la suppression de\n{}".format(" ".join(self.crud.get_selection())))

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
            if self.crud.get_view_prop("form_edit", None):
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
            dialog = CrudForm(self, self.crud)
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                # print("The Ok button was clicked")
                self.update_liststore()
            elif response == Gtk.ResponseType.CANCEL:
                # print("The Cancel button was clicked")
                pass
            dialog.destroy()

class Application(Gtk.Application):
    """ La classe principale d'une application Gnome """

    def __init__(self):
        """
        constructor of the Gtk Application
        create and activate a MyWindow, with self (the MyApplication) as
        application the window belongs to.
        Note that the function in C activate() becomes do_activate() in Python
        """
        Gtk.Application.__init__(self)

        self.window = None

        # Chargement des paramètres
        self.crud = Crud()

    def do_activate(self):
        """
        show the window and all its content
        this line could go in the constructor of MyWindow as well
        self.win.show_all()
        """
        if not self.window:
            # Windows are associated with the application
            # when the last one is closed the application shuts down
            self.window = AppWindow(self, self.crud)

    def do_startup(self):
        """
        Start up the application
        Note that the function in C startup() becomes do_startup() in Python
        """
        Gtk.Application.do_startup(self)

        # create a menu (a Gio.Menu)
        menu = Gio.Menu()

        menu.append("Préférences", "app.preference")

        # append a menu item with label "About" and action "app.about"
        menu.append("About", "app.about")
        # append a menu item with label "Quit" and action "app.quit"
        menu.append("Quit", "app.quit")
        # set menu as the menu for the application
        self.set_app_menu(menu)

        # a new simpleaction - for the application
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.on_quit)
        self.add_action(quit_action)

        # a new simpleaction - for the application
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about)
        self.add_action(about_action)

        preference_action = Gio.SimpleAction.new("preference", None)
        preference_action.connect("activate", self.on_preference)
        self.add_action(preference_action)

    def on_about(self, action, param):
        """
        La fenêtre Au sujet de...
        """
        about = Gtk.AboutDialog()
        about.set_transient_for(self.window)
        about.set_title(self.crud.config["title"])
        about.set_program_name(self.crud.config["name"])
        about.set_version(self.crud.config["version"])
        about.set_copyright(self.crud.config["copyright"])
        about.set_comments(self.crud.config["comments"])
        about.set_website(self.crud.config["web_site"])
        about.set_logo(GdkPixbuf.Pixbuf.new_from_file(self.crud.config["logo"]))
        with open('LICENSE', 'r') as file:
            about.set_license(file.read())
        about.connect("response", lambda d, r: d.destroy())
        about.show()

    def on_preference(self, action, param):
        """
        Paramétrage de l'application
        """
        print "on_preference"

    def on_quit(self, action, param):
        """
        Fin de l'application
        """
        self.quit()

# get the style from the css file and apply it
style_provider = Gtk.CssProvider()
style_provider.load_from_path('style.css')
Gtk.StyleContext.add_provider_for_screen(
    Gdk.Screen.get_default(),
    style_provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

myapp = Application()
exit_status = myapp.run(sys.argv)
sys.exit(exit_status)
