# -*- coding:Utf-8 -*-
"""
    Gestion des éléments
"""
# from crud import Crud

# import sqlite3
# import os
# import urllib2
# import time
# from datetime import datetime
# import re
# import sys
# import itertools
# import crudconst as const

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf

class CrudElement():
    """ Gestion des Elements """
    def __init__(self, parent, crud):
        self.crud = crud
        self.parent = parent

