# -*- coding:Utf-8 -*-
"""
    Gestion des Vues
"""
import re

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

from crudform import CrudForm
from crudel import Crudel
from crud import Crud

class CrudView(GObject.GObject):
    """ Gestion des vues du CRUD
    app_window   : la fenêtre parent Gnome
    crud_portail : l'objet CrudPortail
    crud         : le contexte applicatif
    crudel       : la rubrique appelante de la vue éventuelle
    """

    __gsignals__ = {
        'init_widget': (GObject.SIGNAL_RUN_FIRST, None, (str, str,))
    }
    def do_init_widget(self, str_from, str_arg=""):
        """ Traitement du signal """
        # print "do_init_widget %s(%s) -> %s" % (str_from, str_arg, self.__class__)
        self.crud.remove_all_selection()
        self.label_select.hide()
        self.button_edit.hide()
        self.button_delete.hide()

    def __init__(self, app_window, crud_portail, crud\
            , box_main, box_toolbar, scroll_window, crudel=None):

        GObject.GObject.__init__(self)

        self.crud_portail = crud_portail
        self.app_window = app_window
        self.box_main = box_main
        self.box_toolbar = box_toolbar
        self.scroll_window = scroll_window
        self.crudel = crudel
        self.crud = crud

        # Déclaration des variables globales
        self.treeview = None
        self.liststore = None
        self.current_filter = None
        self.store_filter = None
        self.store_filter_sort = None
        self.search_entry = None
        self.select = None
        self.button_add = None
        self.button_edit = None
        self.button_delete = None
        self.label_select = None
        self.treeiter_selected = None

        self.create_view_toolbar()
        self.create_liststore()
        self.create_treeview()

        self.app_window.show_all()

        if len(self.crud.get_selection()) == 1 and not crudel:
            # au retour d'un formulaire, on remet la sélection sur la ligne
            row_id = self.crud.get_row_id()
            self.treeview.set_cursor(Gtk.TreePath(row_id), None)
            self.treeview.grab_focus()

        # self.crud.remove_all_selection()
        # self.label_select.hide()
        # self.button_edit.hide()
        # self.button_delete.hide()
        # print "crudview init end"
        self.emit("init_widget", self.__class__, "init")

    def get_widget(self):
        """ retourne le container de la vue toolbar + list """
        # print "get_widget"
        return self.box_main

    def create_view_toolbar(self):
        """ Footer pour afficher des infos et le bouton pour ajouter des éléments """
        if self.crud.get_view_prop("searchable", True):
            self.search_entry = Gtk.SearchEntry()
            self.search_entry.connect("search-changed", self.on_search_changed)
            self.box_toolbar.pack_start(self.search_entry, False, True, 3)
            if self.crud.get_view_prop("filter", "") != "":
                self.search_entry.set_text(self.crud.get_view_prop("filter"))
            if not self.crudel:
                self.search_entry.grab_focus()

        self.box_toolbar_select = Gtk.HBox()
        self.button_delete = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_REMOVE))
        self.button_delete.connect("clicked", self.on_button_delete_clicked)
        self.button_delete.set_tooltip_text("Supprimer la sélection")
        self.box_toolbar_select.pack_end(self.button_delete, False, True, 3)
        self.button_edit = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_EDIT))
        self.button_edit.connect("clicked", self.on_button_edit_clicked)
        self.button_edit.set_tooltip_text("Editer le sélection...")
        self.box_toolbar_select.pack_end(self.button_edit, False, True, 3)
        self.label_select = Gtk.Label("0 sélection")
        self.box_toolbar_select.pack_end(self.label_select, False, True, 3)

        if self.crud.get_view_prop("form_add", "") != "":
            # Affichage du bouton d'ajout si formulaire d'ajout présent
            self.button_add = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_ADD))
            self.button_add.connect("clicked", self.on_button_add_clicked)
            self.button_add.set_tooltip_text("Créer un nouvel enregistrement...")
            self.box_toolbar.pack_end(self.button_add, False, True, 3)

        self.box_toolbar.pack_end(self.box_toolbar_select, False, True, 3)
        
    def create_treeview(self):
        """ Création/mise à jour de la treeview associée au liststore """
        # Treview sort and filter
        self.current_filter = None
        #Creating the filter, feeding it with the liststore model
        self.store_filter = self.liststore.filter_new()
        #setting the filter function, note that we're not using the
        self.store_filter.set_visible_func(self.filter_func)
        self.store_filter_sort = Gtk.TreeModelSort(self.store_filter)

        self.treeview = Gtk.TreeView.new_with_model(self.store_filter_sort)

        col_id = 0
        # la 1ére colonne contiendra le n° de ligne row_id
        self.crud.set_view_prop("col_row_id", col_id)
        col_id += 1
        for element in self.crud.get_view_elements():
            crudel = self.crud.get_column_prop(element, "crudel")

            # colonnes crudel
            col_id = crudel.add_tree_view_column(self.treeview, col_id)

            # mémorisation de la clé dans le crud
            if element == self.crud.get_table_prop("key"):
                self.crud.set_view_prop("key_id", col_id)
            # mémorisation du n° de la ligne
            self.crud.set_column_prop(element, "col_id", col_id)

            col_id += 1

        # ajout de la colonne action
        if self.crud.get_view_prop("deletable", False)\
            or self.crud.get_view_prop("form_edit", None) is not None :
            self.crud.set_view_prop("col_action_id", col_id)
            renderer_action_id = Gtk.CellRendererToggle()
            renderer_action_id.connect("toggled", self.on_action_toggle)
            tvc = Gtk.TreeViewColumn("Action", renderer_action_id, active=col_id)
            self.treeview.append_column(tvc)
            col_id += 1
        # ajout d'une dernière colonne
        # afin que la dernière colonne ne prenne pas tous le reste de la largeur
        tvc = Gtk.TreeViewColumn("", Gtk.CellRendererText(), text=col_id)
        self.treeview.append_column(tvc)
        # Connection aux événement changement de ligne sélectionnée
        self.select = self.treeview.get_selection()
        self.select.connect("changed", self.on_tree_selection_changed)

        # Connection au double-clic sur une ligne
        self.treeview.connect("row-activated", self.on_row_actived)

        self.frame = Gtk.Frame()
        self.frame.add(self.treeview)
        self.scroll_window.add(self.frame)
        self.scroll_window.show_all()

    def create_liststore(self):
        """ Création de la structure du liststore à partir du dictionnaire des données """
        col_store_types = []
        # 1ère colonne row_id
        col_store_types.append(GObject.TYPE_INT)
        for element in self.crud.get_view_elements():
            # Création du crudel
            crudel = Crudel.instantiate(self.app_window, self.crud_portail, self, None, self.crud, element, Crudel.TYPE_PARENT_VIEW)
            # crudel = crudel_class(self.app_window, self.crud_portail, self, None, self.crud, element, Crudel.TYPE_PARENT_VIEW)
            self.crud.set_column_prop(element, "crudel", crudel)

            # colonnes techniques color et sortable
            if crudel.get_sql_color() != "":
                col_store_types.append(GObject.TYPE_STRING)
            if crudel.is_sortable():
                col_store_types.append(crudel.get_type_gdk())
            # colonnes crudel
            col_store_types.append(crudel.get_type_gdk())

        # col_action_id
        if self.crud.get_view_prop("deletable", False)\
            or self.crud.get_view_prop("form_edit", None) is not None :
            col_store_types.append(GObject.TYPE_BOOLEAN)
        # dernière colonne vide
        col_store_types.append(GObject.TYPE_STRING)

        self.liststore = Gtk.ListStore(*col_store_types)
        # print "col_store_types", col_store_types

        self.update_liststore()

    def update_liststore(self):
        """ Mise à jour du liststore en relisant la table """
        # Génération du select de la table

        sql = "SELECT "
        b_first = True
        for element in self.crud.get_view_elements():
            crudel = self.crud.get_column_prop(element, "crudel")
            if crudel.is_virtual():
                continue
            if crudel.get_type() == "jointure":
                continue
            if b_first:
                b_first = False
            else:
                sql += ", "
            # colonnes techniques
            if crudel.get_sql_color() != "":
                sql += crudel.get_sql_color() + " as " + element + "_color"
                sql += ", "
            # colonnes affichées
            if crudel.get_sql_get() == "":
                sql += self.crud.get_table_id() + "." + element
            else:
                sql += crudel.get_sql_get() + " as " + element
        # ajout des colonnes de jointure
        for element in self.crud.get_view_elements():
            crudel = self.crud.get_column_prop(element, "crudel")
            if crudel.get_type() == "jointure":
                sql += ", " + crudel.get_jointure_columns()
        sql += " FROM " + self.crud.get_table_id()
        # ajout des tables de jointure
        for element in self.crud.get_view_elements():
            crudel = self.crud.get_column_prop(element, "crudel")
            if crudel.get_type() == "jointure":
                sql += " " + crudel.get_jointure_join()
        sql_where = ""
        if self.crudel and self.crudel.get_sql_where() != "":
            sql_where = self.crudel.crud.replace_from_dict(self.crudel.get_sql_where(), self.crudel.crud.get_form_values())
        if self.crud.get_view_prop("sql_where"):
            if sql_where == "":
                sql_where = self.crud.get_view_prop("sql_where")
            else:
                sql_where = "(" + sql_where + ") AND ("+ self.crud.get_view_prop("sql_where") + ")"
        if sql_where != "":
            sql += " WHERE " + sql_where
        sql += " LIMIT 2000"
        # print sql
        rows = self.crud.sql_to_dict(self.crud.get_table_prop("basename"), sql, self.crud.ctx)
        # print rows
        self.liststore.clear()
        row_id = 0
        for row in rows:
            store = []
            # print row
            # 1ère colonne col_row_id
            store.append(row_id)
            for element in self.crud.get_view_elements():
                crudel = self.crud.get_column_prop(element, "crudel")
                if crudel.is_virtual():
                    continue
                # Mémorisation dans crudel value
                crudel.set_value_sql(row[element])
                # colonnes techniques
                if crudel.get_sql_color() != "":
                    store.append(row[element + "_color"])
                if crudel.is_sortable():
                    store.append(crudel.get_value())
                # colonnes crudel
                display = crudel.get_cell()
                # print element, display
                store.append(display)
            # col_action_id
            if self.crud.get_view_prop("deletable", False)\
                or self.crud.get_view_prop("form_edit", None) is not None:
                store.append(False)
            # dernière colonne vide
            store.append("")
            # print "store", store
            self.liststore.append(store)
            row_id += 1

        # suppression de la sélection
        self.emit("init_widget", self.__class__, "update_listore")

    def filter_func(self, model, iter, data):
        """Tests if the text in the row is the one in the filter"""
        if self.current_filter is None or self.current_filter == "":
            return True
        else:
            bret = False
            for element in self.crud.get_view_elements():
                crudel = self.crud.get_column_prop(element, "crudel")
                if crudel.is_searchable():
                    if re.search(self.current_filter,\
                                 model[iter][self.crud.get_column_prop(element, "col_id")],\
                                 re.IGNORECASE):
                        bret = True
            return bret

    def on_button_add_clicked(self, widget):
        """ Ajout d'un élément """
        self.crud.set_form_id(self.crud.get_view_prop("form_add"))
        self.crud.set_key_value(None)
        self.crud.set_action("create")
        self.crud_portail.set_layout(self.crud_portail.LAYOUT_FORM)
        form = CrudForm(self.app_window, self.crud_portail, self, self.crud, self.crudel)
        self.app_window.show_all()
        form.emit("init_widget", self.__class__, "on_button_add_clicked")

    def on_button_edit_clicked(self, widget):
        """ Edition de l'élément sélectionné"""
        # print "Edition de", self.crud.get_selection()[0]
        self.crud.set_key_value(self.crud.get_selection()[0])
        self.crud.set_form_id(self.crud.get_view_prop("form_edit"))
        self.crud.set_action("update")
        self.crud_portail.set_layout(self.crud_portail.LAYOUT_FORM)
        form = CrudForm(self.app_window, self.crud_portail, self, self.crud, self.crudel)
        self.app_window.show_all()
        form.emit("init_widget", self.__class__, "on_button_edit_clicked")

    def on_button_delete_clicked(self, widget):
        """ Suppression des éléments sélectionnés """
        print "Suppression de ", self.crud.get_selection()
        dialog = Gtk.MessageDialog(parent=self.app_window,\
            flags=Gtk.DialogFlags.MODAL,\
            type=Gtk.MessageType.WARNING,\
            buttons=Gtk.ButtonsType.OK_CANCEL,\
            message_format="Confirmez-vous la suppression de\n{}".format(" ".join(str(self.crud.get_selection()))))

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            for key_value in self.crud.get_selection():
                self.crud.sql_delete_record(key_value)

            self.update_liststore()

        dialog.destroy()

    def on_search_changed(self, widget):
        """ Recherche d'éléments dans la vue """
        if len(self.search_entry.get_text()) == 1:
            return
        self.current_filter = self.search_entry.get_text()
        # mémorisation du filtre dans la vue
        self.crud.set_view_prop("filter", self.current_filter)
        self.store_filter.refilter()

    def on_action_toggle(self, cell, path):
        """ Clic sur coche d'action"""
        # print "Action sur", self.store_filter_sort[path][self.crud.get_view_prop("key_id")]
        key_id = self.store_filter_sort[path][self.crud.get_view_prop("key_id")]
        row_id = self.store_filter_sort[path][self.crud.get_view_prop("col_row_id")]
        self.label_select.hide()
        self.button_edit.hide()
        self.button_delete.hide()
        if self.crud.get_view_prop("deletable", False):
            # plusieurs lignes sélectionables
            if self.liststore[row_id][self.crud.get_view_prop("col_action_id")]:
                self.crud.remove_selection(key_id)
            else:
                self.crud.add_selection(key_id)
            qselect = len(self.crud.get_selection())
            if qselect > 1:
                self.label_select.set_markup("({}) sélections".format(qselect))
                if self.crud.get_view_prop("deletable", False):
                    self.label_select.show()
                    self.button_delete.show()
            elif qselect == 1:
                self.label_select.set_markup("{}".format(key_id))
                if self.crud.get_view_prop("form_edit", None) is not None:
                    self.label_select.show()
                    self.button_edit.show()
                self.label_select.show()
                self.button_delete.show()
            # cochage / décochage de la ligne
            self.liststore[row_id][self.crud.get_view_prop("col_action_id")]\
                = not self.liststore[row_id][self.crud.get_view_prop("col_action_id")]
        else:
            # une seule ligne sélectionable
            if self.liststore[row_id][self.crud.get_view_prop("col_action_id")]:
                self.crud.remove_all_selection()
            else:
                self.crud.remove_all_selection()
                self.crud.add_selection(key_id)
                self.label_select.set_markup("{}".format(key_id))
                self.label_select.show()
                self.button_edit.show()
            # on décoche toutes les lignes sauf la ligne courante
            if not self.crud.get_view_prop("deletable", False):
                for irow in range(len(self.liststore)):
                    if irow != row_id:
                        self.liststore[irow][self.crud.get_view_prop("col_action_id")] = False
            # cochage / décochage de la ligne
            self.liststore[row_id][self.crud.get_view_prop("col_action_id")]\
                = not self.liststore[row_id][self.crud.get_view_prop("col_action_id")]

    def on_tree_selection_changed(self, selection):
        """ Sélection d'une ligne """
        # print "on_tree_selection_changed"
        model, self.treeiter_selected = selection.get_selected()
        if self.treeiter_selected:
            # key_id = self.store_filter_sort[self.treeiter_selected][self.crud.get_view_prop("key_id")]
            row_id = model[self.treeiter_selected][0]
            # print "Select", key_id, row_id
            self.crud.set_row_id(row_id)

    def on_row_actived(self, widget, row, col):
        """ Double clic sur une ligne """
        # print "Activation", widget.get_model()[row][self.crud.get_view_prop("key_id")]
        key_id = widget.get_model()[row][self.crud.get_view_prop("key_id")]
        row_id = widget.get_model()[row][0]
        self.crud.set_row_id(row_id)
        self.crud.remove_all_selection()
        self.crud.add_selection(key_id)
        self.crud.set_key_value(key_id)
        if self.crud.get_view_prop("form_edit", None) is not None:
            self.crud.set_form_id(self.crud.get_view_prop("form_edit"))
            self.crud.set_action("update")
            self.crud_portail.set_layout(self.crud_portail.LAYOUT_FORM)
            form = CrudForm(self.app_window, self.crud_portail, self, self.crud, self.crudel)
            self.app_window.show_all()
            form.emit("init_widget", self.__class__, "on_row_actived")
