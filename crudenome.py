#!/usr/bin/env python
# -*- coding:Utf-8 -*-
"""
    Module principal, c'est le point d'entrée
"""
# https://gtk.developpez.com/doc/fr/gtk/gtk-Stock-Items.html
# from __future__ import unicode_literals
import sys

from crud import Crud
from crudview import CrudView
import crudconst as const

from gi.repository import Gtk, Gdk, GdkPixbuf, Gio
import gi
gi.require_version('Gtk', '3.0')


class AppWindow(Gtk.ApplicationWindow):
    """ La fenêtre principale du Gtk """
    def __init__(self, app, crud):
        Gtk.ApplicationWindow.__init__(self, title="Welcome to CRUDENOME", application=app)

        # Chargement des paramètres
        self.crud = Crud(crud)

        # Initialisation des variables globales
        self.crud_view = None
        self.footerbar = None
        self.button_home = None

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
        # raz widgets
        for widget in self.box_application_menu.get_children():
            Gtk.Widget.destroy(widget)
        
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

        self.crud_view = CrudView(self, self.crud)

    def on_button_home_clicked(self, widget):
        """ Retour au menu général """
        self.layout_type = const.LAYOUT_MENU
        self.create_application_menu()
        self.display_layout()
        self.show_all()

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
