#./venv/bin/python3
# -*- coding:Utf-8 -*-
"""
    Batch de mise à jour des données de la base
"""
import shutil
import os
import datetime, time
import argparse
import sys
import glob
import re

from crud import Crud
from crudel import Crudel
from plugin.picsou_loader import PicsouLoader
import matplotlib.pyplot as plt, matplotlib.gridspec as gridspec

class PicsouBatch():
    """ Actualisation des données """
    # Planification dans cron
    # 55 9,11,16 * * 1-5 /home/pi/git/crudenome/picsou_batch.py -quote -trade -sms
    # 55 17 * * 1-5 /home/pi/git/crudenome/picsou_batch.py -quote -trade -sms -mail

    def __init__(self, args):

        self.args = args
        # Chargement des paramètres
        self.crud = Crud()

        application = self.crud.get_json_content(
            self.crud.config["application_directory"] + "/" + "picsou.json")

        self.crud.set_application(application)

        if self.args.backup:
            self.backup()

        if self.args.restore:
            self.restore()

        if self.args.day:
           self.run_day()
           return

        if self.args.dayrepeat:
           self.day_repeat()
           return

        if self.args.graph:
           self.graphLastQuotes()

        if self.args.note:
           self.update_note()


    def display(self, msg):
        """ docstring """
        print(msg)
        # self.crud.logger.info(msg)
    def pout(self, msg):
        """ docstring """
        sys.stdout.write(msg)
        sys.stdout.flush()
        # self.crud.logger.info(msg)

    def day_repeat(self):
        """ Lancement toutes les 5 minutes de day """
        time1 = time.time()
        isStart = True
        while True:
            time2 = time.time()
            if isStart :
                now = datetime.datetime.now()
                today0910 = now.replace(hour=9, minute=12, second=0, microsecond=0)
                today1750 = now.replace(hour=17, minute=50, second=0, microsecond=0)
                if now > today0910 and now < today1750 :
                    self.run_day()
                else:
                    self.display("Picsou en dehors de la plage autorisée".format())
                isStart = False
            isStart = False
            if ( (time2-time1) > 5 * 60 ):
                now = datetime.datetime.now()
                today0910 = now.replace(hour=9, minute=12, second=0, microsecond=0)
                today1750 = now.replace(hour=17, minute=50, second=0, microsecond=0)
                if now > today0910 and now < today1750 :
                        self.run_day()
                        time1 = time2
                else:
                    self.display("Picsou en dehors de la plage autorisée".format())
            time.sleep(1)

    def run_day(self):
        self.display(datetime.datetime.now().strftime("%Y/%m/%d, %H:%M:%S") + " : Picsou se démène..." )
        
        if self.args.quote:
            loader = PicsouLoader(self, self.crud)
            loader.quotes()

        if self.args.graph:
            self.display("")
            self.graphLastQuotes()

        if self.args.trade:
            loader = PicsouLoader(self, self.crud)
            loader.trade(with_sms=self.args.sms)

        self.display(datetime.datetime.now().strftime("%Y/%m/%d, %H:%M:%S") + " : Picsou se repose" )

    def backup(self):
        """ backup """
        # Put de la base de données sur la box
        ticket_user = os.path.getmtime(self.crud.get_basename())
        ticket_host = os.path.getmtime(self.crud.get_basehost())
        if ticket_user != ticket_host:
            shutil.copy2(self.crud.get_basename(), self.crud.get_basehost())
            self.display("Backup OK %s %s" % (self.crud.get_basehost(), datetime.datetime.fromtimestamp(ticket_user)))
        else:
            self.display("Backup NA %s %s" % (self.crud.get_basehost(), datetime.datetime.fromtimestamp(ticket_user)))

    def restore(self):
        """ restauration """
        # Restauration de la base de données sur la box
        ticket_user = os.path.getmtime(self.crud.get_basename())
        ticket_host = os.path.getmtime(self.crud.get_basehost())
        if ticket_user != ticket_host:
            # shutil.copy2(self.crud.get_basehost(), self.crud.get_basename())
            self.display("Restore OK %s %s" % (self.crud.get_basehost(), datetime.datetime.fromtimestamp(ticket_host)))
        else:
            self.display("Restore NA %s %s" % (self.crud.get_basehost(), datetime.datetime.fromtimestamp(ticket_host)))

    def update_note(self):
        """ Mise à jour du champ note avec des infos pertinentes pour le trading """
        ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
            SELECT * FROM ptf where ptf_enabled = '1' order by ptf_id
            """, {})
        for ptf in ptfs:
            quotes = self.crud.sql_to_dict(self.crud.get_basename(), """
            SELECT * FROM quotes where id = :id order by date desc limit 1
            """, {"id": ptf["ptf_id"]})
            if quotes is None : continue
            quote = quotes[0]
            """
            - P4 : si quotemin < -4 %
            - Q0 : si quotemin < 0 et close > close1
            """
            note = ""
            pmin = (quote["low"] - quote["close1"])/quote["close1"]
            if float(pmin) < -0.04 : note = "P4"
            if quote["low"] < quote["close1"] and quote["close"] > quote["close1"] :
                note += " Q+"
            self.crud.exec_sql(self.crud.get_basename(), """
                update ptf set ptf_note = :note where ptf_id = :id
                """, {"id": ptf["ptf_id"], "note": note})
            if note != "" :
                self.display("{} : {}".format(ptf["ptf_id"], note))

    def graphLastQuotes(self):
        """ """

        def mini_date(sdate):
            return sdate[8:10] + "-" + sdate[5:7]

        self.pout("graphLastQuotes... ")

        # Chargement des commentaires 
        ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
        SELECT * FROM ptf
        """, {})
        notes = {}
        for ptf in ptfs:
            notes[ptf["ptf_id"]] = ptf["ptf_note"]

        quotes = self.crud.sql_to_dict(self.crud.get_basename(), """
        SELECT quotes.*, ptf_name FROM quotes left outer join ptf on ptf_id = id order by id ,date
        """, {})

        id_current = ""
        dquotes = []
        ddate = []
        dzero = []
        dpercent= []
        dhig_p= []
        dhig_n= []
        dlow_p= []
        dlow_n= []
        dvol = []
        labelx = []
        ptf_name = ""
        qclose1 = 0
        if len(quotes) > 0:
            for quote in quotes:
                if id_current == "" : # la 1ère fois
                   id_current = quote["id"]
                   qclose1 = quote["open"]
                   ptf_name = quote["ptf_name"]
                #    self.pout("graphLastQuotes... " + quote["id"])
                # un graphe par ptf
                if id_current == quote["id"] :
                    # chargement des données

                    # le matin
                    dvol.append(quote["volume"])
                    dquotes.append(quote["open"])
                    ddate.append(mini_date(quote["date"]) + " open")
                    labelx.append(mini_date(quote["date"]))
                    dzero.append(0)

                    percent = ((quote["open"]-qclose1) / qclose1)*100
                    dpercent.append( percent )

                    high = quote["high"] if quote["high"] > quote["open"] else quote["open"]
                    dhig = ((high-qclose1) / qclose1)*100
                    if dhig > 0 :
                        dhig_p.append( dhig )
                        dhig_n.append( 0 )
                    else :
                        dhig_p.append( 0 )
                        dhig_n.append( dhig )
                    low = quote["low"] if quote["low"] < quote["open"] else quote["open"]
                    dlow = ((low-qclose1) / qclose1)*100
                    if dlow > 0 :
                        dlow_p.append( dlow )
                        dlow_n.append( 0 )
                    else :
                        dlow_p.append( 0 )
                        dlow_n.append( dlow )

                    # Le soir
                    dvol.append(quote["volume"])
                    dquotes.append(quote["close"])
                    ddate.append(mini_date(quote["date"]) + " close")
                    labelx.append("")
                    dzero.append(0)
                    percent = ((quote["close"]-qclose1) / qclose1)*100
                    dpercent.append( percent )

                    high = quote["high"] if quote["high"] > quote["open"] else quote["open"]
                    dhig = ((high-qclose1) / qclose1)*100
                    if dhig > 0 :
                        dhig_p.append( dhig )
                        dhig_n.append( 0 )
                    else :
                        dhig_p.append( 0 )
                        dhig_n.append( dhig )

                    low = quote["low"] if quote["low"] < quote["open"] else quote["open"]
                    dlow = ((low-qclose1) / qclose1)*100
                    if dlow > 0 :
                        dlow_p.append( dlow )
                        dlow_n.append( 0 )
                    else :
                        dlow_p.append( 0 )
                        dlow_n.append( dlow )

                    qclose1 = quote["close"]
                else:
                    # Dessin du graphe
                    def draw():
                        fig, ax1 = plt.subplots()
                        fig.set_figwidth(12)
                        fig.set_figheight(6)

                        ax1.plot(ddate, dquotes, 'mo-', label='Cotation')
                        ax1.set_ylabel('Cotation en €', fontsize=9)
                        ax1.tick_params(axis="x", labelsize=8)
                        ax1.tick_params(axis="y", labelsize=8)
                        ax1.legend(loc="lower left")

                        ax2 = ax1.twinx()
                        ax2.plot(ddate, dzero, 'k:', linewidth=2)
                        ax2.plot(ddate, dpercent, 'bo:', alpha=0.6, label="Pourcentage")
                        ax2.bar(ddate, dhig_p, color='b', alpha=0.2, label="Max.")
                        ax2.bar(ddate, dhig_n, color='r', alpha=0.2, label="Min.")
                        ax2.bar(ddate, dlow_p, color='b', alpha=0.2)
                        ax2.bar(ddate, dlow_n, color='r', alpha=0.2)
                        ax2.set_ylabel('Cotation en %', fontsize=9)
                        ax2.tick_params(axis="y", labelsize=8)
                        # ax2.yaxis.set_ticklabels(dpercent , minor=True)
                        # plt.gca().yaxis.set_ticks(dpercent, minor = True) 
                        ax2.legend(loc="lower right")
                        ax2.grid()

                        ax3 = ax1.twinx()
                        ax3.bar(ddate, dvol, color='k', alpha=0.1, width=0.4, label="Volume")
                        ax3.get_yaxis().set_visible(False)
                        ax3.legend(loc="lower center")

                        fig.autofmt_xdate()
                        # plt.title(notes[id_current], fontsize=10)
                        plt.subplots_adjust(left=0.06, bottom=0.1, right=0.93, top=0.90, wspace=None, hspace=None)

                        # fig.canvas.draw_idle()
                        plt.xticks(ddate, labelx)
                        # plt.show()
                        # Création du PNG
                        self.pout(" " + id_current)
                        # Recherche du fichier qui peut être classé dans un sous répertoire
                        pattern_path = "\/png\/(.*?){}\.png".format(id_current)
                        comment = ""
                        files = glob.glob(self.crud.get_application_prop("data_directory") + "/png/quotes/**/{}.png".format(id_current), recursive=True)
                        if len(files) == 0:
                            path = "{}/png/quotes/{}.png".format(self.crud.get_application_prop("data_directory"), id_current)
                        else:
                            path = files[0]
                            srep1 = re.search(pattern_path, path).group(1)
                            comment = srep1.replace("quotes", "").replace("/", "")

                        plt.suptitle("Cours de {} - {}".format(id_current, ptf_name), fontsize=11, fontweight='bold')
                        plt.title(comment, loc='right', color="red", backgroundcolor="yellow") 
                        plt.savefig(path)
                        plt.close()
                        # Maj de net dans ptf
                        self.crud.exec_sql(self.crud.get_basename(), """
                        update ptf set ptf_note = :note where ptf_id = :id
                        """, {"id": id_current, "note": comment})

                    draw()

                    # ça repart pour un tour
                    # self.pout(" " + quote["id"])
                    dquotes.clear()
                    ddate.clear()
                    dpercent.clear()
                    dhig_p.clear()
                    dhig_n.clear()
                    dlow_p.clear()
                    dlow_n.clear()
                    dzero.clear()
                    dvol.clear()
                    id_current = quote["id"]
                    qclose1 = quote["open"]
                    ptf_name = quote["ptf_name"]
            if len(dquotes) > 0 : 
                draw()
            self.display("")

if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog='picsou_batch')
    # add a -c/--color option
    parser.add_argument('-trade', action='store_true', default=False, help="Avec activation du trader")
    parser.add_argument('-quote', action='store_true', default=False, help="Avec actualisation des cours du jour")
    parser.add_argument('-backup', action='store_true', default=False, help="Sauvegarder la base sur la box")
    parser.add_argument('-restore', action='store_true', default=False, help="Restauration de la base locale à partir de la base sur la box")
    parser.add_argument('-day', action='store_true', default=False, help="Requête des cours du jour")
    parser.add_argument('-dayrepeat', action='store_true', default=False, help="Requête des cours du jour toutes les 5 minutes")
    parser.add_argument('-sms', action='store_true', default=False, help="Envoi de SMS de recommandation")
    parser.add_argument('-graph', action='store_true', default=False, help="Création graphique derniers cours")
    parser.add_argument('-note', action='store_true', default=False, help="Mise à jour du bloc note")
    # print parser.parse_args()
    if parser._get_args() == 0:
        parser.print_help()
    else:
        PicsouBatch(parser.parse_args())
