# -*- coding:Utf-8 -*-
"""
    Gestion des Vues
"""
import re

from crudform import CrudForm
from crudel import Crudel

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

class CrudView(GObject.GObject):
    """ Gestion des vues du CRUD
    app_window   : la fenêtre parent Gnome
    crud_portail : l'objet CrudPortail
    crud         : le contexte applicatif
    crudel       : la rubrique appelante de la vue éventuelle
    """

    __gsignals__ = {
        'init_widget': (GObject.SIGNAL_RUN_FIRST, None, (str, str,)),
        'refresh_data_view': (GObject.SIGNAL_RUN_FIRST, None, (str,str,))
    }
    def __init__(self, crud, box_main, box_toolbar, scroll_window, args=None):

        GObject.GObject.__init__(self)

        self.crud = crud
        self.crud_portail = crud.get_portail()
        self.crud.set_view(self)
        self.app_window = crud.get_window()
        self.crudel = crud.get_crudel()
        self.box_main = box_main
        self.box_toolbar = box_toolbar
        self.scroll_window = scroll_window
        self.qligne_view = 0 # nbre de lignes de la vue
        if args:
            self.args = args
        else:
            self.args = {}

        # print "View", self.crud.get_table_id(), self.crud.get_view_id()
        # if self.crudel: 
        #     print "View Crudel", self.crudel.element
        # print "View Args", self.args

        # Déclaration des variables globales
        self.treeview = None
        self.liststore = None
        self.current_filter = None
        self.store_filter = None
        self.store_filter_sort = None
        self.search_entry = None
        self.search_entry_sql = None
        self.search_sql = ""
        self.select = None
        self.button_add = None
        self.button_edit = None
        self.button_delete = None
        self.label_select = None
        self.treeiter_selected = None

        self.create_view_toolbar()
        self.create_liststore()
        self.create_treeview()

        if len(self.crud.get_selection()) == 1 and not self.crudel:
            # au retour d'un formulaire, on remet la sélection sur la ligne
            row_id = self.crud.get_row_id()
            self.treeview.set_cursor(Gtk.TreePath(row_id), None)
            self.treeview.grab_focus()

        self.app_window.show_all()

        self.crud.remove_all_selection()
        self.label_select.hide()
        self.button_edit.hide()
        self.button_delete.hide()

    def get_widget(self):
        """ retourne le container de la vue toolbar + list """
        # print "get_widget"
        return self.box_main

    def create_view_toolbar(self):
        """ toolbar pour afficher des infos et le bouton pour ajouter des éléments """
        if self.crud.get_view_prop("searchable", False):
            self.search_entry = Gtk.SearchEntry()
            self.search_entry.get_style_context().add_class('field_search')
            self.search_entry.connect("search-changed", self.on_search_changed)
            self.box_toolbar.pack_start(self.search_entry, False, True, 3)
            if self.crud.get_view_prop("filter", "") != "":
                self.search_entry.set_text(self.crud.get_view_prop("filter"))
            if not self.crudel:
                self.search_entry.grab_focus()
        elif self.crud.get_view_prop("searchable_sql", False):
            self.search_entry_sql = Gtk.SearchEntry()
            self.search_entry_sql.connect("activate", self.on_search_entry_sql_activate)
            self.box_toolbar.pack_start(self.search_entry_sql, False, True, 3)
            self.search_button = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_FIND))
            self.box_toolbar.pack_start(self.search_button, False, True, 3)
            self.search_button.connect("clicked", self.on_search_button_clicked)
            if self.crud.get_view_prop("filter", "") != "":
                self.search_entry_sql.set_text(self.crud.get_view_prop("filter"))
                self.search_sql = self.crud.get_view_prop("filter")
            if not self.crudel:
                self.search_entry_sql.grab_focus()
        # 
        self.qligne_label = Gtk.Label()
        self.box_toolbar.pack_start(self.qligne_label, False, True, 3)

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

        # Affichage des boutons des batchs de la vue
        for element in self.crud.get_view_elements():
            # Création du crudel
            crudel = Crudel.instantiate(self.crud, element, Crudel.TYPE_PARENT_VIEW)
            # Sauvegarde du crudel pour utilisation dans liststore et listview
            self.crud.set_element_prop(element, "crudel", crudel)
            if crudel.get_type() == "batch":
                # print crudel.get_label_short()
                if crudel.get_param("icon_name", False):
                    image = Gtk.Image.new_from_icon_name(crudel.get_param("icon_name", False), Gtk.IconSize.BUTTON)
                else:
                    image = Gtk.Image(stock=Gtk.STOCK_REFRESH)
                batch_button = Gtk.Button(label=crudel.get_label_short(), image=image)
                batch_button.set_image_position(Gtk.PositionType.LEFT) # LEFT TOP RIGHT BOTTOM
                batch_button.set_always_show_image(True)
                batch_button.set_tooltip_text(crudel.get_label_long())
                batch_button.connect("clicked", self.on_batch_button_clicked, crudel)
                self.box_toolbar.pack_end(batch_button, False, True, 3)

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
        # la 2éme colonne contiendra la couleur de fond des cellules recherchables
        self.crud.set_view_prop("col_searchable_id", col_id)
        col_id += 1
        # la 3éme colonne contiendra la couleur de fond des cellules editables
        self.crud.set_view_prop("col_editable_id", col_id)
        col_id += 1
        for element in self.crud.get_view_elements():
            crudel = self.crud.get_element_prop(element, "crudel")
            # colonnes crudel
            # mémorisation du n° de la colonne
            self.crud.set_column_prop(element, "col_id", col_id)
            # mémorisation de la clé dans le crud
            if element == self.crud.get_table_prop("key"):
                self.crud.set_view_prop("key_id", col_id)
            if element == self.crud.get_table_prop("key_display"):
                self.crud.set_view_prop("key_display", col_id)

            col_id = crudel.add_tree_view_column(self.treeview, col_id)
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
        # 2ème colonne row_searchable_id
        col_store_types.append(GObject.TYPE_STRING)
        # 3ème colonne row_editable_id
        col_store_types.append(GObject.TYPE_STRING)
        for element in self.crud.get_view_elements():
            crudel = self.crud.get_element_prop(element, "crudel")
            # colonnes crudel
            if crudel.is_display():
                col_store_types.append(GObject.TYPE_STRING)
            else:
                col_store_types.append(crudel.get_type_gdk())

            # colonnes techniques color et sortable
            if crudel.get_sql_color() != "":
                col_store_types.append(GObject.TYPE_STRING)
            if crudel.is_sortable():
                col_store_types.append(crudel.get_type_gdk())

        # col_action_id
        if self.crud.get_view_prop("deletable", False)\
            or self.crud.get_view_prop("form_edit", None) is not None :
            col_store_types.append(GObject.TYPE_BOOLEAN)
        # dernière colonne vide
        col_store_types.append(GObject.TYPE_STRING)

        self.liststore = Gtk.ListStore(*col_store_types)
        # print "col_store_types", col_store_types
        self.emit("refresh_data_view", "", "")

    def update_liststore(self):
        """ Mise à jour du liststore en relisant la table """
        # Génération du select de la table

        sql = "SELECT "
        b_first = True
        for element in self.crud.get_view_elements():
            crudel = self.crud.get_element_prop(element, "crudel")
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
                sql += self.crud.get_table_id() + "." + element
            else:
                sql += crudel.get_sql_get() + " as " + element
        
        # ajout des colonnes de jointure
        for element in self.crud.get_view_elements():
            crudel = self.crud.get_element_prop(element, "crudel")
            if crudel.with_jointure():
                sql += ", " + crudel.get_jointure("display") + " as " + element

        sql += " FROM " + self.crud.get_table_id()

        # ajout des tables de jointure
        join = ""
        for element in self.crud.get_view_elements():
            crudel = self.crud.get_element_prop(element, "crudel")
            if crudel.with_jointure():
                if crudel.get_jointure("join"):
                    join += " " + crudel.get_jointure("join")

        if join:
            sql += join

        sql_where = ""
        # prise en compte du search_sql
        if self.search_sql != "":
            for element in self.crud.get_view_elements():
                crudel = self.crud.get_element_prop(element, "crudel")
                if crudel.is_searchable():
                    if crudel.with_jointure():
                        if sql_where != "":
                            sql_where += " or "
                        sql_where += crudel.get_jointure("display") + " like '%" + self.search_sql + "%'"
                    else:
                        if sql_where != "":
                            sql_where += " or "
                        sql_where += self.crud.get_table_id() + "."\
                            + element + " like '%" + self.search_sql + "%'"
        if sql_where != "":
            sql_where = "(" + sql_where + ")"
        # Les arguments de la vue entrent dans le where
        for arg in self.args:
            if sql_where != "":
                sql_where += " AND "
            sql_where += self.crud.get_table_id() + "." + arg + " = '"\
                + self.crudel.crud.replace_from_dict(self.args.get(arg), self.crudel.crud.get_form_values()) + "'"
        # prise en compte du sql_where de la vue
        if self.crud.get_view_prop("sql_where"):
            if sql_where != "":
                sql_where += " AND "
            sql_where += self.crud.get_view_prop("sql_where")
        if sql_where != "":
            sql += " WHERE " + sql_where
        if self.crud.get_view_prop("order_by", None):
            sql += " ORDER BY " + self.crud.get_view_prop("order_by")

        sql += " LIMIT " + str(self.crud.get_view_prop("limit", 400))
        # print "VIEW", sql

        # EXECUTION SQL
        rows = self.crud.sql_to_dict(self.crud.get_basename(), sql, self.crud.ctx)

        # print len(rows)
        self.liststore.clear()
        # remplissage des colonnes item_sql
        for element in self.crud.get_view_elements():
            crudel = self.crud.get_element_prop(element, "crudel")
            # crudel.init_crudel_sql()
        row_id = 0
        for row in rows:
            store = []
            # print row
            # 1ère colonne col_row_id
            store.append(row_id)
            # 2ème colonne col_searchable_id
            store.append("#F0F8FF") 
            # 3ème colonne col_editable_id
            store.append("#F0FFF0") 
            for element in self.crud.get_view_elements():
                crudel = self.crud.get_element_prop(element, "crudel")
                # Valorisation du crudel avec la colonne sql
                crudel.init_value()
                if element in row:
                    crudel.set_value_sql(row[element])
                # colonnes crudel
                display = crudel.get_cell()
                # print element, crudel.get_value(), display
                store.append(display)
                # colonnes techniques
                if crudel.get_sql_color() != "":
                    store.append(row[element + "_color"])
                if crudel.is_sortable():
                    store.append(crudel.get_value())
            # col_action_id
            if self.crud.get_view_prop("deletable", False)\
                or self.crud.get_view_prop("form_edit", None) is not None:
                store.append(False)
            # dernière colonne vide
            store.append("")
            # print "store", row_id, store
            self.liststore.append(store)
            row_id += 1

        self.qligne_view = len(rows)
        # suppression de la sélection
        self.emit("init_widget", self.__class__, "update_listore")

    def filter_func(self, model, iter, data):
        """Tests if the text in the row is the one in the filter"""
        if self.current_filter is None or self.current_filter == "":
            return True
        else:
            bret = False
            for element in self.crud.get_view_elements():
                crudel = self.crud.get_element_prop(element, "crudel")
                if crudel.is_searchable():
                    if re.search(self.current_filter,\
                                 model[iter][self.crud.get_column_prop(element, "col_id")],\
                                 re.IGNORECASE):
                        bret = True
            return bret

    def refresh_footer(self):
        """ Préparation du message à afficher dans le footer du portail """
        self.crud_portail.emit("refresh_footer"\
            , self.crud.get_table_id() + "." + self.crud.get_view_id()\
            , "") ## raz du footer
        sql = self.crud.get_view_prop("sql_footer", False)
        if sql:
            rows = self.crud.sql_to_dict(self.crud.get_basename()\
                , sql, self.crud.ctx)
            for row in rows:
                if "sql_footer" in row:
                    self.crud_portail.emit("refresh_footer"\
                        , self.crud.get_table_id() + "." + self.crud.get_view_id()\
                        , row["sql_footer"])

    def do_init_widget(self, str_from, str_arg=""):
        """ Traitement du signal """
        # print "do_init_widget %s(%s) -> %s" % (str_from, str_arg, self.__class__)
        self.crud.remove_all_selection()
        self.label_select.hide()
        self.button_edit.hide()
        self.button_delete.hide()
        self.qligne_label.set_text(str(self.qligne_view) + " ligne(s)")

    def do_refresh_data_view(self, str_from, str_arg=""):
        """ Les données ont été modifiées -> refresh """
        # print "do_refresh_data_view %s.%s" % (str_from, str_arg)
        self.update_liststore()
        self.refresh_footer()

    def on_button_add_clicked(self, widget):
        """ Ajout d'un élément """
        self.crud.set_form_id(self.crud.get_view_prop("form_add"))
        self.crud.set_key_value(None)
        self.crud.set_action("create")
        self.crud_portail.set_layout(self.crud_portail.LAYOUT_FORM)
        # self.crud.set_crudel(None)
        form = CrudForm(self.crud, self.args)
        form.emit("init_widget", self.__class__, "on_button_add_clicked")

    def on_button_edit_clicked(self, widget):
        """ Edition de l'élément sélectionné"""
        # print "Edition de", self.crud.get_selection()[0]
        for key in self.crud.get_selection().keys():
            self.crud.set_key_value(key)
        self.crud.set_form_id(self.crud.get_view_prop("form_edit"))
        self.crud.set_action("update")
        self.crud_portail.set_layout(self.crud_portail.LAYOUT_FORM)
        # self.crud.set_crudel(None)
        form = CrudForm(self.crud, self.args)
        form.emit("init_widget", self.__class__, "on_button_edit_clicked")

    def on_button_delete_clicked(self, widget):
        """ Suppression des éléments sélectionnés """
        # print "Suppression de ", self.crud.get_selection()
        dialog = Gtk.MessageDialog(parent=self.app_window,\
            flags=Gtk.DialogFlags.MODAL,\
            type=Gtk.MessageType.WARNING,\
            buttons=Gtk.ButtonsType.OK_CANCEL,\
            message_format="Confirmez-vous la suppression de\n{}".format(self.crud.get_selection_values()))

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            for key_value in self.crud.get_selection():
                self.crud.sql_delete_record(key_value)

            self.emit("refresh_data_view", "", "")

        dialog.destroy()

    def on_batch_button_clicked(self, widget, crudel):
        """ Action un bouton plugin """
        # print "Action sur ", crudel, widget
        plugin = crudel.get_param("plugin")
        self.crud.set_crudel(crudel)
        plugin_class = self.crud.load_class("plugin." + plugin)
        form = plugin_class(self.crud)

    def on_search_changed(self, widget):
        """ Recherche d'éléments dans la vue """
        if len(self.search_entry.get_text()) == 1:
            return
        self.current_filter = self.search_entry.get_text()
        # mémorisation du filtre dans la vue
        self.crud.set_view_prop("filter", self.current_filter)
        self.store_filter.refilter()

    def on_search_entry_sql_activate(self, widget):
        """ CR dans le champ """
        self.search_button.do_activate(self.search_button)

    def on_search_button_clicked(self, widget):
        """ Recherche d'éléments dans la vue """
        if len(self.search_entry_sql.get_text()) == 1:
            return
        self.search_sql = self.search_entry_sql.get_text()
        # mémorisation du filtre dans la vue
        self.crud.set_view_prop("filter", self.search_sql)
        # relecture de la table avec le filtre
        self.emit("refresh_data_view", "", "")

    def on_action_toggle(self, cell, path):
        """ Clic sur coche d'action"""
        # print "Action sur", self.store_filter_sort[path][self.crud.get_view_prop("key_id")]
        key_id = self.store_filter_sort[path][self.crud.get_view_prop("key_id")]
        key_display = self.store_filter_sort[path][self.crud.get_view_prop("key_display", key_id)]
        row_id = self.store_filter_sort[path][self.crud.get_view_prop("col_row_id")]
        self.label_select.hide()
        self.button_edit.hide()
        self.button_delete.hide()
        if self.crud.get_view_prop("deletable", False):
            # plusieurs lignes sélectionables
            if self.liststore[row_id][self.crud.get_view_prop("col_action_id")]:
                self.crud.remove_selection(key_id)
            else:
                self.crud.add_selection(key_id, key_display)
            qselect = len(self.crud.get_selection())
            if qselect > 3:
                self.label_select.set_markup("({}) sélections".format(qselect))
                self.label_select.show()
                self.button_delete.show()
            elif qselect == 1:
                self.label_select.set_text(self.crud.get_selection_values())
                self.label_select.show()
                if self.crud.get_view_prop("form_edit", None) is not None:
                    self.button_edit.show()
                self.button_delete.show()
            else:
                self.label_select.set_text(self.crud.get_selection_values())
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
                self.crud.add_selection(key_id, key_display)
                self.label_select.set_markup("{}".format(self.crud.get_selection_values()))
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
        key_display = widget.get_model()[row][self.crud.get_view_prop("key_display", key_id)]
        row_id = widget.get_model()[row][0]
        self.crud.set_row_id(row_id)
        self.crud.remove_all_selection()
        self.crud.add_selection(key_id, key_display)
        self.crud.set_key_value(key_id)
        if self.crud.get_view_prop("form_edit", None) is not None:
            self.crud.set_form_id(self.crud.get_view_prop("form_edit"))
            self.crud.set_action("update")
            self.crud_portail.set_layout(self.crud_portail.LAYOUT_FORM)
            # self.crud.set_crudel(None)
            form = CrudForm(self.crud, self.args)
            form.emit("init_widget", self.__class__, "on_row_actived")
