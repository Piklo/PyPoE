"""
CLI Core

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/core.py                                                |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

CLI core utility classes and functions.

Agreement
===============================================================================

See PyPoE/LICENSE

TODO-List
===============================================================================

- Virtual Terminal?

Documentation
===============================================================================

Functions
-------------------------------------------------------------------------------

.. autofunction:: run
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import argparse
import sys
import traceback

# self
from PyPoE.cli.config import ConfigHelper
from PyPoE.cli.message import console, Msg

# =============================================================================
# Globals
# =============================================================================

__all__ = ['run']

# =============================================================================
# Classes
# =============================================================================

# =============================================================================
# Functions
# =============================================================================


def run(parser: argparse.ArgumentParser, config: ConfigHelper):
    """
    Run the CLI application with the given parser and config.

    It will take care of handling parsing the arguments and calling the
    appropriate function and print any tracebacks that occurred during the call.

    Saves config and exits the python client.

    .. warning::
        This function will exist the python client on completion

    Parameters
    ----------
    parser : argparse.ArgumentParser
        assembled argument parser for argument handling
    config : ConfigHelper
        config object to use for the CLI application wide config
    """
    args = parser.parse_args()
    if hasattr(args, 'func'):
        try:
            code = args.func(args)
        except Exception:
            console(traceback.format_exc(), msg=Msg.error)
            code = -1
    else:
        parser.print_help()
        code = 0

    config.validate(config.validator)
    config.write()
    sys.exit(code)

