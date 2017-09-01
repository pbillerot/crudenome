# -*- coding:Utf-8 -*-
from gi.repository import GObject
"""
Constantes
"""
COL_COLOR_BLACK = "#000000"
COL_COLOR_RED = "#006600"
# Tableau de conversion des type de données SQL en GObject.GType
GOBJECT_TYPE = {
    "date": GObject.TYPE_STRING,
    "text": GObject.TYPE_STRING,
    "int": GObject.TYPE_INT,
    "float": GObject.TYPE_FLOAT
}
