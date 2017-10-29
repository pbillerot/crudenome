# -*- coding:Utf-8 -*-
"""
    Import des n derniers cours d'une action
    Calcul du RSI EMA MACD
    Simulateur tradeur
    Calcul des gains

"""
import sqlite3
import time
import datetime
import re
import csv
import sys
from contextlib import closing
import requests
from gi.repository import Gtk

class Picsou():
    """
    Import des n derniers cours d'une action
    """
    def __init__(self, parent):
        self.config = parent.config
        self.tools = parent.tools
        self.cookie, self.crumb = self.get_cookie_crumb("ACA.PA")
        self.parent = parent

    def run(self, ptf_id, nbj):
        """
        Chargement des cours
        """
        # print self.__class__.__name__, self.parent.__class__.__name__, ptf_id, "loading..."

        self.parent.display(ptf_id + " loading...")

        ptfs = self.tools.sql_to_dict("""SELECT * FROM PTF WHERE ptf_id = :id""", {"id": ptf_id})
        self.ptf = ptfs[0]

        self.csv_to_sql(self.ptf, nbj)

        self.insert_last_quote(self.ptf)

        # un petit nettoyage
        self.tools.exec_sql("DELETE FROM QUOTES WHERE close = 'null'", {})
        # ajout des lignes dans la table COURS
        self.tools.exec_sql("""
        insert into cours
        (cours_ptf_id, cours_name, cours_date, cours_close, cours_open, cours_volume, cours_low, cours_high)
        select id, name, date, close, open, volume, low, high 
        from quotes
        left outer join cours on cours_ptf_id = quotes.id and cours_date = quotes.date
        where cours_ptf_id is null
        """, {})

        # calcul du rsi ema12 ema26 macd
        self.calcul_rsi_ema_macd(self.ptf)

    def split_crumb_store(self, v):
        return v.split(':')[2].strip('"')

    def find_crumb_store(self, lines):
        # Looking for
        # ,"CrumbStore":{"crumb":"9q.A4D1c.b9
        for l in lines:
            if re.findall(r'CrumbStore', l):
                return l
        print "Did not find CrumbStore"

    def get_cookie_value(self, r):
        return {'B': r.cookies['B']}

    def get_page_data(self, symbol):
        url = "https://finance.yahoo.com/quote/%s/?p=%s" % (symbol, symbol)
        res = requests.get(url)
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

    def csv_to_sql(self, ptf, nbj):
        """
        Récupération des <nbj> cours d'une action
        """
        # print "csv_to_sql", ptf["ptf_id"], nbj
        if nbj > 10 :
            self.tools.exec_sql("DELETE FROM COURS WHERE cours_ptf_id = :id", {"id": ptf["ptf_id"]})

        end_date = int(time.mktime(datetime.datetime.now().timetuple()))
        start_date = int(time.mktime((datetime.datetime.now() - datetime.timedelta(days=nbj)).timetuple()))
        url = "https://query1.finance.yahoo.com/v7/finance/download/{}?period1={}&period2={}&interval=1d&events=history&crumb={}"\
        .format(ptf["ptf_id"], start_date, end_date, self.crumb)
        # print url

        with requests.Session() as req:
        # with closing(requests.get(url, stream=True, cookies=self.cookie)) as r:
            conn = None
            try:
                res = req.get(url, stream=True, cookies=self.cookie)
                if res.encoding is None:
                    res.encoding = 'utf-8'
                lines = res.iter_lines()
                reader = csv.DictReader(lines)
                to_db = [(ptf["ptf_id"], ptf['ptf_name']\
                    ,i['Date'], i['Open'], i['High'], i['Low'], i['Close'], i['Adj Close'], i['Volume'])\
                    for i in reader]
                conn = sqlite3.connect(self.config["db_name"])
                cursor = conn.cursor()
                cursor.execute("DELETE FROM QUOTES WHERE id = ?", (ptf["ptf_id"],))
                cursor.executemany("""INSERT INTO QUOTES 
                    (id, name, date, open, high, low, close, adjclose, volume) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", to_db)
                conn.commit()
            except sqlite3.Error, e:
                if conn:
                    conn.rollback()
                print("execSql Error {}".format(e.args[0]))
                sys.exit(1)
            except ValueError:
                print("Error {} {}".format(ValueError, reader))
            finally:
                if conn:
                    conn.close()

    def insert_last_quote(self, ptf):
        """
        Insertion mise à jour du dernier cours d'une action
        """
        quote = self.tools.getQuote(ptf["ptf_id"])
        if quote["name"] == 'N/A':
            msg = "-> ERREUR {} non trouvée".format(ptf["ptf_id"])
            raise msg
        
        # print quote

        ptf["ptf_percent"] = quote["percent"]
        ptf["ptf_quote"] = quote["change"]
        
        self.quote = quote # pour récup dans picsou_dlg

        # Suppression du derniers cours dans la base
        self.tools.exec_sql("""
        DELETE FROM COURS WHERE cours_ptf_id = :id and cours_date = :date
        """, quote)
        # Ajout du dernier cours
        self.tools.exec_sql("""INSERT INTO COURS
        (cours_ptf_id, cours_date, cours_close, cours_open, cours_name, cours_volume, cours_low, cours_high, cours_percent) 
        VALUES (:id, :date, :change, :open, :name, :volume, :low, :high, :percent)
        """, quote)

    def calcul_rsi_ema_macd(self, ptf, n=101):
        """
            Calcul des indicateurs RSI EMA12 EMA26 TREND
        """
        # print "Analyse de ", ptf["ptf_id"]
        sql = "SELECT * from COURS where cours_ptf_id = :ptf_id ORDER by cours_date ASC"
        courss = self.tools.sql_to_dict(sql, {"ptf_id": ptf["ptf_id"]})
        # RSI sur 14 jours
        quote = [0] * n
        rsi = 0.0
        emas12 = [0] * n
        emas26 = [0] * n
        emas50 = [0] * n
        macd = [0] * n
        # ordre = {}
        for cours in courss:
            # rotation des valeurs
            for i in range(n-1, 0, -1):
                quote[i] = quote[i-1]
                emas12[i] = emas12[i-1]
                emas26[i] = emas26[i-1]
                emas50[i] = emas50[i-1]
                macd[i] = macd[i-1]

            # valeur à traiter
            quote[0] = cours["cours_close"]

            # saut des n premiers cours pour remplir le tableau v[]
            if quote[n-1] == 0:
                continue

            quote_r = quote[:]
            quote_r.reverse()
            rsi = self.tools.get_rsi(quote_r, 14)

            emas12[0] = self.tools.ema(quote_r, 12)
            emas26[0] = self.tools.ema(quote_r, 26)
            emas50[0] = self.tools.ema(quote_r, 50)
            macd[0] = emas12[0] - emas26[0]

            cours["cours_rsi"] = rsi
            cours["cours_ema12"] = emas12[0]
            cours["cours_ema26"] = emas26[0]
            cours["cours_ema50"] = emas50[0]
            cours["cours_macd"] = macd[0]

            self.tools.exec_sql("""UPDATE COURS
            set cours_rsi = :cours_rsi
            , cours_ema12 = :cours_ema12, cours_ema26 = :cours_ema26, cours_ema50 = :cours_ema50
            , cours_macd = :cours_macd
            , cours_trade = '', cours_quantity = 0, cours_cost = 0, cours_gain = 0, cours_gain_percent = 0
            , cours_nbj = -1
            WHERE cours_ptf_id = :cours_ptf_id and cours_date = :cours_date
            """, cours)
        # nettoyage
        self.tools.exec_sql("""DELETE from COURS WHERE cours_rsi is null""", {})

    def simulateur(self):
        """
        Simulation d'achat et de vente d'actions à partir de l'historique des cours
        - On dispose d'un compte "espèces" d'un montant fixé au départ 10 000 € par exemple
        - On mise un minimum de 1200 $ par transaction pour optimiser les frais de l'ordre de 1 % (mise + retrait)
        - Laisser un cache de 100 € dans le compte espèce par sécurité
        - On mise en priorité sur les actions qui ont la croissance la plus forte
        Boucle sur les dates de l'historiques tri /date,action
        """
        # Raz de la dernière simulation
        self.tools.exec_sql("""UPDATE PTF
        set ptf_intest = "", ptf_test_cost = 0, ptf_test_quantity = 0
        ,ptf_test_gain = 0, ptf_test_gain_percent = 0
        ,ptf_test_nbj = 0, ptf_test_cumul = 0
        """, {})
        self.tools.exec_sql("""UPDATE COURS
        set cours_trade = '', cours_quantity = 0, cours_nbj = 0
        ,cours_cost = 0, cours_gain = 0, cours_gain_percent = 0
        """, {})

        # Boucle sur les PTF
        # On vend les actions en baisse pour libérer du cash
        cumul = 0
        cumulptf = 0
        # ptfs = self.tools.sql_to_dict("""SELECT * FROM ptf WHERE ptf_cac40 = 1
        # ptfs = self.tools.sql_to_dict("""SELECT * FROM ptf where ptf_note is null or ptf_note <> 'exclure'
        ptfs = self.tools.sql_to_dict("""SELECT * FROM ptf where ptf_note is null or ptf_note <> 'exclure'
        ORDER BY ptf_id""", {})
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
            courss = self.tools.sql_to_dict(sql, ptf)

            n = 2 # plage nécessaire pour identifier les changements
            quotes = [0] * n
            emas12 = [0] * n
            emas26 = [0] * n
            emas50 = [0] * n
            macd = [0] * n
            rsis = [0] * n

            quote = 0.0
            intest = ""
            quantity = 0
            cost = 0.0
            nbj = 0
            test_date = ""
            gain = 0.0
            gain_percent = 0.0
            b_macd = True # True quand croisement 12/  26\
            motif = ""
            rsi = 0
            rsi_achat = 0
            b_en_production = False
            for cours in courss:
                # boucle pour récupérer le cours de j-1
                for i in range(n-1, 0, -1):
                    quotes[i] = quotes[i-1]
                    emas12[i] = emas12[i-1]
                    emas26[i] = emas26[i-1]
                    emas50[i] = emas50[i-1]
                    rsis[i] = rsis[i-1]
                    macd[i] = macd[i-1]

                quote = cours["cours_close"]
                quotes[0] = cours["cours_close"]
                emas12[0] = cours["cours_ema12"]
                emas26[0] = cours["cours_ema26"]
                emas50[0] = cours["cours_ema50"]
                rsis[0] = cours["cours_rsi"]
                macd[0] = cours["cours_macd"]

                # saut des n premiers jours
                if quotes[n-1] == 0:
                    continue

                if int(self.config["amount"] / quote) < 1:
                    continue

                btraite = False

                if cours["cours_date"] >= ptf["ptf_date"] and ptf["ptf_inptf"] == "PPP":
                    b_en_production = True

                # SUPPORT -> ACHAT
                b_achat = False

                if intest == "" and rsis[0] < 37:
                    motif += " <37"
                    b_achat = True

                # on évite les tendances plates
                # emas50 > emas26 qui remonte
                # if intest == "" and macd[0] < 0\
                #     and abs(emas50[0]-emas26[0])/emas26[0] > 0.003\
                #     and emas26[0] > emas26[1]:# and emas50[0] > emas26[0]
                #     motif += " 26+"
                #     b_achat = True

                # croisement 12x26
                # if intest == "" and macd[1] < 0 and macd[0] > 0 and emas50[0] > emas50[1] and rsis[0] < 50:
                #     # and abs(emas50[0]-emas26[0])/emas26[0] > 0.003\
                #     # and emas26[0] > emas26[1]:# and emas50[0] > emas26[0]
                #     motif += " 12x26"
                #     b_achat = True

                if intest == "" and b_en_production:
                    b_achat = True

                if b_achat:
                    # SUPPORT -> ACHAT
                    b_macd = False
                    btraite = True
                    rsi = rsis[0]
                    rsi_achat = rsis[0]
                    quantity = int(self.config["amount"] / quote)
                    amount = quantity * quote
                    cost = quote + quote * self.config["cost"] * 2 # frais
                    gain = amount - quantity * cost
                    gain_percent = (gain / amount) * 100
                    nbj = 0
                    test_date = cours["cours_date"]

                    # maj du cours
                    intest = "TTT"
                    cours["cours_trade"] = "SSS"
                    cours["cours_nbj"] = nbj
                    cours["cours_quantity"] = quantity
                    cours["cours_cost"] = cost
                    cours["cours_gain"] = gain
                    cours["cours_gain_percent"] = gain_percent

                    self.tools.exec_sql("""UPDATE COURS
                    set cours_trade = :cours_trade, cours_nbj = :cours_nbj, cours_quantity = :cours_quantity, cours_cost = :cours_cost
                    , cours_gain = :cours_gain, cours_gain_percent = :cours_gain_percent
                    WHERE cours_ptf_id = :cours_ptf_id and cours_date = :cours_date
                    """, cours)

                    ptf["ptf_resistance"] = ""
                    ptf["ptf_support"] = "SSS"
                    ptf["ptf_test_date"] = cours["cours_date"]

                if not btraite and (intest == "TTT" or b_en_production):
                    btraite = True

                    # cas des pertes sans palier dans les 26 jours
                    amount = quantity * quote
                    gain = amount - quantity * cost
                    if amount > 0:
                        gain_percent = (gain / amount) * 100

                    # maj du cours
                    cours["cours_quantity"] = quantity
                    cours["cours_cost"] = cost
                    cours["cours_gain"] = gain
                    cours["cours_gain_percent"] = gain_percent

                    # croisement macd qui permet de valider l'achat récent
                    # if emas26[1] > emas12[1] and emas12[0] > emas26[0]:
                    # if macd[0] > 0:
                    #     motif += " 12x26"
                    #     b_macd = True

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

                    # on vend si emas26 < emas50
                    # if not b_vendre and b_macd and emas26[0] < emas50[0]:
                    # if not b_vendre and emas26[0] < emas50[0] and nbj > 4:
                    #     motif += " 26<50"
                    #     b_vendre = True

                    # if not b_vendre and emas26[0] < emas26[1] and nbj > 2:
                    #     motif += " 26-"
                    #     b_vendre = True

                    # on vend quand le cours est le plus haut
                    # sans     Nbre de mises: 23 Cash: -31749.09 € Gain acquis: -20.96 € Gain : 1854.28 €
                    # avec >65 Nbre de mises: -10 Cash: 6102.30 € Gain acquis: 12.51 € Gain : 26.51 €
                    # avec >70 Nbre de mises: -3 Cash: -2114.33 € Gain acquis: 155.79 € Gain : 503.30 €
                    if rsis[1] > 67:
                        motif += " >67"
                        b_vendre = True

                    # garde-fou : croisemnt 26x12 avant la hausse du 50
                    # if not b_vendre and emas26[0] < emas26[1] and macd[0] < 0 and emas50[0] < emas50[1] and nbj > 2:
                    #     motif += " 26-"
                    #     b_vendre = True

                    if b_vendre and b_en_production:
                        # on signale que la valeur en production doit être vendue
                        # Maj du cours
                        nbj += 1

                        cours["cours_trade"] = intest
                        cours["cours_nbj"] = nbj

                        self.tools.exec_sql("""UPDATE COURS
                        set cours_trade = :cours_trade, cours_nbj = :cours_nbj, cours_quantity = :cours_quantity, cours_cost = :cours_cost
                        , cours_gain = :cours_gain, cours_gain_percent = :cours_gain_percent
                        WHERE cours_ptf_id = :cours_ptf_id and cours_date = :cours_date
                        """, cours)

                        ptf["ptf_resistance"] = "RRR"
                        ptf["ptf_support"] = ""
                    else:
                        # RESISTANCE -> VENTE
                        if b_vendre:
                            nbj += 1

                            cumulptf += gain
                            cumul += gain

                            # maj du cours
                            cours["cours_trade"] = "RRR"
                            cours["cours_nbj"] = nbj

                            self.parent.display("  {} / {} {} {:.0f}/{:.0f} {:.2f} {}j\t{:.2f}€"\
                            .format(test_date, cours["cours_date"], motif, rsi_achat, rsis[0]\
                            , macd[0], nbj, gain))
        
                            self.tools.exec_sql("""UPDATE COURS
                            set cours_trade = :cours_trade, cours_nbj = :cours_nbj, cours_quantity = :cours_quantity, cours_cost = :cours_cost
                            , cours_gain = :cours_gain, cours_gain_percent = :cours_gain_percent
                            WHERE cours_ptf_id = :cours_ptf_id and cours_date = :cours_date
                            """, cours)

                            ptf["ptf_resistance"] = "RRR"
                            ptf["ptf_support"] = ""

                            b_macd = False
                            motif = ""
                            rsi_achat = 0
                            intest = ""
                            nbj = 0
                            quantity = 0
                            cost = 0
                            gain = 0
                            gain_percent = 0
                            test_date = ""
                        else:
                            # Maj du cours
                            nbj += 1

                            cours["cours_trade"] = "TTT"
                            cours["cours_nbj"] = nbj

                            self.tools.exec_sql("""UPDATE COURS
                            set cours_trade = :cours_trade, cours_nbj = :cours_nbj, cours_quantity = :cours_quantity, cours_cost = :cours_cost
                            , cours_gain = :cours_gain, cours_gain_percent = :cours_gain_percent
                            WHERE cours_ptf_id = :cours_ptf_id and cours_date = :cours_date
                            """, cours)

                            ptf["ptf_resistance"] = ""
                            ptf["ptf_support"] = ""

                # MAJ du COURS qui n'est pas en TEST
                if not btraite:
                    btraite = True
                    ptf["ptf_resistance"] = ""
                    ptf["ptf_support"] = ""

                # maj du PTF avec les données du cours
                ptf["ptf_quote"] = cours["cours_close"]
                ptf["ptf_percent"] = cours["cours_percent"]
                ptf["ptf_rsi"] = cours["cours_rsi"]
                ptf["ptf_macd"] = (cours["cours_macd"]/cours["cours_close"]) * 100

            # mise à jour du portefeuille à la fin
            ptf["ptf_test_cost"] = cost
            ptf["ptf_test_quantity"] = quantity
            ptf["ptf_test_gain"] = gain
            ptf["ptf_test_gain_percent"] = gain_percent
            ptf["ptf_test_nbj"] = nbj
            ptf["ptf_intest"] = intest
            ptf["ptf_test_date"] = test_date
            self.tools.exec_sql("""UPDATE PTF
            set ptf_quote = :ptf_quote 
            ,ptf_percent = :ptf_percent 
            ,ptf_quantity = :ptf_quantity
            ,ptf_resistance = :ptf_resistance
            ,ptf_support = :ptf_support
            ,ptf_rsi = :ptf_rsi 
            ,ptf_macd = :ptf_macd 
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
            self.parent.display("{} Gain:{:.2f}\tCumul:{:.2f}".format(ptf["ptf_id"]\
            , cumulptf, cumul))

        # Résumé de la simulation - boucle sur les cours par date pour connaître le cash nécessaire
        courss = self.tools.sql_to_dict("""SELECT * FROM COURS
        WHERE cours_trade in ('SSS','TTT','RRR')
        ORDER BY cours_date, cours_ptf_id""", {})
        cash = 0
        qamount = 0
        cumul = 0
        for cours in courss:
            if cours["cours_trade"] == "SSS":
                cash = cash - cours["cours_cost"] * cours["cours_quantity"]
                qamount += 1
            if cours["cours_trade"] == "RRR":
                cash = cash + cours["cours_close"] * cours["cours_quantity"]
                cumul += cours["cours_gain"]
                qamount -= 1
        # prise en compte des actions en test
        gain_acquis = cumul
        ptfs = self.tools.sql_to_dict("""SELECT * FROM PTF
        WHERE ptf_intest = 'TTT'
        """, ptf)
        for ptf in ptfs:
            cumul += ptf["ptf_test_gain"]

        self.parent.display("Nbre de mises: {} Cash: {:.2f} € Gain acquis: {:.2f} € Gain : {:.2f} € {:.2f}%"\
        .format(qamount, -cash, gain_acquis, cumul, (cumul/-cash)*100))
