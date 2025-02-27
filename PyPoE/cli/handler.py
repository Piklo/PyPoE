"""
Generic Console Handlers

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/handler.py                                             |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Generic console handlers for common tasks.

Agreement
===============================================================================

See PyPoE/LICENSE

Documentation
===============================================================================

.. autoclass:: BaseHandler

.. autoclass:: ConfigHandler

.. autoclass:: SetupHandler
"""

# =============================================================================
# Imports
# =============================================================================

# Python
from argparse import _SubParsersAction, ArgumentParser # pyright: ignore [reportPrivateUsage]
import argparse
import traceback
from typing import Any
import configobj


# 3rd Party
from validate import ValidateError

# self
from PyPoE.cli.config import ConfigError, ConfigHelper
from PyPoE.cli.message import console, Msg

# =============================================================================
# Globals
# =============================================================================

__all__ = [
    'BaseHandler', 'ConfigHandler', 'SetupHandler',
]

# =============================================================================
# Classes
# =============================================================================

class BaseHandler:
    """
    Other handlers should inherit this one.
    """
    def __init__(self, sub_parser: "_SubParsersAction[ArgumentParser]", *args: Any, **kwargs: Any) -> None:
        self.parser: ArgumentParser

    def _help(self, *args: Any) -> int:
        self.parser.print_help()
        return 0

    def _show_error(self, e: Exception) -> int:
        console("%s: %s" % (
            e.__class__.__name__,
            ''.join(e.args)
        ), msg=Msg.error)
        return -1

    def print_sep(self, char: str='-') -> None:
        console(char*70)


class ConfigHandler(BaseHandler):
    """
    Handler for config related tasks.

    Sets up some basic config commands under the config sub menu.

    .. warning::
        Should be included in any application that uses the cli config
    """
    def __init__(self, sub_parser: "_SubParsersAction[ArgumentParser]", config: ConfigHelper):
        """
        Parameters
        ----------
        sub_parser : :py:meth:`argparse.ArgumentParser.add_subparsers`
            sub parsers object
        config : ConfigHelper
            config instance

        Raises
        ------
        PyPoE.cli.config.ConfigError
            if config validation failed
        """
        # Config
        self.config = config
        if not self.config.validate(config.validator):
            raise ConfigError('Config validation failed.')

        # Parsing stuff
        self.parser = sub_parser.add_parser('config', help='Edit config options')
        self.parser.set_defaults(func=self._help)
        config_sub = self.parser.add_subparsers()

        print_debug_parser = config_sub.add_parser(
            'print_debug',
            help='Prints out all registered and internal options for debugging.'
        )
        print_debug_parser.set_defaults(func=self.print_debug)

        print_all_parser = config_sub.add_parser(
            'print_all',
            help='Prints out all registered config options'
        )
        print_all_parser.set_defaults(func=self.print_all)

        get_parser = config_sub.add_parser('get', help='Get config option')
        get_parser.set_defaults(func=self.get)
        keys: list[Any] = config.optionspec.keys()
        get_parser.add_argument(
            'variable',
            choices=keys,
            help='Variable to set',
        )

        set_parser = config_sub.add_parser('set', help='Set config option')
        set_parser.set_defaults(func=self.set)
        keys = config.optionspec.keys()
        set_parser.add_argument(
            'variable',
            choices=keys,
            help='Variable to set',
        )
        set_parser.add_argument(
            'value',
            action='store',
            help='Value to set',
        )

    def print_debug(self, args: argparse.Namespace) -> int:
        """
        Prints out the entire config as string.

        Parameters
        ----------
        args : argparse.Namespace
            namespace object as passed from argument parser

        Returns
        -------
        int
            success code
        """
        console(str(self.config))
        return 0

    def print_all(self, args: argparse.Namespace) -> int:
        """
        Prints all currently registered config variables.

        Parameters
        ----------
        args : argparse.Namespace
            namespace object as passed from argument parser

        Returns
        -------
        int
            success code
        """
        optionspec_keys: list[Any] = self.config.optionspec.keys()
        spec = set(optionspec_keys)
        
        option_keys: list[Any] = self.config.option.keys()
        real = set(option_keys)


        missing = spec.difference(real)
        extra = real.difference(spec)
        configured = spec.difference(missing)


        console('Current stored config variables:')
        for key in sorted(list(configured)):
            console("%s: %s" % (key, self.config.option[key]))

        if missing:
            console('', raw=True)
            console('Missing config variables (require config set):', msg=Msg.error)
            for key in sorted(list(missing)):
                console("%s" % (key, ), Msg.error)

        if extra:
            console('', raw=True)
            console('Extra variables (unused):', msg=Msg.warning)
            for key in sorted(list(extra)):
                console("%s: %s" % (key, self.config.option[key]), msg=Msg.warning)

        return 0

    def get(self, args: argparse.Namespace) -> int:
        """
        Prints the config setting for the specified var.

        Parameters
        ----------
        args : argparse.Namespace
            namespace object as passed from argument parser

        Returns
        -------
        int
            success code
        """
        console('Config setting "%s" is currently set to:\n%s' % (args.variable, self.config.option[args.variable]))
        return 0

    def set(self, args: argparse.Namespace) -> int:
        """
        Sets the specified config setting to the specified value.

        Parameters
        ----------
        args : argparse.Namespace
            namespace object as passed from argument parser

        Returns
        -------
        int
            success code
        """
        try:
            self.config.set_option(args.variable, args.value)
        except ValidateError as e:
            return self._show_error(e)
        self.config.write()

        console('Config setting "%s" has been set to:\n%s' % (args.variable, args.value))

        if self.config.needs_setup(args.variable) and not self.config.is_setup(args.variable):
            console('', raw=True)
            console('Variable needs setup. Please run:\nsetup perform')

        return 0


class SetupHandler(BaseHandler):
    """
    Handler for config setup related tasks.

    Setups up the commands under the "setup" sub menu.

    .. warning::
        Should be included in any application that uses the cli config
    """
    def __init__(self, sub_parser: "_SubParsersAction[ArgumentParser]", config: ConfigHelper): 
        """
        Parameters
        ----------
        sub_parser : :py:meth:`argparse.ArgumentParser.add_subparsers`
            sub parsers object
        config : ConfigHelper
            config instance
        """
        self.config = config
        self.parser = sub_parser.add_parser('setup', help='CLI Interface Setup')
        self.parser.set_defaults(func=self._help)

        setup_sub = self.parser.add_subparsers()

        setup_perform = setup_sub.add_parser(
            'perform',
            help='Perform setup'
        )
        setup_perform.set_defaults(func=self.setup)

    def setup(self, args: argparse.Namespace) -> int:
        """
        Performs the setup (if needed)

        Parameters
        ----------
        args : argparse.Namespace
            namespace object as passed from argument parser

        Returns
        -------
        int
            success code
        """
        console('Performing setup. This may take a while - please wait...')
        self.print_sep()

        setup_section = self.config['Setup'] # type: ignore
        if not isinstance(setup_section, configobj.Section):
            raise TypeError("config option section is not of type configobj.Section")
        
        for key in setup_section: # type: ignore
            if not isinstance(key, str):
                raise TypeError("key is not of type str")
            
            key_section = setup_section[key] # type: ignore
            if not isinstance(key_section, configobj.Section):
                raise TypeError("config option section is not of type configobj.Section")
            
            if key_section['performed']:
                continue
            console('Performing setup for: %s' % key)
            try:
                for func in self.config.setupFunctions[key]:
                    func(args)
            except Exception:
                console('Unexpected error occured during setup:\n')
                console(traceback.format_exc(), msg=Msg.error)
                continue
            key_section['performed'] = True
            self.print_sep()
        console('Done.')
        return 0