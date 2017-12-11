#!/usr/bin/env python
# -*- coding:Utf-8 -*-
"""
    Batch de mise à jour des données de la base
"""
import shutil
import os
import sys
import datetime
import argparse

from crud import Crud
from crudel import Crudel
from plugin.picsou_loader import PicsouLoadQuotes

class PicsouBatch():
    """ Actualisation des données """
    # Planification dans cron
    # 55 9,11,16 * * 1-5 /home/pi/git/crudenome/picsou_batch.py -quote -simul -sms
    # 55 17 * * 1-5 /home/pi/git/crudenome/picsou_batch.py -quote -simul -sms -mail

    def __init__(self, args):

        self.args = args
        # Chargement des paramètres
        self.crud = Crud()

        application = self.crud.get_json_content(
            self.crud.config["application_directory"] + "/" + "picsou.json")

        self.crud.set_application(application)

        # Récupération éventuelle de la base sur le host
        ticket_user = os.path.getmtime(self.crud.get_basename())
        ticket_host = os.path.getmtime(self.crud.get_basehost())
        if ticket_user != ticket_host:
            shutil.copy2(self.crud.get_basehost(), self.crud.get_basename())
            self.display("Restore OK %s %s" % (self.crud.get_basehost(), datetime.datetime.fromtimestamp(ticket_host)))

        element = "_batch"
        self.crud.set_table_id("ptf")
        self.crud.set_view_id("vsimul")
        self.crudel = Crudel.instantiate(self.crud, element, Crudel.TYPE_PARENT_VIEW)
        self.crudel.init_value()
        self.crud.set_element_prop(element, "crudel", self.crudel)
        self.crud.set_crudel(self.crudel)

        self.supports = []
        self.resistances = []
        self.top14 = []
        self.last_date = "1953-06-21"
        self.rsi_time = "12:32"
        self.myptf = []
        self.run_calcul()

        # Put de la base de données sur la box
        ticket_user = os.path.getmtime(self.crud.get_basename())
        ticket_host = os.path.getmtime(self.crud.get_basehost())
        if ticket_user != ticket_host:
            shutil.copy2(self.crud.get_basename(), self.crud.get_basehost())
            self.display("Backup  OK %s %s" % (self.crud.get_basehost(), datetime.datetime.fromtimestamp(ticket_user)))

    def display(self, msg):
        """ docstring """
        print msg
        # self.crud.logger.info(msg)

    def run_calcul(self):
        """ docstring """
        loader = PicsouLoadQuotes(self, self.crud)
        if self.args.quote:
            ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
            SELECT * FROM ptf ORDER BY ptf_id
            """, {})
            self.display("Actualisation des cours...")
            for ptf in ptfs:
                loader.run(ptf["ptf_id"], 10)

        if self.args.histo:
            ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
            SELECT * FROM ptf ORDER BY ptf_id
            """, {})
            self.display("Chargement de l'historique...")
            for ptf in ptfs:
                loader.run(ptf["ptf_id"], 400)

        if self.args.simul:
            loader.simulateur()

            # Maj PTF gain des valeurs en production
            self.crud.exec_sql(self.crud.get_basename(), """
            UPDATE PTF
            set ptf_gain = (ptf_quote - ptf_cost) * ptf_quantity
            WHERE ptf_account is not null and ptf_account <> ''
            """, {})
            self.crud.exec_sql(self.crud.get_basename(), """
            UPDATE PTF
            set ptf_gain_percent = (ptf_gain / (ptf_cost * ptf_quantity)) * 100
            WHERE ptf_account is not null and ptf_account <> ''
            """, {})

            # Maj PTF quantité cout des valeurs non sélectionnées (en ptf ou test)
            self.crud.exec_sql(self.crud.get_basename(), """
            UPDATE PTF
            set ptf_quantity = round(1200 / ptf_quote)
            ,ptf_cost = ptf_quote + ptf_quote * 0.01
            , ptf_gain = 0, ptf_gain_percent = 0
            WHERE ptf_account is null or ptf_account = ''
            """, {})

            # mise à jour du résumé
            last_dates = self.crud.sql_to_dict(self.crud.get_basename(), """
            SELECT max(cours_date) as last_date FROM cours
            """, {})
            self.last_date = last_dates[0]["last_date"]
            # self.rsi_time = loader.quote["time"]
            self.rsi_time = "00:00"
            gainj = self.crud.sql_to_dict(self.crud.get_basename(), """
            SELECT sum(ptf_gainj) AS result FROM PTF WHERE ptf_account is not null and ptf_account <> ''
            """, {})
            gain = self.crud.sql_to_dict(self.crud.get_basename(), """
            SELECT sum(ptf_gain) AS result FROM PTF WHERE ptf_account is not null and ptf_account <> ''
            """, {})
            investi = self.crud.sql_to_dict(self.crud.get_basename(), """
            SELECT sum(ptf_cost * ptf_quantity) AS result FROM PTF WHERE ptf_account is not null and ptf_account <> ''
            """, {})
            self.crud.exec_sql(self.crud.get_basename(), """
            UPDATE RESUME
            set resume_date = :date 
            ,resume_time = :time 
            ,resume_investi = :investi
            ,resume_gainj = :gainj
            ,resume_gain = :gain
            """, {"date": self.last_date, "time": self.rsi_time, "investi": investi[0]["result"], "gain": gain[0]["result"], "gainj": gainj[0]["result"]})
            self.crud.exec_sql(self.crud.get_basename(), """
            UPDATE RESUME
            set resume_percent = (resume_gain / resume_investi) * 100
            """, {})

        if self.args.account:
            loader.account()

        # Mail de compte-rendu
        if self.args.mail or self.args.sms:
            # Mon portefeuille
            ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
            SELECT * FROM ptf WHERE ptf_account is not null and ptf_account <> '' ORDER by ptf_name
            """, {})
            msg = """<tr>
            <th>Action</th>
            <th>Cours</th>
            <th>Evol</th>
            <th>Gain du J</th>
            <th>Gain Tot.</th>
            <th>en %</th>
            <th>Trade</th>
            <th>RSI</th>
            <th>Q12</th>
            <th>Q26</th>
            <th>Note</th>
            <th>&nbsp;</th>
            </tr>"""
            self.myptf.append(msg)
            tot_gainj = 0.0
            tot_cost = 0.0
            tot_brut = 0.0
            sms = ""
            for ptf in ptfs:
                url = '<a href="https://fr.finance.yahoo.com/chart/{0}">{0}</a>'.format(ptf["ptf_id"])
                tot_gainj += ptf["ptf_gainj"]
                tot_cost += ptf["ptf_cost"] * ptf["ptf_quantity"]
                tot_brut += ptf["ptf_quote"] * ptf["ptf_quantity"]
                msg = """<tr>
                <td>{0}</td>
                <td style="text-align: right">{1:3.2f}</td>
                <td style="text-align: right">{2:2.2f} %</td>
                <td style="text-align: right">{3:4.2f} €</td>
                <td style="text-align: right">{4:4.2f} €</td>
                <td style="text-align: right">{5:3.2f} %</td>
                <td style="text-align: right">{6}</td>
                <td style="text-align: right">{7:2.0f}</td>
                <td style="text-align: right">{8:2.2f} %</td>
                <td style="text-align: right">{9:3.2f} %</td>
                <td>{10}</td>
                </tr>""".format(ptf["ptf_name"]\
                , ptf["ptf_quote"]\
                , ptf["ptf_percent"]\
                , ptf["ptf_gainj"]\
                , ptf["ptf_gain"]\
                , ptf["ptf_gain_percent"]\
                , ptf["ptf_rsi"]\
                , ptf["ptf_q12"]\
                , ptf["ptf_q26"]\
                , url)
                self.myptf.append(msg)
                sms += u" :: %s %s %3.2f %2.2f%% %3.2f€" % ( ptf["ptf_id"], ptf["ptf_trade"], ptf["ptf_quote"], ptf["ptf_percent"], ptf["ptf_gainj"])

            msg = """<tr>
            <td>{0}</td>
            <td style="text-align: right">{1}</td>
            <td style="text-align: right">{2}</td>
            <td style="text-align: right">{3:4.2f} €</td>
            <td style="text-align: right">{4:4.2f} €</td>
            <td style="text-align: right">{5:3.2f} %</td>
            <td style="text-align: right">{6}</td>
            <td style="text-align: right">{7}</td>
            <td style="text-align: right">{8}</td>
            <td style="text-align: right">{9}</td>
            <td>{10}</td>
            </tr>""".format("Total"\
            , ""\
            , ""\
            , tot_gainj\
            , tot_brut - tot_cost\
            , ((tot_brut - tot_cost) / tot_cost) * 100\
            , ""\
            , ""\
            , ""\
            , ""\
            , "")
            self.myptf.append(msg)

            # envoi du mail
            subject = u"Picsou du {} Jour {:.2f} € Total {:.2f} €".format(self.last_date, tot_gainj, tot_brut - tot_cost)
            msg = '<h3>{}</h3>\n<table>\n'.format("Mes actions au {}".format(self.last_date))
            msg += '\n'.join(self.myptf)
            msg += '</table>\n'
            dest = self.crudel.get_param("smtp_dest")

        if self.args.mail:
            self.crud.send_mail(dest, subject.encode("utf-8"), msg)

        if self.args.sms:
            self.crud.send_sms(subject.encode("utf-8") + sms.encode("utf-8"))

if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog='picsou_batch')
    # add a -c/--color option
    parser.add_argument('-mail', '--mail', action='store_true', default=False, help="Envoi mail à la fin")
    parser.add_argument('-sms', '--sms', action='store_true', default=False, help="Envoi SMS à la fin")
    parser.add_argument('-histo', '--histo', action='store_true', default=False, help="Rechargement de l'historique des cours sur 400 jours")
    parser.add_argument('-simul', '--simul', action='store_true', default=False, help="Avec recalcul du simulateur")
    parser.add_argument('-quote', '--quote', action='store_true', default=False, help="Requête pour actualiser le cours du jour")
    parser.add_argument('-account', '--account', action='store_true', default=False, help="Requête pour actualiser les comptes")
    # print parser.parse_args()

    PicsouBatch(parser.parse_args())
