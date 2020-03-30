#./venv/bin/python3
# -*- coding:Utf-8 -*-
"""
    Batch de mise à jour des données de la base
"""
import shutil
import os
import datetime, time
import argparse

from crud import Crud
from crudel import Crudel
from plugin.picsou_loader import PicsouLoader

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

        if self.args.dayrepeat:
           self.day_repeat()

    def display(self, msg):
        """ docstring """
        print(msg)
        # self.crud.logger.info(msg)

    def day_repeat(self):
        """ Lancement toutes les 5 minutes de day """
        self.run_day()
        time1 = time.time()
        while True:
            time2 = time.time()
            if ( (time2-time1) > 5 * 60 ):
                print()
                self.run_day()
                time1 = time2
            time.sleep(1)

    def run_day(self):
        self.display(datetime.datetime.now().strftime("%Y/%m/%d, %H:%M:%S") + " : Calcul en cours..." )
        
        if self.args.quote:
            loader = PicsouLoader(self, self.crud)
            loader.quotes()

        if self.args.trade:
            loader = PicsouLoader(self, self.crud)
            loader.trade()

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

if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog='picsou_batch')
    # add a -c/--color option
    parser.add_argument('-trade', action='store_true', default=False, help="Avec activation du trader")
    parser.add_argument('-quote', action='store_true', default=False, help="Avec actualisation des cours du jour")
    parser.add_argument('-backup', action='store_true', default=False, help="Sauvegarder la base sur la box")
    parser.add_argument('-restore', action='store_true', default=False, help="Restauration de la base locale à partir de la base sur la box")
    parser.add_argument('-day', action='store_true', default=False, help="Requête des cours du jour")
    parser.add_argument('-dayrepeat', action='store_true', default=False, help="Requête des cours du jour toutes les 5 minutes")
    # print parser.parse_args()
    if parser._get_args() == 0:
        parser.print_help()
    else:
        PicsouBatch(parser.parse_args())
