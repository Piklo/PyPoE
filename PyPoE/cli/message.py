"""
CLI Message

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/message.py                                             |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

CLI message utility classes and functions.

Agreement
===============================================================================

See PyPoE/LICENSE

TODO-List
===============================================================================

- console output formatting/linebreaks

Documentation
===============================================================================

Classes
-------------------------------------------------------------------------------

.. autoclass:: Msg

.. autoclass:: OutputHook

Functions
-------------------------------------------------------------------------------

.. autofunction:: console
"""

# =============================================================================
# Imports
# =============================================================================

# Python
from typing import Any, Callable, TextIO, Type
import warnings
from enum import Enum
from time import strftime

# 3rd Party
from colorama import Style, Fore

# =============================================================================
# Globals
# =============================================================================

__all__ = ['Msg', 'OutputHook', 'console']

# =============================================================================
# Classes
# =============================================================================


class Msg(Enum):
    """
    Used for :py:func`console` function.

    Parameters
    ----------
    default
        default
    warning
        yellow warning message
    error
        red error message
    """
    default = Style.RESET_ALL
    error = Style.BRIGHT + Fore.RED
    warning = Style.BRIGHT + Fore.YELLOW


class OutputHook:
    """
    Warning hook to reformat / restyle warning messages properly.
    """
    def __init__(self, show_warning: Callable[[Warning | str, Type[Warning], str, int, TextIO | None, str | None], None]):
        self._orig_show_warning = show_warning
        self._orig_format_warning = warnings.formatwarning
        warnings.formatwarning = self.format_warning
        warnings.showwarning = self.show_warning

    def format_warning(self, message: Warning | str, category: Type[Warning], filename: str, lineno: int, line: str | None = None):
        kwargs = {
            'message': message,
            'category': category.__name__,
            'filename': filename,
            'lineno': lineno,
            'line': line,
        }
        f = "%(filename)s:%(lineno)s:\n%(category)s: %(message)s\n" % kwargs
        return console(f, msg=Msg.warning, rtr=True)
    #
    def show_warning(self, *args: Any, **kwargs: Any) -> None:
        self._orig_show_warning(*args, **kwargs)

# =============================================================================
# Functions
# =============================================================================

def console(message: str, msg: Msg = Msg.default, rtr: bool = False, raw: bool = False) -> str | None:
    """
    Send the specified messge to console

    Parameters
    ----------
    message : str
        Message to send
    msg : Msg
        Message type
    rtr : bool
        Return message instead of printing
    raw : bool
        Skip timestamp/colour formatting

    Returns
    -------
    None or str
        if rtr is specified returns formatted message, None otherwise
    """
    if raw:
        f = message
    else:
        f = msg.value + strftime('%X ') + message + Msg.default.value
    if rtr:
        return f
    else:
        print(f)

