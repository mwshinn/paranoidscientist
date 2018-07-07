# Copyright 2018 Max Shinn <max@maxshinnpotential.com>
# 
# This file is part of Paranoid Scientist, and is available under the
# MIT license.  Please see LICENSE.txt in the root directory for more
# information.

from .settings import Settings

print("Warning, paranoid.ignore is depreciated.  " \
      "Use settings.Settings.set(enabled=False) instead.")

Settings.set(enabled=False)
