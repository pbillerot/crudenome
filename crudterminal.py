# -*- coding:Utf-8 -*-
"""
    Fenêtre secondaire
"""

import sys
import os
import io
import threading
import subprocess
import logging
import logging.handlers

from gi.repository import Gtk, GLib, GObject


class CrudTerminal(Gtk.Window, GObject.GObject):
    """ Fenêtre terminal """

    __gsignals__ = {
        'display': (GObject.SIGNAL_RUN_FIRST, None, (str,))
    }

    def __init__(self, crud):
        Gtk.Window.__init__(self, title="Terminal")
        GObject.GObject.__init__(self) # pour  gérer les signaux

        self.crud = crud

        # self.spawn = GAsyncSpawn()
        # self.spawn.connect("process-done", self.on_process_done)
        # self.spawn.connect("stdout-data", self.on_stdout_data)
        # self.spawn.connect("stderr-data", self.on_stderr_data)

        self.activate_focus()
        self.set_border_width(10)
        self.set_default_size(1024, 800)

        vbox = Gtk.VBox()
        self.add(vbox)

        # Raccourcis de commande
        if self.crud.get_application_prop("shell", False):
            self.toolbar_shell = Gtk.HBox()
            commands = self.crud.get_application_prop("shell")
            for key in commands:
                button = Gtk.Button(key, image=Gtk.Image(stock=Gtk.STOCK_EXECUTE))
                button.connect("clicked", self.on_shell_button_clicked, commands[key])
                self.toolbar_shell.pack_end(button, False, True, 3)
            vbox.pack_start(self.toolbar_shell, False, True, 5)

        # Barre input + raz console
        self.toolbar_input = Gtk.HBox()
        vbox.pack_start(self.toolbar_input, False, True, 5)

        self.input_cmd = Gtk.SearchEntry()
        self.input_cmd.connect("activate", self.on_input_cmd_activate)
        self.toolbar_input.pack_start(self.input_cmd, True, True, 3)
        
        self.raz_button = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_DELETE))
        self.raz_button.set_tooltip_text("Nettoyer la console")
        self.raz_button.connect("clicked", self.on_raz_button_clicked)
        self.toolbar_input.pack_end(self.raz_button, False, True, 3)
        
        self.run_button = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_EXECUTE))
        self.run_button.connect("clicked", self.on_run_button_clicked)
        self.toolbar_input.pack_end(self.run_button, False, True, 3)

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
        # self.crud.logger.info(msg)

    def on_display(self, msg):
        print(msg)
        self.textbuffer.insert_at_cursor("\n" + msg, len(msg + "\n"))
        self.textview.set_cursor_visible(True)
        # Scoll to end of Buffer
        iter = self.textbuffer.get_iter_at_line(self.textbuffer.get_line_count())
        self.textview.scroll_to_iter(iter, 0, 0, 0, 0)
        # self.crud.logger.info(msg)

    def on_shell_button_clicked(self, widget, command):
        """ Démarrage du shell """
        # print command
        # self.emit("display", ">>> [%s]" % command)
        self.display(">>> [%s]" % command)

        # Methode 1
        # pid = self.spawn.run(str(command).split(" "))
        # print("Started as process #", pid)

        # Methode 2
        # self.source_id = None
        # pid, stdin, stdout, stderr = GLib.spawn_async(str(command).split(' '),
        #                                 flags=GLib.SpawnFlags.SEARCH_PATH,
        #                                 standard_output=True)
        # io = GLib.IOChannel(stdout)
        # self.source_id = io.add_watch(GLib.IO_IN|GLib.IO_HUP,
        #                               self.write_to_textview,
        #                               priority=GLib.PRIORITY_HIGH)

        # Methode 3
        # process = subprocess.Popen(str(command).split(" "), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True)
        # with process.stdout:
        #     for line in iter(process.stdout.readline, b''):
        #         print line,
        # process.wait() # wait for the subprocess to exit
        # while True:
        #     output = process.stdout.readline()
        #     while Gtk.events_pending():
        #         Gtk.main_iteration()
        #     if output == '' and process.poll() is not None:
        #         break
        #     if output:
        #         print(output.strip())
        #         # self.display(output.strip())

        # print "Process done %s" % process.poll()

        threading.Thread(target=self.thread_process, args=(command,)).start()

    def thread_process(self, command):
        process = subprocess.Popen(str(command).split(" "), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1024, universal_newlines=True)
        with process.stdout:
            for line in iter(process.stdout.readline, b''):
                while Gtk.events_pending():
                    Gtk.main_iteration()
                self.display(line)
        # process.wait() # wait for the subprocess to exit

    def on_input_cmd_activate(self, widget):
        """ CR dans le champ """
        self.run_button.do_activate(self.run_button)

    def on_run_button_clicked(self, widget):
        """ Démarrage du shell """
        command = self.input_cmd.get_text()
        self.display(">>> [%s]" % command)

        p = subprocess.Popen(str(command).split(" "), shell=True, stderr=subprocess.PIPE)
        while True:
            out = p.stderr.read(1)
            if out == '' and p.poll() != None:
                break
            if out != '':
                self.display(str(out))
                sys.stdout.write(str(out))
                sys.stdout.flush()

    def on_raz_button_clicked(self, widget):
        """ Nettoyage de la console """
        self.textbuffer.set_text('')

    def on_process_done(self, sender, retval):
        print("Done. exit code:", retval)

    def on_stdout_data(self, sender, line):
        # print "[STDOUT]", line.strip("\n")
        # while Gtk.events_pending():
        #     Gtk.main_iteration()
        self.display("%s" % line.strip("\n"))

    def on_stderr_data(self, sender, line):
        # print "[STDERR]", line.strip("\n")
        # while Gtk.events_pending():
        #     Gtk.main_iteration()
        self.display("ERR %s" % line.strip("\n"))

    # def write_to_textview(self, io, condition):
    #     print condition
    #     if condition is GLib.IO_IN:
    #         line = io.readline()
    #         self.textbuffer.insert_at_cursor(line)
    #         return True
    #     elif condition is GLib.IO_HUP|GLib.IO_IN:
    #         GLib.source_remove(self.source_id)
    #         return False

class MyStdout:
    def __init__(self, parent):
        self.parent = parent

    def write(self, string):
       if string:
           self.parent.emit("display", string)
        #    print string

class GAsyncSpawn(GObject.GObject):
    """ GObject class to wrap GLib.spawn_async().
    Use:
        s = GAsyncSpawn()
        s.connect('process-done', mycallback)
        s.run(command)
            #command: list of strings
    """
    __gsignals__ = {
        'process-done' : (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
                          (GObject.TYPE_INT, )),
        'stdout-data'  : (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
                          (GObject.TYPE_STRING, )),
        'stderr-data'  : (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
                          (GObject.TYPE_STRING, )),
    }
    def __init__(self):
        GObject.GObject.__init__(self)

    def run(self, cmd):
        """ Run de la commande """
        # print "GAsyncSpawn", cmd
        try:
            ret = GLib.spawn_async(cmd, flags=GLib.SPAWN_DO_NOT_REAP_CHILD|GLib.SPAWN_SEARCH_PATH, standard_output=True, standard_error=True)
        except:
            self._emit_std("stdout", sys.exc_info()[1])
            return

        self.pid, self.idin, self.idout, self.iderr = ret
        self.fout = os.fdopen(self.idout, "r")
        self.ferr = os.fdopen(self.iderr, "r")

        self.source_id = GLib.child_watch_add(self.pid, self._on_done)
        fout_id = GLib.io_add_watch(self.fout, GLib.IO_IN, self._on_stdout)
        GLib.io_add_watch(self.ferr, GLib.IO_IN, self._on_stderr)

        return self.pid

    def _on_done(self, pid, retval, *argv):
        # GLib.source_remove(self.source_id)
        # os.close(self.fout)
        # os.close(self.ferr)
        self.emit("process-done", retval)

    def _emit_std(self, name, value):
        while Gtk.events_pending():
            Gtk.main_iteration()
        self.emit(name + "-data", value)

    def _on_stdout(self, fobj, cond):
        for line in fobj:
            # print line
            while Gtk.events_pending():
                Gtk.main_iteration()
            self._emit_std("stdout", line)
        return True

    def _on_stderr(self, fobj, cond):
        for line in fobj:
            while Gtk.events_pending():
                Gtk.main_iteration()
            self._emit_std("stderr", line)
        return True
