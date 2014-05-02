#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2013       Nick Hall
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# $Id: descendant.py 2228 2013-10-17 16:46:53Z romjerome $

"""Descendant Gramplet"""

#-------------------------------------------------------------------------
#
# GTK modules
#
#-------------------------------------------------------------------------
import gtk

#------------------------------------------------------------------------
#
# Gramps modules
#
#------------------------------------------------------------------------
from gen.plug import Gramplet
from ListModel import ListModel, NOSORT
from gui.editors import EditPerson
from Errors import WindowActiveError
from gen.display.name import displayer as name_displayer
from DateHandler import get_date
from gen.utils import get_birth_or_fallback, get_death_or_fallback
from config import config

from TransUtils import get_addon_translator
_ = get_addon_translator(__file__).gettext

class Descendant(Gramplet):

    def init(self):
        self.gui.WIDGET = self.build_gui()
        self.gui.get_container_widget().remove(self.gui.textview)
        self.gui.get_container_widget().add_with_viewport(self.gui.WIDGET)
        self.gui.WIDGET.show()

    def build_gui(self):
        """
        Build the GUI interface.
        """
        self.view = gtk.TreeView()
        self.view.set_tooltip_column(3)
        titles = [(_('Name'), 0, 230),
                  (_('Birth'), 2, 100),
                  ('', NOSORT, 1),
                  ('', NOSORT, 1), # tooltip
                  ('', NOSORT, 100)] # handle
        self.model = ListModel(self.view, titles, list_mode="tree", 
                               event_func=self.cb_double_click)
        return self.view

    def get_has_data(self, active_handle):
        """
        Return True if the gramplet has data, else return False.
        """
        if active_handle is None:
            return False
        person = self.dbstate.db.get_person_from_handle(active_handle)
        for family_handle in person.get_family_handle_list():
            family = self.dbstate.db.get_family_from_handle(family_handle)
            for child_ref in family.get_child_ref_list():
                return True
        return False
        
    def cb_double_click(self, treeview):
        """
        Handle double click on treeview.
        """
        (model, iter_) = treeview.get_selection().get_selected()
        if not iter_:
            return

        try:
            handle = model.get_value(iter_, 4)
            person = self.dbstate.db.get_person_from_handle(handle)
            EditPerson(self.dbstate, self.uistate, [], person)
        except WindowActiveError:
            pass

    def db_changed(self):
        self.update()

    def active_changed(self, handle):
        self.update()

    def update_has_data(self):
        active_handle = self.get_active('Person')
        self.set_has_data(self.get_has_data(active_handle))
    
    def main(self):
        active_handle = self.get_active('Person')
        self.model.clear()
        if active_handle:
            self.add_to_tree(1, None, active_handle)
            self.view.expand_all()
            self.set_has_data(self.get_has_data(active_handle))
        else:
            self.set_has_data(False)

    def add_to_tree(self, depth, parent_id, person_handle):
        if depth > config.get('behavior.generation-depth'):
            return

        person = self.dbstate.db.get_person_from_handle(person_handle)
        name = name_displayer.display(person)

        birth = get_birth_or_fallback(self.dbstate.db, person)
        death = get_death_or_fallback(self.dbstate.db, person)

        birth_text = birth_date = birth_sort = ''
        if birth:
            birth_date = get_date(birth)
            birth_sort = '%012d' % birth.get_date_object().get_sort_value()
            birth_text = _('%(abbr)s %(date)s') % \
                         {'abbr': birth.type.get_abbreviation(), 
                          'date': birth_date}

        death_date = death_sort = death_text = ''
        if death:
            death_date = get_date(death)
            death_sort = '%012d' % death.get_date_object().get_sort_value()
            death_text = _('%(abbr)s %(date)s') % \
                         {'abbr': death.type.get_abbreviation(), 
                          'date': death_date}

        tooltip = name + '\n' + birth_text + '\n' + death_text

        label = _('%(depth)s. %(name)s') % {'depth': depth, 'name': name}
        item_id = self.model.add([label, birth_date, birth_sort, 
                                  tooltip, person_handle], node=parent_id)

        for family_handle in person.get_family_handle_list():
            family = self.dbstate.db.get_family_from_handle(family_handle)
            for child_ref in family.get_child_ref_list():
                self.add_to_tree(depth + 1, item_id, child_ref.ref)
        return item_id