#!/usr/bin/env python
# -*- coding:Utf-8 -*-
"""
    Fenêtre d'affichage de graphique
    Utilisation de la librairie matplotlib

"""
from picsou_loader import PicsouLoadQuotes
from gi.repository import Gtk, GObject

class PicsouBatch(Gtk.Window):
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

        self.run_button = Gtk.Button(stock=Gtk.STOCK_REFRESH)
        self.run_button.set_always_show_image(True)
        self.run_button.set_tooltip_text("Démarrer l'actualisation...")
        self.run_button.connect("clicked", self.on_run_button_clicked)

        # self.cancel_button = Gtk.Button(stock=Gtk.STOCK_CANCEL)
        # self.cancel_button.set_always_show_image(True)
        # self.cancel_button.connect("clicked", self.on_cancel_button_clicked)

        self.close_button = Gtk.Button(stock=Gtk.STOCK_CLOSE)
        self.close_button.set_always_show_image(True)
        self.close_button.connect("clicked", self.on_close_button_clicked)

        self.with_mail = Gtk.CheckButton()
        self.with_mail.set_label("Envoyer le mail à la fin")
        self.with_mail.set_active(False)

        self.with_histo = Gtk.CheckButton()
        self.with_histo.set_label("Recharger l'historique")
        self.with_histo.set_active(False)

        self.with_simulation = Gtk.CheckButton()
        self.with_simulation.set_label("Simulation")
        self.with_simulation.set_active(False)

        vbox = Gtk.VBox()
        self.add(vbox)

        toolbar = Gtk.HBox()
        vbox.pack_start(toolbar, False, False, 0)

        toolbar.pack_start(self.with_simulation, True, True, 0)
        toolbar.pack_start(self.with_histo, True, True, 0)
        toolbar.pack_start(self.with_mail, True, True, 0)
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
        self.with_mail.set_sensitive(False)
        self.with_histo.set_sensitive(False)
        self.with_simulation.set_sensitive(False)
        self.close_button.set_sensitive(False)

        self.run_calcul()
        self.crud.get_view().emit("refresh_data", "batch", "close")

        # self.cancel_button.hide()
        self.run_button.set_sensitive(True)
        self.with_mail.set_sensitive(True)
        self.with_histo.set_sensitive(True)
        self.with_simulation.set_sensitive(True)
        self.close_button.set_sensitive(True)

    def display(self, msg):
        """ docstring """
        self.textbuffer.insert_at_cursor(msg + "\n", len(msg + "\n"))
        self.textview.set_cursor_visible(True)
        while Gtk.events_pending():
            Gtk.main_iteration()
        # Scoll to end of Buffer
        iter = self.textbuffer.get_iter_at_line(self.textbuffer.get_line_count())
        self.textview.scroll_to_iter(iter, 0, 0, 0, 0)
    
    def run_calcul(self):
        """ docstring """
        if self.with_histo.get_active():
            loader = PicsouLoadQuotes(self, self.crud)
            ptfs = self.crud.sql_to_dict(self.crud.get_table_prop("basename"), """
            SELECT * FROM ptf ORDER BY ptf_id
            """, {})
            for ptf in ptfs:
                while Gtk.events_pending():
                    Gtk.main_iteration()
                # Chargement de l'historique
                loader.run(ptf["ptf_id"], self.crudel.get_param("history"))
            return

        if self.with_simulation.get_active():
            loader = PicsouLoadQuotes(self, self.crud)
            loader.simulateur()
            return

        # Chargement des 10 derniers cours
        loader = PicsouLoadQuotes(self, self.crud)
        ptfs = self.crud.sql_to_dict(self.crud.get_table_prop("basename"), """
        SELECT * FROM ptf ORDER BY ptf_id
        """, {})
        for ptf in ptfs:
            while Gtk.events_pending():
                Gtk.main_iteration()
            # Chargement de l'historique
            loader.run(ptf["ptf_id"], 10)

        loader.simulateur()

        self.crud.exec_sql(self.crud.get_table_prop("basename"), """
        UPDATE PTF
        set ptf_gain = (ptf_quote - ptf_cost) * ptf_quantity
        WHERE ptf_inptf = 'PPP'
        """, {})
        self.crud.exec_sql(self.crud.get_table_prop("basename"), """
        UPDATE PTF
        set ptf_gain_percent = (ptf_gain / (ptf_cost * ptf_quantity)) * 100
        WHERE ptf_inptf = 'PPP'
        """, {})

        # mise à jour du résumé
        self.rsi_date = loader.quote["date"]
        # self.rsi_time = loader.quote["time"]
        self.rsi_time = "00:00"
        gain = self.crud.sql_to_dict(self.crud.get_table_prop("basename"), """
        SELECT sum(ptf_gain) AS result FROM PTF WHERE ptf_inptf = 'PPP'
        """, {})
        investi = self.crud.sql_to_dict(self.crud.get_table_prop("basename"), """
        SELECT sum(ptf_cost * ptf_quantity) AS result FROM PTF WHERE ptf_inptf = 'PPP'
        """, {})
        self.crud.exec_sql(self.crud.get_table_prop("basename"), """
        UPDATE RESUME
        set resume_date = :date 
        ,resume_time = :time 
        ,resume_investi = :investi
        ,resume_gain = :gain
        """, {"date": self.rsi_date, "time": self.rsi_time, "investi": investi[0]["result"], "gain": gain[0]["result"]})
        self.crud.exec_sql(self.crud.get_table_prop("basename"), """
        UPDATE RESUME
        set resume_percent = (resume_gain / resume_investi) * 100
        """, {})

        # Mail de compte-rendu
        if self.with_mail.get_active():
            # TOP 14
            ptfs = self.crud.sql_to_dict(self.crud.get_table_prop("basename"), """
            select * from ptf order by ptf_macd desc limit 14
            """, {})
            for ptf in ptfs:
                url = '<a href="https://fr.finance.yahoo.com/chart/{0}">{0}</a>'.format(ptf["ptf_id"])
                msg = """<tr>
                <td style="text-align: right">{0:3.2f}%</td>
                <td>{1}</td><td>{2}</td>
                <td style="text-align: right">{3:.2f}</td>
                <td style="text-align: right">{4:.2f}%</td>
                <td>{5}</td>
                </tr>
                """.format(ptf["ptf_macd"], ptf["ptf_inptf"], ptf["ptf_name"], ptf["ptf_quote"], ptf["ptf_percent"], url)
                self.top14.append(msg)

            # Mon portefeuille
            ptfs = self.crud.sql_to_dict(self.crud.get_table_prop("basename"), """
            select * from ptf order by ptf_gain_percent desc
            """, {})
            msg = """<tr>
            <th>Action</th>
            <th>Cours</th>
            <th>du J</th>
            <th>Revient</th>
            <th>Nbre</th>
            <th>Gain</th>
            <th>en %</th>
            <th>14 j</th>
            <th>&nbsp;</th>
            </tr>"""
            self.myptf.append(msg)
            for ptf in ptfs:
                url = '<a href="https://fr.finance.yahoo.com/chart/{0}">{0}</a>'.format(ptf["ptf_id"])                
                if ptf["ptf_inptf"] == "PPP" :
                    msg = """<tr>
                    <td>{0}</td>
                    <td style="text-align: right">{1:.2f}</td>
                    <td style="text-align: right">{2:.2f}%</td>
                    <td style="text-align: right">{3:.2f}</td>
                    <td style="text-align: right">{4}</td>
                    <td style="text-align: right">{5:.2f} €</td>
                    <td style="text-align: right">{6:.2f}%</td>
                    <td style="text-align: right">{7:.2f}%</td>
                    <td>{8}</td>
                    </tr>""".format(ptf["ptf_name"], ptf["ptf_quote"], ptf["ptf_percent"], ptf["ptf_cost"], ptf["ptf_quantity"], ptf["ptf_gain"], ptf["ptf_gain_percent"], ptf["ptf_macd"], url)                     
                    self.myptf.append(msg)

                if ptf["ptf_inptf"] == "PPP" and ptf["ptf_resistance"] == "RRR":
                    msg = '<tr><td>{0}</td><td>{1}</td><td style="text-align: right">{2:.2f}</td><td>{3}</td></tr>'\
                    .format(ptf["ptf_date"], ptf["ptf_name"], ptf["ptf_quote"], url)
                    self.resistances.append(msg)

                if ptf["ptf_support"] == "SSS":
                    msg = '<tr><td>{0}</td><td>{1}</td><td style="text-align: right">{2:.2f}</td><td style="text-align: right">{3}</td><td>{4}</td></tr>'\
                    .format(ptf["ptf_date"], ptf["ptf_name"], ptf["ptf_quote"], ptf["ptf_quantity"], url)
                    self.supports.append(msg)

            # envoi du mail
            msg = '<h3>{}</h3>\n<table>\n'.format("Mes actions au {} gain {:.2f} €".format(self.rsi_date, gain[0]["result"]))
            msg += '\n'.join(self.myptf)
            msg += '</table>\n'
            msg += "<h3>{}</h3>\n<table>\n".format(self.crudel.get_param("label_resistance"))
            msg += '\n'.join(self.resistances)
            msg += '</table>\n'
            msg += "<h3>{}</h3>\n<table>\n".format(self.crudel.get_param("label_support"))
            msg += '\n'.join(self.supports)
            msg += '</table>\n'
            msg += "<h3>{}</h3>\n<table>\n".format(self.crudel.get_param("label_top14"))
            msg += '\n'.join(self.top14)
            msg += '</table>\n'
            dest = self.crudel.get_param("smtp_dest")

            self.crud.send_mail(dest, "Picsou du {} gain {:.2f} €".format(self.rsi_date, gain[0]["result"]), msg)
