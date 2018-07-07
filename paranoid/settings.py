# Copyright 2018 Max Shinn <max@maxshinnpotential.com>
# 
# This file is part of Paranoid Scientist, and is available under the
# MIT license.  Please see LICENSE.txt in the root directory for more
# information.

"""A settings manager for Paranoid Scientist.  This manages settings
at a global level.

We use a class here as a singleton.  Rather than a "true" Java-style
singleton, this is just a class which cannot be instantiated, and thus
has a single state.  We use this instead of something at the module
level in order to prevent a "import *" statement from causing
problems.
"""
class Settings:
    """A settings manager for Paranoid Scientist

    Settings can be set either globally or locally.  To change a
    setting globally, call Settings.set().  To change a setting
    locally (on a per-function basis) using a decorator.  For this,
    please refer to the paranoidconfig decorator in decorators.py.

    Settings can be viewed with Settings.get().

    Note that this "class" is a singleton namespace with exclusively
    static methods.  It should not be instantiated.
    """

    FUNCTION_SETTINGS_NAME = "__function_settings__"
    # Default values for settings.  Each variable which can be set
    # either locally or globally must be listed here with a default
    # value.
    # 
    # NOTE TO THE CURIOUS PROGRAMMER: If you found this by digging
    # through the code and trying to find how to change settings, do
    # NOT change them here.  Call Settings.set() at the top of your
    # source file instead.
    __global_setting_values = {
        'enabled' : True,
        'max_runtime': 2,
        'max_cache' : 2,
        'namespace' : {}}
    # Validity functions.  Each variable listed above has an
    # associated validation function.  While not strictly required,
    # these validation functions ensure that the settings are valid.
    __validate_settings = {
        'enabled' : lambda x : x in [True, False],
        'max_runtime' : lambda x : type(x) in [int, float] and x >= 0,
        'max_cache' : lambda x : isinstance(x, int) and x >= 0,
        'namespace' : lambda x : isinstance(x, dict) and all(isinstance(k, str) for k in x.keys())}
    def __init__(self):
        """Do not try to instantiate this."""
        raise TypeError("Do not instantiate the settings module")
    def set(**kwargs):
        """Set configuration parameters.  

        Pass keyword arguments for the parameters you would like to
        set.

        This function is particularly useful to call at the head of
        your script file to disable particular features.  For example,

        >>> from paranoid.settings import Settings
        >>> Settings.set(enabled=False)

        This is syntactic sugar for the _set function.
        """
        for k,v in kwargs.items():
            Settings._set(k, v)
    def _set(name, value, function=None):
        """Internally set a config parameter.

        If you call it with no function, it sets the global parameter.
        If you call it with a function argument, it sets the value for
        the specified function.  Normally, this should only be called
        with a function argument for internal code.

        This should not be called by code outside of the paranoid
        module.
        """

        if name not in Settings.__global_setting_values.keys():
            raise NameError("Invalid setting value")
        if name in Settings.__validate_settings.keys():
            if not Settings.__validate_settings[name](value):
                raise ValueError("Invalid setting: %s = %s" %
                                 (name, value))
        # Set the setting either globally (if no function is passed)
        # or else locally to the function (if a function is passed).
        if function:
            if not hasattr(function, Settings.FUNCTION_SETTINGS_NAME):
                setattr(function, Settings.FUNCTION_SETTINGS_NAME, {})
                # Test if this wraps something.  TODO this will fail
                # for nested decorators.  This also assumes that, if
                # there is a wrapped function (super wraps sub), that
                # if super doesn't have settings, then sup doesn't
                # either.  (This assumption is valid for paranoid
                # decorators since it properly uses update_wrapper,
                # but may not be valid for other decorators.)
                if hasattr(function, "__wrapped__"):
                    setattr(function.__wrapped__,
                            Settings.FUNCTION_SETTINGS_NAME,
                            getattr(function, Settings.FUNCTION_SETTINGS_NAME))
            getattr(function, Settings.FUNCTION_SETTINGS_NAME)[name] = value
        else:
            Settings.__global_setting_values[name] = value
    def get(name, function=None):
        """Get a setting.

        `name` should be the name of the setting to look for.  If the
        optional argument `function` is passed, this will look for a
        value local to the function before retrieving the global
        value.
        """
        if function is not None:
            if hasattr(function, Settings.FUNCTION_SETTINGS_NAME):
                if name in getattr(function, Settings.FUNCTION_SETTINGS_NAME):
                    return getattr(function, Settings.FUNCTION_SETTINGS_NAME)[name]
        return Settings.__global_setting_values[name]
