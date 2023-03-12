"""
.dat Exporter

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/exporter/dat/__init__.py                               |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

.dat Exporter

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python

# 3rd-party

# self
from argparse import _SubParsersAction, ArgumentParser # pyright: ignore [reportPrivateUsage]
from typing import TYPE_CHECKING, TypeAlias, Any
from PyPoE.cli.exporter.dat.parsers.json import JSONExportHandler

# =============================================================================
# Globals
# =============================================================================

__all__ = ['DatHandler']

# =============================================================================
# Classes
# =============================================================================
if TYPE_CHECKING:
    SubparserTAlias: TypeAlias = _SubParsersAction[ArgumentParser]
else:
    SubparserTAlias = Any

class DatHandler:
    """

    :type sql: argparse.ArgumentParser
    """
    def __init__(self, sub_parser: SubparserTAlias):
        """

        :type sub_parser: argparse._SubParsersAction
        """
        parser = sub_parser.add_parser(
            'dat',
            help='.dat export',
        )
        parser.set_defaults(func=lambda: parser.print_help())

        sub = parser.add_subparsers(help='Export type')
        JSONExportHandler(sub)

# =============================================================================
# Functions
# =============================================================================
