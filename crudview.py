# -*- coding:Utf-8 -*-
"""
    Gestion des Vues
"""
from crudform import CrudForm
from crudel import Crudel
import re
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

class CrudView():
    """ Gestion des vues du CRUD
    crud         : le contexte applicatif
    inform=True  : la vue est affichée dans la fenêtre principale
           False : la vue est affichée dans un formulaire en tant que widget
    """
    def __init__(self, app_window, crud_portail, crud):
        self.crud = crud
        self.crud_portail = crud_portail
        self.app_window = app_window

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
        self.label_select.hide()
        self.button_edit.hide()
        self.button_delete.hide()
        if len(self.crud.get_selection()) == 1:
            # au retour d'un formulaire, on remet la sélection sur la ligne
            row_id = self.crud.get_row_id()
            self.treeview.set_cursor(Gtk.TreePath(row_id), None)
            self.treeview.grab_focus()
        self.crud.remove_all_selection()

    def create_view_toolbar(self):
        """ Footer pour afficher des infos et le bouton pour ajouter des éléments """
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.connect("search-changed", self.on_search_changed)
        self.crud_portail.box_toolbar.pack_start(self.search_entry, False, True, 3)
        if self.crud.get_view_prop("filter", "") != "":
            self.search_entry.set_text(self.crud.get_view_prop("filter"))
        self.search_entry.grab_focus()

        self.crud_portail.box_toolbar_select = Gtk.HBox()
        self.button_delete = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_REMOVE))
        self.button_delete.connect("clicked", self.on_button_delete_clicked)
        self.button_delete.set_tooltip_text("Supprimer la sélection")
        self.crud_portail.box_toolbar_select.pack_end(self.button_delete, False, True, 3)
        self.button_edit = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_EDIT))
        self.button_edit.connect("clicked", self.on_button_edit_clicked)
        self.button_edit.set_tooltip_text("Editer le sélection...")
        self.crud_portail.box_toolbar_select.pack_end(self.button_edit, False, True, 3)
        self.label_select = Gtk.Label("0 sélection")
        self.crud_portail.box_toolbar_select.pack_end(self.label_select, False, True, 3)
        self.label_select.hide()
        self.button_edit.hide()
        self.button_delete.hide()

        if self.crud.get_view_prop("form_add", "") != "":
            # Affichage du bouton d'ajout si formulaire d'ajout présent
            self.button_add = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_ADD))
            self.button_add.connect("clicked", self.on_button_add_clicked)
            self.button_add.set_tooltip_text("Créer un nouvel enregistrement...")
            self.crud_portail.box_toolbar.pack_end(self.button_add, False, True, 3)

        self.crud_portail.box_toolbar.pack_end(self.crud_portail.box_toolbar_select, False, True, 3)

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

        self.crud_portail.scroll_window.add(self.treeview)
        self.crud_portail.scroll_window.show_all()

    def create_liststore(self):
        """ Création de la structure du liststore à partir du dictionnaire des données """
        col_store_types = []
        # 1ère colonne row_id
        col_store_types.append(GObject.TYPE_INT)
        for element in self.crud.get_view_elements():
            # Création du crudel
            crudel = Crudel(self.app_window, self.crud_portail, self.crud, element, Crudel.CRUD_PARENT_VIEW)
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
        if self.crud.get_view_prop("sql_where"):
            sql += " WHERE " + self.crud.get_view_prop("sql_where")
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
                display = crudel.get_display()
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
        self.label_select.hide()
        self.button_edit.hide()
        self.button_delete.hide()

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
        dialog = CrudForm(self.app_window, self.crud_portail, self.crud)
        self.app_window.show_all()

    def on_button_edit_clicked(self, widget):
        """ Edition de l'élément sélectionné"""
        # print "Edition de", self.crud.get_selection()[0]
        self.crud.set_key_value(self.crud.get_selection()[0])
        self.crud.set_form_id(self.crud.get_view_prop("form_edit"))
        self.crud.set_action("update")
        dialog = CrudForm(self.app_window, self.crud_portail, self.crud)
        self.app_window.show_all()

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
        if self.liststore[row_id][self.crud.get_view_prop("col_action_id")]:
            self.crud.remove_selection(key_id)
        else:
            self.crud.add_selection(key_id)
        qselect = len(self.crud.get_selection())
        if qselect > 1:
            self.label_select.set_markup("({}) sélections".format(qselect))
            self.label_select.show()
            self.button_edit.hide()
            if self.crud.get_view_prop("deletable", False):
                self.button_delete.show()
        elif qselect == 1:
            self.label_select.set_markup("{}".format(key_id))
            self.label_select.show()
            if self.crud.get_view_prop("form_edit", None) is not None:
                self.button_edit.show()
            if self.crud.get_view_prop("deletable", False):
                self.button_delete.show()
        else:
            self.label_select.hide()
            self.button_edit.hide()
            self.button_delete.hide()

        self.liststore[row_id][self.crud.get_view_prop("col_action_id")]\
            = not self.liststore[row_id][self.crud.get_view_prop("col_action_id")]

    def on_tree_selection_changed(self, selection):
        """ Sélection d'une ligne """
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
            dialog = CrudForm(self.app_window, self.crud_portail, self.crud)
            self.app_window.show_all()
