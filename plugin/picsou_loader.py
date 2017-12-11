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
        self.parent.display(ptf_id + " loading...")

        ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
        SELECT * FROM PTF WHERE ptf_id = :id
        """, {"id": ptf_id})
        self.ptf = ptfs[0]

        self.csv_to_quotes(self.ptf, nbj)

        # un petit nettoyage
        # ajout des lignes dans la table COURS
        self.crud.exec_sql(self.crud.get_basename(), """
        delete from cours
        where cours_ptf_id = :id and cours_ptf_id || cours_date in
        (select id || date from quotes)
        """, {"id": ptf_id})
        self.crud.exec_sql(self.crud.get_basename(), """
        insert into cours
        (cours_ptf_id, cours_name, cours_date, cours_close
        , cours_open, cours_volume, cours_low, cours_high)
        select id, name, date, close, open, volume, low, high 
        from quotes
        left outer join cours on cours_ptf_id = quotes.id and cours_date = quotes.date
        where cours_ptf_id is null and quotes.id = :id
        """, {"id": ptf_id})
        self.crud.exec_sql(self.crud.get_basename(), """
        UPDATE COURS
        set cours_percent = ( (cours_close - cours_open) / cours_open) * 100 
        """, {})

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
        sql = "SELECT * from COURS where cours_ptf_id = :ptf_id ORDER by cours_date ASC"
        courss = self.crud.sql_to_dict(self.crud.get_basename(), sql, {"ptf_id": ptf["ptf_id"]})
        # RSI sur 14 jours
        quote = [0] * n
        rsi = 0.0
        emas12 = [0] * n
        emas26 = [0] * n
        emas50 = [0] * n
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
                q12[i] = q12[i-1]
                q26[i] = q26[i-1]

            # valeur à traiter
            quote[0] = cours["cours_close"]

            # saut des n premiers cours pour remplir le tableau v[]
            if quote[n-1] == 0:
                continue

            quote_r = quote[:]
            quote_r.reverse()
            rsi = self.get_rsi(quote_r, 14)

            emas12[0] = self.ema(quote_r, 12)
            emas26[0] = self.ema(quote_r, 26)
            emas50[0] = self.ema(quote_r, 50)
            if emas26[1] != 0:
                # trend[0] = ((emas50[0] - emas50[1]) / emas50[1]) * 100 * 50 # 50 jours en %
                # trend = nbre de jour de hausse à la suite du ema26
                if emas26[0] > emas26[1]:
                    if q26[0] < 0:
                        q26[0] = 1
                    else:
                        q26[0] = q26[0] + 1
                else:
                    if q26[0] > 0:
                        q26[0] = -1
                    else:
                        q26[0] = q26[0] - 1
                if emas12[0] > emas12[1]:
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
            cours["cours_q26"] = q26[0]
            cours["cours_q12"] = q12[0]

            self.crud.exec_sql(self.crud.get_basename(), """
            UPDATE COURS
            set cours_rsi = :cours_rsi
            , cours_ema12 = :cours_ema12, cours_ema26 = :cours_ema26, cours_ema50 = :cours_ema50
            , cours_q26 = :cours_q26
            , cours_q12 = :cours_q12
            , cours_trade = '', cours_quantity = 0, cours_cost = 0, cours_gainj = 0, cours_gain = 0, cours_gain_percent = 0
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
        set ptf_account = '', ptf_intest = "", ptf_test_cost = 0, ptf_test_quantity = 0
        ,ptf_test_gain = 0, ptf_test_gain_percent = 0
        ,ptf_test_nbj = 0, ptf_test_cumul = 0
        """, {})
        self.crud.exec_sql(self.crud.get_basename(), """
        UPDATE COURS
        set cours_trade = '', cours_quantity = 0, cours_nbj = 0
        ,cours_cost = 0, cours_gainj = 0, cours_gain = 0, cours_gain_percent = 0
        """, {})
        self.crud.exec_sql(self.crud.get_basename(), """
        DELETE FROM MVT
        WHERE mvt_account = 'SIMUL'
        """, {})

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
            self.parent.display(ptf["ptf_id"] + "...")
            while Gtk.events_pending():
                Gtk.main_iteration() # libération des messages UI
            cumulptf = 0
            # Boucle sur les COURS du PTF
            sql = """SELECT * FROM COURS
            WHERE cours_ptf_id = :ptf_id
            ORDER BY cours_date ASC"""
            courss = self.crud.sql_to_dict(self.crud.get_basename(), sql, ptf)

            n = 2 # plage nécessaire pour identifier les changements
            quotes = [0] * n
            emas12 = [0] * n
            emas26 = [0] * n
            emas50 = [0] * n
            rsis = [0] * n
            q12 = [0] * n
            q26 = [0] * n

            quote = 0.0
            gainj = 0
            intest = ""
            quantity = 0
            cost = 0.0
            nbj = 0
            test_date = ""
            gain = 0.0
            gain_percent = 0.0
            motif = ""
            rsi_achat = 0
            b_en_production = False
            rsi_67 = False
            for cours in courss:
                # boucle pour récupérer le cours de j-1
                for i in range(n-1, 0, -1):
                    quotes[i] = quotes[i-1]
                    emas12[i] = emas12[i-1]
                    emas26[i] = emas26[i-1]
                    emas50[i] = emas50[i-1]
                    rsis[i] = rsis[i-1]
                    q26[i] = q26[i-1]
                    q12[i] = q12[i-1]

                quote = cours["cours_close"]
                quotes[0] = cours["cours_close"]
                emas12[0] = cours["cours_ema12"]
                emas26[0] = cours["cours_ema26"]
                emas50[0] = cours["cours_ema50"]
                rsis[0] = cours["cours_rsi"]
                q26[0] = cours["cours_q26"]
                q12[0] = cours["cours_q12"]

                # saut des n premiers jours
                if quotes[n-1] == 0:
                    continue

                if int(self.crudel.get_param("amount") / quote) < 1:
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

                # if intest == "" and rsis[1] < 37 and rsis[0] > rsis[1]:
                #     motif = " <37"
                #     b_achat = True

                if not b_en_test and not b_achat and q26[0] > 4 and rsis[0] < 50:
                # if intest == "" and not b_achat and q12[0] > 2 and q26[0] > 5:
                    motif = " >4J"
                    b_en_test = True
                    b_achat = True

                if b_achat:
                    # SUPPORT -> ACHAT
                    btraite = True
                    rsi_achat = rsis[0]
                    quantity = int(self.crudel.get_param("amount") / quote)
                    amount = quantity * quote
                    cost = quote + quote * self.crudel.get_param("cost") * 2 # frais
                    gain = amount - quantity * cost
                    gainj = (cours["cours_close"] - cours["cours_open"]) * quantity
                    gain_percent = (gain / amount) * 100
                    nbj = 0
                    test_date = cours["cours_date"]
                    fee = quote * quantity * 0.0052

                    # maj du cours
                    intest = "TTT"
                    cours["cours_trade"] = "SSS"
                    cours["cours_quantity"] = quantity
                    cours["cours_cost"] = cost
                    cours["cours_gainj"] = gainj
                    cours["cours_gain"] = gain
                    cours["cours_gain_percent"] = gain_percent

                    if b_en_test:
                        # Ajout d'un mouvement
                        self.crud.exec_sql(self.crud.get_basename(), """
                        INSERT INTO MVT
                        (mvt_account, mvt_date, mvt_ptf_id, mvt_trade, mvt_exec, mvt_quantity, mvt_fee)
                        VALUES
                        ('SIMUL', :cours_date, :cours_ptf_id, 'Achat', :cours_close, :cours_quantity, 6.15)
                        """, cours)

                    ptf["ptf_trade"] = "SSS"
                    ptf["ptf_test_date"] = cours["cours_date"]

                if not btraite and (b_en_test or b_en_production):
                    btraite = True

                    # cas des pertes sans palier dans les 26 jours
                    amount = quantity * quote
                    gain = amount - quantity * cost
                    gainj = (cours["cours_close"] - cours["cours_open"]) * quantity
                    if amount > 0:
                        gain_percent = (gain / amount) * 100

                    # maj du cours
                    cours["cours_quantity"] = quantity
                    cours["cours_cost"] = cost
                    cours["cours_gainj"] = gainj
                    cours["cours_gain"] = gain
                    cours["cours_gain_percent"] = gain_percent

                    # Faut-il vendre ?
                    b_vendre = False

                    # on vend si emas50 baisse
                    # if not b_vendre and emas50[0] < emas50[1] and nbj > 10:
                    #     motif += " 50-"
                    #     b_vendre = True

                    # on vend si perte > 50 € et si nbj > 4
                    # if not b_vendre and emas50[0] < emas50[1] and nbj > 4 and gain < -50:
                    #     motif += " -50"
                    #     b_vendre = True

                    # if not b_vendre and emas26[0] < emas26[1] and nbj > 2:
                    #     motif += " 26-"
                    #     b_vendre = True

                    # on vend quand le cours est le plus haut
                    # sans     Nbre de mises: 23 Cash: -31749.09 € Gain acquis: -20.96 € Gain : 1854.28 €
                    # avec >65 Nbre de mises: -10 Cash: 6102.30 € Gain acquis: 12.51 € Gain : 26.51 €
                    # avec >70 Nbre de mises: -3 Cash: -2114.33 € Gain acquis: 155.79 € Gain : 503.30 €
                    if rsis[0] > 67:
                        rsi_67 = True
                        # b_vendre = True

                    if rsi_67 and emas12[0] < emas12[1]:
                        motif += " >67"
                        b_vendre = True

                    # if rsi_67 and rsis[0] < rsis[1]:
                    #     motif += " >67"
                    #     b_vendre = True

                    # garde-fou : 
                    # if not b_vendre and emas50[0] < emas50[1] and gain < 0 and nbj > 26:
                    if not b_vendre and q26[0] < 0 and gain < 0 and nbj > 20:
                        motif += " 20J"
                        b_vendre = True

                    if b_vendre and b_en_production:
                        # on signale que la valeur en production doit être vendue
                        # Maj du cours
                        nbj += 1

                        cours["cours_trade"] = "RRR"

                        ptf["ptf_trade"] = "RRR"
                    else:
                        # RESISTANCE -> VENTE
                        if b_vendre:
                            nbj += 1

                            cumulptf += gain
                            cumul += gain

                            # maj du cours
                            cours["cours_trade"] = "RRR"

                            # self.parent.display("  {} / {} {} {:.0f}/{:.0f} {:.2f} {}j\t{:.2f}€"\
                            # .format(test_date, cours["cours_date"], motif, rsi_achat, rsis[0]\
                            # , q26[0], nbj, gain))
        
                            ptf["ptf_trade"] = "RRR"

                            # Ajout d'un mouvement
                            self.crud.exec_sql(self.crud.get_basename(), """
                            INSERT INTO MVT
                            (mvt_account, mvt_date, mvt_ptf_id, mvt_trade, mvt_exec, mvt_quantity, mvt_fee)
                            VALUES
                            ('SIMUL', :cours_date, :cours_ptf_id, 'Vente', :cours_close, :cours_quantity, 6.15)
                            """, cours)

                            motif = ""
                            rsi_achat = 0
                            intest = ""
                            nbj = 0
                            quantity = 0
                            cost = 0
                            gain = 0
                            gain_percent = 0
                            test_date = ""
                            rsi_67 = False
                        else:
                            # Maj du cours
                            nbj += 1

                            cours["cours_trade"] = "TTT"
                            cours["cours_nbj"] = nbj
                            cours["cours_intest"] = "1" if b_en_test else ""
                            cours["cours_inptf"] = "1" if b_en_production else ""

                            ptf["ptf_trade"] = ""

                # maj du cours
                cours["cours_nbj"] = nbj
                cours["cours_gainj"] = gainj
                cours["cours_intest"] = 1 if b_en_test else ""
                cours["cours_inptf"] = 1 if b_en_production else ""
                if b_en_production:
                    pass
                self.crud.exec_sql(self.crud.get_basename(), """
                UPDATE COURS
                set cours_trade = :cours_trade, cours_nbj = :cours_nbj
                ,cours_inptf = :cours_inptf, cours_intest = :cours_intest
                ,cours_quantity = :cours_quantity
                ,cours_cost = :cours_cost, cours_gainj = :cours_gainj
                ,cours_gain = :cours_gain, cours_gain_percent = :cours_gain_percent
                WHERE cours_ptf_id = :cours_ptf_id and cours_date = :cours_date
                """, cours)

                # MAJ du COURS qui n'est pas en TEST
                if not btraite:
                    btraite = True
                    ptf["ptf_trade"] = ""

                # maj du PTF avec les données du cours
                ptf["ptf_quote"] = cours["cours_close"]
                ptf["ptf_gainj"] = cours["cours_gainj"]
                ptf["ptf_percent"] = cours["cours_percent"]
                ptf["ptf_rsi"] = cours["cours_rsi"]
                ptf["ptf_q26"] = cours["cours_q26"]
                ptf["ptf_q12"] = cours["cours_q12"]

            # mise à jour du portefeuille à la fin
            ptf["ptf_test_cost"] = cost
            ptf["ptf_test_quantity"] = quantity
            ptf["ptf_test_gain"] = gain
            ptf["ptf_test_gain_percent"] = gain_percent
            ptf["ptf_test_nbj"] = nbj
            ptf["ptf_intest"] = intest
            ptf["ptf_test_date"] = test_date
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
            ,ptf_intest = :ptf_intest
            ,ptf_test_date = :ptf_test_date
            ,ptf_test_cost = :ptf_test_cost
            ,ptf_test_quantity = :ptf_test_quantity
            ,ptf_test_gain = :ptf_test_gain
            ,ptf_test_gain_percent = :ptf_test_gain_percent
            ,ptf_test_cumul = :ptf_test_cumul
            ,ptf_test_nbj = :ptf_test_nbj
            WHERE ptf_id = :ptf_id
            """, ptf)
            # self.parent.display("{} Gain:{:.2f}\tCumul:{:.2f}".format(ptf["ptf_id"]\
            # , cumulptf, cumul))

        # Résumé de la simulation - boucle sur les cours par date pour connaître le cash nécessaire
        # courss = self.crud.sql_to_dict(self.crud.get_basename(), """
        # SELECT * FROM COURS
        # WHERE cours_trade in ('SSS','TTT','RRR')
        # ORDER BY cours_date, cours_ptf_id
        # """, {})
        # cash = 0
        # qamount = 0
        # cumul = 0
        # for cours in courss:
        #     if cours["cours_trade"] == "SSS":
        #         cash = cash - cours["cours_cost"] * cours["cours_quantity"]
        #         qamount += 1
        #     if cours["cours_trade"] == "RRR":
        #         cash = cash + cours["cours_close"] * cours["cours_quantity"]
        #         cumul += cours["cours_gain"]
        #         qamount -= 1
        # prise en compte des actions en test
        # gain_acquis = cumul
        # ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
        # SELECT * FROM PTF
        # WHERE ptf_intest = 'TTT'
        # """, ptf)
        # for ptf in ptfs:
        #     cumul += ptf["ptf_test_gain"]
        # resume = "Nbre de mises: {} Cash: {:.2f} € Gain acquis: {:.2f} € Gain : {:.2f} € {:.2f}%"\
        # .format(qamount, -cash, gain_acquis, cumul, (cumul/-cash)*100)
        # resume_sql = u"Nbre de mises: <b>{}</b> Cash: <b>{:.2f} €</b> Gain acquis: <b>{:.2f} €</b> Gain : <b>{:.2f} €</b> <b>{:.2f}%</b>"\
        # .format(qamount, -cash, gain_acquis, cumul, (cumul/-cash)*100)
        # # self.parent.display(resume)
        # self.crud.exec_sql(self.crud.get_basename(), """
        # UPDATE RESUME
        # SET resume_simul = :resume
        # """, {"resume": resume_sql})

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

        # Boucle sur les MVT /account valeur date
        mvts = self.crud.sql_to_dict(self.crud.get_basename(), """
        SELECT * FROM mvt
        ORDER BY mvt_account, mvt_ptf_id, mvt_date asc, mvt_trade asc
        """, {})
        account = ""
        ptf_id = ""
        quantity_left = 0
        money = 0 # /account
        latent = 0 # /account
        gain_day = 0 # /account
        fee = 0 # /account
        ptf_latent = 0  # /ptf
        ptf_input = 0   # /ptf
        ptf_output = 0  # /ptf
        ptf_gain_day = 0  # /ptf
        mvt_id = 0
        quantity_lefts = {}
        for mvt in mvts:
            if mvt["mvt_account"] != account:
                # changement de compte
                if account != "":
                    # update money latent
                    latent += ptf_latent
                    gain_day += ptf_gain_day
                    money += ptf_input + ptf_output
                    # MAJ ACCOUNT
                    self.crud.exec_sql(self.crud.get_basename(), """
                    UPDATE ACCOUNT
                    set acc_money = acc_initial + :money, acc_latent = :latent
                    ,acc_gain_day = :gain_day
                    WHERE acc_id = :account
                    """, {"account": account, "money": money, "latent": latent, "gain_day": gain_day})
                    # Sélection des MVTs non soldés
                    if quantity_left > 0:
                        for key in quantity_lefts:
                            self.crud.exec_sql(self.crud.get_basename(), """
                            UPDATE MVT
                            set mvt_select = '1'
                            WHERE mvt_id = :mvt_id
                            """, {"mvt_id": key})

                # ...
                # initialisation nouveau account
                account = mvt["mvt_account"]
                rows = self.crud.sql_to_dict(self.crud.get_basename(), """
                SELECT acc_fee FROM ACCOUNT WHERE acc_id = :account
                """, {"account": account})
                for row in rows:
                    fee = row["acc_fee"]
                money = 0
                latent = 0
                gain_day = 0
                ptf_output = 0
                ptf_input = 0
                ptf_latent = 0
                ptf_gain_day = 0
                ptf_id = ""
                quantity_left = 0

            if mvt["mvt_ptf_id"] != ptf_id:
                # changement de ptf
                # Sélection des MVTs non soldés
                if quantity_left > 0:
                    for key in quantity_lefts:
                        self.crud.exec_sql(self.crud.get_basename(), """
                        UPDATE MVT
                        set mvt_select = '1'
                        WHERE mvt_id = :mvt_id
                        """, {"mvt_id": key})

                # initialisation nouveau ptf
                money += ptf_input + ptf_output
                latent += ptf_latent
                gain_day += ptf_gain_day
                ptf_output = 0
                ptf_input = 0
                ptf_latent = 0
                ptf_gain_day = 0
                quantity_left = 0
                ptf_id = mvt["mvt_ptf_id"]
                quantity_lefts.clear()

            mvt_id = mvt["mvt_id"]

            if mvt["mvt_trade"] == "Achat":
                quantity_left += mvt["mvt_quantity"]
                ptf_output = ptf_output - mvt["mvt_exec"] * mvt["mvt_quantity"] - mvt["mvt_fee"]
                mvt["mvt_output"] = - mvt["mvt_exec"] * mvt["mvt_quantity"] - mvt["mvt_fee"]
                mvt["mvt_gain"] = (mvt["mvt_quote"] - mvt["mvt_exec"]) * mvt["mvt_quantity"] * (1 - fee/100)
                mvt["mvt_gain_percent"] = (mvt["mvt_gain"] / (mvt["mvt_exec"] * mvt["mvt_quantity"])) * 100
                quantity_lefts[mvt_id] = quantity_left
            else:
                quantity_left -= mvt["mvt_quantity"]
                ptf_input = ptf_input + mvt["mvt_exec"] * mvt["mvt_quantity"] - mvt["mvt_fee"]
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
            # update money latent
            latent += ptf_latent
            gain_day += ptf_gain_day
            money += ptf_input + ptf_output
            self.crud.exec_sql(self.crud.get_basename(), """
            UPDATE ACCOUNT
            set acc_money = acc_initial + :money, acc_latent = :latent
            ,acc_gain_day = :gain_day
            WHERE acc_id = :account
            """, {"account": account, "money": money, "latent": latent, "gain_day": gain_day})
            # Sélection des MVTs non soldés
            if quantity_left > 0:
                for key in quantity_lefts:
                    self.crud.exec_sql(self.crud.get_basename(), """
                    UPDATE MVT
                    set mvt_select = '1'
                    WHERE mvt_id = :mvt_id
                    """, {"mvt_id": key})

        # calcul du gain
        self.crud.exec_sql(self.crud.get_basename(), """
        UPDATE ACCOUNT
        set acc_gain = acc_money + acc_latent - acc_initial
        """, {})
        # SELECTION DES MVTS EN COURS
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
                        "ptf_gain_percent": ptf_gain / ptf_output * 100
                    }
                    self.crud.exec_sql(self.crud.get_basename(), """
                    UPDATE PTF
                    set ptf_account = :accounts
                    ,ptf_date = :ptf_date
                    ,ptf_quantity = :ptf_quantity
                    ,ptf_gainj = :ptf_gainj
                    ,ptf_gain = :ptf_gain
                    ,ptf_cost = :ptf_cost
                    ,ptf_gain_percent = :ptf_gain_percent
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
