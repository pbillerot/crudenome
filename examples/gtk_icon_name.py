#/usr/bin/python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class MainWindow(Gtk.Window):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.connect("delete-event", Gtk.main_quit)

        #icon_name = "applications-mail"
        icon_name = "internet-mail"
        icon_theme = Gtk.IconTheme.get_default()

        found_icons = set()
        for res in range(0, 512, 2):
            icon = icon_theme.lookup_icon(icon_name, res, 0)
            print(icon)
            if icon != None:
                found_icons.add(icon.get_filename())

        if len(found_icons) > 0:
            print("\n".join(found_icons))
            sizes = Gtk.IconTheme.get_default().get_icon_sizes(icon_name)
            max_size = max(sizes)
            print("max size = {} ({})".format(max_size, sizes))
            pixbuf = icon_theme.load_icon(icon_name, max_size, 0)
            self.set_default_icon_list([pixbuf])

        self.show_all()

    def run(self):
        Gtk.main()


def main(args):
    mainwdw = MainWindow()
    mainwdw.run()