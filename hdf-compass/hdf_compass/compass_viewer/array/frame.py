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
Implements a viewer frame for compass_model.Array.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import wx
import wx.grid
from wx.lib.newevent import NewCommandEvent

import numpy as np

import os
import logging
import numpy

log = logging.getLogger(__name__)

from ..frame import NodeFrame
from .plot import LinePlotFrame, LineXYPlotFrame, ContourPlotFrame

class ArrayPanel(wx.Panel):
    """ Simple array panel with grid display """
    def __init__(self, parent, node):
        super(ArrayPanel, self).__init__(parent)
        self.node = node
        
        # Create a simple grid to show the array data
        self.grid = wx.grid.Grid(self)
        
        # Set up grid based on array shape
        if len(node.shape) == 0:  # scalar
            self.grid.CreateGrid(1, 1)
            self.grid.SetCellValue(0, 0, str(node[:]))
        elif len(node.shape) == 1:  # 1D array
            rows = min(node.shape[0], 1000)  # Limit display for performance
            self.grid.CreateGrid(rows, 1)
            data = node[:rows]
            for i in range(rows):
                self.grid.SetCellValue(i, 0, str(data[i]))
        else:  # 2D or higher
            rows = min(node.shape[0], 100)
            cols = min(node.shape[1], 100) if len(node.shape) > 1 else 1
            self.grid.CreateGrid(rows, cols)
            if len(node.shape) == 2:
                data = node[:rows, :cols]
                for i in range(rows):
                    for j in range(cols):
                        self.grid.SetCellValue(i, j, str(data[i, j]))
        
        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.grid, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
    def copy(self):
        """ Copy selected data to clipboard """
        pass  # TODO: Implement
        
    def export(self, path):
        """ Export data to CSV file """
        pass  # TODO: Implement
        
    def plot_data(self):
        """ Plot the data """
        pass  # TODO: Implement
        
    def plot_xy(self):
        """ Plot XY data """
        pass  # TODO: Implement


# Indicates that the slicing selection may have changed.
# These events are emitted by the SlicerPanel.
ArraySlicedEvent, EVT_ARRAY_SLICED = NewCommandEvent()
ArraySelectionEvent, EVT_ARRAY_SELECTED = NewCommandEvent()

# Menu and button IDs
ID_VIS_MENU_PLOT = wx.NewId()
ID_VIS_MENU_PLOTXY = wx.NewId()
ID_VIS_MENU_COPY = wx.NewId()
ID_VIS_MENU_EXPORT = wx.NewId()

def gen_csv(data, delimiters):
    """ converts any N-dimensional array to a CSV-string """
    if(type(data) == numpy.ndarray or type(data) == list):
        return delimiters[0].join(map(lambda x: gen_csv(x,delimiters[1:]), data))
    else:
        return str(data)

class ArrayFrame(NodeFrame):
    """
    Top-level frame displaying objects of type compass_model.Array.

    From top to bottom, has:

    1. Toolbar (see ArrayFrame.init_toolbar)
    2. SlicerPanel, with controls for changing what's displayed.
    3. An ArrayGrid, which displays the data in a spreadsheet-like view.
    """

    last_open_csv = os.getcwd()
    csv_delimiters_copy = ['\n', '\t']
    csv_delimiters_export = ['\n', ',']

    def __init__(self, node, pos=None):
        """ Create a new array frame """
        super(ArrayFrame, self).__init__(node, size=(800, 400), title=node.display_name, pos=pos)

        # Create toolbar
        # Only create toolbar if it doesn't exist
        existing_toolbar = self.GetToolBar()
        if existing_toolbar:
            self.toolbar = existing_toolbar
        else:
            self.toolbar = self.CreateToolBar()
        self.toolbar.AddTool(wx.ID_COPY, "Copy", wx.ArtProvider.GetBitmap(wx.ART_COPY))
        self.toolbar.AddTool(wx.ID_SAVEAS, "Export", wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE))
        self.toolbar.AddTool(wx.ID_ZOOM_IN, "Plot Data", wx.ArtProvider.GetBitmap(wx.ART_PLUS))
        self.toolbar.AddTool(wx.ID_ZOOM_OUT, "Plot XY", wx.ArtProvider.GetBitmap(wx.ART_MINUS))
        self.toolbar.Realize()

        # Create array panel
        self.array_panel = ArrayPanel(self, node)
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.GetSizer().Add(self.array_panel, 1, wx.EXPAND)

        # Bind events
        self.Bind(wx.EVT_TOOL, self.on_copy, id=wx.ID_COPY)
        self.Bind(wx.EVT_TOOL, self.on_export, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_TOOL, self.on_plot_data, id=wx.ID_ZOOM_IN)
        self.Bind(wx.EVT_TOOL, self.on_plot_xy, id=wx.ID_ZOOM_OUT)

    def on_copy(self, evt):
        """ Handle copy toolbar button """
        self.array_panel.copy()

    def on_export(self, evt):
        """ Handle export toolbar button """
        with wx.FileDialog(self, "Export array", wildcard="CSV files (*.csv)|*.csv",
                          style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                self.array_panel.export(path)

    def on_plot_data(self, evt):
        """ Handle plot data toolbar button """
        self.array_panel.plot_data()

    def on_plot_xy(self, evt):
        """ Handle plot XY toolbar button """
        self.array_panel.plot_xy()

    def on_selected(self, evt):
        """ User has chosen to display a different part of the dataset. """
        idx = 0
        for x in self.indices:
            self.slicer.set_spin_max(idx, self.node.shape[x]-1)
            idx = idx + 1
        
        self.grid.ResetView()

    def get_selected_data(self):
        """
        function to get the selected data in an array
        returns (data, names, line)
            data: array of sliced data
            names: name array for plots
            line: bool-value, True if 1D-Line, False if 2D
        """
        cols = self.grid.GetSelectedCols()
        rows = self.grid.GetSelectedRows()
        rank = len(self.node.shape)
        
        # Scalar data can't be line-plotted.
        if rank == 0:
            return None, None, True

        # Get data currently in the grid
        if rank > 1 and self.node.dtype.names is None:
            args = []
            for x in xrange(rank):
                if x == self.row:
                    args.append(slice(None, None, None))
                elif x == self.col:
                    args.append(slice(None, None, None))
                else:
                    idx = 0
                    for y in self.indices:
                        if y == x:
                            args.append(self.slicer.indices[idx])
                            break
                        idx = idx + 1
            data = self.node[tuple(args)]
            if self.row > self.col:
                data = np.transpose(data)
        else:
            data = self.node[self.slicer.indices]

        # Columns in the view are selected
        if len(cols) != 0:
            # The data is compound
            if self.node.dtype.names is not None:
                names = [self.grid.GetColLabelValue(x) for x in cols]
                data = [data[n] for n in names]
                return data, names, True

            # Plot multiple columns independently
            else:
                if rank > 1:
                    data = [data[(slice(None, None, None),c)] for c in cols]

                names = ["Col %d" % c for c in cols] if len(data) > 1 else None
                return data, names, True

        # Rows in view are selected
        elif len(rows) != 0:
            
            data = [data[(r,)] for r in rows]
            names = ["Row %d" % r for r in rows] if len(data) > 1 else None
            return data, names, True
        
        # No row or column selection.  Plot everything  
        else:
            # The data is compound
            if self.node.dtype.names is not None:
                names = [self.grid.GetColLabelValue(x) for x in xrange(self.grid.GetNumberCols())]
                data = [data[n] for n in names]
                return data, names, True

            # Plot 1D
            elif rank == 1:
                return [data], [], True

            # Plot 2D
            else:
                return data, [], False

    def on_sliced(self, evt):
        """ User has chosen to display a different part of the dataset. """
        self.grid.Refresh()

    def on_workaround_timer(self, evt):
        """ See slicer.enable_spinctrls docs """
        self.timer.Destroy()
        self.slicer.enable_spinctrls()

    @property
    def indices(self):
        """ A tuple of integer indices appropriate for dim selection.

        """
        l = []
        for x in xrange(len(self.node.shape)):
            if x == self.row or x == self.col:
                continue    
            l.append(x)
        return tuple(l)
        
    @property
    def row(self):
        """ The dimension selected for the row
        """
        return self.rowSpin.GetValue()
        
    @property
    def col(self):
        """ The dimension selected for the column
        """
        return self.colSpin.GetValue()
        
        
    def on_dimSpin(self, evt):
        """ Dimmension Spinbox value changed; notify parent to refresh the grid. """
        pos = evt.GetPosition()
        otherSpinner = self.rowSpin
        
        if evt.GetEventObject() == self.rowSpin :
            otherSpinner = self.colSpin

        if pos == otherSpinner.GetValue():
            if (pos > 0) :
                pos =  pos - 1
            else:
                pos = pos + 1
            otherSpinner.SetValue(pos)
        
        wx.PostEvent(self, ArraySelectionEvent(self.GetId()))

class SlicerPanel(wx.Panel):
    """
    Holds controls for data access.

    Consult the "indices" property, which returns a tuple of indices that
    prefix the array.  This will be RANK-2 elements long, unless hasfields
    is true, in which case it will be RANK-1 elements long.
    """

    @property
    def indices(self):
        """ A tuple of integer indices appropriate for slicing.

        Will be RANK-2 elements long, RANK-1 if compound data is in use
        (hasfields == True).
        """
        return tuple([x.GetValue() for x in self.spincontrols])

    def __init__(self, parent, shape, hasfields):
        """ Create a new slicer panel.

        parent:     The wxPython parent window
        shape:      Shape of the data to visualize
        hasfields:  If True, the data is compound and the grid can only
                    display one axis.  So, we should display an extra spinbox.
        """
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.shape = shape
        self.hasfields = hasfields
        self.spincontrols = []

        # Rank of the underlying array
        rank = len(shape)

        # Rank displayable in the grid.  If fields are present, they occupy
        # the columns, so the data displayed is actually 1-D.
        visible_rank = 1 if hasfields else 2

        sizer = wx.BoxSizer(wx.HORIZONTAL)  # Will arrange the SpinCtrls
                
        if rank > visible_rank:
            infotext = wx.StaticText(self, wx.ID_ANY, "Array Indexing: ")
            sizer.Add(infotext, 0, flag=wx.EXPAND | wx.ALL, border=10)

            for idx in xrange(rank - visible_rank):
                maxVal = shape[idx] - 1
                if not hasfields:
                    maxVal = shape[self.parent.indices[idx]] - 1
                sc = wx.SpinCtrl(self, max=maxVal, value="0", min=0)
                sizer.Add(sc, 0, flag=wx.EXPAND | wx.ALL, border=10)
                sc.Disable()
                self.spincontrols.append(sc)

        self.SetSizer(sizer)

        self.Bind(wx.EVT_SPINCTRL, self.on_spin)

    def enable_spinctrls(self):
        """ Unlock the spin controls.

        Because of a bug in wxPython on Mac, by default the first spin control
        has bizarre contents (and control focus) when the panel starts up.
        Call this after a short delay (e.g. 100 ms) to enable indexing.
        """
        for sc in self.spincontrols:
            sc.Enable()

    def set_spin_max(self, idx, max):
        self.spincontrols[idx].SetRange(0, max)
        
    def on_spin(self, evt):
        """ Spinbox value changed; notify parent to refresh the grid. """
        wx.PostEvent(self, ArraySlicedEvent(self.GetId()))


class ArrayGrid(wx.grid.Grid):
    """
    Grid class to display the Array.

    Cell contents and appearance are handled by the table model in ArrayTable.
    """

    def __init__(self, parent, node, slicer):
        wx.grid.Grid.__init__(self, parent)
        table = ArrayTable(parent)
        self.SetTable(table, True)

        # Column selection is always allowed
        selmode = wx.grid.Grid.wxGridSelectColumns
        
        # Row selection is forbidden for compound types, and for
        # scalar/1-D datasets
        if node.dtype.names is None and len(node.shape) > 1:
            selmode |= wx.grid.Grid.wxGridSelectRows
        
        self.SetSelectionMode(selmode)
           
    def ResetView(self):
            """Trim/extend the grid if needed"""
            rowChange = self.GetTable().GetRowsCount() - self.GetNumberRows()
            colChange = self.GetTable().GetColsCount() - self.GetNumberCols()
            if rowChange != 0 or colChange != 0:
                self.ClearGrid()
                locker = wx.grid.GridUpdateLocker(self)
                if rowChange > 0:
                    msg = wx.grid.GridTableMessage(
                        self.GetTable(),
                        wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED,
                        rowChange
                    )
                    self.ProcessTableMessage(msg)
                elif rowChange < 0:
                    msg = wx.grid.GridTableMessage(
                        self.GetTable(),
                        wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED,
                        0,
                        -rowChange
                    )
                    self.ProcessTableMessage(msg)
                    
                if colChange > 0:
                    msg = wx.grid.GridTableMessage(
                        self.GetTable(),
                        wx.grid.GRIDTABLE_NOTIFY_COLS_APPENDED,
                        colChange
                    )
                    self.ProcessTableMessage(msg)
                elif colChange < 0:
                    msg = wx.grid.GridTableMessage(
                        self.GetTable(),
                        wx.grid.GRIDTABLE_NOTIFY_COLS_DELETED,
                        0,
                        -colChange
                    )
                    self.ProcessTableMessage(msg)

            # The scroll bars aren't resized (at least on windows)
            # Jiggling the size of the window rescales the scrollbars
            # h,w = self.GetSize()
            # self.SetSize((h+1, w))
            # self.SetSize((h, w))
            self.ForceRefresh()


class LRUTileCache(object):
    """
        Simple tile-based LRU cache which goes between the Grid and
        the Array object.  Caches tiles along the last 1 or 2 dimensions
        of a dataset.

        Access is via __getitem__.  Because this class exists specifically
        to support point-based callbacks for the Grid, arguments may
        only be indices, not slices.
    """

    TILESIZE = 100  # Tiles will have shape (100,) or (100, 100)
    MAXTILES = 50  # Max number of tiles to retain in the cache

    def __init__(self, arr):
        """ *arr* is anything implementing compass_model.Array """
        import collections
        self.cache = collections.OrderedDict()
        self.arr = arr

    def __getitem__(self, args):
        """ Restricted to an index or tuple of indices. """

        if not isinstance(args, tuple):
            args = (args,)

        # Split off the last 1 or 2 dimensions
        coarse_position, fine_position = args[0:-2], args[-2:]

        def clip(x):
            """ Round down to nearest TILESIZE; takes e.g. 181 -> 100 """
            return (x // self.TILESIZE) * self.TILESIZE

        # Tuple with index of tile corner
        tile_key = coarse_position + tuple(clip(x) for x in fine_position)

        # Slice which will be applied to dataset to retrieve tile
        tile_slice = coarse_position + tuple(slice(clip(x), clip(x) + self.TILESIZE) for x in fine_position)

        # Index applied to tile to retrieve the desired data point
        tile_data_index = tuple(x % self.TILESIZE for x in fine_position)

        # Case 1: Add tile to cache, ejecting oldest tile if needed
        if not tile_key in self.cache:

            if len(self.cache) >= self.MAXTILES:
                self.cache.popitem(last=False)

            tile = self.arr[tile_slice]
            self.cache[tile_key] = tile

        # Case 2: Mark the tile as recently accessed
        else:
            tile = self.cache.pop(tile_key)
            self.cache[tile_key] = tile

        return tile[tile_data_index]


class ArrayTable(wx.grid.PyGridTableBase):
    """
    "Table" class which provides data and metadata for the grid to display.

    The methods defined here define the contents of the table, as well as
    the number of rows, columns and their values.
    """

    def __init__(self, parent):
        """ Create a new Table instance for use with a grid control.

        node:     An compass_model.Array implementation instance.
        slicer:   An instance of SlicerPanel, so we can see what indices the
                  user has requested.
        """
        wx.grid.PyGridTableBase.__init__(self)

        self.node = parent.node
        self.selecter = parent
        self.slicer = parent.slicer

        self.rank = len(self.node.shape)
        self.names = self.node.dtype.names

        self.cache = LRUTileCache(self.node)

    def GetNumberRows(self):
        """ Callback for number of rows displayed by the grid control """
        if self.rank == 0:
            return 1
        elif self.rank == 1:
            return self.node.shape[0]
        elif self.names is not None:
            return self.node.shape[-1]
        return self.node.shape[self.selecter.row]

    def GetNumberCols(self):
        """ Callback for number of columns displayed by the grid control.

        Note that if compound data is in use, columns display the field names.
        """
        if self.names is not None:
            return len(self.names)
        if self.rank < 2:
            return 1
        return self.node.shape[self.selecter.col]

    def GetValue(self, row, col):
        """ Callback which provides data to the Grid.

        row, col:   Integers giving row and column position (0-based).
        """
        # Scalar case
        if self.rank == 0:
            data = self.node[()]
            if self.names is None:
                return data
            return data[col]

        # 1D case
        if self.rank == 1:
            data = self.cache[row]
            if self.names is None:
                return data
            return data[self.names[col]]

        # ND case.  Watch out for compound mode!
        if self.names is not None:
            args = self.slicer.indices + (row,)
        else:
            l = []
            for x in xrange(self.rank):
                if x == self.selecter.row:
                    l.append(row)
                elif x == self.selecter.col:
                    l.append(col)
                else:
                    idx = 0
                    for y in self.selecter.indices:
                        if y == x:
                            l.append(self.slicer.indices[idx])
                            break
                        idx = idx + 1
            args = tuple(l)
        
        data = self.cache[args]
        if self.names is None:
            return data
        return data[self.names[col]]

    def GetRowLabelValue(self, row):
        """ Callback for row labels.

        Row number is used unless the data is scalar.
        """
        if self.rank == 0:
            return "Value"
        return str(row)

    def GetColLabelValue(self, col):
        """ Callback for column labels.

        Column number is used, except for scalar or 1D data, or if we're
        displaying field names in the columns.
        """
        if self.names is not None:
            return self.names[col]
        if self.rank == 0 or self.rank == 1:
            return "Value"
        return str(col)
