# Authors: John Dennis <jdennis@redhat.com>
# Authors: Dan Walsh <dwalsh@redhat.com>
#
# Copyright (C) 2006-2010 Red Hat, Inc.
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
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

# Needed to silence warnings if X display is not present
import warnings
warnings.filterwarnings('ignore', 'could not open display')

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

#------------------------------------------------------------------------------

__all__ = ['display_traceback',
           ]


#------------------------------------------------------------------------------

def display_traceback(who, parent=None):
    if Gdk.Display.get_default() is None:
        return None

    import traceback

    stacktrace = traceback.format_exc()
    message = _("Oops, %s hit an error!" % who)

    title = who + ' ' + _("Error")
    dlg = Gtk.Dialog(title, parent, 0, (Gtk.STOCK_OK, Gtk.ResponseType.OK))
    dlg.set_position(Gtk.WindowPosition.CENTER)
    dlg.set_default_size(600, 400)

    text_view = Gtk.TextView()
    text_view.get_buffer().set_text(message + '\n\n' + stacktrace)
    text_view.set_editable(False)
    text_view.set_cursor_visible(False)

    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scrolled_window.add(text_view)

    dlg.vbox.pack_start(scrolled_window, True, True, 0)

    dlg.show_all()
    rc = dlg.run()
    dlg.destroy()
    if rc == Gtk.ResponseType.OK:
        return True
    return None
