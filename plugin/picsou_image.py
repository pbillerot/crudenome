# -*- coding:Utf-8 -*-
from gi.repository import Gtk, GObject

class PicsouImage(Gtk.Window):
    """ Affichage d'une image dans une Gtk.Window """

    __gsignals__ = {
        'init_widget': (GObject.SIGNAL_RUN_FIRST, None, (str, str,))
    }
    def do_init_widget(self, str_from, str_arg=""):
        """ Traitement du signal """
        # print ("do_init_widget {}({}) -> {}".format(str_from, str_arg, self.__class__))

    def refresh_data(self):
        print("Refresh_data {}...".format(self.arg))
        self.update_widget()
        return False

    def __init__(self, crud, arg):
        Gtk.Window.__init__(self, title=arg)
        self.crud = crud
        self.arg = arg
        self.set_size_request(800, 600)

        self.create_widget()
        
        # GObject.timeout_add(1000 * 60 * 5, self.refresh_data)

    def create_widget(self):
        """ Construction du dessin et du toolbar """
        path = "{}/png/{}".format(self.crud.get_application_prop("data_directory"),self.arg)
        self.image = Gtk.Image()
        self.image.set_from_file(path)
        self.add(self.image)
        self.show_all()

    def update_widget(self):
        self.remove(self.image)
        while Gtk.events_pending():
                Gtk.main_iteration()
        self.create_widget()

