# -*- coding:Utf-8 -*-
"""
    Fenêtre d'affichage de graphique
    Utilisation de la librairie matplotlib

"""
import shutil
import os
import datetime, time
from .picsou_loader import PicsouLoadQuotes, PicsouLoader
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

        self.with_coursdujour = Gtk.CheckButton()
        self.with_coursdujour.set_label("Cours de jour")
        self.with_coursdujour.set_active(False)

        self.with_schedule = Gtk.CheckButton()
        self.with_schedule.set_label("Boucle 10 minutes")
        self.with_schedule.set_active(False)

        vbox = Gtk.VBox()
        self.add(vbox)

        toolbar = Gtk.HBox()
        vbox.pack_start(toolbar, False, False, 0)

        toolbar.pack_start(self.with_coursdujour, True, True, 0)
        toolbar.pack_start(self.with_schedule, True, True, 0)
        # toolbar.pack_start(self.with_simulation, True, True, 0)
        # toolbar.pack_start(self.with_histo, True, True, 0)
        # toolbar.pack_start(self.with_mail, True, True, 0)
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
        self.with_coursdujour.set_sensitive(False)
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
        self.with_coursdujour.set_sensitive(True)
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
        self.textbuffer.Text = ""
        while Gtk.events_pending():
            Gtk.main_iteration()


    def run_calcul(self):
        """ docstring """
        self.display(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") + " : run_calcul" )
        if self.with_histo.get_active():
            loader = PicsouLoadQuotes(self, self.crud)
            ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
            SELECT * FROM ptf where ptf_disabled is null or ptf_disabled <> '1' ORDER BY ptf_id
            """, {})
            for ptf in ptfs:
                while Gtk.events_pending():
                    Gtk.main_iteration()
                # Chargement de l'historique
                loader.run(ptf["ptf_id"], 500)
            return

        if self.with_simulation.get_active():
            loader = PicsouLoadQuotes(self, self.crud)
            loader.simulateur()
            loader.account()
            return

        if self.with_coursdujour.get_active():
            loader = PicsouLoader(self, self.crud)
            ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
            SELECT * FROM ptf where ptf_disabled is null or ptf_disabled <> '1' ORDER BY ptf_id
            """, {})
            for ptf in ptfs:
                while Gtk.events_pending():
                    Gtk.main_iteration()
                # Chargement de l'historique
                loader.run(ptf["ptf_id"], 7)

            loader.trade()

            return

        # Chargement des 10 derniers cours
        loader = PicsouLoadQuotes(self, self.crud)
        ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
        SELECT * FROM ptf 
        where ptf_disabled is null or ptf_disabled <> '1'
        ORDER BY ptf_id
        """, {})
        for ptf in ptfs:
            while Gtk.events_pending():
                Gtk.main_iteration()
            # Chargement de l'historique
            loader.run(ptf["ptf_id"], 10)

        loader.simulateur()
        loader.account()

        rows = self.crud.sql_to_dict(self.crud.get_basename(), """
        SELECT printf('SIMUL
        Gain du jour: %8.2f €
                Cash: %8.2f €
              Espèce: %8.2f €
                Gain: %8.2f €
              Latent: %8.2f €
                 soit %8.2f prc
        ', acc_gain_day, acc_initial, acc_money, acc_gain, acc_latent, acc_percent) AS sql_footer
        FROM ACCOUNT where acc_id = 'SIMUL'
        """, {})
        self.display(rows[0]["sql_footer"])

        # Mail de compte-rendu
        if self.with_mail.get_active():
            # TOP 14
            ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
            select * from ptf order by ptf_q26 desc limit 14
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
                """.format(ptf["ptf_q26"], ptf["ptf_account"], ptf["ptf_name"], ptf["ptf_quote"], ptf["ptf_percent"], url)
                self.top14.append(msg)

            # Mon portefeuille
            ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
            select * from ptf order by ptf_gainp desc
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
                if ptf["ptf_account"] is not None and ptf["ptf_account"] != "":
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
                    </tr>""".format(ptf["ptf_name"], ptf["ptf_quote"], ptf["ptf_percent"], ptf["ptf_cost"], ptf["ptf_quantity"], ptf["ptf_gain"], ptf["ptf_gainp"], ptf["ptf_q26"], url)                     
                    self.myptf.append(msg)

                if ptf["ptf_account"] is not None and ptf["ptf_account"] != "" and ptf["ptf_trade"] == "RRR":
                    msg = '<tr><td>{0}</td><td>{1}</td><td style="text-align: right">{2:.2f}</td><td>{3}</td></tr>'\
                    .format(ptf["ptf_date"], ptf["ptf_name"], ptf["ptf_quote"], url)
                    self.resistances.append(msg)

                if ptf["ptf_trade"] == "SSS":
                    msg = '<tr><td>{0}</td><td>{1}</td><td style="text-align: right">{2:.2f}</td><td style="text-align: right">{3}</td><td>{4}</td></tr>'\
                    .format(ptf["ptf_date"], ptf["ptf_name"], ptf["ptf_quote"], ptf["ptf_quantity"], url)
                    self.supports.append(msg)

            # envoi du mail
            # msg = '<h3>{}</h3>\n<table>\n'.format("Mes actions au {} gain {:.2f} €".format(self.rsi_date, gain[0]["result"]))
            # msg += '\n'.join(self.myptf)
            # msg += '</table>\n'
            # msg += "<h3>{}</h3>\n<table>\n".format(self.crudel.get_param("label_resistance"))
            # msg += '\n'.join(self.resistances)
            # msg += '</table>\n'
            # msg += "<h3>{}</h3>\n<table>\n".format(self.crudel.get_param("label_support"))
            # msg += '\n'.join(self.supports)
            # msg += '</table>\n'
            # msg += "<h3>{}</h3>\n<table>\n".format(self.crudel.get_param("label_top14"))
            # msg += '\n'.join(self.top14)
            # msg += '</table>\n'
            # dest = self.crudel.get_param("smtp_dest")

            # subject = u"Picsou du {} gain {:.2f} €".format(self.rsi_date, gain[0]["result"])
            # self.crud.send_mail(dest, subject, msg)
