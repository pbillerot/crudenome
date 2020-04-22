# -*- coding:Utf-8 -*-
from gi.repository import Gtk, GObject, GdkPixbuf
from crudel import Crudel
import glob

class PicsouDiapo(Gtk.Window):
    """ Affichage d'une image dans une Gtk.Window """

    def __init__(self, crud, args):
        Gtk.Window.__init__(self, title=args)
        self.crud = crud
        self.args = args

        self.width = self.args["width"] if self.args.get("width") is not None else 800
        self.heigth = self.args["height"] if self.args.get("height") is not None else 600
        self.nb_cols = self.args["nb_cols"] if self.args.get("nb_cols") is not None else 3
        self.set_size_request(self.width, self.heigth)

        self.directory = "{}/{}".format(self.crud.get_application_prop("data_directory"),self.args["directory"])

        self.set_title("Historique des cours")

        self.create_widget()

    def create_widget(self):
        """ Construction des diapos """
        vbox = Gtk.VBox()
        hbox = None
        self.nb_cols = 2
        icol = 0
        files = sorted([f for f in glob.glob(self.directory + "/*.png")])
        for file_path in files:
            # print(file_path)
            if icol == 0:
                hbox = Gtk.HBox()
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(file_path, self.width//self.nb_cols - 4, -1, True)
            image = Gtk.Image.new_from_pixbuf(pixbuf)
            hbox.pack_start(image, False, False, 0)
            icol+=1
            if icol >= self.nb_cols:
                vbox.pack_start(hbox, False, False, 0)
                icol = 0
                hbox = None
        if hbox is not None:
            vbox.pack_start(hbox, False, False, 0)


        scroll_window = Gtk.ScrolledWindow()
        scroll_window.set_policy(Gtk.PolicyType.ALWAYS, Gtk.PolicyType.ALWAYS)
        scroll_window.add_with_viewport(vbox)

        self.add(scroll_window)
        self.show_all()
