#!/usr/bin/env python
# -*- coding:Utf-8 -*-
# http://python-gtk-3-tutorial.readthedocs.io/en/latest/index.html
"""
    Fonctions utiles regroupées dans une classe
"""
# from __future__ import unicode_literals
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
import re
import sys
import itertools
import smtplib
import importlib
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class Crud:
    """
    Fonctions utiles regroupées dans une classe
    """
    application = {}
    ctx = {
        "app": None,
        "window": None,
        "portail": None,
        "view": None,
        "form": None,
        "crudel": None,
        "table_id": None,
        "view_id": None,
        "form_id": None,
        "row_id": None,
        "key_value": None,
        "action": None, # create read update delete
        "selected": [],
        "errors": [],
    }
    config = {}

    def __init__(self, crud=None, duplicate=False):
        """
        Chargement du dictionnaire config.json
        """
        if crud is None:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            os.chdir(dir_path)
            with open("config.json") as json_data_file:
                self.config = json.load(json_data_file)
        else:
            if duplicate:
                self.application = dict(crud.application)
                self.ctx = dict(crud.ctx)
                self.config = crud.config
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

    def exec_sql(self, db_path, sql, params):
        """
        Exécution d'un ordre sql
        """
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            pp = {}
            for param in params:
                if params[param] is None or isinstance(params[param], int) or isinstance(params[param], float):
                    pp[param] = params[param]
                else:
                    pp[param] = params[param].decode("utf-8")
                    # pp[param] = params[param]
            # print sql, pp
            cursor.execute(sql, pp)
            conn.commit()
        except sqlite3.Error, exc:
            if conn:
                conn.rollback()

            print "Error", exc.args[0], sql, params
            self.add_error("%s %s %s" % (exc.args[0], sql, params))
            # sys.exit(1)
        finally:
            if conn:
                conn.close()

    def sql_to_dict(self, db_path, sql, params):
        """
        Chargement du résultat d'une requête sql dans dictionnaire
        """
        # print "Sql:", db_path, params, sql
        conn = None
        data = None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # print sql, params
            cursor.execute(sql, params)
            desc = cursor.description
            column_names = [col[0] for col in desc]
            data = [OrderedDict(itertools.izip(column_names, row)) for row in cursor]
        except sqlite3.Error, exc:
            if conn:
                conn.rollback()

            print "Error", exc.args[0], sql, params
            self.add_error("%s %s %s" % (exc.args[0], sql, params))
            # sys.exit(1)
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

    # GETTER SETTER

    # app: nom de l'application
    def get_app(self):
        """ Obtenir le nom de l'application courante """
        return self.ctx["app"]
    def set_app(self, val):
        """ Valoriser le nom de l'application courante """
        self.ctx["app"] = val

    # window
    def get_window(self):
        """ window """
        return self.ctx["window"]
    def set_window(self, val):
        """ set """
        self.ctx["window"] = val

    # portail
    def get_portail(self):
        """ portail """
        return self.ctx["portail"]
    def set_portail(self, val):
        """ set """
        self.ctx["portail"] = val

    # view
    def get_view(self):
        """ view """
        return self.ctx["view"]
    def set_view(self, val):
        """ set """
        self.ctx["view"] = val

    # form
    def get_form(self):
        """ form """
        return self.ctx["form"]
    def set_form(self, val):
        """ set """
        self.ctx["form"] = val

    # crudel
    def get_crudel(self):
        """ form """
        return self.ctx["crudel"]
    def set_crudel(self, val):
        """ set """
        self.ctx["crudel"] = val

    # table_id
    def get_table_id(self):
        """ table_id """
        return self.ctx["table_id"]
    def set_table_id(self, val):
        """ set """
        self.ctx["table_id"] = val

    # view_id
    def get_view_id(self):
        """ view_id """
        return self.ctx["view_id"]
    def set_view_id(self, val):
        """ set """
        self.ctx["view_id"] = val

    # form_id
    def get_form_id(self):
        """ form_id """
        return self.ctx["form_id"]
    def set_form_id(self, val):
        """ set """
        self.ctx["form_id"] = val

    # row_id
    def get_row_id(self):
        """ row_id """
        return self.ctx["row_id"]
    def set_row_id(self, val):
        """ set """
        self.ctx["row_id"] = val

    # key
    def get_key_id(self):
        """ key_id """
        return self.get_table_prop("key")
    def get_key_value(self):
        """ key_value """
        return self.ctx["key_value"]
    def set_key_value(self, val):
        """ set """
        self.ctx["key_value"] = val

    # action
    def get_action(self):
        """ action """
        return self.ctx["action"]
    def set_action(self, val):
        """ set """
        self.ctx["action"] = val

    # errors
    def get_errors(self):
        """ get """
        return self.ctx["errors"]
    def add_error(self, label_error):
        """ add """
        self.ctx["errors"].append(label_error)
    def remove_all_errors(self):
        """ remove """
        self.ctx["errors"][:] = []

    # selection
    def add_selection(self, row_id):
        """ ajouter un élément dans la sélection """
        self.ctx["selected"].append(row_id)
    def remove_selection(self, row_id):
        """ supprimer un élément de la sélection """
        self.ctx["selected"].remove(row_id)
    def remove_all_selection(self):
        """ supprimer un élément de la sélection """
        self.ctx["selected"][:] = []
    def get_selection(self):
        """ Fournir les éléments de la sélection """
        return self.ctx["selected"]

    # DICTIONNAIRE de l'application
    # application
    def get_application(self):
        """ Obtenir l'application courante """
        return self.application
    def set_application(self, application):
        """ Chargement du contexte de l'application """
        self.application = application
    def get_application_prop(self, prop, default=""):
        """ Obtenir la valeur d'une propriété de l'application courante """
        return self.application.get(prop, default)
    def get_application_tables(self):
        """ Obtenir la liste des tables de l'application courante """
        return self.application["tables"]

    # table
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
    def get_table_values(self, dico=None):
        """ Remplir "dict" avec les valeurs des éléments de la table courante """
        if dico is None:
            dico = {}
        for element in self.get_table_elements():
            dico[element] = self.get_element_prop(element, "value")
        return dico

    # view
    def get_view_prop(self, prop, default=""):
        """ Obtenir la valeur d'une propriété de la vue courante """
        return self.application["tables"][self.ctx["table_id"]]["views"][self.ctx["view_id"]].get(prop, default)
    def get_view_elements(self):
        """ Obtenir la liste des colonnes de la vue courante """
        return self.application["tables"][self.ctx["table_id"]]["views"][self.ctx["view_id"]]["elements"]
    def set_view_prop(self, prop, value):
        """ Ajouter/mettre à jour une propriété de la vue courante """
        self.application["tables"][self.ctx["table_id"]]["views"][self.ctx["view_id"]][prop] = value

    # form
    def get_form_prop(self, prop, default=""):
        """ Obtenir la valeur d'une propriété du formulaire courant """
        return self.application["tables"][self.ctx["table_id"]]["forms"][self.ctx["form_id"]].get(prop, default)
    def get_form_values(self, dico=None):
        """ Remplir "dict" avec les valeurs des champs du formulaire courant """
        if dico is None:
            dico = {}
        for element in self.get_form_elements():
            dico[element] = self.get_field_prop(element, "value")
        return dico
    def get_form_elements(self):
        """ Obtenir la liste des champs du formulaire courant """
        return self.application["tables"][self.ctx["table_id"]]["forms"][self.ctx["form_id"]]["elements"]
    def set_form_prop(self, prop, value):
        """ Ajouter/mettre à jour une propriété du formulaire courant """
        self.application["tables"][self.ctx["table_id"]]["forms"][self.ctx["form_id"]][prop] = value

    # element
    def get_element_prop(self, element, prop, default=""):
        """ Obtenir la valeur d'une propriété d'un élément (colonne) de la table courante """
        return self.application["tables"][self.ctx["table_id"]]["elements"][element].get(prop, default)
    def set_element_prop(self, element, prop, value):
        """ Ajouter/mettre à jour une propriété d'une rubrique (colonne) de la table courante """
        self.application["tables"][self.ctx["table_id"]]["elements"][element][prop] = value

    # paramètres
    def get_element_param(self, element, params, default=None):
        """ Obtenir la valeur d'un paramètre d'un élément """
        if self.application["tables"][self.ctx["table_id"]]["elements"][element].get("params", None):
            return self.application["tables"][self.ctx["table_id"]]["elements"][element].get("params").get(params, default)
        else:
            return default

    # column
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

    # field
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

    def replace_from_dict(self, text, word_dict):
        """ Remplace par leur valeur les mots entre accolades {mot} trouvés dans le dictionnaire """
        for key in word_dict:
            # print key, word_dict[key], type(word_dict[key])
            if isinstance(word_dict[key], int):
                text = text.replace("{" + key + "}", str(word_dict[key]))
            elif isinstance(word_dict[key], float):
                text = text.replace("{" + key + "}", str(word_dict[key]))
            elif isinstance(word_dict[key], bool):
                text = text.replace("{" + key + "}", str(word_dict[key]))
            else:
                text = text.replace("{" + key + "}", word_dict[key].decode("utf-8"))
        return text

    def sql_update_record(self):
        """ Mise à jour de l'enregistrement du formulaire courant """
        sql = "UPDATE " + self.get_table_id() + " SET "
        b_first = True
        params = {}
        for element in self.get_form_elements():
            if element == self.get_key_id():
                continue
            if b_first:
                b_first = False
            else:
                sql += ", "
            if self.get_field_prop(element, "sql_put", None):
                sql += element + " = " + self.get_field_prop(element, "sql_put")
            else:
                sql += element + " = :" + element
            params[element] = self.get_field_prop(element, "value")

        sql += " WHERE " + self.get_key_id() + " = :" + self.get_key_id()
        params[self.get_key_id()] = self.get_key_value()
        # on remplace les {rubrique} par leur valeur
        sql = self.replace_from_dict(sql, params)
        # print sql, params
        self.exec_sql(self.get_table_prop("basename"), sql, params)
        if self.get_form_prop("sql_post", "") != "":
            sql = self.replace_from_dict(self.get_form_prop("sql_post"), params)
            self.exec_sql(self.get_table_prop("basename"), sql, params)

    def sql_insert_record(self):
        """ Création de l'enregistrement du formulaire courant """
        sql = "INSERT INTO " + self.get_table_id() + " ("
        params = {}
        b_first = True
        for element in self.get_form_elements():
            if self.get_field_prop(element, "type") == "counter":
                continue
            if b_first:
                b_first = False
            else:
                sql += ", "
            sql += element
            params[element] = self.get_field_prop(element, "value")
        sql += ") VALUES ("
        b_first = True
        for element in self.get_form_elements():
            if self.get_field_prop(element, "type") == "counter":
                continue
            if b_first:
                b_first = False
            else:
                sql += ", "
            sql += ":" + element
        sql += ")"
        # on remplace les {rubrique} par leur valeur
        sql = self.replace_from_dict(sql, params)
        # print sql, params
        self.exec_sql(self.get_table_prop("basename"), sql, params)
        # post_sql
        if self.get_form_prop("sql_post", "") != "":
            sql = self.replace_from_dict(self.get_form_prop("sql_post"), params)
            self.exec_sql(self.get_table_prop("basename"), sql, params)

    def sql_delete_record(self, key_value):
        """ Suppression d'un enregistrement de la vue courante """
        sql = "DELETE FROM " + self.get_table_id() + " WHERE " + self.get_key_id() + " = :" + self.get_key_id()
        params = {}
        params[self.get_key_id()] = key_value
        # print sql, params
        self.exec_sql(self.get_table_prop("basename"), sql, params)

    def sql_exist_key(self):
        """ Savoir si l'enregsitrement existe """
        sql = "SELECT count(*) as count FROM " + self.get_table_id() + " WHERE " + self.get_key_id() + " = :key_id"
        params = {}
        params["key_id"] = self.get_field_prop(self.get_key_id(), "value")
        rows = self.sql_to_dict(self.get_table_prop("basename"), sql, params)
        if rows[0]["count"] > 0:
            return True
        else:
            return False

    def get_key_from_bracket(self, text):
        """ Retourne la clé entre parenthèses 
        "Label bla bla (key)" va retourner "key"
        """
        res = re.search('.*\((.*)\).*', text)
        if res:
            return res.group(1)
        else:
            return text

    def load_class(self, full_class_string):
        """
        dynamically load a class from a string
        """

        class_data = full_class_string.split(".")
        module_path = ".".join(class_data[:-1])
        class_str = class_data[-1]

        module = importlib.import_module(module_path)
        # Finally, we retrieve the Class
        return getattr(module, class_str)