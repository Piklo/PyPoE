"""
.dat export base handler

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/exporter/dat/handler.py                                |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

.dat export base handler

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python

# 3rd-party
from argparse import ArgumentParser
import argparse
from tqdm import tqdm

# self
from PyPoE.poe.constants import VERSION
from PyPoE.poe.file import dat
from PyPoE.cli.message import console, Msg
from PyPoE.cli.exporter import config
from PyPoE.cli.exporter.util import get_content_path
from PyPoE.poe.file.file_system import FileSystem

# =============================================================================
# Globals
# =============================================================================

__all__ = []

# =============================================================================
# Classes
# =============================================================================


class DatExportHandler:
    def add_default_arguments(self, parser: ArgumentParser):
        """

        :param parser:
        :type parser: argparse.ArgumentParser

        :return:
        """
        parser.set_defaults(func=self.handle)
        parser.add_argument(
            '--files', '--file',
            help='.dat files to export',
            nargs='*',
        )

        parser.add_argument(
            '-lang', '--language',
            help='Language subdirectory to use',
            dest='language',
            default=None,
        )

    def handle(self, args: argparse.Namespace):
        ver = config.get_option('version')

        if ver != VERSION.DEFAULT:
            console('Loading specification for %s' % ver)
            dat.set_default_spec(version=ver)

        spec = dat.default_spec
        if args.files is None:
            args.files = list(spec)
        else:
            files: set[str] = set()

            for file_name in args.files:
                if file_name in spec:
                    files.add(file_name)
                elif not file_name.endswith('.dat'):
                    file_name += '.dat'
                    if file_name not in spec:
                        console('.dat file "%s" is not in specification. Removing.' % file_name, msg=Msg.error)
                    else:
                        files.add(file_name)

            files_list = list(files)
            files_list.sort()
            args.files = files_list

        args.spec = spec

    def _read_dat_files(self, args: argparse.Namespace, prefix: str=''):
        path = get_content_path()

        console(prefix + 'Loading file system...')

        file_system = FileSystem(root_path=path)
        
        console(prefix + 'Reading .dat files')

        dat_files:dict[str, dat.DatFile] = {}
        lang = args.language or config.get_option('language')
        dir_path = "Data/"
        if lang != 'English':
            #ggpk_data = index.get_dir_record("Data/%s" % lang)
            dir_path = "Data/%s/" % lang
        remove: list[str] = []
        for name in tqdm(args.files):
            file_path = dir_path + name + '64'
            try:
                data = file_system.get_file(file_path)
            except FileNotFoundError:
                console('Skipping "%s" (missing)' % file_path, msg=Msg.warning)
                remove.append(name)
                continue

            df = dat.DatFile(name)

            df.read(file_path_or_raw=data, use_dat_value=False, x64=True)

            dat_files[name] = df

        for file_name in remove:
            args.files.remove(file_name)

        return dat_files


# =============================================================================
# Functions
# =============================================================================
