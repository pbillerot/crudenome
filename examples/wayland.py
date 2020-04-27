import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository.GdkPixbuf import Pixbuf

icon = ("firefox")

class IconViewWindow(Gtk.Window):

  def __init__(self):
    Gtk.Window.__init__(self)
    self.set_default_size(200, 200)

    liststore = Gtk.ListStore(Pixbuf, str)
    iconview = Gtk.IconView.new()
    iconview.set_model(liststore)
    iconview.set_pixbuf_column(0)
    iconview.set_text_column(1)

    pixbuf24 = Gtk.IconTheme.get_default().load_icon(icon, 24, 0)
    pixbuf32 = Gtk.IconTheme.get_default().load_icon(icon, 32, 0)
    pixbuf48 = Gtk.IconTheme.get_default().load_icon(icon, 48, 0)
    pixbuf64 = Gtk.IconTheme.get_default().load_icon(icon, 64, 0)
    pixbuf96 = Gtk.IconTheme.get_default().load_icon(icon, 96, 0)
    self.set_icon_list([pixbuf24, pixbuf32, pixbuf48, pixbuf64, pixbuf96])
    liststore.append([pixbuf64, "firefox"])

    self.add(iconview)

win = IconViewWindow()
win.connect("delete-event", Gtk.main_quit)
win.show_all()
Gtk.main()