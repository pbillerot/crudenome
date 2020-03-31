# -*- coding:Utf-8 -*-
from gi.repository import Gtk, GObject
from crudel import Crudel

class PicsouImage(Gtk.Window):
    """ Affichage d'une image dans une Gtk.Window """

    __gsignals__ = {
        'init_widget': (GObject.SIGNAL_RUN_FIRST, None, (str, str,))
    }
    def do_init_widget(self, str_from, str_arg=""):
        """ Traitement du signal """
        # print ("do_init_widget {}({}) -> {}".format(str_from, str_arg, self.__class__))

    def __init__(self, crud, arg):
        Gtk.Window.__init__(self, title=arg)
        self.crud = crud
        self.arg = arg
        self.set_size_request(800, 600)

        self.create_widget()

    def create_widget(self):
        """ Construction du dessin et du toolbar """
        path = "{}/png/{}".format(self.crud.get_application_prop("data_directory"),self.arg)
        self.image = Gtk.Image()
        self.image.set_from_file(path)
        self.add(self.image)
        self.show_all()
