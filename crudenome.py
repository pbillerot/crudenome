#!/usr/bin/env python
# -*- coding:Utf-8 -*-
# http://python-gtk-3-tutorial.readthedocs.io/en/latest/index.html
# https://gtk.developpez.com/doc/fr/gtk/gtk-Stock-Items.html
import sys
from pprint import pprint
from crud import Ctx, Crud, NumberEntry
from cruddlg import FormDlg
import crudconst as const
import collections
import re

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, Gio

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
        self.button_add = None

        self.set_title(self.crud.config["name"])
        self.activate_focus()
        self.set_border_width(10)
        self.set_default_size(1200, 600)
        self.set_icon_from_file(self.crud.config["logo"])

        self.vbox = Gtk.VBox(spacing=3)
        self.add(self.vbox)

        self.create_scroll_window()
        self.create_toolbar()
        self.create_footerbar()
        self.create_view()

        self.show_all()

        self.search_entry.grab_focus()

    def display(self, msg):
        """ Affichage de message dans la fenêtre des traces """
        print msg

    def create_footerbar(self):
        """ Footer pour afficher des infos et le bouton pour ajouter des éléments """
        self.footerbar = Gtk.HBox()
        self.button_add = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_ADD))
        self.button_add.connect("clicked", self.on_button_add_clicked)
        self.footerbar.pack_end(self.button_add, False, True, 3)
        self.button_add.hide()
        self.vbox.pack_end(self.footerbar, False, True, 0)

    def create_toolbar(self):
        """ Toolbar avec la recherche et les boutons pour afficher les vues """
        self.headerbar = Gtk.HeaderBar()
        self.headerbar.set_show_close_button(True)
        self.headerbar.props.title = self.crud.config["title"]
        self.set_titlebar(self.headerbar)

        # CREATION DES BOUTONS DES VUES
        hbox_button = Gtk.HBox() # box qui permet d'inverser l'ordre de présentation des boutons
        # Lecture des fichiers d'application
        file_list = self.crud.directory_list(self.crud.config["application_directory"])
        table_first = None
        view_first = None
        for application_file in file_list:
            application_store = self.crud.get_json_content(
                self.crud.config["application_directory"] + "/" + application_file)
            self.crud.tables = application_store["tables"]
            for table_id in self.crud.tables:
                self.crud.table_id = table_id
                if table_first is None:
                    table_first = table_id
                for view_id in self.crud.tables[table_id]["views"]:
                    self.crud.view_id = view_id
                    if view_first is None:
                        view_first = view_id
                    # les boutons sont ajoutés dans le dictionnaire de la vue
                    self.crud.set_vue_prop("button", Gtk.Button(self.crud.get_vue_prop("title")))
                    self.crud.get_vue_prop("button").connect("clicked",
                                                             self.on_button_view_clicked,
                                                             table_id, view_id)
                    hbox_button.pack_start(self.crud.get_vue_prop("button"), False, False, 5)

        # mise en relief du bouton vue courante
        self.crud.table_id = table_first
        self.crud.view_id = view_first
        self.crud.get_vue_prop("button").get_style_context().add_class('button_selected')

        self.headerbar.pack_start(hbox_button)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.connect("search-changed", self.on_search_changed)

        self.headerbar.pack_end(self.search_entry)

    def create_scroll_window(self):
        """ Création du container de la vue à afficher """
        # La scrollwindow va contenir la treeview
        self.scroll_window = Gtk.ScrolledWindow()
        self.scroll_window.set_hexpand(True)
        self.scroll_window.set_vexpand(True)

        # print "1", self.scroll_window
        self.vbox.pack_start(self.scroll_window, True, True, 3)

    def create_view(self):
        """ Création de la vue """
        # Affichage du bouton d'ajout si formulaire d'ajout présent
        self.crud.form_id = self.crud.get_vue_prop("form_add", "")
        if self.crud.form_id == "":
            self.button_add.hide()
        else:
            self.button_add.set_tooltip_text(self.crud.get_formulaire_prop("title"))
            self.button_add.show()

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

        if self.treeview is not None:
            self.scroll_window.remove(self.treeview)

        self.treeview = Gtk.TreeView.new_with_model(self.store_filter_sort)

        # CellRenderers
        textleft = Gtk.CellRendererText()
        textright = Gtk.CellRendererText()
        textright.set_property('xalign', 1.0)
        textcenter = Gtk.CellRendererText()
        textcenter.set_property('xalign', 0.5)
        icon_renderer = Gtk.CellRendererPixbuf()
        edit_toggle = Gtk.CellRendererToggle()
        edit_toggle.connect("toggled", self.on_edit_toggle)
        action_toggle = Gtk.CellRendererToggle()
        action_toggle.connect("toggled", self.on_action_toggle)

        col_id = 0
        # la colonne qui contiendra le n° de ligne row_id
        self.crud.set_vue_prop("col_row_id", col_id)
        tvc = Gtk.TreeViewColumn("id", textcenter, text=col_id)
        self.treeview.append_column(tvc)
        col_id += 1
        for element in self.crud.get_vue_elements():
            if self.crud.get_colonne_prop(element, "type") == "int":
                renderer = textright
            else:
                renderer = textleft
            tvc = Gtk.TreeViewColumn(self.crud.get_rubrique_prop(element, "label_short")\
                , renderer, text=col_id)
            if self.crud.get_colonne_prop(element, "sortable", False):
                tvc.set_sort_column_id(col_id)
            if element == self.crud.get_table_prop("key"):
                self.crud.set_vue_prop("key_id", col_id)
            if self.crud.get_colonne_prop(element, "expandable", False):
                tvc.set_expand(True)
            if self.crud.get_colonne_prop(element, "col_width", 0) > 0:
                tvc.set_min_width(self.crud.get_colonne_prop(element, "col_width"))
            self.crud.set_colonne_prop(element, "row_id", col_id)
            self.treeview.append_column(tvc)
            col_id += 1

        self.crud.set_vue_prop("col_action_id", col_id)
        tvc = Gtk.TreeViewColumn("Action", action_toggle, active=col_id)
        self.treeview.append_column(tvc)
        col_id += 1
        # dernière colonne vide
        tvc = Gtk.TreeViewColumn("", textleft, text=col_id)
        self.treeview.append_column(tvc)

        self.select = self.treeview.get_selection()
        self.select.connect("changed", self.on_tree_selection_changed)

        self.treeview.connect("row-activated", self.on_row_actived)

        # for col in self.treeview.get_columns():
        #     pprint(col.get_title())

        # print "2", self.scroll_window

        self.scroll_window.add(self.treeview)
        self.scroll_window.show_all()

    def create_liststore(self):
        """ Création de la structure du liststore à partir du dictionnaire des données """
        col_store_types = []
        # col_row_id
        col_store_types.append(const.GOBJECT_TYPE["int"])

        for element in self.crud.get_vue_elements():
            col_store_types.append(const.GOBJECT_TYPE[self.crud.get_rubrique_prop(element, "type")])

        # col_action_id
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
        id_row = 0
        for element in self.crud.get_vue_elements():
            if b_first:
                sql += element
                b_first = False
            else:
                sql += ", " + element
            id_row += 1

        sql += " FROM " + self.crud.table_id
        sql += " LIMIT 10 "
        rows = self.crud.sql_to_dict(self.crud.get_table_prop("basename"), sql, {})
        self.liststore.clear()
        row_id = 0
        for row in rows:
            store = []
            # col_row_id
            store.append(row_id)
            for element in self.crud.get_vue_elements():
                display = self.crud.get_colonne_prop(element, "format", "")
                if display == "":
                    store.append(row[element])
                else:
                    store.append(display.format(row[element]))
            # col_action_id
            store.append(False)
            # dernière colonne vide
            store.append("")
            self.liststore.append(store)
            row_id += 1

    def filter_func(self, model, iter, data):
        """Tests if the text in the row is the one in the filter"""
        if self.current_filter is None or self.current_filter == "":
            return True
        else:
            bret = False
            for element in self.crud.get_vue_elements():
                if self.crud.get_colonne_prop(element, "searchable", False):
                    if re.search(self.current_filter,
                                 model[iter][self.crud.get_colonne_prop(element, "row_id")],
                                 re.IGNORECASE):
                        bret = True
            return bret

    def on_button_view_clicked(self, widget, table_id, view_id):
        """ Activation d'une vue """
        self.crud.tables[self.crud.table_id]["views"][self.crud.view_id]["button"].get_style_context().remove_class('button_selected')

        self.crud.table_id = table_id
        self.crud.view_id = view_id
        self.crud.get_vue_prop("button").get_style_context().add_class('button_selected')
        self.create_view()

    def on_button_add_clicked(self, widget):
        """ Ajout d'un élément """
        print "on_button_add_clicked"
        self.crud.form_id = self.crud.get_vue_prop("form_add")

        dialog = FormDlg(self, self.crud)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            print("The Ok button was clicked")
        elif response == Gtk.ResponseType.CANCEL:
            print("The Cancel button was clicked")
        dialog.destroy()

    def on_search_changed(self, widget):
        """ Recherche d'éléments dans la vue """
        if len(self.search_entry.get_text()) == 1:
            return
        self.current_filter = self.search_entry.get_text()
        self.store_filter.refilter()

    def on_edit_toggle(self, cell, path):
        """ Edition de """
        print "Edit de", self.store_filter_sort[path][self.crud.get_vue_prop("key_id")]
        self.crud.key_value = self.store_filter_sort[path][self.crud.get_vue_prop("key_id")]
        self.crud.form_id = self.crud.get_vue_prop("form_edit")
        dialog = FormDlg(self, self.crud)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            print("The Ok button was clicked")
        elif response == Gtk.ResponseType.CANCEL:
            print("The Cancel button was clicked")
        dialog.destroy()

    def on_action_toggle(self, cell, path):
        """ Clic sur coche d'action"""
        print "Action sur", self.store_filter_sort[path][self.crud.get_vue_prop("key_id")]
        self.crud.key_value = self.store_filter_sort[path][self.crud.get_vue_prop("key_id")]
        row_id = self.store_filter_sort[path][self.crud.get_vue_prop("col_row_id")]
        self.liststore[row_id][self.crud.get_vue_prop("col_action_id")]\
            = not self.liststore[row_id][self.crud.get_vue_prop("col_action_id")]

    def on_tree_selection_changed(self, selection):
        """ Sélection d'une ligne """
        model, self.treeiter_selected = selection.get_selected()
        if self.treeiter_selected:
            print "Select", self.store_filter_sort[self.treeiter_selected][self.crud.get_vue_prop("key_id")]

    def on_row_actived(self, widget, row, col):
        """ Double clic sur une ligne """
        print "Activation", widget.get_model()[row][self.crud.get_vue_prop("key_id")]

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
