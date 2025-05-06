##############################################################################
# Copyright by The HDF Group.                                                #
# All rights reserved.                                                       #
#                                                                            #
# This file is part of the HDF Compass Viewer. The full HDF Compass          #
# copyright notice, including terms governing use, modification, and         #
# terms governing use, modification, and redistribution, is contained in     #
# the file COPYING, which can be found at the root of the source code        #
# distribution tree.  If you do not have access to this file, you may        #
# request a copy from help@hdfgroup.org.                                     #
##############################################################################
"""
Handles list and icon view for Container display.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import wx
from wx.lib.pubsub import pub

import logging
log = logging.getLogger(__name__)

from hdf_compass import compass_model
from ..events import CompassOpenEvent
from ..events import ContainerSelectionEvent

ID_CONTEXT_MENU_OPEN = wx.ID_ANY
ID_CONTEXT_MENU_OPENWINDOW = wx.ID_ANY
ID_CONTEXT_MENU_COPY = wx.ID_ANY


class ContainerList(wx.ListCtrl):
    """ List control for displaying container contents """

    def __init__(self, parent, node, **kwds):
        """ Create a new container list control """
        style = wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN
        if 'style' in kwds:
            style |= kwds.pop('style')
        super(ContainerList, self).__init__(parent, style=style, **kwds)

        self.node = node
        self.parent = parent

        # Create columns
        self.InsertColumn(0, "Name")
        self.InsertColumn(1, "Type")
        self.InsertColumn(2, "Size")

        # Set column widths
        self.SetColumnWidth(0, 200)
        self.SetColumnWidth(1, 100)
        self.SetColumnWidth(2, 100)

        # Set size hints
        self.SetMinSize((400, 300))

        # Populate list
        self.populate()

        # Bind events
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_right_click)
        self.Bind(wx.EVT_MENU, self.on_copy, id=wx.ID_COPY)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)

    def populate(self):
        """ Populate the list with container contents """
        self.DeleteAllItems()
        for i, child in enumerate(self.node):
            self.InsertItem(i, child.display_name)
            self.SetItem(i, 1, child.__class__.__name__)
            self.SetItem(i, 2, str(child.size))

    def on_item_activated(self, evt):
        """ Handle item activation """
        index = evt.GetIndex()
        child = self.node[index]
        # Get the current position of the parent frame
        pos = self.parent.GetPosition()
        # Create and post the open event with position
        open_event = CompassOpenEvent(child, pos=pos)
        wx.PostEvent(wx.GetApp(), open_event)
        evt.Skip()

    def on_item_selected(self, evt):
        """ Handle item selection """
        index = evt.GetIndex()
        child = self.node[index]
        # Create and post the selection event
        selection_event = ContainerSelectionEvent(child)
        wx.PostEvent(self.parent, selection_event)
        evt.Skip()

    def on_right_click(self, evt):
        """ Handle right click """
        menu = wx.Menu()
        menu.Append(wx.ID_COPY, "Copy")
        self.PopupMenu(menu)
        menu.Destroy()

    def on_copy(self, evt):
        """ Handle copy menu item """
        index = self.GetFirstSelected()
        if index != -1:
            child = self.node[index]
            pub.sendMessage('compass.copy', node=child)

    def copy_to_clipboard(self):
        """ Copy selected item to clipboard """
        index = self.GetFirstSelected()
        if index != -1:
            child = self.node[index]
            pub.sendMessage('compass.copy', node=child)

    @property
    def selection(self):
        """ Return the currently selected node, or None """
        index = self.GetFirstSelected()
        if index != -1:
            return self.node[index]
        return None


class ContainerIconList(ContainerList):
    """
    Icon view of nodes in a Container.
    """

    def __init__(self, parent, node):
        """ New icon list view
        """
        style = wx.LC_ICON | wx.LC_AUTOARRANGE | wx.BORDER_SUNKEN
        super(ContainerIconList, self).__init__(parent, node, style=style)
        
        self.node = node

        # Set minimum size for icon view
        self.SetMinSize((600, 400))

        # Set up image list for icons
        self.il = wx.GetApp().imagelists[64]
        self.SetImageList(self.il, wx.IMAGE_LIST_NORMAL)

        # Clear any existing items
        self.DeleteAllItems()

        # Populate with icons
        for item in range(len(self.node)):
            try:
                subnode = self.node[item]
                image_index = self.il.get_index(type(subnode))
                self.InsertItem(item, subnode.display_name, image_index)
            except:
                log.exception("Error adding icon item")

        # Force initial layout
        self.Layout()
        self.Refresh()

    def populate(self):
        """ Override populate to handle icon view """
        self.DeleteAllItems()
        for item in range(len(self.node)):
            try:
                subnode = self.node[item]
                image_index = self.il.get_index(type(subnode))
                self.InsertItem(item, subnode.display_name, image_index)
            except:
                log.exception("Error adding icon item")
        self.Layout()
        self.Refresh()


class ContainerReportList(ContainerList):
    """
    List view of the container's contents.

    Uses a wxPython virtual list, allowing millions of items in a container
    without any slowdowns.
    """

    def __init__(self, parent, node):
        """ Create a new list view.

        parent: wxPython parent object
        node:   Container instance to be displayed
        """

        style = wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN
        super(ContainerReportList, self).__init__(parent, node, style=style)

        self.node = node

        # Clear and recreate columns for report view
        self.ClearAll()
        self.InsertColumn(0, "Name")
        self.InsertColumn(1, "Kind")
        self.SetColumnWidth(0, 300)
        self.SetColumnWidth(1, 200)

        # Set minimum size
        self.SetMinSize((500, 400))

        # Set up image list
        self.il = wx.GetApp().imagelists[16]
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

        # Set up virtual list
        self.SetItemCount(len(node))

        # Bind virtual list events
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)

        # Force initial layout
        self.Layout()
        self.Refresh()

    def OnGetItemText(self, item, col):
        """ Callback method to support virtual list ctrl """
        try:
            if col == 0:
                return self.node[item].display_name
            elif col == 1:
                return type(self.node[item]).class_kind
        except:
            log.exception("Error getting item text")
        return ""

    def OnGetItemImage(self, item):
        """ Callback method to support virtual list ctrl """
        try:
            subnode = self.node[item]
            return self.il.get_index(type(subnode))
        except:
            log.exception("Error getting item image")
            return -1

    def populate(self):
        """ Override populate to use virtual list """
        self.SetItemCount(len(self.node))
        self.Refresh()
