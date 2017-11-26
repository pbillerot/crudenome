#!/usr/bin/env python
# -*- coding:Utf-8 -*-
"""
    Batch de mise à jour des données de la base
"""
import shutil
import os
import datetime

from crud import Crud
from crudel import Crudel
from plugin.picsou_loader import PicsouLoadQuotes

class PicsouBatch():
    """ Actualisation des données """
    # Planification dans cron
    # 55 9,11,16,17 * * 1-5 ./git/crudenome/picsou_batch.py

    def __init__(self):

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
            print "Restore OK %s %s" % (self.crud.get_basehost(), datetime.datetime.fromtimestamp(ticket_host))

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
        self.rsi_date = "2017-07-11"
        self.rsi_time = "14:35"
        self.myptf = []
        self.run_calcul()

        # Put de la base de données sur la box
        ticket_user = os.path.getmtime(self.crud.get_basename())
        shutil.copy2(self.crud.get_basename(), self.crud.get_basehost())
        print "Backup  OK %s %s" % (self.crud.get_basehost(), datetime.datetime.fromtimestamp(ticket_user))

    def display(self, msg):
        """ docstring """
        print msg

    def run_calcul(self):
        """ docstring """
        if 1==1:
            loader = PicsouLoadQuotes(self, self.crud)
            ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
            SELECT * FROM ptf ORDER BY ptf_id
            """, {})
            print "Chargement de l'historique..."
            for ptf in ptfs:
                loader.run(ptf["ptf_id"], 10)

            loader.simulateur()

            self.crud.exec_sql(self.crud.get_basename(), """
            UPDATE PTF
            set ptf_gain = (ptf_quote - ptf_cost) * ptf_quantity
            WHERE ptf_inptf = 'PPP'
            """, {})
            self.crud.exec_sql(self.crud.get_basename(), """
            UPDATE PTF
            set ptf_gain_percent = (ptf_gain / (ptf_cost * ptf_quantity)) * 100
            WHERE ptf_inptf = 'PPP'
            """, {})

            # mise à jour du résumé
            self.rsi_date = loader.quote["date"]
            # self.rsi_time = loader.quote["time"]
            self.rsi_time = "00:00"
            gain = self.crud.sql_to_dict(self.crud.get_basename(), """
            SELECT sum(ptf_gain) AS result FROM PTF WHERE ptf_inptf = 'PPP'
            """, {})
            investi = self.crud.sql_to_dict(self.crud.get_basename(), """
            SELECT sum(ptf_cost * ptf_quantity) AS result FROM PTF WHERE ptf_inptf = 'PPP'
            """, {})
            self.crud.exec_sql(self.crud.get_basename(), """
            UPDATE RESUME
            set resume_date = :date 
            ,resume_time = :time 
            ,resume_investi = :investi
            ,resume_gain = :gain
            """, {"date": self.rsi_date, "time": self.rsi_time, "investi": investi[0]["result"], "gain": gain[0]["result"]})
            self.crud.exec_sql(self.crud.get_basename(), """
            UPDATE RESUME
            set resume_percent = (resume_gain / resume_investi) * 100
            """, {})

        # Mail de compte-rendu
        if 1==1:
            # Mon portefeuille
            ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
            SELECT * FROM ptf WHERE ptf_inptf = 'PPP' ORDER by ptf_name
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
            <th>E50</th>
            <th>E200</th>
            <th>Note</th>
            <th>&nbsp;</th>
            </tr>"""
            self.myptf.append(msg)
            tot_gainj = 0.0
            tot_cost = 0.0
            tot_brut = 0.0
            for ptf in ptfs:
                url = '<a href="https://fr.finance.yahoo.com/chart/{0}">{0}</a>'.format(ptf["ptf_id"])
                quote1 = ptf["ptf_quote"] * 100 / (ptf["ptf_percent"] + 100)
                gainj = (ptf["ptf_quote"] - quote1) * ptf["ptf_quantity"]
                # gainj = ptf["ptf_quote"] * ptf["ptf_percent"] / 100 * ptf["ptf_quantity"]
                tot_gainj += gainj
                tot_cost += ptf["ptf_cost"] * ptf["ptf_quantity"]
                tot_brut += ptf["ptf_quote"] * ptf["ptf_quantity"]
                msg = """<tr>
                <td>{0}</td>
                <td style="text-align: right">{1:3.2f}</td>
                <td style="text-align: right">{3:2.2f} %</td>
                <td style="text-align: right">{2:4.2f} €</td>
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
                , gainj\
                , ptf["ptf_gain"]\
                , ptf["ptf_gain_percent"]\
                , ptf["ptf_resistance"]\
                , ptf["ptf_rsi"]\
                , ptf["ptf_macd"]\
                , ptf["ptf_e200"]\
                , url)
                self.myptf.append(msg)

            msg = """<tr>
            <td>{0}</td>
            <td style="text-align: right"></td>
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
            msg = '<h3>{}</h3>\n<table>\n'.format("Mes actions au {}".format(self.rsi_date))
            msg += '\n'.join(self.myptf)
            msg += '</table>\n'
            dest = self.crudel.get_param("smtp_dest")

            self.crud.send_mail(dest, "Picsou du {} Jour {:.2f} € Total {:.2f} €".decode("utf-8")\
            .format(self.rsi_date, tot_gainj, tot_brut - tot_cost)\
            , msg.decode("utf-8"))

if __name__ == '__main__':
    PicsouBatch()
