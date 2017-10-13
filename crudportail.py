# -*- coding:Utf-8 -*-
"""
    Gestion du portail, layout
"""
from crudview import CrudView
from crudform import CrudForm
from crudwindow import MyWindow
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
    """ LAYOUT
    button_home box_view 
    box_frame V
        box_app H
            box_sidebar V box_main V
                            box_toolbar H
                            box_content V
                                scroll_window
        footerbar H
            footer_label
    """
    # Constantes
    LAYOUT_MENU = 1
    LAYOUT_VIEW = 2
    LAYOUT_FORM = 5

    def __init__(self, app_window, crud):
        self.crud = crud
        self.app_window = app_window

        # Déclaration des variables globales
        self.crud_view = None
        self.footerbar = None
        self.button_home = None

        # layout
        self.layout_type = CrudPortail.LAYOUT_MENU

        # box_view
        self.box_view = Gtk.HBox(spacing=0)

        # box_frame
        self.box_frame = Gtk.VBox(spacing=0)
        self.app_window.add(self.box_frame)

        # box_app
        self.box_app = Gtk.HBox(spacing=0)
        self.box_frame.pack_start(self.box_app, True, True, 0)

        # box_footerbar
        self.footerbar = Gtk.HBox(spacing=0)
        self.box_frame.pack_end(self.footerbar, False, True, 0)

        # box_sidebar
        self.box_sidebar = Gtk.VBox(spacing=0)
        self.box_app.pack_start(self.box_sidebar, False, True, 3)

        # box_main
        self.box_main = Gtk.VBox(spacing=0) # box_view_toolbar box_view_list
        self.box_app.pack_end(self.box_main, True, True, 5)

        # box_toolbar
        self.box_toolbar = Gtk.HBox(spacing=0)
        self.box_toolbar.set_border_width(6)
        self.frame = Gtk.Frame()
        self.frame.add(self.box_toolbar)
        self.box_main.pack_start(self.frame, False, False, 3)

        # box_content
        self.box_content = Gtk.VBox(spacing=0)
        self.box_main.pack_end(self.box_content, True, True, 3)
        self.scroll_window = Gtk.ScrolledWindow()
        self.scroll_window.set_hexpand(True)
        self.scroll_window.set_vexpand(True)
        self.box_content.pack_end(self.scroll_window, True, True, 3)

        self.create_toolbar()
        self.create_footerbar()
        self.set_layout(CrudPortail.LAYOUT_MENU)
        
        self.create_application_menu()

        self.app_window.show_all()

    def set_layout(self, layout_type):
        """ Affichage du layout """
        if layout_type:
            self.layout_type = layout_type

        if self.layout_type == CrudPortail.LAYOUT_MENU:
            for widget in self.box_view.get_children():
                Gtk.Widget.destroy(widget)
            for widget in self.box_sidebar.get_children():
                Gtk.Widget.destroy(widget)
            for widget in self.box_toolbar.get_children():
                Gtk.Widget.destroy(widget)
            # for widget in self.box_content.get_children():
            #     Gtk.Widget.destroy(widget)
            for widget in self.scroll_window.get_children():
                Gtk.Widget.destroy(widget)
            self.headerbar.props.title = self.crud.config["title"]
        elif self.layout_type == CrudPortail.LAYOUT_VIEW:
            for widget in self.box_toolbar.get_children():
                Gtk.Widget.destroy(widget)
            # for widget in self.box_content.get_children():
            #     Gtk.Widget.destroy(widget)
            for widget in self.scroll_window.get_children():
                Gtk.Widget.destroy(widget)
            self.headerbar.props.title = self.crud.get_application_prop("title")
        elif self.layout_type == CrudPortail.LAYOUT_FORM:
            # for widget in self.box_view.get_children():
            #     Gtk.Widget.destroy(widget)
            # for widget in self.box_sidebar.get_children():
            #     Gtk.Widget.destroy(widget)
            for widget in self.box_toolbar.get_children():
                Gtk.Widget.destroy(widget)
            # for widget in self.box_content.get_children():
            #     Gtk.Widget.destroy(widget)
            for widget in self.scroll_window.get_children():
                Gtk.Widget.destroy(widget)
            self.headerbar.props.title = self.crud.get_application_prop("title")

        if self.crud.get_application_prop("menu_orientation", "horizontal") == "horizontal":
            for widget in self.box_sidebar.get_children():
                Gtk.Widget.destroy(widget)

    def display(self, msg):
        """ Affichage de message dans la fenêtre des traces """
        print msg

    def create_application_menu(self):
        """ menu des applications """
        # raz widgets
        for widget in self.box_toolbar.get_children():
            Gtk.Widget.destroy(widget)

        file_list = self.crud.directory_list(self.crud.config["application_directory"])
        for application_file in file_list:
            application = self.crud.get_json_content(self.crud.config["application_directory"]\
                + "/" + application_file)
            self.crud.set_application(application)
            button = Gtk.Button(self.crud.get_application_prop("title"))
            button.connect("clicked", self.on_button_application_clicked, application_file)
            self.box_toolbar.pack_start(button, False, False, 3)

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

        self.headerbar.pack_start(self.box_view)

    def create_footerbar(self):
        """ Footer pour afficher des infos et le bouton pour ajouter des éléments """
        footer_label = Gtk.Label()
        footer_label.set_markup('<sub>Développé avec <a href="{}">{}</a> {} {}</sub>'.format(\
            self.crud.config["web_site"]\
            , self.crud.config["title"]\
            , self.crud.config["version"]\
            , self.crud.config["copyright"]\
            ))
        self.footerbar.pack_start(footer_label, False, True, 3)

    def create_sidebar(self):
        """ Création des boutons d'activation des vues de l'application """
        table_first = None
        view_first = None
        for table_id in self.crud.get_application_tables():
            self.crud.set_table_id(table_id)
            if table_first is None:
                table_first = table_id
            for view_id in self.crud.get_table_views():
                self.crud.set_view_id(view_id)
                if self.crud.get_view_prop("hide", False):
                    continue
                if view_first is None:
                    view_first = view_id
                # les boutons sont ajoutés dans le dictionnaire de la vue
                self.crud.set_view_prop("button", Gtk.Button(self.crud.get_view_prop("title")))
                self.crud.get_view_prop("button").connect("clicked",
                                                          self.on_button_view_clicked,
                                                          table_id, view_id)
                if self.crud.get_application_prop("menu_orientation") == "horizontal":
                    self.box_view.pack_start(self.crud.get_view_prop("button"),
                                                     False, False, 3)
                if self.crud.get_application_prop("menu_orientation") == "vertical":
                    self.box_sidebar.pack_start(self.crud.get_view_prop("button"),
                                                     False, False, 3)

        # mise en relief du bouton vue courante
        self.crud.set_table_id(table_first)
        self.crud.set_view_id(view_first)
        self.crud.get_view_prop("button").get_style_context().add_class('button_selected')

    def on_button_application_clicked(self, widget, application_file):
        """ Activation d'une application """
        application = self.crud.get_json_content(
            self.crud.config["application_directory"] + "/" + application_file)
        self.crud.set_application(application)
        self.set_layout(CrudPortail.LAYOUT_VIEW)
        self.create_sidebar()
        self.crud_view = CrudView(self.app_window, self, self.crud, self.box_main, self.box_toolbar, self.scroll_window, None, None)

    def on_button_home_clicked(self, widget):
        """ Retour au menu général """
        self.layout_type = CrudPortail.LAYOUT_MENU
        self.set_layout(self.LAYOUT_MENU)
        self.create_application_menu()
        self.app_window.show_all()

    def on_button_view_clicked(self, widget, table_id, view_id):
        """ Activation d'une vue """
        self.crud.get_view_prop("button").get_style_context().remove_class('button_selected')

        # init ctx
        self.crud.set_table_id(table_id)
        self.crud.set_view_id(view_id)
        self.crud.get_view_prop("button").get_style_context().add_class('button_selected')
        # raz view_toolbar
        for widget in self.box_toolbar.get_children():
            Gtk.Widget.destroy(widget)

        self.set_layout(CrudPortail.LAYOUT_VIEW)
        
        self.crud_view = CrudView(self.app_window, self, self.crud, self.box_main, self.box_toolbar, self.scroll_window, None, None)

    def do_form(self, crud_view, crud):
        """ Demande d'activation d'un formulaire """
        # raz view_toolbar
        for widget in self.box_toolbar.get_children():
            Gtk.Widget.destroy(widget)
        self.set_layout(CrudPortail.LAYOUT_FORM)
        form = CrudForm(self.app_window, self, crud_view, crud, None, None)
        form.emit("init_widget", self.__class__, "do_form")
