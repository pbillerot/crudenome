# -*- coding:Utf-8 -*-
"""
    Fenêtre d'affichage de graphique
    Utilisation de la librairie matplotlib

"""
import shutil
import os
import datetime, time
from .picsou_loader import PicsouLoader
from gi.repository import Gtk, GObject

class PicsouBatchUi(Gtk.Window):
    """ Actualisation des données """

    __gsignals__ = {
        'init_widget': (GObject.SIGNAL_RUN_FIRST, None, (str,str,))
    }
    def do_init_widget(self, str_from, str_arg=""):
        """ Traitement du signal """
        # print "do_init_widget %s(%s) -> %s" % (str_from, str_arg, self.__class__)

    def __init__(self, crud):
        Gtk.Window.__init__(self, title="Actualisation des données")

        self.crud = crud
        self.crudel = crud.get_crudel()

        self.activate_focus()
        self.set_border_width(10)
        self.set_default_size(1200, 800)

        self.supports = []
        self.resistances = []
        self.top14 = []
        self.rsi_date = "2017-07-11"
        self.rsi_time = "14:35"
        self.myptf = []

        self.run_button = Gtk.Button("Exécuter")
        # self.run_button = Gtk.Button(stock=Gtk.STOCK_REFRESH)
        self.run_button.set_always_show_image(True)
        self.run_button.set_tooltip_text("Démarrer l'actualisation...")
        self.run_button.connect("clicked", self.on_run_button_clicked)

        # self.cancel_button = Gtk.Button(stock=Gtk.STOCK_CANCEL)
        # self.cancel_button.set_always_show_image(True)
        # self.cancel_button.connect("clicked", self.on_cancel_button_clicked)

        self.close_button = Gtk.Button(stock=Gtk.STOCK_CLOSE)
        self.close_button.set_always_show_image(True)
        self.close_button.connect("clicked", self.on_close_button_clicked)

        self.with_trade = Gtk.CheckButton()
        self.with_trade.set_label("Trading")
        self.with_trade.set_active(False)

        self.with_quote = Gtk.CheckButton()
        self.with_quote.set_label("Cours du jour")
        self.with_quote.set_active(False)

        self.with_schedule = Gtk.CheckButton()
        self.with_schedule.set_label("Boucle 10 minutes")
        self.with_schedule.set_active(False)

        vbox = Gtk.VBox()
        self.add(vbox)

        toolbar = Gtk.HBox()
        vbox.pack_start(toolbar, False, False, 0)

        toolbar.pack_start(self.with_trade, True, True, 0)
        toolbar.pack_start(self.with_quote, True, True, 0)
        toolbar.pack_start(self.with_schedule, True, True, 0)
        toolbar.pack_start(self.run_button, True, True, 0)
        toolbar.pack_start(self.close_button, True, True, 0)
        # toolbar.pack_start(self.cancel_button, True, True, 0)

        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_hexpand(True)
        scrolledwindow.set_vexpand(True)
        vbox.pack_start(scrolledwindow, True, True, 5)

        self.textview = Gtk.TextView()
        self.textview.set_monospace(True)
        self.textview.set_editable(True)
        self.textbuffer = self.textview.get_buffer()
        scrolledwindow.add(self.textview)

        self.show_all()

    def quit(self, event, data=None):
        """ docstring """
        # print "quit", event, data
        self.destroy()

    # def on_cancel_button_clicked(self, widget):
    #     """ docstring """
    #     self.emit('delete-event', None)

    def on_close_button_clicked(self, widget):
        """ docstring """
        self.destroy()

    def on_run_button_clicked(self, widget):
        """ docstring """
        # self.cancel_button.set_sensitive(False)
        self.run_button.set_sensitive(False)
        # self.with_mail.set_sensitive(False)
        # self.with_histo.set_sensitive(False)
        # self.with_simulation.set_sensitive(False)
        self.with_quote.set_sensitive(False)
        self.close_button.set_sensitive(False)

        if self.with_schedule.get_active():
            self.run_calcul()
            self.crud.get_view().emit("refresh_data_view", "batch", "close")
            time1 = time.time()
            while True:
                if self.with_schedule.get_active():
                    time2 = time.time()
                    if ( (time2-time1) > 10 * 60 ):
                        self.run_calcul()
                        self.crud.get_view().emit("refresh_data_view", "batch", "close")
                        time1 = time2
                else:
                    break
                while Gtk.events_pending():
                    Gtk.main_iteration()
                time.sleep(1)
        else:
            self.run_calcul()
            self.crud.get_view().emit("refresh_data_view", "batch", "close")

        # Put de la base de données sur la box
        # ticket_user = os.path.getmtime(self.crud.get_basename())
        # ticket_host = os.path.getmtime(self.crud.get_basehost())
        # if ticket_user > ticket_host:
        #     # shutil.copy2(self.crud.get_basename(), self.crud.get_basehost())
        #     self.display("Backup  OK %s %s" % (self.crud.get_basehost(), datetime.datetime.fromtimestamp(ticket_user)))

        # self.cancel_button.hide()
        self.run_button.set_sensitive(True)
        # self.with_mail.set_sensitive(True)
        # self.with_histo.set_sensitive(True)
        # self.with_simulation.set_sensitive(True)
        self.with_quote.set_sensitive(True)
        self.close_button.set_sensitive(True)


    def display(self, msg):
        """ docstring """
        self.textbuffer.insert_at_cursor("\n" + msg, len(msg + "\n"))
        self.textview.set_cursor_visible(True)
        while Gtk.events_pending():
            Gtk.main_iteration()
        # Scoll to end of Buffer
        iter = self.textbuffer.get_iter_at_line(self.textbuffer.get_line_count())
        self.textview.scroll_to_iter(iter, 0, 0, 0, 0)
        self.crud.logger.info(msg)

    def clearMessage(self):
        """ docstring """
        start = self.textbuffer.get_iter_at_line(self.textbuffer.get_line_count())
        self.textbuffer.delete(self.textbuffer.get_iter_at_line(0), self.textbuffer.get_end_iter())
        while Gtk.events_pending():
            Gtk.main_iteration()

    def run_calcul(self):
        """ docstring """
        self.clearMessage()
        if self.with_trade.get_active():
            loader = PicsouLoader(self, self.crud)
            loader.trade()

        if self.with_quote.get_active():
            loader = PicsouLoader(self, self.crud)
            loader.quote()

