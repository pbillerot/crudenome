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
from collections import OrderedDict
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
from gi.repository import Gtk, GObject

class Ctx(object):
    """ Gestion du contexte du CRUD """
    crud = None

    def __init__(self, crud=None):
        if crud is None:
            self.crud = Crud()
        else:
            self.crud = crud

class Crud(object):
    """
    Fonctions utiles regroupées dans une classe
    """
    tables = {}
    table_id = "id"
    view_id = "id"
    form_id = "id"
    config = {}
    key_value = "id"


    def __init__(self, crud=None):
        """
        Chargement du dictionnaire config.json
        """
        if crud is None:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            os.chdir(dir_path)
            with open("config.json") as json_data_file:
                self.config = json.load(json_data_file)
        else:
            self.tables = crud.tables
            self.table_id = crud.table_id
            self.view_id = crud.view_id
            self.form_id = crud.form_id
            self.config = crud.config

    def get_json_content(self, path):
        """
        Retourne le contenu d'un fichier json dans un dictionnaire
        """
        store = {}
        with open(path) as json_data_file:
            store = json.load(json_data_file, object_pairs_hook=OrderedDict)
        return store

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
        except sqlite3.Error, exc:
            if conn:
                conn.rollback()

            print "Error {}\n{}\n{}".format(exc.args[0], sql, params)
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

    def get_table_prop(self, prop, default=""):
        """ Obtenir la valeur d'une propriété de la table courante """
        return self.tables[self.table_id].get(prop, default)

    def get_table_elements(self):
        """ Obtenir la liste des rubriques de la table courante """
        return self.tables[self.table_id]["elements"]

    def get_vue_prop(self, prop, default=""):
        """ Obtenir la valeur d'une propriété de la vue courante """
        return self.tables[self.table_id]["views"][self.view_id].get(prop, default)

    def get_vue_elements(self):
        """ Obtenir la liste des colonnes de la vue courante """
        return self.tables[self.table_id]["views"][self.view_id]["elements"]

    def set_vue_prop(self, prop, value):
        """ Ajouter/mettre à jour une propriété de la vue courante """
        self.tables[self.table_id]["views"][self.view_id][prop] = value

    def get_formulaire_prop(self, prop, default=""):
        """ Obtenir la valeur d'une propriété du formulaire courant """
        return self.tables[self.table_id]["forms"][self.form_id].get(prop, default)

    def get_formulaire_elements(self):
        """ Obtenir la liste des champs du formulaire courant """
        return self.tables[self.table_id]["forms"][self.form_id]["elements"]

    def set_formulaire_prop(self, prop, value):
        """ Ajouter/mettre à jour une propriété du formulaire courant """
        self.tables[self.table_id]["forms"][self.form_id][prop] = value

    def get_rubrique_prop(self, element, prop, default=""):
        """ Obtenir la valeur d'une propriété d'un élément (colonne) de la table courante """
        return self.tables[self.table_id]["elements"][element].get(prop, default)

    def set_rubrique_prop(self, element, prop, value):
        """ Ajouter/mettre à jour une propriété d'une rubrique (colonne) de la table courante """
        self.tables[self.table_id]["elements"][element][prop] = value

    def get_colonne_prop(self, element, prop, default=""):
        """
        Obtenir la valeur d'une propriété d'une colonne de la vue courante
        Si la propriété de la colonne n'est pas définie au niveau de la colonne
        on recherchera au niveau de la rubrique
        """
        value = self.tables[self.table_id]["views"][self.view_id]["elements"][element].get(prop, None)
        return self.get_rubrique_prop(element, prop, default) if value is None else value

    def set_colonne_prop(self, element, prop, value):
        """ Ajouter/mettre à jour une propriété d'une colonne de la vue courante """
        self.tables[self.table_id]["views"][self.view_id]["elements"][element][prop] = value

    def get_champ_prop(self, element, prop, default):
        """
        Obtenir la valeur d'une propriété d'un champ du formulaire courant
        Si la propriété du champ n'est pas définie au niveau du champ
        on recherchera au niveau de la rubrique
        """
        value = self.tables[self.table_id]["forms"][self.form_id]["elements"][element].get(prop, None)
        return self.get_rubrique_prop(element, prop, default) if value is None else value

    def set_champ_prop(self, element, prop, value):
        """ Ajouter/mettre à jour une propriété d'un champ du formulaire courant """
        self.tables[self.table_id]["forms"][self.form_id]["elements"][element][prop] = value

class NumberEntry(Gtk.Entry):
    """ Input numéric seulement """
    def __init__(self):
        Gtk.Entry.__init__(self)
        self.connect('changed', self.on_changed_number_entry)

    def on_changed_number_entry(self):
        """ Ctrl de la saisie """
        text = self.get_text().strip()
        self.set_text(''.join([i for i in text if i in '0123456789']))
