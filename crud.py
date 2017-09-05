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
    application = {}
    ctx = {
        "table_id": None,
        "view_id": None,
        "form_id": None,
        "key_id": None,
        "key_value": None
    }
    config = {}


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
            self.application = crud.application
            self.ctx = crud.ctx
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

            print "Error", exc.args[0], sql, params
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

            print "Error", exc.args[0], sql, params
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

    def get_table_id(self):
        """ table_id """
        return self.ctx["table_id"]

    def get_view_id(self):
        """ view_id """
        return self.ctx["view_id"]

    def get_form_id(self):
        """ form_id """
        return self.ctx["form_id"]

    def get_key_id(self):
        """ key_id """
        return self.ctx["key_id"]

    def get_key_value(self):
        """ key_value """
        return self.ctx["key_value"]

    def set_table_id(self, val):
        """ set """
        self.ctx["table_id"] = val

    def set_view_id(self, val):
        """ set """
        self.ctx["view_id"] = val

    def set_form_id(self, val):
        """ set """
        self.ctx["form_id"] = val

    def set_key_id(self, val):
        """ set """
        self.ctx["key_id"] = val

    def set_key_value(self, val):
        """ set """
        self.ctx["key_value"] = val

    def set_application(self, application):
        """ Chargement du contexte de l'application """
        self.application = application

    def get_application_prop(self, prop, default=""):
        """ Obtenir la valeur d'une propriété de l'application courante """
        return self.application.get(prop, default)

    def get_application_tables(self):
        """ Obtenir la liste des tables de l'application courante """
        return self.application["tables"]

    def get_table_views(self):
        """ Obtenir la liste des vues de la table courante """
        return self.application["tables"][self.ctx["table_id"]]["views"]

    def get_table_forms(self):
        """ Obtenir la liste des formulaire de la table courante """
        return self.application["tables"][self.ctx["table_id"]]["forms"]

    def get_table_prop(self, prop, default=""):
        """ Obtenir la valeur d'une propriété de la table courante """
        return self.application["tables"][self.ctx["table_id"]].get(prop, default)

    def get_table_elements(self):
        """ Obtenir la liste des rubriques de la table courante """
        return self.application["tables"][self.ctx["table_id"]]["elements"]

    def get_view_prop(self, prop, default=""):
        """ Obtenir la valeur d'une propriété de la vue courante """
        return self.application["tables"][self.ctx["table_id"]]["views"][self.ctx["view_id"]].get(prop, default)

    def get_view_elements(self):
        """ Obtenir la liste des colonnes de la vue courante """
        return self.application["tables"][self.ctx["table_id"]]["views"][self.ctx["view_id"]]["elements"]

    def set_view_prop(self, prop, value):
        """ Ajouter/mettre à jour une propriété de la vue courante """
        self.application["tables"][self.ctx["table_id"]]["views"][self.ctx["view_id"]][prop] = value

    def get_form_prop(self, prop, default=""):
        """ Obtenir la valeur d'une propriété du formulaire courant """
        return self.application["tables"][self.ctx["table_id"]]["forms"][self.ctx["form_id"]].get(prop, default)

    def get_form_elements(self):
        """ Obtenir la liste des champs du formulaire courant """
        return self.application["tables"][self.ctx["table_id"]]["forms"][self.ctx["form_id"]]["elements"]

    def set_form_prop(self, prop, value):
        """ Ajouter/mettre à jour une propriété du formulaire courant """
        self.application["tables"][self.ctx["table_id"]]["forms"][self.ctx["form_id"]][prop] = value

    def get_element_prop(self, element, prop, default=""):
        """ Obtenir la valeur d'une propriété d'un élément (colonne) de la table courante """
        return self.application["tables"][self.ctx["table_id"]]["elements"][element].get(prop, default)

    def set_element_prop(self, element, prop, value):
        """ Ajouter/mettre à jour une propriété d'une rubrique (colonne) de la table courante """
        self.application["tables"][self.ctx["table_id"]]["elements"][element][prop] = value

    def get_column_prop(self, element, prop, default=""):
        """
        Obtenir la valeur d'une propriété d'une colonne de la vue courante
        Si la propriété de la colonne n'est pas définie au niveau de la colonne
        on recherchera au niveau de la rubrique
        """
        value = self.application["tables"][self.ctx["table_id"]]["views"][self.ctx["view_id"]]["elements"][element].get(prop, None)
        return self.get_element_prop(element, prop, default) if value is None else value

    def set_column_prop(self, element, prop, value):
        """ Ajouter/mettre à jour une propriété d'une colonne de la vue courante """
        self.application["tables"][self.ctx["table_id"]]["views"][self.ctx["view_id"]]["elements"][element][prop] = value

    def get_field_prop(self, element, prop, default=""):
        """
        Obtenir la valeur d'une propriété d'un champ du formulaire courant
        Si la propriété du champ n'est pas définie au niveau du champ
        on recherchera au niveau de la rubrique
        """
        value = self.application["tables"][self.ctx["table_id"]]["forms"][self.ctx["form_id"]]["elements"][element].get(prop, None)
        return self.get_element_prop(element, prop, default) if value is None else value

    def set_field_prop(self, element, prop, value):
        """ Ajouter/mettre à jour une propriété d'un champ du formulaire courant """
        self.application["tables"][self.ctx["table_id"]]["forms"][self.ctx["form_id"]]["elements"][element][prop] = value

class NumberEntry(Gtk.Entry):
    """ Input numéric seulement """
    def __init__(self):
        Gtk.Entry.__init__(self)
        self.connect('changed', self.on_changed_number_entry)

    def on_changed_number_entry(self):
        """ Ctrl de la saisie """
        text = self.get_text().strip()
        self.set_text(''.join([i for i in text if i in '0123456789']))
