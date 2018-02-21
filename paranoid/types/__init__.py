# Copyright 2018 Max Shinn <max@maxshinnpotential.com>
# 
# This file is part of Paranoid Scientist, and is available under the
# MIT license.  Please see LICENSE.txt in the root directory for more
# information.

from .base import *
from .collections import *
from .numeric import *
from .string import *


try:
    import numpy as __np
    __np.seterr(all="raise")
    __np.seterr(under="ignore")
except ImportError:
    pass
