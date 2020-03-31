# -*- coding:Utf-8 -*-
"""
    Fenêtre d'affichage de graphique
    Utilisation de la librairie matplotlib

    matplotlib. colors
    b : blue.
    g : green.
    r : red.
    c : cyan.
    m : magenta.
    y : yellow.
    k : black.
    w : white.

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
        """ Initialisation du widget après __init__ """
        # print ("do_init_widget {}({}) -> {}".format(str_from, str_arg, self.__class__))
        print("PicsouGraphDay.init... " + self.ptf_id)
        self.create_widget()

    def refresh_data(self):
        print("Refresh_data {}...".format(self.ptf_id))
        if self.vbox:
            self.update_widget()
            return True
        else:
            print("Refresh_data {} end ".format(self.ptf_id))
            return False

    def __init__(self, crud, arg):
        Gtk.Window.__init__(self, title="Graphique du jour")
        
        self.crud = crud
        self.ptf_id = arg

        # à revoir car perpétuel jusqu'à l'arrêt de l'application
        # GObject.timeout_add(1000 * 60 * 5, self.refresh_data)

    def create_widget(self):
        """ Construction du dessin et du toolbar """
        fig = self.create_graph()
        if fig:
            self.canvas = FigureCanvas(fig)  # a Gtk.DrawingArea
            self.canvas.set_size_request(800, 600)

            self.vbox = Gtk.VBox()
            self.vbox.pack_start(self.canvas, True, True, 0)

            self.toolbar = Gtk.HBox()
            navigationbar = NavigationToolbar(self.canvas, self)
            self.toolbar.pack_start(navigationbar, False, False, 0)
            button_url = Gtk.LinkButton("https://fr.finance.yahoo.com/chart/" + self.ptf_id, "Yahoo")
            self.toolbar.pack_end(button_url, False, False, 0)

            self.vbox.pack_end(self.toolbar, False, False, 0)
            self.add(self.vbox)

        self.show_all()

    def update_widget(self):
        self.remove(self.vbox)
        while Gtk.events_pending():
                Gtk.main_iteration()
        self.create_widget()

    def create_graph(self):
        """ """
        ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
        SELECT * FROM PTF WHERE ptf_id = :id
        """, {"id": self.ptf_id})
        ptf = ptfs[0]
        cdays = self.crud.sql_to_dict(self.crud.get_basename(), """
        SELECT * FROM cdays WHERE cdays_ptf_id = :id order by cdays_time
        """, {"id": self.ptf_id})

        self.set_title("Cours de " + self.ptf_id + " - " + ptf["ptf_name"])
        self.activate_focus()
        self.set_border_width(10)
        self.set_default_size(1200, 800)

        # Debut matplotlib

        cdays_times = []
        cdays_quotes = []
        cdays_opens = []
        cdays_rsi = []
        cdays_ema = []
        cdays_sma = []
        cdays_trades = []
        cdays_date = ""
        if len(cdays) > 0:
            for cday in cdays:
                cdays_date = cday["cdays_date"]
                cdays_times.append(cday["cdays_time"][11:16])
                cdays_quotes.append(float(cday["cdays_close"]))
                cdays_opens.append(float(cday["cdays_open"]))
                cdays_rsi.append(float(cday["cdays_rsi"]))
                cdays_ema.append(float(cday["cdays_ema"]))
                cdays_sma.append(float(cday["cdays_sma"]))
                if cday["cdays_trade"] in ('BUY', '...', 'SELL'):
                    cdays_trades.append(float(cday["cdays_close"]))
                else:
                    cdays_trades.append(None)

            fig, ax1 = plt.subplots()
            fig.set_figwidth(16)
            fig.set_figheight(9)
            ax1.plot(cdays_times, cdays_quotes, 'o-', label='Cours')
            ax1.plot(cdays_times, cdays_trades, 'o-', label='Trade', linewidth=2)
            ax1.plot(cdays_times, cdays_ema, 'r:', label='EMA')
            ax1.plot(cdays_times, cdays_sma, 'g:', label='SMA')
            ax1.plot(cdays_times, cdays_opens, 'k:', label='Open')
            ax1.set_ylabel('Cours (Euro)')
            ax1.set_xlabel('Heure')
            ax1.tick_params(axis="x", labelsize=6)
            ax1.legend(loc=3)

            ax2 = ax1.twinx()
            ax2.plot(cdays_times, cdays_rsi, 'm:', label='RSI')
            ax2.set_ylabel('RSI')
            ax2.legend(loc=4)

            fig.autofmt_xdate()
            plt.suptitle("{} {} du {} ".format(self.ptf_id, ptf["ptf_name"], cday["cdays_date"]))
            plt.subplots_adjust(left=0.08, bottom=0.1, right=0.93, top=0.93, wspace=None, hspace=None)
            plt.grid()
            
            png_path = "{}/png/{}.png".format(self.crud.get_application_prop("data_directory")
                ,self.ptf_id)
            plt.savefig(png_path)
            plt.close()

            return fig

