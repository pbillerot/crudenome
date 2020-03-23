# -*- coding:Utf-8 -*-
"""
    Fenêtre d'affichage de graphique
    Utilisation de la librairie matplotlib

"""
from datetime import datetime

from crudel import Crudel

from gi.repository import Gtk, GObject

# import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.backends.backend_gtk3 import NavigationToolbar2GTK3 as NavigationToolbar

class PicsouGraphDay(Gtk.Window):

    """ Affichage d'un graphique dans une Gtk.Window """
    __gsignals__ = {
        'init_widget': (GObject.SIGNAL_RUN_FIRST, None, (str, str,))
    }
    def do_init_widget(self, str_from, str_arg=""):
        """ Traitement du signal """
        # print "do_init_widget %s(%s) -> %s" % (str_from, str_arg, self.__class__)

    def __init__(self, crud):
        Gtk.Window.__init__(self, title="Graphique du jour")

        self.crud = crud
        self.crudel = crud.get_crudel()
        # relecture de l'enregistrement de la vue
        rows = self.crud.get_sql_row(Crudel.TYPE_PARENT_VIEW)
        for row in rows:
            for element in self.crud.get_view_elements():
                crudel = Crudel.instantiate(self.crud, element, Crudel.TYPE_PARENT_VIEW)
                crudel.init_value()
                self.crud.set_element_prop(element, "crudel", crudel)
                if row.get(element, False):
                    crudel.set_value_sql(row[element])
        values = self.crud.get_table_values()
        ptf_id = self.crudel.get_param_replace("ptf_id")
        ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
        SELECT * FROM PTF WHERE ptf_id = :id
        """, {"id": ptf_id})
        ptf = ptfs[0]
        cdays = self.crud.sql_to_dict(self.crud.get_basename(), """
        SELECT * FROM cdays WHERE cdays_ptf_id = :id order by cdays_time
        """, {"id": ptf_id})

        self.set_title("Cours de " + ptf_id + " - " + ptf["ptf_name"])
        self.activate_focus()
        self.set_border_width(10)
        self.set_default_size(1200, 800)

        # Debut matplotlib

        cdays_times = []
        cdays_quotes = []
        cdays_ema = []
        cdays_sma = []
        cdays_min = []
        cdays_max = []
        for cday in cdays:
            cdays_times.append(cday["cdays_time"][11:16])
            cdays_quotes.append(float(cday["cdays_close"]))
            cdays_ema.append(float(cday["cdays_ema"]))
            cdays_sma.append(float(cday["cdays_sma"]))
            cdays_min.append(float(cday["cdays_min"]))
            cdays_max.append(float(cday["cdays_max"]))

        fig, ax1 = plt.subplots()

        ax1.plot(cdays_times, cdays_quotes, 'o-', label='Cours')
        ax1.plot(cdays_times, cdays_ema, '-', label='EMA')
        ax1.plot(cdays_times, cdays_sma, '-', label='SMA')
        ax1.plot(cdays_times, cdays_min, '-', label='MIN')
        ax1.plot(cdays_times, cdays_max, '-', label='Max')
        ax1.set_ylabel('Cours (Euro)')
        ax1.set_xlabel('Heure')
        ax1.legend(loc=3)

        fig.autofmt_xdate()
        plt.suptitle("Cours du jour de " + ptf_id + " - " + ptf["ptf_name"])
        plt.grid()

        canvas = FigureCanvas(fig)  # a Gtk.DrawingArea
        canvas.set_size_request(800, 600)

        vbox = Gtk.VBox()
        self.add(vbox)
        vbox.pack_start(canvas, True, True, 0)

        toolbar = Gtk.HBox()
        navigationbar = NavigationToolbar(canvas, self)
        toolbar.pack_start(navigationbar, False, False, 0)
        button_url = Gtk.LinkButton("https://fr.finance.yahoo.com/chart/" + ptf_id, "Yahoo")
        toolbar.pack_end(button_url, False, False, 0)

        vbox.pack_end(toolbar, False, False, 0)

        self.show_all()

class PicsouGraph(Gtk.Window):

    """ Affichage d'un graphique dans une Gtk.Window """
    __gsignals__ = {
        'init_widget': (GObject.SIGNAL_RUN_FIRST, None, (str, str,))
    }
    def do_init_widget(self, str_from, str_arg=""):
        """ Traitement du signal """
        # print "do_init_widget %s(%s) -> %s" % (str_from, str_arg, self.__class__)

    def __init__(self, crud):
        Gtk.Window.__init__(self, title="Graphique")

        self.crud = crud
        self.crudel = crud.get_crudel()
        # relecture de l'enregistrement de la vue
        rows = self.crud.get_sql_row(Crudel.TYPE_PARENT_VIEW)
        for row in rows:
            for element in self.crud.get_view_elements():
                crudel = Crudel.instantiate(self.crud, element, Crudel.TYPE_PARENT_VIEW)
                crudel.init_value()
                self.crud.set_element_prop(element, "crudel", crudel)
                if row.get(element, False):
                    crudel.set_value_sql(row[element])
        values = self.crud.get_table_values()
        ptf_id = self.crudel.get_param_replace("ptf_id")
        ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
        SELECT * FROM PTF WHERE ptf_id = :id
        """, {"id": ptf_id})
        ptf = ptfs[0]
        cours = self.crud.sql_to_dict(self.crud.get_basename(), """
        SELECT * FROM cours WHERE cours_ptf_id = :id order by cours_date
        """, {"id": ptf_id})

        self.set_title("Cours de " + ptf_id + " - " + ptf["ptf_name"])
        self.activate_focus()
        self.set_border_width(10)
        self.set_default_size(1200, 800)

        # Debut matplotlib

        cours_dates = []
        cours_quotes = []
        cours_ema12 = []
        cours_ema26 = []
        cours_ema50 = []
        cours_trade = []
        cours_ppp = []
        cours_volume = []
        cours_rsi = []
        for cour in cours:
            dt = datetime.strptime(cour["cours_date"], '%Y-%m-%d')
            cours_dates.append(dt)
            cours_quotes.append(float(cour["cours_close"]))
            cours_ema12.append(float(cour["cours_ema12"]))
            cours_ema26.append(float(cour["cours_ema26"]))
            cours_ema50.append(float(cour["cours_ema50"]))
            if cour["cours_trade"] in ('SSS', 'TTT', 'RRR'):
                cours_trade.append(float(cour["cours_close"]))
            else:
                cours_trade.append(None)
            if ptf["ptf_date"] != "" and cour["cours_date"] >= ptf["ptf_date"]:
                cours_ppp.append(float(cour["cours_close"]))
            else:
                cours_ppp.append(None)
            cours_volume.append(float(cour["cours_volp"]) * 0.6)
            cours_rsi.append(float(cour["cours_rsi"]))

        # plt.style.use('seaborn-paper')
        # fig = plt.figure()
        # ax1 = plt.subplot(111)

        fig, ax1 = plt.subplots()

        ax1.plot(cours_dates, cours_quotes, 'o-', label='Cours')
        ax1.plot(cours_dates, cours_ema12, '-', label='EMA 12')
        ax1.plot(cours_dates, cours_ema26, '-', label='EMA 26')
        ax1.plot(cours_dates, cours_ema50, '-', label='EMA 50')
        ax1.plot(cours_dates, cours_trade, 'o-', label='Simul', linewidth=2)
        ax1.plot(cours_dates, cours_ppp, 'o-', label='Réel', linewidth=2)
        ax1.set_ylabel('Cours (Euro)')
        ax1.set_xlabel('Date')
        ax1.legend(loc=3)

        # format the ticks
        # days = mdates.DayLocator()
        # daysFmt = mdates.DateFormatter('%d')
        # months = mdates.MonthLocator()
        # monthsFmt = mdates.DateFormatter('%Y-%m')
        # ax1.xaxis.set_major_locator(months)
        # ax1.xaxis.set_major_formatter(monthsFmt)
        # ax1.xaxis.set_minor_locator(days)
        # ax1.xaxis.set_minor_formatter(daysFmt)

        ax2 = ax1.twinx()
        ax2.plot(cours_dates, cours_rsi, 'm:', label='RSI')
        ax2.bar(cours_dates, cours_volume, align='center', alpha=0.5, label='Volume')
        # ax2.plot(cours_dates, cours_volume, 'c:', label='Volume')
        ax2.set_ylabel('RSI ou Volume')
        ax2.legend(loc=4)

        fig.autofmt_xdate()
        plt.suptitle("Cours de " + ptf_id + " - " + ptf["ptf_name"])
        plt.grid()
        # plt.savefig('dates-tutorial01.png')
        # plt.show()

        canvas = FigureCanvas(fig)  # a Gtk.DrawingArea
        canvas.set_size_request(800, 600)

        vbox = Gtk.VBox()
        self.add(vbox)
        vbox.pack_start(canvas, True, True, 0)

        toolbar = Gtk.HBox()
        navigationbar = NavigationToolbar(canvas, self)
        toolbar.pack_start(navigationbar, False, False, 0)
        button_url = Gtk.LinkButton("https://fr.finance.yahoo.com/chart/" + ptf_id, "Yahoo")
        toolbar.pack_end(button_url, False, False, 0)

        vbox.pack_end(toolbar, False, False, 0)

        # sw = Gtk.ScrolledWindow()
        # self.add(sw)
        # # A scrolled window border goes outside the scrollbars and viewport
        # sw.set_border_width(10)
        # sw.add_with_viewport(canvas)

        # self.add(Gtk.Label("This is another window"))

        self.show_all()
