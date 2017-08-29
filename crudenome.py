#!/usr/bin/env python
# -*- coding:Utf-8 -*-
# http://python-gtk-3-tutorial.readthedocs.io/en/latest/index.html
# https://gtk.developpez.com/doc/fr/gtk/gtk-Stock-Items.html
import sys
from pprint import pprint
from tools import Tools, NumberEntry
import constants as const

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gio

class AppWindow(Gtk.ApplicationWindow):
    """
    La fenêtre principale du Gtk
    """
    def __init__(self, app):
        Gtk.Window.__init__(self, title="Welcome to GNOME", application=app)

        # Chargement des paramètres
        self.app = app
        self.tools = app.tools
        self.config = self.tools.get_config()

        # Initialisation des variables globales
        self.tables = None
        self.table_id = None
        self.view_id = None
        self.form_id = None
        self.treeview = None
        self.liststore = None
        self.current_filter = None

        self.set_title(self.config["name"])
        self.activate_focus()
        self.set_border_width(10)
        self.set_default_size(1200, 600)
        self.set_icon_from_file(self.config["logo"])

        self.vbox = Gtk.VBox(spacing=3)
        self.add(self.vbox)

        self.create_toolbar()
        self.create_scroll_window()
        self.create_view()
        self.create_footerbar()

        self.show_all()

        self.search_entry.grab_focus()

    def display(self, msg):
        """
        Affichage de message dans la fenêtre des traces
        """
        print msg

    def create_footerbar(self):
        """
        Footer pour afficher des infos et le bouton pour ajouter des éléments
        """
        self.footerbar = Gtk.HBox()

        self.button_add = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_ADD))
        self.button_add.set_tooltip_text("Ajouter une action...")
        # self.button_add.connect("clicked", self.on_button_add_clicked)

        self.footerbar.pack_end(self.button_add, False, True, 3)

        self.vbox.pack_end(self.footerbar, False, True, 0)

    def create_toolbar(self):
        """
        Toolbar avec la recherche et les boutons pour afficher les vues
        """
        self.headerbar = Gtk.HeaderBar()
        self.headerbar.set_show_close_button(True)
        self.headerbar.props.title = self.config["title"]
        self.set_titlebar(self.headerbar)

        # CREATION DES BOUTONS DES VUES
        self.button_views = {}
        hbox_button = Gtk.HBox() # box qui permet d'inverser l'ordre de présentation des boutons
        # Lecture des fichiers d'application 
        file_list = self.tools.directory_list(self.config["application_directory"])
        for application_file in file_list:
            application_store = self.tools.get_json_content(self.config["application_directory"] + "/" + application_file)
            self.tables = application_store["tables"]
            for table_id in self.tables:
                if self.table_id is None:
                    self.table_id = table_id
                for view_id in self.tables[table_id]["views"]:
                    if self.view_id is None:
                        self.view_id = view_id
                    self.button_view = Gtk.Button(self.get_vue_prop("title"))
                    self.button_view.connect("clicked", self.on_button_view_clicked, table_id, view_id)
                    self.button_views[table_id + "_" + view_id] = self.button_view
                    hbox_button.pack_end(self.button_view, False, False, 5)

        self.headerbar.pack_start(hbox_button)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.connect("search-changed", self.on_search_changed)

        self.headerbar.pack_end(self.search_entry)

    def on_button_view_clicked(self, widget, table_id, view_id):
        """
        Activation d'une vue
        """
        self.table_id = table_id
        self.view_id = view_id
        self.create_view()

    def on_button_add_clicked(self, widget):
        """
        Ajout d'un élément
        """
        print "on_button_add_clicked"

    def on_search_changed(self, widget):
        """
        Recherche d'éléments dans la vue
        """
        if len(self.search_entry.get_text()) == 1:
            return
        self.current_filter = self.search_entry.get_text()
        self.store_filter.refilter()

    def create_scroll_window(self):
        """
        Création du container de la vue à afficher
        """
        # La scrollwindow va contenir la treeview
        self.scroll_window = Gtk.ScrolledWindow()
        self.scroll_window.set_hexpand(True)
        self.scroll_window.set_vexpand(True)

        self.vbox.pack_start(self.scroll_window, True, True, 3)

    def create_view(self):
        """
        Création de la vue (liststore)
        """
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
            del(self.treeview)

        self.treeview = Gtk.TreeView.new_with_model(self.store_filter_sort)

        # CellRenderers
        textleft = Gtk.CellRendererText()
        textright = Gtk.CellRendererText()
        textright.set_property('xalign', 1.0)
        textcenter = Gtk.CellRendererText()
        textcenter.set_property('xalign', 0.5)

        id_row = 0
        for element in self.tables[self.table_id]["views"][self.view_id]["elements"]:
            tvc = Gtk.TreeViewColumn(self.get_rubrique_prop(element, "label_short")\
                , textleft, text=id_row)
            self.treeview.append_column(tvc)
            id_row += 1

        # for col in self.treeview.get_columns():
        #     pprint(col.get_title())

        self.scroll_window.add(self.treeview)
        self.scroll_window.show_all()

    def create_liststore(self):
        """ Création de la structure du liststore à partir du dictionnaire des données """
        # Génération de la structure du liststore
        col_store_types = []
        for element in self.tables[self.table_id]["views"][self.view_id]["elements"]:
            col_store_types.append(const.GOBJECT_TYPE[self.get_rubrique_prop(element, "type")])

        self.liststore = Gtk.ListStore(*col_store_types)

        self.update_liststore()

    def update_liststore(self):
        """ Mise à jour du liststore en relisant la table """
        # Génération du select de la table

        sql = "SELECT "
        b_first = True
        col_store_types = []
        id_row = 0
        for element in self.tables[self.table_id]["views"][self.view_id]["elements"]:
            if b_first:
                sql += element
                b_first = False
            else:
                sql += ", " + element
            col_store_types.append("str")
            id_row += 1

        sql += " FROM " + self.table_id 
        sql += " LIMIT 10 "
        rows = self.tools.sql_to_dict(self.get_table_prop("basename"), sql, {})
        self.liststore.clear()
        for row in rows:
            self.liststore.append(row.values())

    def filter_func(self, model, iter, data):
        """Tests if the text in the row is the one in the filter"""
        if self.current_filter is None or self.current_filter == "":
            return True
        # else:
        #     if self.current_filter == "*":
        #         return len(model[iter][const.COL_NOTE]) > 0
        #     else:
        #         return re.search(self.current_filter, model[iter][const.COL_ID], re.IGNORECASE) \
        #             or re.search(self.current_filter, model[iter][const.COL_NAME], re.IGNORECASE) \
        #             or re.search(self.current_filter, model[iter][const.COL_TRADE], re.IGNORECASE) \
        #             or re.search(self.current_filter, model[iter][const.COL_INPTF], re.IGNORECASE) \
        #             or re.search(self.current_filter, model[iter][const.COL_INTEST], re.IGNORECASE) \
        #             or re.search(self.current_filter, model[iter][const.COL_NOTE], re.IGNORECASE)

    def get_table_prop(self, prop):
        """ Obtenir la valeur d'une propriété de la table courante """
        return self.tables[self.table_id][prop]

    def get_vue_prop(self, prop):
        """ Obtenir la valeur d'une propriété de la vue courante """
        return self.tables[self.table_id]["views"][self.view_id][prop]

    def get_formulaire_prop(self, prop):
        """ Obtenir la valeur d'une propriété du formulaire courant """
        return self.tables[self.table_id]["forms"][self.form_id][prop]

    def get_rubrique_prop(self, element, prop):
        """ Obtenir la valeur d'une propriété d'un élément (colonne) de la table courante """
        return self.tables[self.table_id]["elements"][element][prop]

    def get_colonne_prop(self, element, prop):
        """ Obtenir la valeur d'une propriété d'une colonne de la vue courante """
        return self.tables[self.table_id]["views"][self.view_id]["elements"][element][prop]

    def get_champ_prop(self, element, prop):
        """ Obtenir la valeur d'une propriété d'un champ du formulaire courant """
        return self.tables[self.table_id]["forms"][self.form_id]["elements"][element][prop]

class Application(Gtk.Application):
    """
    La classe principale d'une application Gnome
    """

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
        self.tools = Tools()
        self.config = self.tools.get_config()

    def do_activate(self):
        """
        show the window and all its content
        this line could go in the constructor of MyWindow as well
        self.win.show_all()
        """
        if not self.window:
            # Windows are associated with the application
            # when the last one is closed the application shuts down
            self.window = AppWindow(self)

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
        about.set_title(self.config["title"])
        about.set_program_name(self.config["name"])
        about.set_version(self.config["version"])
        about.set_copyright(self.config["copyright"])
        about.set_comments(self.config["comments"])
        about.set_website(self.config["web_site"])
        about.set_logo(GdkPixbuf.Pixbuf.new_from_file(self.config["logo"]))
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

myapp = Application()
exit_status = myapp.run(sys.argv)
sys.exit(exit_status)
