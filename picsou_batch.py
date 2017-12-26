#!/usr/bin/env python
# -*- coding:Utf-8 -*-
"""
    Batch de mise à jour des données de la base
"""
import shutil
import os
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

        if self.args.histo:
            ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
            SELECT * FROM ptf ORDER BY ptf_id
            """, {})
            self.display("Chargement de l'historique...")
            for ptf in ptfs:
                loader.run(ptf["ptf_id"], 500)

        if self.args.quote:
            ptfs = self.crud.sql_to_dict(self.crud.get_basename(), """
            SELECT * FROM ptf ORDER BY ptf_id
            """, {})
            self.display("Actualisation des cours...")
            for ptf in ptfs:
                loader.run(ptf["ptf_id"], 10)

        if self.args.simul:
            loader.simulateur()

        if self.args.account:
            loader.account()

        rows = self.crud.sql_to_dict(self.crud.get_basename(), """
        SELECT printf('SIMUL
        Gain du jour: %8.2f €
                Cash: %8.2f €
              Espèce: %8.2f €
                Gain: %8.2f €
              Latent: %8.2f €
                 soit %8.2f prc',acc_gain_day, acc_initial, acc_money, acc_gain, acc_latent, acc_percent) AS sql_footer
        FROM ACCOUNT where acc_id = 'SIMUL'
        """, {})
        self.display(rows[0]["sql_footer"])

        # Mail de compte-rendu

        if self.args.mail:
            self.crud.set_table_id("ptf")
            self.crud.set_view_id("vrapport")
            html = self.crud.get_sql_report()
            # envoi du mail
            subject = u"Picsou du {}".format(self.last_date)
            dest = self.crudel.get_param("smtp_dest")
            self.crud.send_mail(dest, subject.encode("utf-8"), html.encode("utf-8"))

        # if self.args.sms:
        #     self.crud.send_sms(subject.encode("utf-8") + sms.encode("utf-8"))

if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog='picsou_batch')
    # add a -c/--color option
    parser.add_argument('-mail', '--mail', action='store_true', default=False, help="Envoi mail à la fin")
    parser.add_argument('-sms', '--sms', action='store_true', default=False, help="Envoi SMS à la fin")
    parser.add_argument('-histo', '--histo', action='store_true', default=False, help="Rechargement de l'historique des cours sur 500 jours")
    parser.add_argument('-simul', '--simul', action='store_true', default=False, help="Avec recalcul du simulateur")
    parser.add_argument('-quote', '--quote', action='store_true', default=False, help="Requête pour actualiser le cours du jour")
    parser.add_argument('-account', '--account', action='store_true', default=False, help="Requête pour actualiser les comptes")
    # print parser.parse_args()

    PicsouBatch(parser.parse_args())
