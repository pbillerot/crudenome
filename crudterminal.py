#!/usr/bin/env python
# -*- coding:Utf-8 -*-
"""
    Fenêtre secondaire
"""
from shell import shell

from gi.repository import Gtk


class CrudTerminal(Gtk.Window):
    """ Fenêtre terminal """
    def __init__(self, crud):
        Gtk.Window.__init__(self, title="Terminal")

        self.crud = crud

        self.activate_focus()
        self.set_border_width(10)
        self.set_default_size(1200, 800)

        vbox = Gtk.VBox()
        self.add(vbox)

        self.toolbar = Gtk.HBox()
        vbox.pack_start(self.toolbar, False, True, 5)

        self.input_cmd = Gtk.SearchEntry()
        self.input_cmd.connect("activate", self.on_input_cmd_activate)
        self.toolbar.pack_start(self.input_cmd, True, True, 3)
        self.run_button = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_EXECUTE))
        self.run_button.connect("clicked", self.on_run_button_clicked)
        self.toolbar.pack_end(self.run_button, False, True, 3)

        scrolledwindow = Gtk.ScrolledWindow()
        vbox.pack_start(scrolledwindow, True, True, 5)

        self.textview = Gtk.TextView()
        self.textview.set_monospace(True)
        self.textview.set_editable(True)
        self.textbuffer = self.textview.get_buffer()
        scrolledwindow.add(self.textview)  

        self.show_all()
        self.input_cmd.grab_focus()

    def display(self, msg):
        self.textbuffer.insert_at_cursor(msg + "\n", len(msg + "\n"))
        self.textview.set_cursor_visible(True)
        while Gtk.events_pending():
            Gtk.main_iteration()
        # Scoll to end of Buffer
        iter = self.textbuffer.get_iter_at_line(self.textbuffer.get_line_count())
        self.textview.scroll_to_iter(iter, 0, 0, 0, 0)

    def on_input_cmd_activate(self, widget):
        """ CR dans le champ """
        self.run_button.do_activate(self.run_button)

    def on_run_button_clicked(self, widget):
        """ Démarrage du shell """
        command = self.input_cmd.get_text().encode("utf-8")

        self.display("Exécution de [%s]" % command)
        cmd = shell(command)
        for line in cmd.output():
            self.display(line)
