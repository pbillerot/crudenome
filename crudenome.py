#/usr/bin/python3
# -*- coding:Utf-8 -*-
"""
    Module principal, c'est le point d'entrée
"""
import os
import shutil
import datetime
import sys
import argparse
import time
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')
from gi.repository import Gtk, Gdk, GdkPixbuf, Gio, Notify

from crud import Crud
from crudportail import CrudPortail

class AppWindow(Gtk.ApplicationWindow):
    """ La fenêtre principale du Gtk """
    def __init__(self, app, args, crud):
        Gtk.ApplicationWindow.__init__(self, title="Welcome to CRUDENOME", application=app)

        # When the window is given the "delete_event" signal (this is given
        # by the window manager, usually by the "close" option, or on the
        # titlebar), we ask it to call the delete_event () functionpip inst
        # as defined above. The data passed to the callback
        # function is NULL and is ignored in the callback function.
        self.connect('delete-event', self.delete_event)

        # Here we connect the "destroy" event to a signal handler.  
        # This event occurs when we call gtk_widget_destroy() on the window,
        # or if we return FALSE in the "delete_event" callback.
        # self.connect("destroy", Gtk.main_quit)

        Notify.init('Crudenome')

        self.args = args # paramètre
        self.crud = crud
        self.crud.set_window(self)

        self.set_title(self.crud.config["name"])
        self.activate_focus()
        self.set_border_width(10)
        self.set_default_size(1280, 600)
        if "icon_file" in self.crud.config:
            self.set_icon_from_file(self.get_resource_path(self.crud.config["icon_file"]))
        if "icon_name" in self.crud.config:
            self.set_icon_name(self.crud.config["icon_name"])

        self.crud_portail = CrudPortail(self.crud)

    def get_resource_path(self, rel_path):
        dir_of_py_file = os.path.dirname(__file__)
        rel_path_to_resource = os.path.join(dir_of_py_file, rel_path)
        abs_path_to_resource = os.path.abspath(rel_path_to_resource)
        return abs_path_to_resource

    def delete_event(self, widget, event, data=None):
        # If you return FALSE in the "delete_event" signal handler,
        # GTK will emit the "destroy" signal. Returning TRUE means
        # you don't want the window to be destroyed.
        # This is useful for popping up 'are you sure you want to quit?'
        # type dialogs.
        # print "delete event occurred"

        # if self.crud.get_basehost():
        #     ticket_user = os.path.getmtime(self.crud.get_basename())
        #     ticket_host = os.path.getmtime(self.crud.get_basehost())
            # if ticket_user > ticket_host:
            #     # la base du host a changée depuis la dernière prise
            #     dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.QUESTION,
            #                         Gtk.ButtonsType.YES_NO, "La base sur le serveur a changée")
            #     dialog.format_secondary_text("Veux-tu écraser la base du serveur ?")
            #     response = dialog.run()
            #     if response == Gtk.ResponseType.YES:
            #         shutil.copy2(self.crud.get_basename(), self.crud.get_basehost())
            #         self.crud.logger.info("Backup  OK %s %s", self.crud.get_basehost(), datetime.datetime.fromtimestamp(ticket_host))
            #         notif = Notify.Notification.new('Backup OK'\
            #         , "%s %s" % (self.crud.get_basehost(), datetime.datetime.fromtimestamp(ticket_host))\
            #         , 'dialog-information')
            #         # notif.add_action(
            #         #     'id_callback', # identifiant
            #         #     'Fermer', # texte du bouton
            #         #     self.on_notif, # function callback de notre bouton
            #         #     None, # user_datas, ce dont vous avez besoin dans la callback
            #         #     None # fonction qui supprime les user_datas
            #         # )
            #         notif.show()
            #         time.sleep(3)
            #         # return True
            #     elif response == Gtk.ResponseType.NO:
            #         self.crud.logger.info("Backup abandonné")

            #     dialog.destroy()
            # else:
                # shutil.copy2(self.crud.get_basename(), self.crud.get_basehost())
                # self.crud.logger.info("Backup  OK %s %s", self.crud.get_basehost(), datetime.datetime.fromtimestamp(ticket_host))
                # notif = Notify.Notification.new('Backup OK'\
                # , "%s %s" % (self.crud.get_basehost(), datetime.datetime.fromtimestamp(ticket_host))\
                # , 'dialog-information')
                # # notif.add_action(
                # #     'id_callback', # identifiant
                # #     'Fermer', # texte du bouton
                # #     self.on_notif, # function callback de notre bouton
                # #     None, # user_datas, ce dont vous avez besoin dans la callback
                # #     None # fonction qui supprime les user_datas
                # # )
                # notif.show()
                # time.sleep(3)
                # # return True

        # Change FALSE to TRUE and the main window will not be destroyed
        # with a "delete_event".
        return False

    def on_notif(self, notif_object, action_name, users_data):
        """ action sur boutn de la notification """
        notif_object.close()
        Gtk.main_quit()

class Application(Gtk.Application):
    """ La classe principale d'une application Gnome """

    def __init__(self, *args, **kwargs):
        """
        constructor of the Gtk Application
        create and activate a MyWindow, with self (the MyApplication) as
        application the window belongs to.
        Note that the function in C activate() becomes do_activate() in Python
        """
        Gtk.Application.__init__(self, flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE, **kwargs)
        self.args = args # store for parsed command line options

        self.window = None

    def do_activate(self):
        """
        show the window and all its content
        this line could go in the constructor of MyWindow as well
        self.win.show_all()
        """

        if not self.window:
            # Windows are associated with the application
            # when the last one is closed the application shuts down
    
            # Chargement des paramètres
            self.crud = Crud()
            if self.args.application:
                self.crud.set_app(self.args.application)
    
            self.window = AppWindow(self, self.args, self.crud)

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

    def do_command_line(self, args):
        '''
        Gtk.Application command line handler
        called if Gio.ApplicationFlags.HANDLES_COMMAND_LINE is set.
        must call the self.do_activate() to get the application up and running.
        '''
        # https://docs.python.org/fr/3/howto/argparse.html"
        # print "do_command_line", args.get_arguments()

        Gtk.Application.do_command_line(self, args) # call the default commandline handler
        # make a command line parser
        parser = argparse.ArgumentParser(prog='crudenome')
        # add a -c/--color option
        parser.add_argument('-a', '--application', help="Nom de l'application au démarrage")
        # parse the command line stored in args, but skip the first element (the filename)
        # self.args = parser.parse_args(args.get_arguments()[1:])
        self.args = parser.parse_args()
        # call the main program do_activate() to start up the app
        self.do_activate()
        return 0

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
        # print "on_preference"

    def on_quit(self, action, param):
        """
        Fin de l'application
        """
        # print "quit"
        self.quit()

# get the style from the css file and apply it
style_provider = Gtk.CssProvider()
style_provider.load_from_path(os.path.dirname(os.path.realpath(__file__)) + '/style.css')
Gtk.StyleContext.add_provider_for_screen(
    Gdk.Screen.get_default(),
    style_provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

myapp = Application()
exit_status = myapp.run(sys.argv)
sys.exit(exit_status)
