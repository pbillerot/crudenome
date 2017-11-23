#!/usr/bin/env python
# -*- coding:Utf-8 -*-
"""
    Batch de mise à jour des données de la base
"""
import shutil
import os
import datetime

class PicsouRestore():
    """ Script au démarrage de l'application """
    DIR_HOST = "/mnt/freebox"
    PATH_BASENAME = "/data/picsou/picsou.sqlite"

    def __init__(self, crud):

        # Get de la base de données sur la box
        path_host = self.DIR_HOST + self.PATH_BASENAME
        path_user = os.path.expanduser("~") + self.PATH_BASENAME
        ticket_host = os.path.getmtime(path_host)
        ticket_user = os.path.getmtime(path_user)
        if ticket_host > ticket_user:
            print "Restore %s %s" % (path_host, datetime.datetime.fromtimestamp(ticket_host))
            shutil.copy2(path_host, path_user)

class PicsouBackup():
    """ Script de backup de la base sur le host """
    DIR_HOST = "/mnt/freebox"
    PATH_BASENAME = "/data/picsou/picsou.sqlite"

    def __init__(self, crud):

        # Get de la base de données sur la box
        path_host = self.DIR_HOST + self.PATH_BASENAME
        path_user = os.path.expanduser("~") + self.PATH_BASENAME
        ticket_host = os.path.getmtime(path_host)
        ticket_user = os.path.getmtime(path_user)
        if ticket_user > ticket_host:
            print "Backup %s %s" % (path_host, datetime.datetime.fromtimestamp(ticket_user))
            shutil.copy2(path_user, path_host)
