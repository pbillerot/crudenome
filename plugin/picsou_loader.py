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

class PicsouLoadQuotes():
    """
    Import des n derniers cours d'une action
    """
    def __init__(self, parent, crud):

        self.crud = crud
        self.crudel = crud.get_crudel()
        self.parent = parent

        self.cookie, self.crumb = self.get_cookie_crumb("ACA.PA")
        self.quote = {}

    def run(self, ptf_id, nbj):
        """
        Chargement des cours
        """
        self.parent.display(ptf_id + " quote...")

        ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
        SELECT * FROM PTF WHERE ptf_id = :id
        """, {"id": ptf_id})
        self.ptf = ptfs[0]

        self.csv_to_quotes(self.ptf, nbj)

        # un petit nettoyage
        self.crud.exec_sql(self.crud.get_basename(), """
        delete from cours
        where cours_ptf_id = :id and cours_ptf_id || cours_date in
        (select id || date from quotes)
        """, {"id": ptf_id})
        # insertion des cours
        self.crud.exec_sql(self.crud.get_basename(), """
        insert into cours
        (cours_ptf_id, cours_name, cours_date, cours_close
        , cours_open, cours_volume, cours_low, cours_high)
        select id, name, date, close, open, volume, low, high 
        from quotes
        left outer join cours on cours_ptf_id = quotes.id and cours_date = quotes.date
        where cours_ptf_id is null and quotes.id = :id
        """, {"id": ptf_id})
        # calcul cours_percent
        self.crud.exec_sql(self.crud.get_basename(), """
        UPDATE COURS
        set cours_percent = ( (cours_close - cours_open) / cours_open) * 100 
        """, {})
        # calcul du volume moyen et volume max
        self.crud.exec_sql(self.crud.get_basename(), """
        DELETE FROM COURS_VOL WHERE ptf_id = :id
        """, {"id": ptf_id})
        self.crud.exec_sql(self.crud.get_basename(), """
        INSERT INTO COURS_VOL (ptf_id, vol_moy, vol_max)
            SELECT cours_ptf_id
            , sum(cours_volume) / count( * ) AS vol_moy
            , max(cours_volume) AS vol_max
            FROM cours AS tt
            WHERE tt.cours_ptf_id = :id
        """, {"id": ptf_id})
        self.crud.exec_sql(self.crud.get_basename(), """
        UPDATE ptf SET 
        ptf_vol_moy = ( select vol_moy from cours_vol where cours_vol.ptf_id = :id )
        , ptf_vol_max = ( select vol_max from cours_vol where cours_vol.ptf_id = :id )
        WHERE ptf.ptf_id = :id
        """, {"id": ptf_id})

        # calcul du rsi ema12 ema26
        self.calcul_rsi_ema(self.ptf)

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

    def get_page_data(self, symbol):
        url = "https://finance.yahoo.com/quote/%s/?p=%s" % (symbol, symbol)
        try:
            res = requests.get(url)
        except ValueError:
            self.crud.logger.error("Error %s %s", (ValueError, url))
            sys.exit(1)
        cookie = self.get_cookie_value(res)
        # lines = r.text.encode('utf-8').strip().replace('}', '\n')
        lines = res.content.strip().replace('}', '\n')
        return cookie, lines.split('\n')

    def get_cookie_crumb(self, symbol):
        cookie, lines = self.get_page_data(symbol)
        crumb = self.split_crumb_store(self.find_crumb_store(lines))
        # Note: possible \u002F value
        # ,"CrumbStore":{"crumb":"FWP\u002F5EFll3U"
        # FWP\u002F5EFll3U
        crumb2 = crumb.decode('unicode-escape')
        return cookie, crumb2

    def csv_to_quotes(self, ptf, nbj):
        """
        Récupération des <nbj> cours d'une action
        """
        # print "csv_to_sql", ptf["ptf_id"], nbj
        if nbj > 10 :
            self.crud.exec_sql(self.crud.get_basename(), """
            DELETE FROM COURS WHERE cours_ptf_id = :id
            """, {"id": ptf["ptf_id"]})

        end_date = int(time.mktime(datetime.datetime.now().timetuple()))
        start_date = int(time.mktime((datetime.datetime.now() - datetime.timedelta(days=nbj)).timetuple()))
        url = "https://query1.finance.yahoo.com/v7/finance/download/{}?period1={}&period2={}&interval=1d&events=history&crumb={}"\
        .format(ptf["ptf_id"], start_date, end_date, self.crumb)
        # print url

        with requests.Session() as req:
            conn = None
            try:
                res = req.get(url, stream=True, cookies=self.cookie)
                if res.encoding is None:
                    res.encoding = 'utf-8'
                lines = res.iter_lines()
                iline = 0
                quotes = []
                for line in lines:
                    line = ptf["ptf_id"] + "," + ptf["ptf_name"] + "," + line
                    if iline > 0 and line.find("null") == -1:
                        quotes.append(line.split(","))
                        # print line.split(",")
                    iline += 1
                # col_csv = ['date', 'open', 'high', 'low', 'close', 'adjclose', 'volume']
                # quotes = dict(zip(col_csv, lines))
                # reader = csv.DictReader(lines)
                # to_db = [(ptf["ptf_id"], ptf['ptf_name']\
                #     ,i['Date'], i['Open'], i['High'], i['Low'], i['Close'], i['Adj Close'], i['Volume'])\
                #     for i in reader]
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
            except sqlite3.Error, e:
                if conn:
                    conn.rollback()
                self.crud.logger.error("execSql Error %s", e.args[0])
                sys.exit(1)
            except ValueError:
                self.crud.logger.error("Error %s %s", ValueError, url)
            finally:
                if conn:
                    conn.close()

    def exists_quote(self, ptf):
        """
        Contrôle existence d'une valeur
        """
        end_date = int(time.mktime(datetime.datetime.now().timetuple()))
        start_date = int(time.mktime((datetime.datetime.now() - datetime.timedelta(days=1)).timetuple()))
        url = "https://query1.finance.yahoo.com/v7/finance/download/{}?period1={}&period2={}&interval=1d&events=history&crumb={}"\
        .format(ptf, start_date, end_date, self.crumb)
        # print url

        bret = False
        with requests.Session() as req:
            try:
                res = req.get(url, stream=True, cookies=self.cookie)
                if res.encoding is None:
                    res.encoding = 'utf-8'
                lines = res.iter_lines()
                iline = 0
                quotes = []
                for line in lines:
                    line = ptf["ptf_id"] + "," + ptf["ptf_name"] + "," + line
                    if iline > 0 and line.find("null") == -1:
                        quotes.append(line.split(","))
                        # print line.split(",")
                        bret = True
                    iline += 1
            except ValueError:
                self.crud.logger.error("Error %s %s", ValueError, url)
                bret = False
            finally:
                pass
        return bret

    def calcul_rsi_ema(self, ptf, n=101):
        """
            Calcul des indicateurs RSI EMA12 EMA26 TREND
        """
        # print "Analyse de ", ptf["ptf_id"]

        # recup du vol_max
        rows = self.crud.sql_to_dict(self.crud.get_basename(), """
        SELECT ptf_vol_max FROM ptf
        WHERE ptf_id = :id
        """, {'id': ptf["ptf_id"]})
        vol_max = rows[0]["ptf_vol_max"]


        sql = "SELECT * from COURS where cours_ptf_id = :ptf_id ORDER by cours_date ASC"
        courss = self.crud.sql_to_dict(self.crud.get_basename(), sql, {"ptf_id": ptf["ptf_id"]})
        # RSI sur 14 jours
        quote = [0] * n
        rsi = 0.0
        rsis = [0] * n
        emas12 = [0] * n
        emas26 = [0] * n
        emas50 = [0] * n
        trend26 = [0] * n
        trend50 = [0] * n
        min12 = [0] * n
        min26 = [0] * n
        min50 = [0] * n
        max12 = [0] * n
        max26 = [0] * n
        max50 = [0] * n
        q50 = [0] * n
        q26 = [0] * n
        q12 = [0] * n
        # ordre = {}
        for cours in courss:
            # rotation des valeurs
            for i in range(n-1, 0, -1):
                quote[i] = quote[i-1]
                emas12[i] = emas12[i-1]
                emas26[i] = emas26[i-1]
                emas50[i] = emas50[i-1]
                trend26[i] = trend26[i-1]
                trend50[i] = trend50[i-1]
                min12[i] = min12[i-1]
                min26[i] = min26[i-1]
                min50[i] = min50[i-1]
                max12[i] = max12[i-1]
                max26[i] = max26[i-1]
                max50[i] = max50[i-1]
                rsis[i] = rsis[i-1]
                q12[i] = q12[i-1]
                q26[i] = q26[i-1]
                q50[i] = q50[i-1]

            # valeur à traiter
            quote[0] = cours["cours_close"]
            volume = cours["cours_volume"]

            # saut des n premiers cours pour remplir le tableau v[]
            if quote[n-1] == 0:
                continue

            quote_r = quote[:]
            quote_r.reverse()
            rsi = self.get_rsi(quote_r, 14)
            rsis[0] = rsi
            emas12[0] = self.ema(quote_r, 12)
            emas26[0] = self.ema(quote_r, 26)
            emas50[0] = self.ema(quote_r, 50)
            min12[0] = min(emas12[:6])
            min26[0] = min(emas26[:13])
            min50[0] = min(emas50[:25])
            max12[0] = max(emas12[:6])
            max26[0] = max(emas26[:13])
            max50[0] = max(emas50[:25])
            if min26[0] != 0 and min50[0] != 0 and max26[0] != 0 and max50[0] != 0 :
                if emas26[0] == max26[0]:
                    trend26[0] = (emas26[0] - min26[0]) / min26[0] * 100
                else:
                    trend26[0] = (emas26[0] - max26[0]) / max26[0] * 100
                if emas50[0] == max50[0]:
                    trend50[0] = (emas50[0] - min50[0]) / min50[0] * 100
                else:
                    trend50[0] = (emas50[0] - max50[0]) / max50[0] * 100
            if emas26[1] != 0:
                # trend[0] = ((emas50[0] - emas50[1]) / emas50[1]) * 100 * 50 # 50 jours en %
                # trend = nbre de jour de hausse à la suite du ema26
                if emas50[0] >= emas50[1]:
                    if q50[0] < 0:
                        q50[0] = 1
                    else:
                        q50[0] = q50[0] + 1
                else:
                    if q50[0] > 0:
                        q50[0] = -1
                    else:
                        q50[0] = q50[0] - 1

                if emas26[0] >= emas26[1]:
                    if q26[0] < 0:
                        q26[0] = 1
                    else:
                        q26[0] = q26[0] + 1
                else:
                    if q26[0] > 0:
                        q26[0] = -1
                    else:
                        q26[0] = q26[0] - 1

                if emas12[0] >= emas12[1]:
                    if q12[0] < 0:
                        q12[0] = 1
                    else:
                        q12[0] = q12[0] + 1
                else:
                    if q12[0] > 0:
                        q12[0] = -1
                    else:
                        q12[0] = q12[0] - 1

            cours["cours_rsi"] = rsi
            cours["cours_ema12"] = emas12[0]
            cours["cours_ema26"] = emas26[0]
            cours["cours_ema50"] = emas50[0]
            cours["cours_min12"] = min12[0]
            cours["cours_min26"] = min26[0]
            cours["cours_min50"] = min50[0]
            cours["cours_max12"] = max12[0]
            cours["cours_max26"] = max26[0]
            cours["cours_max50"] = max50[0]
            cours["cours_trend26"] = trend26[0]
            cours["cours_trend50"] = trend50[0]
            cours["cours_q50"] = q50[0]
            cours["cours_q26"] = q26[0]
            cours["cours_q12"] = q12[0]
            cours["cours_volp"] = (volume) / vol_max * 100

            self.crud.exec_sql(self.crud.get_basename(), """
            UPDATE COURS
            set cours_rsi = :cours_rsi
            , cours_ema12 = :cours_ema12, cours_ema26 = :cours_ema26, cours_ema50 = :cours_ema50
            , cours_min12 = :cours_min12, cours_min26 = :cours_min26, cours_min50 = :cours_min50
            , cours_max12 = :cours_max12, cours_max26 = :cours_max26, cours_max50 = :cours_max50
            , cours_trend26 = :cours_trend26, cours_trend50 = :cours_trend50
            , cours_volp = :cours_volp
            , cours_q50 = :cours_q50
            , cours_q26 = :cours_q26
            , cours_q12 = :cours_q12
            , cours_trade = '', cours_quantity = 0, cours_cost = 0, cours_gainj = 0, cours_gain = 0, cours_gainp = 0
            , cours_nbj = -1
            WHERE cours_ptf_id = :cours_ptf_id and cours_date = :cours_date
            """, cours)
        # nettoyage
        self.crud.exec_sql(self.crud.get_basename(), """
        DELETE from COURS WHERE cours_rsi is null
        """, {})

    def simulateur(self):
        """
        Simulation d'achat et de vente d'actions à partir de l'historique des cours
        - On dispose d'un compte "espèces" d'un montant fixé au départ 10 000 € par exemple
        - On mise un minimum de 1200 $ par transaction pour optimiser les frais de l'ordre de 2 % (mise + retrait)
        - Laisser un cache de 100 € dans le compte espèce par sécurité
        - On mise en priorité sur les actions qui ont la croissance la plus forte
        Boucle sur les dates de l'historiques tri /date,action
        """
        # Raz de la dernière simulation
        self.crud.exec_sql(self.crud.get_basename(), """
        UPDATE PTF
        set ptf_account = ''
        """, {})
        self.crud.exec_sql(self.crud.get_basename(), """
        UPDATE COURS
        set cours_trade = '', cours_quantity = 0, cours_nbj = 0
        ,cours_cost = 0, cours_gainj = 0, cours_gain = 0, cours_gainp = 0
        """, {})
        self.crud.exec_sql(self.crud.get_basename(), """
        DELETE FROM MVT
        WHERE mvt_account = 'SIMUL'
        """, {})

        # recup mise minimum dans simul
        rows = self.crud.sql_to_dict(self.crud.get_basename(), """
        SELECT * FROM account
        WHERE acc_id = 'SIMUL'
        """, {})
        acc_bet = rows[0]["acc_bet"]
        acc_fee = rows[0]["acc_fee"]

        # MAJ account de PTF
        mvts = self.crud.sql_to_dict(self.crud.get_basename(), """
        SELECT * FROM mvt
        WHERE mvt_select = '1'
        ORDER BY mvt_ptf_id, mvt_date asc
        """, {})
        ptf_id = ""
        accounts = {}
        for mvt in mvts:
            if mvt["mvt_ptf_id"] != ptf_id:
                # changement de ptf
                params = {
                    "accounts": ' '.join(accounts.keys()),
                    "ptf_id": ptf_id,
                }
                self.crud.exec_sql(self.crud.get_basename(), """
                UPDATE PTF
                set ptf_account = :accounts
                where ptf_id = :ptf_id
                """, params)

                # initialisation nouveau ptf
                accounts.clear()
                ptf_id = mvt["mvt_ptf_id"]

            accounts[mvt["mvt_account"]] = mvt["mvt_quantity"]

        # Boucle sur les PTF
        # On vend les actions en baisse pour libérer du cash
        cumul = 0
        cumulptf = 0
        if self.crudel.get_param("cac40_only"):
            ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
            SELECT * FROM ptf WHERE ptf_cac40 = 1
            ORDER BY ptf_id
            """, {})
        else:
            ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
            SELECT * FROM ptf
            ORDER BY ptf_id
            """, {})
        for ptf in ptfs:
            # if ptf["ptf_id"] not in ('TFI.PA'):
            #     continue
            self.parent.display(ptf["ptf_id"] + " simul...")
            while Gtk.events_pending():
                Gtk.main_iteration() # libération des messages UI
            cumulptf = 0
            # Boucle sur les COURS du PTF
            sql = """SELECT * FROM COURS
            WHERE cours_ptf_id = :ptf_id
            ORDER BY cours_date ASC"""
            courss = self.crud.sql_to_dict(self.crud.get_basename(), sql, ptf)

            n = 3 # plage nécessaire pour identifier les changements
            quotes = [0] * n
            emas12 = [0] * n
            emas26 = [0] * n
            emas50 = [0] * n
            trend26 = [0] * n
            trend50 = [0] * n
            min12 = [0] * n
            min26 = [0] * n
            min50 = [0] * n
            max12 = [0] * n
            max26 = [0] * n
            max50 = [0] * n
            emv = [0] * n
            volp = [0] * n
            rsis = [0] * n
            q12 = [0] * n
            q26 = [0] * n
            q50 = [0] * n
            qvol = [0] * n

            quote = 0.0
            gainj = 0
            intest = ""
            quantity = 0
            quantity_achat = 0
            cost = 0.0
            nbj = 0
            gain = 0.0
            gain_percent = 0.0
            motif = ""
            rsi_achat = 0
            b_en_production = False
            rsi_67 = False
            rsi_37 = False
            date_achat = ""
            trend = 0
            trend_achat = 0
            nbj_vente = 0
            for cours in courss:
                # boucle pour récupérer le cours de j-1
                for i in range(n-1, 0, -1):
                    quotes[i] = quotes[i-1]
                    emas12[i] = emas12[i-1]
                    emas26[i] = emas26[i-1]
                    emas50[i] = emas50[i-1]
                    trend26[i] = trend26[i-1]
                    trend50[i] = trend50[i-1]
                    min12[i] = min12[i-1]
                    min26[i] = min26[i-1]
                    min50[i] = min50[i-1]
                    max12[i] = max12[i-1]
                    max26[i] = max26[i-1]
                    max50[i] = max50[i-1]
                    emv[i] = emv[i-1]
                    volp[i] = volp[i-1]
                    rsis[i] = rsis[i-1]
                    q50[i] = q50[i-1]
                    q26[i] = q26[i-1]
                    q12[i] = q12[i-1]
                    qvol[i] = qvol[i-1]

                quote = cours["cours_close"]
                quotes[0] = cours["cours_close"]
                emas12[0] = cours["cours_ema12"]
                emas26[0] = cours["cours_ema26"]
                emas50[0] = cours["cours_ema50"]
                trend26[0] = cours["cours_trend26"]
                trend50[0] = cours["cours_trend50"]
                max12[0] = cours["cours_max12"]
                max26[0] = cours["cours_max26"]
                max50[0] = cours["cours_max50"]
                min12[0] = cours["cours_min12"]
                min26[0] = cours["cours_min26"]
                min50[0] = cours["cours_min50"]
                volp[0] = cours["cours_volp"]
                rsis[0] = cours["cours_rsi"]
                q50[0] = cours["cours_q50"]
                q26[0] = cours["cours_q26"]
                q12[0] = cours["cours_q12"]

                # saut des n premiers jours
                if quotes[n-1] == 0:
                    continue

                if int(acc_bet / quote) < 1:
                    continue

                btraite = False

                if ptf["ptf_account"] is not None and ptf["ptf_account"] != "" and cours["cours_date"] >= ptf["ptf_date"]:
                    b_en_production = True

                # SUPPORT -> ACHAT
                b_achat = False

                if intest == "":
                    b_en_test = False
                else:
                    b_en_test = True

                delta0 = emas12[0] - emas50[0]
                delta1 = emas12[1] - emas50[1]
                delta2 = emas12[2] - emas50[2]
                nbj_vente += 1

                # basé sur ema50 tout simplement
                if intest == "" and trend26[0] > 0 and trend50[0] > 0 \
                    and nbj_vente > 3:
                    motif = " ema50"
                    b_achat = True
                # if intest == "" and trend26[0] > 0 and nbj_vente > 3:
                #     motif = " ema26"
                #     b_achat = True
                # if intest == "" and trend26[0] > 0.14 \
                #     :
                #     motif = " ema26"
                #     b_achat = True

                # if intest == "" and rsi_37 and q26[0] > 0 :
                #     motif = " rsi37"
                #     b_achat = True
                # if rsis[0] < 37:
                #     rsi_37 = True

                # gestion des paliers
                # if not b_en_test and emas12[0] > emas12[1] and emas12[1] < emas12[2] and emas12[1] > min12[0] and q50[0] > 0:
                #     motif = " pal12"
                #     b_en_test = True
                #     b_achat = True

                # macd 12 26 50
                # if not b_en_test \
                #     and delta0 > delta2\
                #     and q12[0] > 0 and q26[0] > 0 and q50[0] > 0\
                #     and emas12[0] > emas26[0] and emas26[0] > emas50[0]\
                #     and emas12[2] > emas26[2] and emas26[2] > emas50[2]:
                #     motif = " em+++"
                #     b_en_test = True
                #     b_achat = True

                # la plus efficace
                # if not b_en_test and q26[0] > 4 and rsis[0] < 50:
                #     motif = " rsi50"
                #     b_en_test = True
                #     b_achat = True

                # Volume d'achat important
                # if not b_en_test and volp[0] > 100 and quotes[0] > quotes[1]\
                #     and delta0 > delta2\
                #     and q12[0] > 0 and q26[0] > 0 and q50[0] > 0\
                #     and emas12[0] > emas26[0] and emas26[0] > emas50[0]:
                #     motif = " aa100"
                #     b_en_test = True
                #     b_achat = True

                if b_achat:
                    # SUPPORT -> ACHAT
                    if date_achat == "":
                        date_achat = cours["cours_date"]
                    trend_achat = trend
                    btraite = True
                    rsi_achat = rsis[0]
                    quantity_achat = int(acc_bet / quote)
                    quantity += int(acc_bet / quote)
                    amount = quantity * quote
                    fee = quote * quantity * acc_fee / 100
                    cost = quote + quote * acc_fee * 2 / 100 # frais
                    gain = amount - quantity * cost
                    gainj = (cours["cours_close"] - cours["cours_open"]) * quantity
                    gain_percent = (gain / amount) * 100
                    nbj = 0

                    # maj du cours
                    intest = "TTT"
                    cours["cours_trade"] = "SSS"
                    cours["cours_quantity"] = quantity
                    cours["cours_quantity_achat"] = quantity_achat
                    cours["cours_fee"] = fee
                    cours["cours_nbj"] = nbj
                    cours["cours_cost"] = cost
                    cours["cours_gainj"] = gainj
                    cours["cours_gain"] = gain
                    cours["cours_gainp"] = gain_percent

                    # Ajout d'un mouvement
                    self.crud.exec_sql(self.crud.get_basename(), """
                    INSERT INTO MVT
                    (mvt_account, mvt_date, mvt_ptf_id, mvt_trade, mvt_exec, mvt_quantity, mvt_fee)
                    VALUES
                    ('SIMUL', :cours_date, :cours_ptf_id, 'Achat', :cours_close, :cours_quantity_achat, :cours_fee)
                    """, cours)

                    ptf["ptf_trade"] = "SSS"

                    rsi_37 = False

                if not btraite and b_en_test:
                    btraite = True

                    # cas des pertes sans palier dans les 26 jours
                    amount = quantity * quote
                    # le gain est faux en raison des achats en plusieurs fois,
                    # il faudrait faire la moyenne des coûts
                    gain = amount - quantity * cost
                    gainj = (cours["cours_close"] - cours["cours_open"]) * quantity
                    if amount > 0:
                        gain_percent = (gain / amount) * 100

                    # maj du cours
                    cours["cours_quantity"] = quantity
                    cours["cours_cost"] = cost
                    cours["cours_gainj"] = gainj
                    cours["cours_gain"] = gain
                    cours["cours_gainp"] = gain_percent

                    # Faut-il vendre ?
                    b_vendre = False

                    #  on vend si ema50 descend
                    if q50[0] < 0:
                        motif += " ema50"
                        b_vendre = True

                    #  on vend si ema26 descend
                    # if q26[0] < 0:
                    #     motif += " ema26"
                    #     b_vendre = True

                    # le sommet
                    # if rsis[1] > 67:
                    #     rsi_67 = True
                    # if rsi_67 and rsis[0] < rsis[1]:
                    #     motif += " rsi67"
                    #     b_vendre = True
                    # if rsis[1] > 67 and q12[0] < 0:
                    #     motif += " rsi67"
                    #     b_vendre = True

                    # q12 en baisse confirmée
                    # if not b_vendre and q12[0] < -1 and nbj > 5:
                    #     motif += " vvq12"
                    #     b_en_test = True
                    #     b_vendre = True

                    # Volume de vente important
                    if not b_vendre and volp[0] > 60 and quotes[0] < quotes[1]:
                        motif += " vol60"
                        b_en_test = True
                        b_vendre = True

                    # le delta entre 12 et 50 se reserre
                    # if not b_vendre and delta0 < delta2:
                    #     motif += " d1250"
                    #     b_en_test = True
                    #     b_vendre = True

                    # garde-fou :
                    # if not b_vendre and emas50[0] < emas50[1] and gain < 0 and nbj > 26:
                    # if not b_vendre and q26[0] < 0 and gain < 0 and nbj > 17:
                    #     motif += " sec19"
                    #     b_vendre = True

                    if b_vendre:
                        nbj += 1
                        nbj_vente = 0
                        cumulptf += gain
                        cumul += gain

                        # maj du cours
                        cours["cours_trade"] = "RRR"

                        if gain > 0:
                            self.parent.display("  {:8.2f}€\t{:7.2f}€\t\t{} / {} {:.0f}/{:.0f} {:4.2f}\t{:3.0f}j {}"\
                            .format(cumul, gain, date_achat, cours["cours_date"], rsi_achat, rsis[0], trend_achat, nbj, motif))
                        else:
                            self.parent.display("  {:8.2f}€\t\t{:7.2f}€\t{} / {} {:.0f}/{:.0f} {:4.2f}\t{:3.0f}j {}"\
                            .format(cumul, gain, date_achat, cours["cours_date"], rsi_achat, rsis[0], trend_achat, nbj, motif))
    
                        # Ajout d'un mouvement
                        fee = quote * quantity * acc_fee / 100
                        cours["cours_fee"] = fee

                        self.crud.exec_sql(self.crud.get_basename(), """
                        INSERT INTO MVT
                        (mvt_account, mvt_date, mvt_ptf_id, mvt_trade, mvt_exec, mvt_quantity, mvt_fee)
                        VALUES
                        ('SIMUL', :cours_date, :cours_ptf_id, 'Vente', :cours_close, :cours_quantity, :cours_fee)
                        """, cours)

                        motif = ""
                        rsi_achat = 0
                        intest = ""
                        nbj = 0
                        quantity_achat = 0
                        quantity = 0
                        cost = 0
                        gain = 0
                        gain_percent = 0
                        rsi_37 = False
                        rsi_67 = False
                        date_achat = ""
                    else:
                        # Maj du cours 
                        nbj += 1
                        cours["cours_trade"] = "TTT"
                        ptf["ptf_trade"] = ""

                # maj du cours
                cours["cours_quantity"] = quantity
                cours["cours_nbj"] = nbj
                cours["cours_gainj"] = gainj
                cours["cours_intest"] = 1 if b_en_test else ""
                cours["cours_inptf"] = 1 if b_en_production else ""
                self.crud.exec_sql(self.crud.get_basename(), """
                UPDATE COURS
                set cours_trade = :cours_trade, cours_nbj = :cours_nbj
                ,cours_inptf = :cours_inptf, cours_intest = :cours_intest
                ,cours_quantity = :cours_quantity
                ,cours_cost = :cours_cost, cours_gainj = :cours_gainj
                ,cours_gain = :cours_gain, cours_gainp = :cours_gainp
                WHERE cours_ptf_id = :cours_ptf_id and cours_date = :cours_date
                """, cours)

                # MAJ du COURS qui n'est pas en TEST
                if not btraite:
                    btraite = True
                    ptf["ptf_trade"] = ""

                if  b_en_production and \
                (trend26[0] > 0) or \
                (rsi_67 and rsis[0] < rsis[1]) or \
                (q26[0] < 0 and gain < 0 and nbj > 20):
                    # on signale que la valeur en production doit être vendue
                    rsi_67 = False
                    ptf["ptf_trade"] = "RRR"

                # maj du PTF avec les données du cours
                ptf["ptf_quote"] = cours["cours_close"]
                ptf["ptf_gainj"] = cours["cours_gainj"]
                ptf["ptf_percent"] = cours["cours_percent"]
                ptf["ptf_rsi"] = cours["cours_rsi"]
                ptf["ptf_q26"] = cours["cours_q26"]
                ptf["ptf_q12"] = cours["cours_q12"]
                ptf["ptf_nbj"] = cours["cours_nbj"]
                ptf["ptf_volp"] = cours["cours_volp"]

            # mise à jour du portefeuille à la fin
            self.crud.exec_sql(self.crud.get_basename(), """
            UPDATE PTF
            set ptf_quote = :ptf_quote 
            ,ptf_gainj = :ptf_gainj 
            ,ptf_percent = :ptf_percent 
            ,ptf_quantity = :ptf_quantity
            ,ptf_trade = :ptf_trade
            ,ptf_rsi = :ptf_rsi
            ,ptf_q26 = :ptf_q26
            ,ptf_q12 = :ptf_q12
            ,ptf_volp = :ptf_volp
            WHERE ptf_id = :ptf_id
            """, ptf)

    def get_rsi(self, prices, n=14):
        deltas = np.diff(prices)
        seed = deltas[:n+1]
        up = seed[seed>=0].sum()/n
        down = -seed[seed<0].sum()/n
        rs = up/down
        rsi = np.zeros_like(prices)
        rsi[:n] = 100. - 100./(1.+rs)

        for i in range(n, len(prices)):
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
    def sma(self, data, window):
        """
        Calculates Simple Moving Average
        http://fxtrade.oanda.com/learn/forex-indicators/simple-moving-average
        """
        if len(data) < window:
            return 0
        return sum(data[-window:]) / float(window)        

    def account(self):
        """
        Parcours de l'historique des mouvements
        pour calculer :
        - le solde des différents opérations
        - le solde par portefeuille
        - le solde global
        """
        # Raz de la dernière simulation
        self.crud.exec_sql(self.crud.get_basename(), """
        UPDATE MVT
        set mvt_quote = 0, mvt_percent = 0
        , mvt_input = 0, mvt_output = 0
        , mvt_gain = 0, mvt_gain_percent = 0
        , mvt_select = ''
        """, {})
        # Récupération de la dernière cotation
        self.crud.exec_sql(self.crud.get_basename(), """
        UPDATE MVT
        set mvt_quote = (select ptf_quote from ptf where ptf_id = mvt_ptf_id)
        ,mvt_percent = (select ptf_percent from ptf where ptf_id = mvt_ptf_id)
        """, {})

        # Init PTF
        self.crud.exec_sql(self.crud.get_basename(), """
        UPDATE PTF
        set ptf_account = '', ptf_date = '', ptf_quantity = 0
        """, {})

        # Init ACCOUNT
        self.crud.exec_sql(self.crud.get_basename(), """
        UPDATE ACCOUNT
        set acc_date = '', acc_money = 0, acc_latent = 0, acc_initial = 0, acc_gain = 0, acc_gain_day = 0, acc_percent = 0
        """, {})

        # Boucle sur les MVT /account valeur date
        mvts = self.crud.sql_to_dict(self.crud.get_basename(), """
        SELECT * FROM mvt
        ORDER BY mvt_account, mvt_ptf_id, mvt_date asc, mvt_trade asc
        """, {})
        account = ""
        ptf_id = ""
        quantity_left = 0
        latent = 0 # /account
        gain_day = 0 # /account
        fee = 0 # /account
        ptf_latent = 0  # /ptf
        ptf_gain_day = 0  # /ptf
        mvt_id = 0
        quantity_lefts = {}
        for mvt in mvts:
            if mvt["mvt_account"] != account:
                # changement de compte
                if account != "":
                    # update latent gain du jour
                    latent += ptf_latent
                    gain_day += ptf_gain_day
                    if quantity_left > 0:
                        # Sélection des MVTs non soldés
                        for key in quantity_lefts:
                            self.crud.exec_sql(self.crud.get_basename(), """
                            UPDATE MVT
                            set mvt_select = '1'
                            WHERE mvt_id = :mvt_id
                            """, {"mvt_id": key})
                    # MAJ ACCOUNT
                    self.crud.exec_sql(self.crud.get_basename(), """
                    UPDATE ACCOUNT
                    set acc_latent = :latent
                    ,acc_gain_day = :gain_day
                    WHERE acc_id = :account
                    """, {"account": account, "latent": latent, "gain_day": gain_day})

                # ...
                # initialisation nouveau account
                account = mvt["mvt_account"]
                rows = self.crud.sql_to_dict(self.crud.get_basename(), """
                SELECT acc_fee FROM ACCOUNT WHERE acc_id = :account
                """, {"account": account})
                for row in rows:
                    fee = row["acc_fee"]
                latent = 0
                gain_day = 0
                ptf_latent = 0
                ptf_gain_day = 0
                ptf_id = ""
                quantity_left = 0

            if mvt["mvt_ptf_id"] != ptf_id:
                # changement de ptf
                latent += ptf_latent
                gain_day += ptf_gain_day
                # Sélection des MVTs non soldés
                if quantity_left > 0:
                    for key in quantity_lefts:
                        self.crud.exec_sql(self.crud.get_basename(), """
                        UPDATE MVT
                        set mvt_select = '1'
                        WHERE mvt_id = :mvt_id
                        """, {"mvt_id": key})

                # initialisation nouveau ptf
                ptf_latent = 0
                ptf_gain_day = 0
                quantity_left = 0
                ptf_id = mvt["mvt_ptf_id"]
                quantity_lefts.clear()

            mvt_id = mvt["mvt_id"]

            if mvt["mvt_trade"] == "Achat":
                quantity_left += mvt["mvt_quantity"]
                mvt["mvt_output"] = - mvt["mvt_exec"] * mvt["mvt_quantity"] - mvt["mvt_fee"]
                mvt["mvt_gain"] = (mvt["mvt_quote"] - mvt["mvt_exec"]) * mvt["mvt_quantity"] * (1 - fee/100)
                mvt["mvt_gain_percent"] = (mvt["mvt_gain"] / (mvt["mvt_exec"] * mvt["mvt_quantity"])) * 100
                quantity_lefts[mvt_id] = quantity_left
            else:
                quantity_left -= mvt["mvt_quantity"]
                mvt["mvt_input"] = mvt["mvt_exec"] * mvt["mvt_quantity"] - mvt["mvt_fee"]

            if quantity_left == 0:
                quantity_lefts.clear()

            # Mise à jour du mvt
            ptf_latent = quantity_left * mvt["mvt_quote"] * (1 - fee/100)
            if mvt["mvt_percent"] != 0:
                ptf_gain_day = (mvt["mvt_quote"] - mvt["mvt_quote"] / ( 1 + mvt["mvt_percent"] / 100)) * quantity_left
            mvt["mvt_gain_day"] = ptf_gain_day
            mvt["mvt_left"] = quantity_left
            self.crud.exec_sql(self.crud.get_basename(), """
            UPDATE MVT
            set mvt_input = :mvt_input, mvt_output = :mvt_output
            , mvt_left = :mvt_left, mvt_gain = :mvt_gain
            , mvt_gain_percent = :mvt_gain_percent, mvt_gain_day = :mvt_gain_day
            WHERE mvt_id = :mvt_id
            """, mvt)
        # traitement dernière rupture
        if account != "":
            # update latent et gain du jour
            latent += ptf_latent
            gain_day += ptf_gain_day
            if quantity_left > 0:
                # Sélection des MVTs non soldés
                for key in quantity_lefts:
                    self.crud.exec_sql(self.crud.get_basename(), """
                    UPDATE MVT
                    set mvt_select = '1'
                    WHERE mvt_id = :mvt_id
                    """, {"mvt_id": key})
            # MAJ ACCOUNT
            self.crud.exec_sql(self.crud.get_basename(), """
            UPDATE ACCOUNT
            set acc_latent = :latent
            ,acc_gain_day = :gain_day
            WHERE acc_id = :account
            """, {"account": account, "latent": latent, "gain_day": gain_day})

        # SELECTION DES MVTS EN COURS par PTF
        mvts = self.crud.sql_to_dict(self.crud.get_basename(), """
        SELECT * FROM mvt
        WHERE mvt_select = '1'
        ORDER BY mvt_ptf_id, mvt_date asc
        """, {})
        ptf_id = ""
        accounts = {}
        ptf_date = ""
        ptf_quantity = 0
        ptf_gainj = 0
        ptf_gain = 0
        ptf_output = 0
        for mvt in mvts:
            if mvt["mvt_ptf_id"] != ptf_id:
                # changement de ptf
                if ptf_quantity > 0:
                    params = {
                        "accounts": ' '.join(accounts.keys()),
                        "ptf_id": ptf_id,
                        "ptf_date": ptf_date,
                        "ptf_quantity": ptf_quantity,
                        "ptf_gainj": ptf_gainj,
                        "ptf_gain": ptf_gain,
                        "ptf_cost": ptf_output,
                        "ptf_gainp": ptf_gain / ptf_output * 100
                    }
                    self.crud.exec_sql(self.crud.get_basename(), """
                    UPDATE PTF
                    set ptf_account = :accounts
                    ,ptf_date = :ptf_date
                    ,ptf_quantity = :ptf_quantity
                    ,ptf_gainj = :ptf_gainj
                    ,ptf_gain = :ptf_gain
                    ,ptf_cost = :ptf_cost
                    ,ptf_gainp = :ptf_gainp
                    where ptf_id = :ptf_id
                    """, params)

                # initialisation nouveau ptf
                accounts.clear()
                ptf_date = ""
                ptf_quantity = 0
                ptf_gainj = 0
                ptf_gain = 0
                ptf_output = 0
                ptf_id = mvt["mvt_ptf_id"]

            accounts[mvt["mvt_account"]] = mvt["mvt_quantity"]
            ptf_quantity += mvt["mvt_quantity"]
            ptf_gainj += mvt["mvt_gain_day"]
            ptf_gain += mvt["mvt_gain"]
            ptf_output += mvt["mvt_output"]
            ptf_date = mvt["mvt_date"]
        # dernier MVT
        if ptf_quantity > 0:
            params = {
                "accounts": ' '.join(accounts.keys()),
                "ptf_id": ptf_id,
                "ptf_date": ptf_date,
                "ptf_quantity": ptf_quantity,
                "ptf_gainj": ptf_gainj,
                "ptf_gain": ptf_gain,
                "ptf_cost": ptf_output,
                "ptf_gainp": ptf_gain / ptf_output * 100
            }
            self.crud.exec_sql(self.crud.get_basename(), """
            UPDATE PTF
            set ptf_account = :accounts
            ,ptf_date = :ptf_date
            ,ptf_quantity = :ptf_quantity
            ,ptf_gainj = :ptf_gainj
            ,ptf_gain = :ptf_gain
            ,ptf_cost = :ptf_cost
            ,ptf_gainp = :ptf_gainp
            where ptf_id = :ptf_id
            """, params)

        # SELECTION DES MVTS EN COURS par account et par date
        mvts = self.crud.sql_to_dict(self.crud.get_basename(), """
        SELECT * FROM mvt
        ORDER BY mvt_account, mvt_date asc, mvt_trade desc
        """, {})
        acc_id = ""
        debit = 0
        cash = 0
        for mvt in mvts:
            if mvt["mvt_account"] != acc_id and acc_id != "":
                self.crud.exec_sql(self.crud.get_basename(), """
                UPDATE ACCOUNT
                set acc_initial = :debit
                ,acc_money = :cash
                where acc_id = :acc_id
                """, {"acc_id": acc_id, "debit": debit, "cash": cash})
                cash = 0
                debit = 0
            acc_id = mvt["mvt_account"]
            if mvt["mvt_trade"] == "Achat":
                if cash - -mvt["mvt_output"] < 0:
                    debit = debit + -mvt["mvt_output"] - cash
                    cash = 0
                else:
                    cash = cash + mvt["mvt_output"]
                # print "%s %s %s %s d:%.2f c:%.2f m:%.2f" % (mvt["mvt_account"], mvt["mvt_date"], mvt["mvt_ptf_id"], mvt["mvt_trade"], debit, cash, mvt["mvt_output"])
            else:
                cash = cash + mvt["mvt_input"]
                # print "%s %s %s %s d:%.2f c:%.2f m:%.2f" % (mvt["mvt_account"], mvt["mvt_date"], mvt["mvt_ptf_id"], mvt["mvt_trade"], debit, cash, mvt["mvt_input"])
        # dernier mvt
        if acc_id != "":
            self.crud.exec_sql(self.crud.get_basename(), """
            UPDATE ACCOUNT
            set acc_initial = :debit
            ,acc_money = :cash
            where acc_id = :acc_id
            """, {"acc_id": acc_id, "debit": debit, "cash": cash})

        # calcul du gain
        self.crud.exec_sql(self.crud.get_basename(), """
        UPDATE ACCOUNT
        set acc_gain = acc_money + acc_latent - acc_initial 
        , acc_percent = (acc_money + acc_latent - acc_initial) / acc_initial * 100
        """, {})
