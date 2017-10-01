# -*- coding:Utf-8 -*-
"""
    Gestion du portail, layout
"""
from crudview import CrudView

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

class CrudPortail():
    """ Gestion du portail
    Gère le LAYOUT de la fenêtre principale
    Affiche la liste des applications, la liste des vues d'une application
    paramètres:
    crud         : le contexte applicatif
    """
    # Constantes
    LAYOUT_MENU = 1
    LAYOUT_VIEW_H = 2
    LAYOUT_VIEW_V = 3

    def __init__(self, app_window, crud):
        self.crud = crud
        self.app_window = app_window

        # Déclaration des variables globales
        self.crud_view = None
        self.footerbar = None
        self.button_home = None

        # layout
        self.layout_type = CrudPortail.LAYOUT_MENU
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

        self.app_window.add(self.box_one)

        self.create_application_menu()
        self.create_toolbar()
        self.create_footerbar()

        self.display_layout()

        self.app_window.show_all()

    def display_layout(self):
        """ Affichage du layout """
        if self.layout_type == CrudPortail.LAYOUT_MENU:
            for widget in self.box_toolbar_view.get_children():
                Gtk.Widget.destroy(widget)
            for widget in self.box_view_sidebar.get_children():
                Gtk.Widget.destroy(widget)
            for widget in self.box_view_toolbar.get_children():
                Gtk.Widget.destroy(widget)
            for widget in self.box_view_list.get_children():
                Gtk.Widget.destroy(widget)
            self.headerbar.props.title = self.crud.config["title"]
        elif self.layout_type == CrudPortail.LAYOUT_VIEW_H:
            for widget in self.box_application_menu.get_children():
                Gtk.Widget.destroy(widget)
            for widget in self.box_view_sidebar.get_children():
                Gtk.Widget.destroy(widget)
            self.box_view.show()
            self.headerbar.props.title = self.crud.get_application_prop("title")
            self.box_toolbar_right.show()
        elif self.layout_type == CrudPortail.LAYOUT_VIEW_V:
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
            application = self.crud.get_json_content(self.crud.config["application_directory"]\
                + "/" + application_file)
            self.crud.set_application(application)
            button = Gtk.Button(self.crud.get_application_prop("title"))
            button.connect("clicked", self.on_button_application_clicked, application_file)
            self.box_application_menu.pack_start(button, True, True, 3)

    def create_toolbar(self):
        """ Toolbar avec la recherche et les boutons pour afficher les vues """
        self.headerbar = Gtk.HeaderBar()
        self.headerbar.set_show_close_button(True)
        self.headerbar.props.title = self.crud.config["title"]
        self.app_window.set_titlebar(self.headerbar)

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
            self.layout_type = CrudPortail.LAYOUT_VIEW_H
        else:
            self.layout_type = CrudPortail.LAYOUT_VIEW_V

        self.display_layout()

        self.crud_view = CrudView(self.app_window, self, self.crud)

    def on_button_home_clicked(self, widget):
        """ Retour au menu général """
        self.layout_type = CrudPortail.LAYOUT_MENU
        self.create_application_menu()
        self.display_layout()
        self.app_window.show_all()

    def on_button_view_clicked(self, widget, table_id, view_id):
        """ Activation d'une vue """
        self.crud.get_view_prop("button").get_style_context().remove_class('button_selected')

        # init ctx
        self.crud.set_table_id(table_id)
        self.crud.set_view_id(view_id)
        self.crud.set_key_id(self.crud.get_table_prop("key"))
        self.crud.get_view_prop("button").get_style_context().add_class('button_selected')
        # raz view_toolbar
        for widget in self.box_view_toolbar.get_children():
            Gtk.Widget.destroy(widget)
        # raz view_list
        for widget in self.box_view_list.get_children():
            Gtk.Widget.destroy(widget)

        self.display_layout()

        self.crud_view = CrudView(self.app_window, self, self.crud)
