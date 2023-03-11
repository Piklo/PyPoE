"""
CLI config utilities

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/config.py                                              |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Utilities to setup the config on the CLI interface.

Documentation
===============================================================================

Classes
-------------------------------------------------------------------------------

.. autoclass:: ConfigHelper
    :no-inherited-members:

Exceptions
-------------------------------------------------------------------------------

.. autoclass:: ConfigError

.. autoclass:: SetupError

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import sys
from collections.abc import Iterable
from typing import Any, Callable

# 3rd party
from configobj import ConfigObj
import configobj
from validate import Validator

# self
from PyPoE.cli.message import console, Msg
from PyPoE.shared.config.validator import functions

# =============================================================================
# Globals
# =============================================================================

__all__ = ['ConfigError', 'SetupError', 'ConfigHelper']

# =============================================================================
# Exceptions
# =============================================================================


class ConfigError(ValueError):
    pass


class SetupError(ValueError):
    pass


# =============================================================================
# Classes
# =============================================================================


#TODO: add link to configobj doc or doc the extra stuff separatly.
class ConfigHelper(ConfigObj):
    """
    Extended regular config obj that can perform special tasks and extended
    handling.

    Generally the new options should be used over the direct usage of inherited
    functions.
    """
    def __init__(self, infile: str) -> None:
        ConfigObj.__init__(self, infile=infile, raise_errors=True, configspec=ConfigObj())

        # Fix missing main sections
        for item in ['Config', 'Setup']:
            if item not in self:
                self.update({item: {}})
            
            if self.configspec is None:
                raise TypeError("configspec is None")
            if item not in self.configspec:
                self.configspec.update({item: {}})

        self.validator = Validator()
        self.validator.functions.update(functions)
        self._listeners: dict[str, list[Callable[[Any, Any, Any], Any]]] = {}
        self._setupFunctions: dict[str, Iterable[Callable[[Any], Any]]] = {} 

    @property
    def option(self) -> configobj.Section:
        """
        Returns config option section from the config handler.

        Returns
        -------
        configobj.Section
        """
        config = self['Config'] # type: ignore
        if not isinstance(config, configobj.Section):
            raise TypeError("config option section is not of type configobj.Section")

        return config

    @property
    def optionspec(self) -> configobj.Section:
        """
        Returns config option specification section from the config handler.

        Returns
        -------
        configobj.Section
        """
        configspec = self.configspec
        if configspec is None:
            raise TypeError("configspec is None")
        
        config = configspec['Config'] # type: ignore
        if not isinstance(config, configobj.Section):
            raise TypeError("config option specification section is not of type configobj.Section")

        return config

    @property
    def setup(self) -> configobj.Section:
        """
        Returns config setup section from the config handler.

        Returns
        -------
        configobj.Section
        """
        config = self['Setup'] # type: ignore
        if not isinstance(config, configobj.Section):
            raise TypeError("config setup section is not of type configobj.Section")

        return config

    @property
    def setupspec(self) -> configobj.Section:
        """
        Returns config setup specification section from the config handler.

        Returns
        -------
        configobj.Section
        """
        configspec = self.configspec
        if configspec is None:
            raise TypeError("configspec is None")
        
        config = configspec['Setup'] # type: ignore
        if not isinstance(config, configobj.Section):
            raise TypeError("config setup specification section is not of type configobj.Section")

        return config

    def add_option(self, key: str, specification: str) -> None:
        """
        Adds (registers) a new config option with the specified key and
        specification.
        The key must be unique.

        Parameters
        ----------
        key : str
            key to use for storage
        specification : str
            config specification string for validating values for this key
        Raises
        ------
        KeyError
            if the key is a duplicate
        """
        if key in self.optionspec:
            raise KeyError('Duplicate key: %s' % key)
        self.optionspec[key] = specification

    def get_option(self, key: str, safe: bool=True) -> Any:
        """
        Returns the handled value for the specified key from the config.

        If the safe option is specified the function will check if any setups
        for the specified key need to be formed and raises an Error if the
        setup is pending. If False this behaviour is disabled

        .. warning::
            if the specified key is missing this method will shutdown the CLI
            with an error message to configure the key


        Parameters
        ----------
        key : str
            key to retrieve the value for
        safe : bool
            whether to check setup is needed

        Returns
        -------
        object
            handled value

        Raises
        ------
        SetupError
            if the setup for the key was not performed
        """
        if safe and key in self.setup:
            section = self.setup[key] # type: ignore
            if not isinstance(section, configobj.Section):
                raise TypeError(f"setup[{key}] section is not of type configobj.Section")
            if not section['performed']:
                raise SetupError('Setup not performed.')
        try:
            value = self.option[key]
        except KeyError:
            console(
                'Config variable "%s" is not configured. Consider running:' %
                key, msg=Msg.error)
            console('config set "%s" "<value>"' % key, msg=Msg.error)
            console('Exiting...', msg=Msg.error)
            sys.exit(-1)

        return self.validator.check(self.optionspec[key], value)

    def set_option(self, key: str, value: Any) -> None:
        """
        Sets the key to the specified value.

        The function will also take care of the following:
        - invalidate setups registered for this key, if any
        - validate the value
        - execute listeners

        Parameters
        ----------
        key : str
            the option key to set
        value : object
            the value to set the key to
        Raises
        ------
        validate.ValidationError
            if the validation of the value failed
        """
        if key in self.setup:
            section = self.setup[key] # type: ignore
            if not isinstance(section, configobj.Section):
                raise TypeError(f"setup[{key}] section is not of type configobj.Section")
            section['performed'] = False

        # Raise ValidationError
        value = self.validator.check(self.optionspec[key], value)

        if key in self._listeners:
            for f in self._listeners[key]:
                f(key, value, self.option[key])

        self.option[key] = value

    def register_setup(self, key: str, funcs: Callable[[Any], Any] | Iterable[Callable[[Any], Any]]) -> None:
        """
        Registers one or multiple functions that will be called to perform
        the setup for the specified config key.

        This will also create the according setup keys if non existent

        .. note::
            Setup variables should be registered using this function before
            using any other 'setup' related functions.

        Parameters
        ----------
        key : str
            config key to register the setup for
        funcs : callable or Iterable[callable]
            a function or iterable of functions to be called when the setup
            for the specified key is performed

        Raises
        ------
        TypeError
            if funcs is not callable

        """
        if key not in self.setup:
            self.setup.update({
                key: {
                    'performed': False,
                },
            })

        self.setupspec.update({
            key: {
                'performed': 'boolean()',
            },
        })

        if isinstance(funcs, Iterable):
           for f in funcs:
               if not callable(f):
                   raise TypeError('Callable expected.')
        elif not callable(funcs):
            raise TypeError('Callabe expected.')
        else:
            funcs = (funcs, )

        self._setupFunctions[key] = funcs

    def add_setup_listener(self, config_key: str, function: Callable[[Any, Any, Any], Any]) -> None:
        """
        Adds a listener for the specified config key that triggers when the
        config value was changed.

        Function should take 3 arguments:
        * key: The key that was changed
        * value: the new value
        * old_value: the old value
        
        Parameters
        ----------
        config_key : str
            config key to register the listener for
        function : callable
            callable to add as listener

        Raises
        ------
        TypeError
            if function is not callable
        """
        if not callable(function):
             raise TypeError('Callabe expected.')

        if config_key in self._listeners:
            self._listeners[config_key].append(function)
        else:
            self._listeners[config_key] = [function, ]

    def add_setup_variable(self, setup_key: str, variable_key: str, specification: str) -> None:
        """
        Adds a setup variable, i.e. a variable related to a specific setup

        For example this is useful to store additional information required to
        check whether a new run of setup is needed.

        Parameters
        ----------
        setup_key : str
            the setup key to register the variable for
        variable_key : str
            the key of the variable itself (must be unique)
        specification : str
            the config specification to use for the variable

        Raises
        ------
        KeyError
            if the setup key does not exist
        KeyError
            if the variable key is a duplicate

        """
        if setup_key not in self.setupspec:
            raise KeyError('Setup key "%s" is invalid' % setup_key)
        if variable_key in self.setupspec[setup_key]:
            raise KeyError('Duplicate key: %s' % variable_key)
        
        section = self.setupspec[setup_key] # type: ignore
        if not isinstance(section, configobj.Section):
            raise TypeError(f"setupspec[{setup_key}] section is not of type configobj.Section")
        
        section[variable_key] = specification

    def get_setup_variable(self, setup_key: str, variable_key: str) -> Any:
        """
        Returns the stored variable for the specified setup key

        Parameters
        ----------
        setup_key : str
            the setup key to retrieve the variable for
        variable_key : str
            the config key of the variable to retrieve

        Returns
        -------
        object
            the value of the variable
        """
        section = self.setup[setup_key] # type: ignore
        if not isinstance(section, configobj.Section):
            raise TypeError(f"setup[{setup_key}] section is not of type configobj.Section")
        
        return section[variable_key]

    def set_setup_variable(self, setup_key: str, variable_key: str, value: Any) -> None:
        """
        Sets the value for the specified setup key and variable

        Parameters
        ----------
        setup_key : str
            the setup key to set the variable for
        variable_key : str
            the config key of the variable to set
        value : object
            the value to set the variable to

        Raises
        ------
        validate.ValidationError
            if the validation of the value failed

        """
        # Raise ValidationError
        setupspecsection = self.setupspec[setup_key] # type: ignore
        if not isinstance(setupspecsection, configobj.Section):
            raise TypeError(f"setupspec[{setup_key}] section is not of type configobj.Section")
        value = self.validator.check(setupspecsection[variable_key], value)
        
        setupsection = self.setup[setup_key] # type: ignore
        if not isinstance(setupsection, configobj.Section):
            raise TypeError(f"setup[{setup_key}] section is not of type configobj.Section")
        setupsection[variable_key] = value

    def needs_setup(self, key: str) -> bool:
        """
        Returns whether the specified config key requires setup or not.

        .. warning ::
            This does not return whether the setup is performed, only whether
            this is a config key that requires setup.

            If you want to know whether setup was performed use is_setup.

        Parameters
        ----------
        key : str
            the setup key to check

        Returns
        -------
        bool
            True if setup needs to be performed
        """
        return key in self.setup

    def is_setup(self, variable: str) -> bool:
        """
        Returns whether the specified config key has it's setup performed

        Parameters
        ----------
        key : str
            the setup key to check

        Returns
        -------
        bool
            True if setup is performed
        """
        section = self.setup[variable] # type: ignore
        if not isinstance(section, configobj.Section):
            raise TypeError(f"setup[{variable}] section is not of type configobj.Section")
        
        value = section['performed'] # type: ignore
        if not isinstance(value, bool):
            raise TypeError(f"section['performed'] section is not of type bool")

        return value

    def setup_or_raise(self, variable: str) -> bool:
        """
        Returns True if setup is performed for the specified config variable
        and raises an error if it isn't.

        Parameters
        ----------
        variable : str
            config variable to check against

        Returns
        -------
        True
            if setup is performed

        Raises
        ------
        SetupError
            if setup is not performed
        """
        if not self.is_setup(variable):
            raise SetupError('Setup for %s not performed' % variable)
        return True