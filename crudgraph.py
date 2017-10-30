#!/usr/bin/env python
# -*- coding:Utf-8 -*-
"""
    Fenêtre d'affichage de graphique
    Utilisation de la librairie matplotlib

"""
from datetime import datetime

from gi.repository import Gtk

# import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.backends.backend_gtk3 import NavigationToolbar2GTK3 as NavigationToolbar


class CrudGraph(Gtk.Window):
    """ Affichage d'un graphique dans une Gtk.Window """
    def __init__(self, crud):
        Gtk.Window.__init__(self, title="Graphique")

        self.crud = crud
        

        # application = self.crud.get_json_content(
        #     self.crud.config["application_directory"] + "/" + "picsou.json")
        # self.crud.set_application(application)
        # self.crud.set_table_id("cours")
        # cours = self.crud.sql_to_dict(self.crud.get_table_prop("basename"),\
        #     "SELECT * FROM cours WHERE cours_ptf_id = 'TFI.PA' order by cours_date",\
        #     {}
        # )

        # self.set_title("Cours de " + ptf["ptf_id"] + " - " + ptf["ptf_name"])
        self.activate_focus()
        self.set_border_width(10)
        self.set_default_size(1200, 800)

        # """ Debut matplotlib """

        # cours_dates = []
        # cours_quotes = []
        # cours_ema12 = []
        # cours_ema26 = []
        # cours_ema50 = []
        # cours_trade = []
        # cours_ppp = []
        # cours_volume = []
        # cours_rsi = []
        # for cour in cours:
        #     dt = datetime.strptime(cour["cours_date"], '%Y-%m-%d')
        #     cours_dates.append(dt)
        #     cours_quotes.append(float(cour["cours_close"]))
        #     cours_ema12.append(float(cour["cours_ema12"]))
        #     cours_ema26.append(float(cour["cours_ema26"]))
        #     cours_ema50.append(float(cour["cours_ema50"]))
        #     if cour["cours_trade"] in ('SSS', 'TTT', 'RRR'):
        #         cours_trade.append(float(cour["cours_close"]))
        #     else:
        #         cours_trade.append(None)
        #     if ptf["ptf_date"] != "" and cour["cours_date"] >= ptf["ptf_date"]:
        #         cours_ppp.append(float(cour["cours_close"]))
        #     else:
        #         cours_ppp.append(None)
        #     cours_volume.append(float(cour["cours_volume"]))
        #     cours_rsi.append(float(cour["cours_rsi"]))

        # # plt.style.use('seaborn-paper')
        # # fig = plt.figure()
        # # ax1 = plt.subplot(111)

        # fig, ax1 = plt.subplots()

        # ax1.plot(cours_dates, cours_quotes, 'o-', label='Cours')
        # ax1.plot(cours_dates, cours_ema12, '-', label='EMA 12')
        # ax1.plot(cours_dates, cours_ema26, '-', label='EMA 26')
        # ax1.plot(cours_dates, cours_ema50, '-', label='EMA 50')
        # ax1.plot(cours_dates, cours_trade, 'o-', label='Simul', linewidth=2)
        # ax1.plot(cours_dates, cours_ppp, 'o-', label='Réel'.decode("utf-8"), linewidth=2)
        # ax1.set_ylabel('Cours (Euro)')
        # ax1.set_xlabel('Date')
        # ax1.legend(loc=3)

        # # format the ticks
        # # days = mdates.DayLocator()
        # # daysFmt = mdates.DateFormatter('%d')
        # # months = mdates.MonthLocator()
        # # monthsFmt = mdates.DateFormatter('%Y-%m')
        # # ax1.xaxis.set_major_locator(months)
        # # ax1.xaxis.set_major_formatter(monthsFmt)
        # # ax1.xaxis.set_minor_locator(days)
        # # ax1.xaxis.set_minor_formatter(daysFmt)

        # ax2 = ax1.twinx()
        # ax2.plot(cours_dates, cours_rsi, '--', label='RSI')
        # ax2.set_ylabel('RSI')
        # ax2.legend(loc=4)

        # fig.autofmt_xdate()
        # plt.suptitle("Cours de " + ptf_id + " - " + ptf["ptf_name"])
        # plt.grid()
        # # plt.savefig('dates-tutorial01.png')
        # # plt.show()

        # canvas = FigureCanvas(fig)  # a Gtk.DrawingArea
        # canvas.set_size_request(800, 600)

        # vbox = Gtk.VBox()
        # self.add(vbox)
        # vbox.pack_start(canvas, True, True, 0)
        # toolbar = NavigationToolbar(canvas, self)
        # vbox.pack_end(toolbar, False, False, 0)

        # sw = Gtk.ScrolledWindow()
        # self.add(sw)
        # # A scrolled window border goes outside the scrollbars and viewport
        # sw.set_border_width(10)
        # sw.add_with_viewport(canvas)

        # self.add(Gtk.Label("This is another window"))
        self.show_all()