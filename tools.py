#!/usr/bin/env python
# -*- coding:Utf-8 -*-
# http://python-gtk-3-tutorial.readthedocs.io/en/latest/index.html
"""
    Fonctions utiles regroupées dans une classe
"""
from email.mime.text import MIMEText
# from logging.handlers import RotatingFileHandler
# import logging
import sqlite3
import os
import json
# import urlparse
# import httplib
# import urllib2
# import time
# from datetime import datetime
# import re
import sys
import itertools
import smtplib
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class Tools(object):
    """
    Fonctions utiles regroupées dans une classe
    """
    def __init__(self):
        """
        Chargement du dictionnaire config.json
        """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        os.chdir(dir_path)
        with open("config.json") as json_data_file:
            self.config = json.load(json_data_file)

    def get_json_content(self, path):
        """
        Retourne le contenu d'un fichier json dans un dictionnaire
        """
        store = {}
        with open(path) as json_data_file:
            store = json.load(json_data_file)
        return store

    def get_config(self):
        """
        Retourne le dictionnaire config
        """
        return self.config

    def exec_sql(self, sql, params):
        """
        Exécution d'un ordre sql
        """
        conn = None
        try:
            conn = sqlite3.connect(self.config["db_name"])
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
        except sqlite3.Error, e:
            if conn:
                conn.rollback()

            print "Error {}\n{}\n{}".format(e.args[0], sql, params)
            sys.exit(1)
        finally:
            if conn:
                conn.close()

    def sql_to_dict(self, db, sql, params):
        """
        Chargement du résultat d'une requête sql dans dictionnaire
        """
        conn = None
        data = None
        try:
            conn = sqlite3.connect(db)
            cursor = conn.cursor()
            cursor.execute(sql, params)
            desc = cursor.description
            column_names = [col[0] for col in desc]
            data = [dict(itertools.izip(column_names, row)) for row in cursor]

        except sqlite3.Error, exc:
            if conn:
                conn.rollback()

            print "Error {}\n{}\n{}".format(exc.args[0], sql, params)
            sys.exit(1)
        finally:
            if conn:
                conn.close()

        return data

    def send_mail(self, dests, subject, body):
        """
        Envoyer un mail
        """
        from_addr = self.config["smtp_from"]

        mail = MIMEText(body, "html", "utf-8")
        mail['From'] = from_addr
        mail['Subject'] = subject

        smtp = smtplib.SMTP()
        smtp.connect(self.config["smtp_host"])

        for _i in dests:
            smtp.sendmail(from_addr, _i, mail.as_string())

        smtp.close()

    def directory_list(self, path):
        """
        Liste des fichiers d'un répertoire
        """
        file_list = []
        for filename in os.listdir(path):
            file_list.append(filename)
        return file_list

class NumberEntry(Gtk.Entry):
    """ Input numéric seulement """
    def __init__(self):
        Gtk.Entry.__init__(self)
        self.connect('changed', self.on_changed_number_entry)

    def on_changed_number_entry(self):
        """ Ctrl de la saisie """
        text = self.get_text().strip()
        self.set_text(''.join([i for i in text if i in '0123456789']))
