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
from __future__ import absolute_import, division, print_function, unicode_literals

from .model import HDF5Store, HDF5Group, HDF5Dataset, HDF5KV
from hdf_compass import compass_model

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Register the HDF5Store with the compass model
compass_model.push(HDF5Store)
