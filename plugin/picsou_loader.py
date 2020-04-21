# -*- coding:Utf-8 -*-
"""
Import des n derniers cours d'une action
"""
import sqlite3
import time
import datetime
import re
import sys
import requests
import numpy as np
from gi.repository import Gtk
from plugin.picsou_graph import PicsouGraphDay

class PicsouLoader():
    """
    Import du derniers cours du jour d'une action et simulation de trading
    """
    def __init__(self, parent, crud):

        self.crud = crud # framework de gestion de l'interface Gnome Gtk
        self.crudel = crud.get_crudel() # framework de gestion des éléments 
        self.parent = parent

        # la requête yahoo finace requiert un cookie
        self.cookie, self.crumb = self.get_cookie_crumb("ACA.PA") 
        self.quote = {} # dernière cotation

    def quotes(self):
        ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
        SELECT * FROM ptf where ptf_enabled = '1' ORDER BY ptf_id
        """, {})
        self.pout("Quote of ")
        for ptf in ptfs:
            while Gtk.events_pending():
                Gtk.main_iteration()
            self.pout(" {}".format(ptf["ptf_id"]))

            # Chargement de l'historique
            qlast = self.crud.get_application_prop("constants")["qlast_quotes"]
            self.csv_to_quotes(ptf, qlast)

            # Calcul du percent par rapport à la veille
            cours = self.crud.sql_to_dict(self.crud.get_basename(), """
            SELECT * FROM quotes WHERE id = :id order by id ,date
            """, {"id": ptf["ptf_id"]})
            if len(cours) > 0:
                close1 = 0.0
                for quote in cours:
                    if close1 == 0.0 : 
                        close1 = quote["open"]
                    self.crud.exec_sql(self.crud.get_basename(), """
                    update quotes set close1 = :close1 where id = :id and date = :date
                    """, {"id": quote["id"], "close1": close1, "date": quote["date"]})
                    close1 = quote["close"]

            # Suppression des cours des jours antérieurs
            self.crud.exec_sql(self.crud.get_basename(), """
            delete from cdays
            where cdays_date <> date('now')
            """, {})
            # insertion du dernier cours récupéré dans self.quote
            self.crud.exec_sql(self.crud.get_basename(), """
            insert into cdays
            (cdays_ptf_id, cdays_name, cdays_date, cdays_close
            , cdays_open, cdays_volume, cdays_low, cdays_high, cdays_time, cdays_close1)
            select id, name, date, close, open, volume, low, high, datetime('now', 'localtime'), close1
            from quotes
            where quotes.id = :id and quotes.date = date('now')
            """, {"id": ptf["ptf_id"]})
            # calcul cours_percent
            self.crud.exec_sql(self.crud.get_basename(), """
            UPDATE cdays
            set cdays_percent = ( (cdays_close - cdays_close1) / cdays_close1) * 100 
            """, {})

    def trade(self, with_sms=False):
        """
        Simulation d'achat et de vente d'actions à partir du cours de la journée
        https://www.abcbourse.com/apprendre/11_lecon3.html
        Voici ce qui fait le succès de la MACD: le signal arrive encore plus tôt que la détection par croisement des MMA20 et MMA50 de la dernière leçon. Mais cela en fait aussi le danger, car retenez bien que plus un indicateur signale tôt, plus il a tendance à se tromper. Il faut donc travailler la MACD avec d'autres artifices pour confirmer sa validité.
        Une règle de validation vient s'ajouter à cette règle de base. Lors du croisement de la MACD avec sa ligne de signal, on ne rentrera que si la MACD et le signal ont été du même côté pendant un minimum de 14 séances que l'on compte à l'envers en comptant le jour du croisement. Ce minimum permet de s'assurer que l'on était dans une situation suffisamment stable pour que le croisement de la MACD avec sa ligne de signal ait du sens.
        """
        rsimin = self.crud.get_application_prop("constants")["rsimin"]
        rsimax = self.crud.get_application_prop("constants")["rsimax"]
        macdbuy = self.crud.get_application_prop("constants")["macdbuy"]
        hours_limit = self.crud.get_application_prop("constants")["hours_limit"]
        minutes_limit = self.crud.get_application_prop("constants")["minutes_limit"]
        declench_percent = self.crud.get_application_prop("constants")["declench_percent"]
        # Calcul du timestamp du jour à 17 heures 20 (heure limite d'achat)
        time_limit = datetime.datetime.now().replace(hour=hours_limit, minute=minutes_limit, second=0, microsecond=0).timestamp()

        # Nettoyage de la simulation du jour
        datetoday = datetime.datetime.now().strftime("%Y-%m-%d")
        self.crud.exec_sql(self.crud.get_basename(), """
        delete from trades where trades_date = :date
        """, {"date": datetoday})

        # Boucle sur les PTF
        ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
        SELECT * FROM ptf WHERE ptf_enabled = '1'
        ORDER BY ptf_id
        """, {})
        fcostp = self.crud.get_application_prop("constants")["cost"] # coût de la transaction ex: 0.012 %
        fstake = self.crud.get_application_prop("constants")["stake"] # mise ou enjeu
        fday = 0.0
        journal = []
        self.display("")
        self.pout("Trade...")
        with_cday = False
        for ptf in ptfs:
            self.pout(" " + ptf["ptf_id"])
            while Gtk.events_pending():
                Gtk.main_iteration() # libération des messages UI

            # Chargement des actions à suivres
            is_in_orders = False 
            orders = self.crud.sql_to_dict(self.crud.get_basename(), """
            SELECT * FROM orders where orders_ptf_id = :id and orders_order = 'buy' ORDER BY orders_ptf_id
            """, {"id": ptf["ptf_id"]})
            if len(orders) > 0 : is_in_orders = True 

            # Boucle sur les COURS du PTF
            sql = """SELECT * FROM cdays
            WHERE cdays_ptf_id = :ptf_id
            ORDER BY cdays_time ASC"""
            cdays = self.crud.sql_to_dict(self.crud.get_basename(), """
            SELECT * FROM cdays
            WHERE cdays_ptf_id = :ptf_id
            ORDER BY cdays_time ASC
            """, ptf)

            quote = 0.0
            quote1 = 0.0
            quote2 = 0.0
            quote3 = 0.0
            nbc = 0
            quotes = []
            rsi = 50
            rsi1 = 0.0
            ema = 0.0
            ema1 = 0.0
            sma = 0.0
            sma0 = 0.0
            sma1 = 0.0
            sma2 = 0.0
            sma3 = 0.0
            emas = []
            smas = []
            trade = ""
            cday_time = 0
            cday_time_buy = 0
            fbuy = 0.0
            fachat = 0.0
            fsell = 0.0
            fvente = 0.0
            iquantity = 0
            fgain = 0.0
            fgainp = 0.0
            trade = ""
            cas = ""
            # Gestion des volumes
            vol = 0
            vol1 = 0 # vol - 1 pour calculer le delta dvol
            dvol = 0
            dvols = [] # vol1 - vol
            vevo = 0 # % / max dvols
            vevos = [] 
            if len(cdays) > 0 :
                with_cday = True
                for cday in cdays:
                    nbc+=1
                    quote3 = quote2
                    quote2 = quote1
                    quote1 = quote
                    rsi1 = rsi
                    ema1 = ema
                    sma3 = sma2
                    sma2 = sma1
                    sma1 = sma
                    vol1 = vol

                    # Calcul du timestamp du cours courant
                    cday_time_str = datetime.datetime.strptime(cday["cdays_time"], '%Y-%m-%d %H:%M:%S')
                    cday_time = cday_time_str.timestamp()
                    # Calcul du timestamp du jour à 17 heures 20 (heure limite d'achat)
                    time_limit = cday_time_str.replace(hour=hours_limit, minute=minutes_limit, second=0, microsecond=0).timestamp()

                    quote = cday["cdays_close"]
                    quotes.append(quote)
                    vol = cday["cdays_volume"]
                    dvol = vol - vol1
                    dvols.append(dvol)

                    # vevo = (dvol/max(dvols))*100
                    vevo = (dvol/max(dvols))*100

                    sma = self.sma(quotes, 14)
                    if nbc == 1 : sma0 = sma
                    if nbc > 13 : 
                        rsi = self.rsi(quotes, 14)
                        window = nbc//2 if nbc < 28 else 14
                        ema = self.ema(quotes, window)
                    else:
                        ema = sma

                    if trade == "BUY" : trade = "..."
                    if trade == "SELL": trade = ""

                    # SMS si macd et si is_in_orders
                    if is_in_orders :
                        url = "https://fr.finance.yahoo.com/chart/{}".format(ptf["ptf_id"])
                        if trade == "..." and self.is_macd_sell(ema1, sma1, ema, sma) : 
                            if with_sms :
                                msg = "PICSOU VENTE {} : actions à {:7.2f} €".format(ptf["ptf_id"], quote)
                                self.crud.send_sms(msg)
                        if trade == "..." and rsi > rsimax : 
                            if with_sms :
                                msg = "PICSOU VENTE {} : actions à {:7.2f} €".format(ptf["ptf_id"], quote)
                                self.crud.send_sms(msg)
                        if trade == "" and cday_time > time_limit and cday["cdays_percent"] < declench_percent:
                            trade = "BUY"
                            if with_sms :
                                msg = "PICSOU ACHAT {} : {} actions à {:7.2f} €".format(ptf["ptf_id"], int(fstake//quote), quote)
                                self.crud.send_sms(msg)
                    else :
                        if trade in ("BUY","...") : # l'action a été vendue car n'est plus présent dans orders
                            trade = "SELL"

                    # VENTE
                    # if trade in ("BUY","..."):
                    #     if rsi > rsimax : trade = "SELL"
                    #     if self.is_macd_sell(ema1, sma1, ema, sma) : trade = "SELL"

                    # ACHAT 
                    # if trade == "WAIT" : 
                    #     if rsi > rsi1 : trade = "BUY" 

                    # cas = "!rsi macd_buy < {} ,rsi macd_sell".format(macdbuy)

                    # if trade == "":
                    #     # if rsi < rsimin : trade = "BUY"
                    #     if self.is_macd_buy(ema1, sma1, ema, sma) and rsi < macdbuy : trade = "BUY"

                    # # FIN DE JOURNEE, on vend tout avant la cloture
                    # if cday_time > time_limit : 
                    #     if trade == "BUY" : trade = ""
                    #     if trade == "..." : trade = "SELL"

                    # TRAITEMENT DU BUY ET SELL
                    if trade == "BUY":
                        cday_time_buy = cday["cdays_time"]
                        fbuy = quote
                        iquantity = fstake//fbuy
                        # On augmente la banque si pas assez de cash
                        fcost_buy = fbuy*iquantity*fcostp
                        fachat = fbuy*iquantity + fcost_buy
                        journal.append({"time": cday["cdays_time"], "ope": -fachat
                        ,"message": "{} ...ACHAT {} \tde {:3.0f} actions à {:7.2f} € soit {:7.2f} € net (frais {:5.2f} €)"
                        .format(cday["cdays_time"], cday["cdays_ptf_id"], iquantity, fbuy, fachat, fcost_buy)
                        })

                        # Enregistrement du trade
                        self.crud.exec_sql(self.crud.get_basename(), """
                        insert into trades (trades_ptf_id, trades_date, trades_time, trades_order, trades_buy, trades_sell
                        ,trades_quantity, trades_cost, trades_gain, trades_gainp)
                        select :ptf_id, :cdays_date, :cdays_time, 'ACHAT', :fbuy, :fsell, :iquantity, :fcost, :fgain, :fgainp
                        where not exists (select 1 from trades where trades_ptf_id = :ptf_id and trades_time = :cdays_time)
                        """, {"ptf_id": ptf["ptf_id"], "cdays_date": cday["cdays_date"], "cdays_time": cday["cdays_time"]
                        ,"fbuy": fbuy, "fsell": None, "iquantity": iquantity
                        ,"fcost": fcost_buy
                        , "fgain":None, "fgainp": None
                        })

                    if trade == "SELL":
                        fsell = quote
                        # Enregistrement du TRADE
                        fcost_sell = fsell*iquantity*fcostp
                        fvente = fsell*iquantity - fcost_sell
                        fgain = fvente -fachat
                        fgainp = (fgain / fachat) * 100
                        fday += fgain 
                        journal.append({"time": cday["cdays_time"], "ope": fvente
                        , "message": "{} VENTE... {} \tde {:3.0f} actions à {:7.2f} € soit {:7.2f} € net (frais {:5.2f} €) gain {:7.2f} €"
                        .format(cday["cdays_time"], cday["cdays_ptf_id"], iquantity, fsell, fvente, fcost_sell, fgain)
                        })

                        # Enregistrement du trade terminé
                        self.crud.exec_sql(self.crud.get_basename(), """
                        insert into trades (trades_ptf_id, trades_date, trades_time, trades_order, trades_buy, trades_sell
                        ,trades_quantity, trades_cost, trades_gain, trades_gainp)
                        select :ptf_id, :cdays_date, :cdays_time, 'VENTE', :fbuy, :fsell, :iquantity, :fcost, :fgain, :fgainp
                        where not exists (select 1 from trades where trades_ptf_id = :ptf_id and trades_time = :cdays_time)
                        """, {"ptf_id": ptf["ptf_id"], "cdays_date": cday["cdays_date"], "cdays_time": cday["cdays_time"]
                        ,"fbuy": fbuy, "fsell": fsell, "iquantity": iquantity
                        ,"fcost": fcost_sell
                        , "fgain": fgain, "fgainp": fgainp
                        })

                    cday["cdays_rsi"] = rsi
                    cday["cdays_ema"] = ema
                    cday["cdays_sma"] = sma
                    cday["cdays_trade"] = trade
                    cday["cdays_dvol"] = dvol
                    cday["cdays_vevo"] = vevo

                    self.crud.exec_sql(self.crud.get_basename(), """
                    UPDATE cdays
                    set cdays_rsi = :cdays_rsi, cdays_ema = :cdays_ema, cdays_sma = :cdays_sma
                    ,cdays_trade = :cdays_trade, cdays_dvol = :cdays_dvol, cdays_vevo = :cdays_vevo
                    WHERE cdays_id = :cdays_id
                    """, cday)
                # fin cday du ptf en cours
                # if trade == "BUY":
                #     # Envoi du SMS
                #     if with_sms:
                #         url = "https://fr.finance.yahoo.com/chart/{}".format(ptf["ptf_id"])
                #         msg = "PICSOU ACHAT {} : {} actions à {:7.2f} € {}".format(ptf["ptf_id"], int(iquantity), fbuy, url)
                #         self.crud.send_sms(msg)

                # if trade == "SELL":
                #     # Envoi du SMS
                #     if with_sms and ptf["ptf_top"] == 1:
                #         url = "https://fr.finance.yahoo.com/chart/{}".format(ptf["ptf_id"])
                #         msg = "PICSOU VENTE {} : {} actions à {:7.2f} € (gain: {:7.2f} €) {}".format(ptf["ptf_id"], int(iquantity), fsell, fgain, url)
                #         self.crud.send_sms(msg)

                if trade == "...":
                    fsell = quote
                    # Mise à jour du TRADE en cours
                    fcost_sell = fsell*iquantity*fcostp
                    fvente = fsell*iquantity - fcost_sell
                    fgain = fvente -fachat
                    fgainp = (fgain / fachat) * 100
                    fday += fgain 
                    journal.append({"time": cday["cdays_time"], "ope": fvente
                    , "message": "{} ..WAIT.. {} \tde {:3.0f} actions à {:7.2f} € soit {:7.2f} € net (frais {:5.2f} €) gain {:7.2f} €"
                    .format(cday["cdays_time"], cday["cdays_ptf_id"], iquantity, fsell, fvente, fcost_sell, fgain)
                    })

                    self.crud.exec_sql(self.crud.get_basename(), """
                    update trades set trades_ptf_id = :ptf_id
                    ,trades_sell = :fsell
                    ,trades_cost = :fcost
                    ,trades_gain = :fgain
                    ,trades_gainp = :fgainp
                    where trades_ptf_id = :ptf_id and trades_time = :cday_time_buy
                    """, {"ptf_id": ptf["ptf_id"]
                    ,"fsell": fsell
                    ,"fcost": fcost_sell
                    ,"fgain": fgain
                    ,"fgainp": fgainp
                    ,"cday_time_buy": cday_time_buy
                    })
                # Génération du graphique
                graph = PicsouGraphDay(self.crud, {
                    "ptf_id": ptf["ptf_id"]
                    ,"path": "png/{}/{}.png".format(
                        cday["cdays_date"]
                        ,cday["cdays_ptf_id"]
                        )
                    })
                graph.create_graph()

        if with_cday:
            # fin ptfs
            # Compte-rendu dans TRADES de fday, fcash, fdayp
            # Calcul du cash nécessaire pour réaliser les opérations
            self.display("")
            self.display("--- OPERATIONS DU JOUR ---")
            fcash = 0.0
            fbank = 0.0
            # tri du journal sur time
            journal_sorted=sorted(journal, key = lambda k:k['time'])
            for j in journal_sorted:
                if j["ope"] < 0 and fbank < abs(j["ope"]):
                    delta = fbank - j["ope"]
                    fcash = fcash + abs(delta)
                    fbank = fbank + abs(delta)
                    fbank = fbank + j["ope"]
                else:
                    fbank = fbank + j["ope"]
                self.display(j["message"])
                # self.display("{} ope: {:+7.2f} € \tcash: {:+7.2f} € \tbank: {:+7.2f} €".format(j["time"], j["ope"], fcash, fbank))

            self.crud.exec_sql(self.crud.get_basename(), """
            UPDATE trades
            set trades_cash = :fcash
            ,trades_day = :fday
            WHERE trades_date = date('now')
            """, {"fcash": fcash, "fday": fday})
            # Info sur console
            self.display("--- BILAN DU JOUR {} : {}-{} ({}) gain {:7.2f} € Cash {:7.2f} €"
            .format(cday["cdays_date"], rsimin, rsimax, cas, fday, fcash))

            # Report des gain dans PTF
            # self.crud.exec_sql(self.crud.get_basename(), """
            # UPDATE ptf 
            # SET ptf_gain = (select sum(trades_gain) as gain from trades where trades_ptf_id = ptf_id group by trades_ptf_id)
            # """, {})
        else:
            self.display("")

    def display(self, msg):
        self.parent.display(msg)
    def pout(self, msg):
        self.parent.pout(msg)

    def is_macd_buy(self, ema1, sma1, ema, sma):
        # Croisement ema sma par le bas avec montée importante du ema
        return True if sma1 > ema1 and ema >= sma and ema > ema1 else False

    def is_macd_sell(self, ema1, sma1, ema, sma):
        return True if ema1 >= sma1 and sma > ema and ema < ema1 else False

    def split_crumb_store(self, v):
        return v.split(':')[2].strip('"')

    def find_crumb_store(self, lines):
        # Looking for
        # ,"CrumbStore":{"crumb":"9q.A4D1c.b9
        for l in lines:
            if re.findall(r'CrumbStore', l):
                return l
        self.crud.logger.error("Did not find CrumbStore")

    def get_cookie_value(self, r):
        return {'B': r.cookies['B']}

    def get_cookie_crumb(self, symbol):
        cookie, lines = self.get_page_data(symbol)
        crumb = self.split_crumb_store(self.find_crumb_store(lines))
        return cookie, crumb

    def get_page_data(self, symbol):
        url = "https://finance.yahoo.com/quote/%s/?p=%s" % (symbol, symbol)
        try:
            r = requests.get(url)
        except ValueError:
            self.crud.logger.error("Error %s %s", (ValueError, url))
            sys.exit(1)
        cookie = self.get_cookie_value(r)
        lines = r.content.decode('unicode-escape').strip(). replace('}', '\n')
        return cookie, lines.split('\n')

    def get_data(self, symbol, start_date, end_date, cookie, crumb):
        """ modéle """
        filename = '%s.csv' % (symbol)
        url = "https://query1.finance.yahoo.com/v7/finance/download/%s?period1=%s&period2=%s&interval=1d&events=history&crumb=%s" % (symbol, start_date, end_date, crumb)
        response = requests.get(url, cookies=cookie)
        with open (filename, 'wb') as handle:
            for block in response.iter_content(1024):
                handle.write(block)

    def csv_to_quotes(self, ptf, nbj):
        """
        Récupération des derniers cours d'une action
        """
        # end_date = int(time.mktime(datetime.datetime.now().timetuple()))
        end_date = int(time.time())
        start_date = int(time.mktime((datetime.datetime.now() - datetime.timedelta(days=nbj)).timetuple()))
        # start_date = 0
        # self.cookie, self.crumb = self.get_cookie_crumb(ptf["ptf_id"])
        url = "https://query1.finance.yahoo.com/v7/finance/download/{}?period1={}&period2={}&interval=1d&events=history&crumb={}"\
        .format(ptf["ptf_id"], start_date, end_date, self.crumb)
        # self.display(url)

        with requests.Session() as req:
            conn = None
            try:
                res = req.get(url, cookies=self.cookie)
                for block in res.iter_content(256):
                    if b'error' in block:
                        raise ValueError("ERREUR yahoo %s" % block)
                # with open("quote.txt", 'wb') as handle:
                #     for block in res.iter_content(1024):
                #         handle.write(block)

                if res.encoding is None:
                    res.encoding = 'utf-8'
                lines = res.iter_lines()
                iline = 0
                quotes = []
                for line in lines:
                    line = ptf["ptf_id"] + "," + ptf["ptf_name"] + "," + str(line).replace("b'", "").replace("'", "")
                    if "null" in line:
                        continue
                    if iline > 0 and line.find("null") == -1:
                        quotes.append(line.split(","))
                        # print line.split(",")
                    iline += 1
                conn = sqlite3.connect(self.crud.get_basename())
                cursor = conn.cursor()
                cursor.execute("DELETE FROM QUOTES WHERE id = ?", (ptf["ptf_id"],))
                cursor.executemany("""INSERT INTO QUOTES 
                    (id, name, date, open, high, low, close, adjclose, volume) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", quotes)
                conn.commit()
                if len(quotes) == 0:
                    self.crud.logger.error("Erreur quotes %s", ptf["ptf_id"])
                    exit(1)
                else:
                    # on alimente quote avec la dernière cotation
                    # pour récup dans picsou_batch
                    col_csv = ['id', 'name', 'date', 'open', 'high', 'low', 'close', 'adj close', 'volume']
                    self.quote = dict(zip(col_csv, quotes.pop()))
            except sqlite3.Error as e:
                if conn:
                    conn.rollback()
                self.crud.logger.error("execSql Error %s", e.args[0])
                sys.exit(1)
            except ValueError:
                self.crud.logger.error("Error %s %s", ValueError, url)
            finally:
                if conn:
                    conn.close()

    def rsi(self, data, n=14):
        deltas = np.diff(data)
        seed = deltas[:n+1]
        up = seed[seed>=0].sum()/n
        down = -seed[seed<0].sum()/n
        rs = up/down
        rsi = np.zeros_like(data)
        rsi[:n] = 100. - 100./(1.+rs)

        for i in range(n, len(data)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta

            up = (up*(n-1) + upval)/n
            down = (down*(n-1) + downval)/n
            rs = up/down
            rsi[i] = 100. - 100./(1.+rs)
        return rsi[len(rsi)-1]

    def ema(self, data, window):
        if len(data) < 2 * window:
            raise ValueError("data is too short")
            # return 0
        c = 2.0 / (window + 1)
        current_ema = self.sma(data[-window*2:-window], window)
        for value in data[-window:]:
            current_ema = (c * value) + ((1 - c) * current_ema)
        # print window, current_ema, data
        return current_ema        

    def sma2(self, data, window):
        """
        Calculates Simple Moving Average
        http://fxtrade.oanda.com/learn/forex-indicators/simple-moving-average
        """
        if len(data) < window:
            return 0
        return sum(data[-window:]) / float(window)       

    def sma(self, data, window):
        """
        Calculates Simple Moving Average
        http://fxtrade.oanda.com/learn/forex-indicators/simple-moving-average
        """
        if len(data) < window:
            return sum(data) / float(len(data))
        return sum(data[-window:]) / float(window)
