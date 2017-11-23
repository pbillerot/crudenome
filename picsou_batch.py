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
from plugin.picsou_backup import PicsouBackup, PicsouRestore

class PicsouBatch():
    """ Actualisation des données """
    DIR_HOST = "/mnt/freebox"
    PATH_BASENAME = "/data/picsou/picsou.sqlite"
    def __init__(self):

        # # Get de la base de données sur la box
        # path_host = self.DIR_HOST + self.PATH_BASENAME
        # path_user = os.path.expanduser("~") + self.PATH_BASENAME
        # ticket_host = os.path.getmtime(path_host)
        # ticket_user = os.path.getmtime(path_user)
        # if ticket_host != ticket_user:
        #     print "Get %s %s" % (path_host, datetime.datetime.fromtimestamp(ticket_host))
        #     shutil.copy2(path_host, path_user)

        # Chargement des paramètres
        self.crud = Crud()

        application = self.crud.get_json_content(
            self.crud.config["application_directory"] + "/" + "picsou.json")

        self.crud.set_application(application)
        self.crud.set_table_id("ptf")
        self.crud.set_view_id("vsimul")

        # Récupération éventuelle de la base sur le host
        PicsouRestore(self.crud)

        element = "_batch"
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
        PicsouBackup(self.crud)

    def display(self, msg):
        """ docstring """
        print msg

    def run_calcul(self):
        """ docstring """

        loader = PicsouLoadQuotes(self, self.crud)
        ptfs = self.crud.sql_to_dict(self.crud.get_table_basename(), """
        SELECT * FROM ptf ORDER BY ptf_id
        """, {})
        print "Chargement de l'historique..."
        for ptf in ptfs:
            loader.run(ptf["ptf_id"], 10)

        loader.simulateur()

        self.crud.exec_sql(self.crud.get_table_basename(), """
        UPDATE PTF
        set ptf_gain = (ptf_quote - ptf_cost) * ptf_quantity
        WHERE ptf_inptf = 'PPP'
        """, {})
        self.crud.exec_sql(self.crud.get_table_basename(), """
        UPDATE PTF
        set ptf_gain_percent = (ptf_gain / (ptf_cost * ptf_quantity)) * 100
        WHERE ptf_inptf = 'PPP'
        """, {})

        # mise à jour du résumé
        self.rsi_date = loader.quote["date"]
        # self.rsi_time = loader.quote["time"]
        self.rsi_time = "00:00"
        gain = self.crud.sql_to_dict(self.crud.get_table_basename(), """
        SELECT sum(ptf_gain) AS result FROM PTF WHERE ptf_inptf = 'PPP'
        """, {})
        investi = self.crud.sql_to_dict(self.crud.get_table_basename(), """
        SELECT sum(ptf_cost * ptf_quantity) AS result FROM PTF WHERE ptf_inptf = 'PPP'
        """, {})
        self.crud.exec_sql(self.crud.get_table_basename(), """
        UPDATE RESUME
        set resume_date = :date 
        ,resume_time = :time 
        ,resume_investi = :investi
        ,resume_gain = :gain
        """, {"date": self.rsi_date, "time": self.rsi_time, "investi": investi[0]["result"], "gain": gain[0]["result"]})
        self.crud.exec_sql(self.crud.get_table_basename(), """
        UPDATE RESUME
        set resume_percent = (resume_gain / resume_investi) * 100
        """, {})

        # Mail de compte-rendu
        if 1==0:
            # TOP 14
            ptfs = self.crud.sql_to_dict(self.crud.get_table_basename(), """
            select * from ptf order by ptf_macd desc limit 14
            """, {})
            for ptf in ptfs:
                url = '<a href="https://fr.finance.yahoo.com/chart/{0}">{0}</a>'.format(ptf["ptf_id"])
                msg = """<tr>
                <td style="text-align: right">{0:3.2f}%</td>
                <td>{1}</td><td>{2}</td>
                <td style="text-align: right">{3:.2f}</td>
                <td style="text-align: right">{4:.2f}%</td>
                <td>{5}</td>
                </tr>
                """.format(ptf["ptf_macd"], ptf["ptf_inptf"], ptf["ptf_name"], ptf["ptf_quote"], ptf["ptf_percent"], url)
                self.top14.append(msg)

            # Mon portefeuille
            ptfs = self.crud.sql_to_dict(self.crud.get_table_basename(), """
            select * from ptf order by ptf_gain_percent desc
            """, {})
            msg = """<tr>
            <th>Action</th>
            <th>Cours</th>
            <th>du J</th>
            <th>Revient</th>
            <th>Nbre</th>
            <th>Gain</th>
            <th>en %</th>
            <th>14 j</th>
            <th>&nbsp;</th>
            </tr>"""
            self.myptf.append(msg)
            for ptf in ptfs:
                url = '<a href="https://fr.finance.yahoo.com/chart/{0}">{0}</a>'.format(ptf["ptf_id"])                
                if ptf["ptf_inptf"] == "PPP" :
                    msg = """<tr>
                    <td>{0}</td>
                    <td style="text-align: right">{1:.2f}</td>
                    <td style="text-align: right">{2:.2f}%</td>
                    <td style="text-align: right">{3:.2f}</td>
                    <td style="text-align: right">{4}</td>
                    <td style="text-align: right">{5:.2f} €</td>
                    <td style="text-align: right">{6:.2f}%</td>
                    <td style="text-align: right">{7:.2f}%</td>
                    <td>{8}</td>
                    </tr>""".format(ptf["ptf_name"], ptf["ptf_quote"], ptf["ptf_percent"], ptf["ptf_cost"], ptf["ptf_quantity"], ptf["ptf_gain"], ptf["ptf_gain_percent"], ptf["ptf_macd"], url)                     
                    self.myptf.append(msg)

                if ptf["ptf_inptf"] == "PPP" and ptf["ptf_resistance"] == "RRR":
                    msg = '<tr><td>{0}</td><td>{1}</td><td style="text-align: right">{2:.2f}</td><td>{3}</td></tr>'\
                    .format(ptf["ptf_date"], ptf["ptf_name"], ptf["ptf_quote"], url)
                    self.resistances.append(msg)

                if ptf["ptf_support"] == "SSS":
                    msg = '<tr><td>{0}</td><td>{1}</td><td style="text-align: right">{2:.2f}</td><td style="text-align: right">{3}</td><td>{4}</td></tr>'\
                    .format(ptf["ptf_date"], ptf["ptf_name"], ptf["ptf_quote"], ptf["ptf_quantity"], url)
                    self.supports.append(msg)

            # envoi du mail
            msg = '<h3>{}</h3>\n<table>\n'.format("Mes actions au {} gain {:.2f} €".format(self.rsi_date, gain[0]["result"]))
            msg += '\n'.join(self.myptf)
            msg += '</table>\n'
            msg += "<h3>{}</h3>\n<table>\n".format(self.crudel.get_param("label_resistance"))
            msg += '\n'.join(self.resistances)
            msg += '</table>\n'
            msg += "<h3>{}</h3>\n<table>\n".format(self.crudel.get_param("label_support"))
            msg += '\n'.join(self.supports)
            msg += '</table>\n'
            msg += "<h3>{}</h3>\n<table>\n".format(self.crudel.get_param("label_top14"))
            msg += '\n'.join(self.top14)
            msg += '</table>\n'
            dest = self.crudel.get_param("smtp_dest")

            self.crud.send_mail(dest, "Picsou du {} gain {:.2f} €".format(self.rsi_date, gain[0]["result"]), msg)

if __name__ == '__main__':
    PicsouBatch()