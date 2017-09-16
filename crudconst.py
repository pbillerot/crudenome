# -*- coding:Utf-8 -*-
from gi.repository import GObject
"""
Constantes
"""
COL_COLOR_BLACK = "#000000"
COL_COLOR_RED = "#006600"
# Tableau de conversion des type de données SQL en GObject.GType
GOBJECT_TYPE = {
    "button": GObject.TYPE_OBJECT,
    "check": GObject.TYPE_BOOLEAN,
    "combo": GObject.TYPE_OBJECT,
    "counter": GObject.TYPE_INT,
    "date": GObject.TYPE_STRING,
    "float": GObject.TYPE_FLOAT,
    "int": GObject.TYPE_INT,
    "jointure": GObject.TYPE_STRING,
    "text": GObject.TYPE_STRING,
    "uid": GObject.TYPE_STRING
}
LAYOUT_MENU = 1
LAYOUT_VIEW_H = 2
LAYOUT_VIEW_V = 3
