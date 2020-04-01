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
import pandas as pd
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
        for ptf in ptfs:
            while Gtk.events_pending():
                Gtk.main_iteration()
            # Chargement de l'historique
            self.parent.display("Quote of {}...".format(ptf["ptf_id"]))

            self.csv_to_quotes(ptf, 7)
            
            # Suppression des cours des jours antérieurs
            self.crud.exec_sql(self.crud.get_basename(), """
            delete from cdays
            where cdays_date <> date('now')
            """, {})
            # insertion du dernier cours récupéré dans self.quote
            self.crud.exec_sql(self.crud.get_basename(), """
            insert into cdays
            (cdays_ptf_id, cdays_name, cdays_date, cdays_close
            , cdays_open, cdays_volume, cdays_low, cdays_high, cdays_time)
            select id, name, date, close, open, volume, low, high, datetime('now', 'localtime') 
            from quotes
            where quotes.id = :id and quotes.date = date('now')
            """, {"id": ptf["ptf_id"]})
            # calcul cours_percent
            self.crud.exec_sql(self.crud.get_basename(), """
            UPDATE cdays
            set cdays_percent = ( (cdays_close - cdays_open) / cdays_open) * 100 
            """, {})

    def trade(self):
        """
        Simulation d'achat et de vente d'actions à partir du cours de la journée
        https://www.abcbourse.com/apprendre/11_lecon3.html
        Voici ce qui fait le succès de la MACD: le signal arrive encore plus tôt que la détection par croisement des MMA20 et MMA50 de la dernière leçon. Mais cela en fait aussi le danger, car retenez bien que plus un indicateur signale tôt, plus il a tendance à se tromper. Il faut donc travailler la MACD avec d'autres artifices pour confirmer sa validité.
        Une règle de validation vient s'ajouter à cette règle de base. Lors du croisement de la MACD avec sa ligne de signal, on ne rentrera que si la MACD et le signal ont été du même côté pendant un minimum de 14 séances que l'on compte à l'envers en comptant le jour du croisement. Ce minimum permet de s'assurer que l'on était dans une situation suffisamment stable pour que le croisement de la MACD avec sa ligne de signal ait du sens.
        """
        rsimin = self.crud.get_application_prop("trade")["rsimin"]
        rsimax = self.crud.get_application_prop("trade")["rsimax"]
        # Calcul du timestamp du jour à 17 heures 20 (heure limite d'achat)
        time_limit = datetime.datetime.now().replace(hour=17, minute=25, second=0, microsecond=0).timestamp()

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
        fcostp = self.crud.get_application_prop("trade")["cost"] # coût de la transaction ex: 0.012 %
        fstake = self.crud.get_application_prop("trade")["stake"] # mise ou enjeu
        fday = 0.0
        journal = []
        for ptf in ptfs:
            self.parent.display(ptf["ptf_id"] + " trade... ")
            while Gtk.events_pending():
                Gtk.main_iteration() # libération des messages UI
            # Boucle sur les COURS du PTF
            sql = """SELECT * FROM cdays
            WHERE cdays_ptf_id = :ptf_id
            ORDER BY cdays_time ASC"""
            cdays = self.crud.sql_to_dict(self.crud.get_basename(), sql, ptf)

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
            sma1 = 0.0
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
            firstQuoteIsPositive = False
            for cday in cdays:
                nbc+=1
                quote3 = quote2
                quote2 = quote1
                quote1 = quote
                rsi1 = rsi
                ema1 = ema
                sma1 = sma

                # Calcul du timestamp du cours courant
                cday_time = datetime.datetime.strptime(cday["cdays_time"], '%Y-%m-%d %H:%M:%S').timestamp()

                if nbc == 1 :
                    firstQuoteIsPositive = True if cday["cdays_percent"] > 0 else False

                quote = cday["cdays_close"]
                quotes.append(quote)

                sma = self.sma(quotes, 14)
                if nbc > 13 : 
                    rsi = self.rsi(quotes, 14)
                    window = nbc//2 if nbc < 28 else 14
                    ema = self.ema(quotes, window)
                else:
                    ema = sma

                if trade == "BUY" : trade = "..."
                if trade == "SELL": trade = ""

                # VENTE
                if trade in ("BUY","..."):
                    if rsi > rsimax : trade = "SELL"
                # fin de journée, on vend tout avant la cloture
                if cday_time > time_limit and trade in ("BUY","...") : 
                    trade = "SELL"

                # ACHAT si dans la période du marché 
                # et si pas de trade en cours pour l'action
                if trade == "WAIT" : 
                    if rsi > rsi1 : trade = "BUY"

                if cday_time < time_limit and trade == "":
                    # if rsi < rsimin : trade = "WAIT"
                    if rsi < rsimin : trade = "BUY"

                if trade == "BUY":
                    if cday_time > time_limit : 
                        trade = ""
                    else:
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

                self.crud.exec_sql(self.crud.get_basename(), """
                UPDATE cdays
                set cdays_rsi = :cdays_rsi, cdays_ema = :cdays_ema, cdays_sma = :cdays_sma
                ,cdays_trade = :cdays_trade
                WHERE cdays_id = :cdays_id
                """, cday)
            # fin cday du ptf en cours
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

        # fin ptfs
        # Compte-rendu dans TRADES de fday, fcash, fdayp
        # Calcul du cash nécessaire pour réaliser les opérations
        self.parent.display("--- OPERATIONS DU JOUR ---")
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
            self.parent.display(j["message"])
            # self.parent.display("{} ope: {:+7.2f} € \tcash: {:+7.2f} € \tbank: {:+7.2f} €".format(j["time"], j["ope"], fcash, fbank))

        self.crud.exec_sql(self.crud.get_basename(), """
        UPDATE trades
        set trades_cash = :fcash
        ,trades_day = :fday
        WHERE trades_date = date('now')
        """, {"fcash": fcash, "fday": fday})
        # Info sur console
        self.parent.display("--- BILAN DU JOUR : gain {:7.2f} € Cash {:7.2f} € "
        .format(fday, fcash))

        # Report des gain dans PTF
        self.crud.exec_sql(self.crud.get_basename(), """
        UPDATE ptf 
        SET ptf_gain = (select sum(trades_gain) as gain from trades where trades_ptf_id = ptf_id group by trades_ptf_id)
        """, {})

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
        start_date = int(time.mktime((datetime.datetime.now() - datetime.timedelta(days=3)).timetuple()))
        # start_date = 0
        # self.cookie, self.crumb = self.get_cookie_crumb(ptf["ptf_id"])
        url = "https://query1.finance.yahoo.com/v7/finance/download/{}?period1={}&period2={}&interval=1d&events=history&crumb={}"\
        .format(ptf["ptf_id"], start_date, end_date, self.crumb)
        # self.parent.display(url)

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
