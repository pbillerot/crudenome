# -*- coding:Utf-8 -*-
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
# import time
# from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler

import re
import itertools
import smtplib
import importlib

import requests
from crudel import Crudel

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
        "selected": {},
        "errors": [],
        "ticket": None
    }
    config = {}

    def __init__(self, crud=None, duplicate=False):
        """
        Chargement du dictionnaire config.json
        """
        if crud is None:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            # chargement de config.json
            os.chdir(dir_path)
            with open("config.json") as json_data_file:
                self.config = json.load(json_data_file)

            # Remplacement de ~
            for key in self.config:
                param = self.config[key]
                if not isinstance(self.config[key], dict):
                    self.config[key] = self.config[key].replace("~", os.path.expanduser("~"))
            # chargement de local.json et fusion dans config
            if self.config["local_config"]:
                with open(self.config["local_config"]) as json_data_file:
                    conf = json.load(json_data_file)
                    self.config.update(conf)

            # Remplacement de ~
            for key in self.config:
                if isinstance(self.config[key], str):
                    self.config[key] = self.config[key].replace("~", os.path.expanduser("~"))
        else:
            if duplicate:
                self.application = dict(crud.application)
                self.ctx = dict(crud.ctx)
                self.config = crud.config
            else:
                self.application = crud.application
                self.ctx = crud.ctx
                self.config = crud.config
        self.init_logger()

    #
    # FONCTIONS GENERALES
    #
    def send_sms(self, msg):
        """ envoi d'un sms """
        result = requests.get(self.config["sms"] % requests.utils.quote(msg))
        self.logger.info("SMS %s %s %s", result.status_code, result.headers, result.content)

    def init_logger(self):
        """ Initialisation du logger """
        # création de l'objet logger qui va nous servir à écrire dans les logs
        self.logger = logging.getLogger()
        # on met le niveau du logger à DEBUG, comme ça il écrit tout
        # self.logger.setLevel(logging.DEBUG)
        self.logger.setLevel(logging.INFO)

        # création d'un formateur qui va ajouter le temps, le niveau
        # de chaque message quand on écrira un message dans le log
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(module)s.%(funcName)s :: %(message)s')
        # création d'un handler qui va rediriger une écriture du log vers
        # un fichier en mode 'append', avec 1 backup et une taille max de 1Mo
        file_handler = RotatingFileHandler('log/crud.log', 'a', 1000000, 3)
        # on lui met le niveau sur DEBUG, on lui dit qu'il doit utiliser le formateur
        # créé précédement et on ajoute ce handler au logger
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # création d'un second handler qui va rediriger chaque écriture de log
        # sur la console
        # stream_handler = logging.StreamHandler()
        # stream_handler.setLevel(logging.DEBUG)
        # self.logger.addHandler(stream_handler)

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
                    pp[param] = params[param]
            # print sql, pp
            self.logger.info("SQL EXEC [%s]", sql )
            self.logger.info("SQL EXEC %s", self.get_params_display(pp))
            cursor.execute(sql, pp)
            conn.commit()
        except sqlite3.Error as exc:
            if conn:
                conn.rollback()
            self.logger.error("Error %s %s %s", exc.args[0], sql, params)
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
            self.logger.info("SQL DICT [%s]", sql )
            self.logger.info("SQL DICT %s", self.get_params_display(params))
            cursor.execute(sql, params)
            desc = cursor.description
            column_names = [col[0] for col in desc]
            data = [OrderedDict(zip(column_names, row)) for row in cursor]
        except sqlite3.Error as exc:
            if conn:
                conn.rollback()

            print("Error", exc.args[0], sql, params)
            self.add_error("%s %s %s" % (exc.args[0], sql, params))
            # sys.exit(1)
        finally:
            if conn:
                conn.close()

        return data

    def get_sql(self, db_path, sql):
        """
        Requête sql pour lire une donnée dans la table
        """
        conn = None
        data = ""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            self.logger.info("SQL [%s]", sql)
            cursor.execute(sql, {})
            data = cursor[0][0]
        except sqlite3.Error as exc:
            print("Error", exc.args[0], sql)
            self.add_error("%s %s" % (exc.args[0], sql))
        finally:
            if conn:
                conn.close()
        return data

    def get_params_display(self, params):
        """ formattage pour l'affichage des paramètres transmis à une requete sql """
        fmt = ""
        for key in params:
            if params[key] is None:
                continue
            # if isinstance(params[key], (str, int, float)):
            if fmt != "":
                fmt += ", "
            fmt += "%s='%s'" % (key, str(params[key]))
        return "params: [%s]" % fmt

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
            self.logger.info("Mail to %s %s" % (_i, subject))

        smtp.close()

    def directory_list(self, path):
        """
        Liste des fichiers d'un répertoire
        """
        file_list = []
        for filename in os.listdir(path):
            file_list.append(filename)
        return file_list

    # GETTER SETTER DU CRUD

    # app: nom de l'application
    def get_app(self):
        """ Obtenir le nom de l'application courante """
        return self.ctx["app"]
    def set_app(self, val):
        """ Valoriser le nom de l'application courante """
        self.ctx["app"] = val

    # ticket
    def get_ticket(self):
        """ Obtenir le ticket de la base de données lors de la prise """
        return self.ctx["ticket"]
    def set_ticket(self, val):
        """ Mettre à jour le ticket de la base de données de la prise """
        self.ctx["ticket"] = val

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
    def add_selection(self, row_id, row_name):
        """ ajouter un élément dans la sélection """
        self.ctx["selected"][row_id] = row_name
    def remove_selection(self, row_id):
        """ supprimer un élément de la sélection """
        del self.ctx["selected"][row_id]
    def remove_all_selection(self):
        """ supprimer un élément de la sélection """
        self.ctx["selected"].clear()
    def get_selection(self):
        """ Fournir les éléments de la sélection """
        return self.ctx["selected"]
    def get_selection_values(self):
        """ Fournir les éléments de la sélection séparés par une virgule"""
        values = ""
        for key in self.ctx["selected"]:
            value = self.ctx["selected"][key]
            if values != "":
                values += " "
            if isinstance(value, (float, int)):
                values += "[" + str(value) + "]"
            else:
                values += "[" + value + "]"
        return values

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
    def get_basename(self):
        """ Obtenir le chemin d'accès à la base de données de la table courante """
        basename = self.application.get("basename")
        path = basename.replace("~", os.path.expanduser("~"))
        return path
    def get_basehost(self):
        """ Obtenir le chemin d'accès à la base de données de la table courante """
        basehost = self.application.get("basehost", None)
        if basehost:
            path = basehost.replace("~", os.path.expanduser("~"))
            return path
        else:
            return None
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
    def set_table_prop(self, prop, value):
        """ Ajouter/mettre à jour une propriété de la table courante """
        self.application["tables"][self.ctx["table_id"]][prop] = value
    def get_table_elements(self):
        """ Obtenir la liste des rubriques de la table courante """
        return self.application["tables"][self.ctx["table_id"]]["elements"]
    def get_table_values(self, dico=None):
        """ Remplir "dict" avec les valeurs des éléments de la table courante """
        if dico is None:
            dico = {}
        for element in self.get_table_elements():
            crudel = self.get_element_prop(element, "crudel", None)
            if crudel is not None:
                dico[element] = self.get_element_prop(element, "crudel").get_value()
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
            dico[element] = self.get_element_prop(element, "crudel").get_value()
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

    # jointure
    def get_element_jointure(self, element, params, default=None):
        """ Obtenir la valeur d'un paramètre d'une jointure """
        if self.application["tables"][self.ctx["table_id"]]["elements"][element].get("jointure", None):
            return self.application["tables"][self.ctx["table_id"]]["elements"][element].get("jointure").get(params, default)
        else:
            return default

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
            if word_dict.get(key, None) is None:
                continue
            if isinstance(word_dict[key], int):
                text = text.replace("{" + key + "}", str(word_dict[key]))
            elif isinstance(word_dict[key], float):
                text = text.replace("{" + key + "}", str(word_dict[key]))
            elif isinstance(word_dict[key], bool):
                text = text.replace("{" + key + "}", str(word_dict[key]))
            else:
                text = text.replace("{" + key + "}", (word_dict[key]))
        return text

    def sql_update_record(self):
        """ Mise à jour de l'enregistrement du formulaire courant """
        sql = "UPDATE " + self.get_table_id() + " SET "
        b_first = True
        params = {}
        for element in self.get_form_elements():
            if element == self.get_key_id():
                continue
            crudel = self.get_element_prop(element, "crudel")
            if crudel.is_read_only():
                continue
            if crudel.is_virtual():
                continue
            if b_first:
                b_first = False
            else:
                sql += ", "
            if self.get_field_prop(element, "sql_put", None):
                sql += element + " = " + self.get_field_prop(element, "sql_put")
            else:
                sql += element + " = :" + element
            params[element] = self.get_element_prop(element, "crudel").get_value()

        sql += " WHERE " + self.get_key_id() + " = :" + self.get_key_id()
        params[self.get_key_id()] = self.get_key_value()
        # on remplace les {rubrique} par leur valeur
        sql = self.replace_from_dict(sql, params)
        # print sql, params
        self.exec_sql(self.get_basename(), sql, params)
        if self.get_form_prop("sql_post", "") != "":
            sql = self.replace_from_dict(self.get_form_prop("sql_post"), params)
            self.exec_sql(self.get_basename(), sql, params)

    def sql_insert_record(self):
        """ Création de l'enregistrement du formulaire courant """
        sql = "INSERT INTO " + self.get_table_id() + " ("
        params = {}
        b_first = True
        for element in self.get_form_elements():
            if self.get_field_prop(element, "type") == "counter":
                continue
            crudel = self.get_element_prop(element, "crudel")
            if crudel.is_read_only():
                continue
            if crudel.is_virtual():
                continue
            if b_first:
                b_first = False
            else:
                sql += ", "
            sql += element
            params[element] = self.get_element_prop(element, "crudel").get_value()
        sql += ") VALUES ("
        b_first = True
        for element in self.get_form_elements():
            if self.get_field_prop(element, "type") == "counter":
                continue
            crudel = self.get_element_prop(element, "crudel")
            if crudel.is_read_only():
                continue
            if crudel.is_virtual():
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
        self.exec_sql(self.get_basename(), sql, params)
        # post_sql
        if self.get_form_prop("sql_post", "") != "":
            sql = self.replace_from_dict(self.get_form_prop("sql_post"), params)
            self.exec_sql(self.get_basename(), sql, params)

    def sql_delete_record(self, key_value):
        """ Suppression d'un enregistrement de la vue courante """
        sql = "DELETE FROM " + self.get_table_id() + " WHERE " + self.get_key_id() + " = :" + self.get_key_id()
        params = {}
        params[self.get_key_id()] = key_value
        # print sql, params
        self.exec_sql(self.get_basename(), sql, params)

    def sql_exist_key(self):
        """ Savoir si l'enregsitrement existe """
        sql = "SELECT count(*) as count FROM " + self.get_table_id() + " WHERE " + self.get_key_id() + " = :key_id"
        params = {}
        params["key_id"] = self.get_element_prop(self.get_key_id(), "crudel").get_value()
        rows = self.sql_to_dict(self.get_basename(), sql, params)
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

    def get_sql_row(self, type_parent):
        """ Charger les colonnes de l'enregistreement courant """
        sql = "SELECT "
        b_first = True
        elements = self.get_view_elements() if type_parent == Crudel.TYPE_PARENT_VIEW else self.get_form_elements()
        for element in elements:
            crudel = Crudel.instantiate(self, element, type_parent)
            crudel.init_value()
            self.set_element_prop(element, "crudel", crudel)
            if crudel.is_virtual():
                continue
            if crudel.with_jointure()\
            and (crudel.is_read_only() or type_parent == Crudel.TYPE_PARENT_VIEW):
                continue
            if b_first:
                b_first = False
            else:
                sql += ", "
            # colonnes affichées
            if crudel.get_sql_get() == "":
                sql += self.get_table_id() + "." + element
            else:
                sql += crudel.get_sql_get() + " as " + element
            # colonnes techniques
            if crudel.get_sql_color() != "":
                sql += ", "
                sql += crudel.get_sql_color() + " as " + element + "_color"

        # ajout des colonnes de jointure
        for element in elements:
            crudel = self.get_element_prop(element, "crudel")
            if crudel.is_virtual():
                continue
            if crudel.with_jointure()\
            and (crudel.is_read_only() or type_parent == Crudel.TYPE_PARENT_VIEW):
                sql += ", " + crudel.get_jointure("column") + " as " + element

        sql += " FROM " + self.get_table_id()

        # ajout des tables de jointure
        join = ""
        for element in elements:
            crudel = self.get_element_prop(element, "crudel")
            if crudel.is_virtual():
                continue
            if crudel.with_jointure()\
            and (crudel.is_read_only() or type_parent == Crudel.TYPE_PARENT_VIEW):
                if crudel.get_jointure("join"):
                    join += " " + crudel.get_jointure("join")
        if join:
            sql += join

        sql_where = self.get_key_id() + " = :key_value"
        if sql_where != "":
            sql += " WHERE " + sql_where

        rows = self.sql_to_dict(self.get_basename(), sql, self.ctx)
        return rows

    def get_sql_report(self):
        """ Rapport HTML de la vue courante"""
        sql = "SELECT "
        b_first = True
        elements = self.get_view_elements()
        html = '<table border="1" cellspacing="0" cellpadding="3">'
        html += '<tr>'
        for element in elements:
            crudel = Crudel.instantiate(self, element, Crudel.TYPE_PARENT_VIEW)
            crudel.init_value()
            self.set_element_prop(element, "crudel", crudel)

            html += '<th>%s</th>' % crudel.get_label_short()

            # colonnes techniques
            if crudel.get_sql_color() != "":
                sql += ", "
                sql += crudel.get_sql_color() + " as " + element + "_color"
            if crudel.is_virtual():
                continue
            if crudel.with_jointure():
                continue
            if b_first:
                b_first = False
            else:
                sql += ", "
            # colonnes affichées
            if crudel.get_sql_get() == "":
                sql += self.get_table_id() + "." + element
            else:
                sql += crudel.get_sql_get() + " as " + element
        html += '</tr>'

        # ajout des colonnes de jointure
        for element in elements:
            crudel = self.get_element_prop(element, "crudel")
            if crudel.with_jointure():
                sql += ", " + crudel.get_jointure("column") + " as " + element

        sql += " FROM " + self.get_table_id()

        # ajout des tables de jointure
        join = ""
        for element in elements:
            crudel = self.get_element_prop(element, "crudel")
            if crudel.with_jointure():
                if crudel.get_jointure("join"):
                    join += " " + crudel.get_jointure("join")
        if join:
            sql += join

        # prise en compte du sql_where de la vue
        sql_where = ""
        if self.get_view_prop("sql_where"):
            sql_where += self.get_view_prop("sql_where")
        if sql_where != "":
            sql += " WHERE " + sql_where
        if self.get_view_prop("order_by", None):
            sql += " ORDER BY " + self.get_view_prop("order_by")

        sql += " LIMIT " + str(self.get_view_prop("limit", 400))

        rows = self.sql_to_dict(self.get_basename(), sql, self.ctx)
        for row in rows:
            html += '<tr>'
            for element in self.get_view_elements():
                crudel = self.get_element_prop(element, "crudel")
                if element in row:
                    crudel.set_value_sql(row[element])
                if crudel.get_sql_color() != "":
                    color = ' style="color: %s"' % row[element + "_color"]
                else:
                    color = ""
                html += '<td align="%s"%s>%s</td>' % (crudel.get_col_align("left"), color, crudel.get_display())
            html += '</tr>'
        html += '<table>'
        return html
