"""
Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/poe/patchserver.py                                         |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Utility functions and classes for connecting to the PoE patch server and
downloading files from it.


Agreement
===============================================================================

See PyPoE/LICENSE

Documentation
===============================================================================

Public API
-------------------------------------------------------------------------------

.. autoclass:: Patch

Internal API
-------------------------------------------------------------------------------

.. autofunction:: socket_fd_open
.. autofunction:: socket_fd_close

"""

# =============================================================================
# Imports
# =============================================================================

# Python
import socket
import struct
import io
import os
from urllib import request
from urllib.error import URLError

# 3rd-party

# self

# =============================================================================
# Globals
# =============================================================================

__all__ = []

# =============================================================================
# Functions
# =============================================================================

def socket_fd_open(socket_fd):
    """
    Create a TCP/IP socket object from a
    :meth:`socket.socket.detach` file descriptor.
    Uses :func:`socket.fromfd`.

    Parameters
    ---------
    socket_fd : fd
        File descriptor to build socket from.

    Returns
    ------
    socket : :mod:`socket`
    """

    # open new socket from fd
    sock = socket.fromfd(fd=socket_fd,
                         family=socket.AF_INET,
                         type=socket.SOCK_STREAM,
                         proto=socket.IPPROTO_TCP)
    return sock

def socket_fd_close(socket_fd):
    """
    Shutdown (FIN) and close a TCP/IP socket object from a
    :meth:`socket.socket.detach` file descriptor.

    Parameters
    ---------
    socket_fd : fd
        File descriptor for socket to close
    """

    sock = socket_fd_open(socket_fd)
    # fin the connection
    sock.shutdown(socket.SHUT_RDWR)
    # close the socket
    sock.close()

# =============================================================================
# Classes
# =============================================================================


class Patch(object):
    """
    Class that handles connecting to the patching server and downloading files
    from the patching server.

    Attributes
    ----------
    patch_url : str
        Base patch url for the current PoE version. This does not point to a
        specific, load-balanced server
    patch_cdn_url : str
        Load-balanced patching url including port for the current PoE version.
    sock_fd : fd
        Socket file descriptor for connection to patch server
    """

    _SERVER = 'pathofexile.com'
    _PORT = 12995
    # use patch proto 4
    _PROTO = b'\x01\x04'

    def __init__(self, master_server=_SERVER, master_port=_PORT):
        """
        Automatically fetches patching urls on class creation.

        .. note::

            Parameter shouldn't be required to be changed; if the servers change
            please create a pull request/issue on Github.

        Parameters
        ----------
        master_server : str
            Domain or IP address of the master patching server
        master_port : int
            Port to use when connecting to the master patching server
        """
        self._master_server = (master_server, master_port)
        self.update_patch_urls()

    def __del__(self):
        """
        Automatically close the patchserver connection and socket.
        """

        sock = socket_fd_open(self.sock_fd)
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            sock.close()
        except OSError:
            raise

    def update_patch_urls(self):
        """
        Updates the patch urls from the master server.

        Open a connection to the patchserver, get webroot details,
        detach from socket, and store socket file descriptor as :attr:`sock_fd`

        .. note::

            Recreate socket object later with: :func:`.socket_fd_open`

            When finished, destroy socket with: :func:`.socket_fd_close`.
            Equivalent is called in :meth:`.__del__`
        """
        with socket.socket(proto=socket.IPPROTO_TCP) as sock:
            sock.connect(self._master_server)
            sock.send(Patch._PROTO)
            data = io.BytesIO(sock.recv(1024))

            unknown = struct.unpack('B', data.read(1))[0]
            blank = struct.unpack('33s', data.read(33))[0]

            url_length = struct.unpack('B', data.read(1))[0]
            self.patch_url = data.read(url_length*2).decode('utf-16')

            blank = struct.unpack('B', data.read(1))[0]

            url2_length = struct.unpack('B', data.read(1))[0]
            self.patch_cdn_url = data.read(url2_length*2).decode('utf-16')

            # Close this later!
            self.sock_fd = sock.detach()

    def download(self, file_path, dst_dir=None, dst_file=None):
        """
        Downloads the file at the specified path from the patching server.

        Any intermediate directories for the write paths will be automatically
        created.

        Parameters
        ----------
        file_path : str
            path of the file relative to the content.ggpk root directory
        dst_dir : str
            Write the file to the specified directory.

            The target directory is seen as the root directory, thus the
            file will be written according to it's ``file_path``

            Mutually exclusive with the ``dst_file`` argument.
        dst_file : str
            Write the file to the specified location.

            Unlike dst_dir this will ignore any naming conventions from
            ``file_path``, so for example ``Data/Mods.dat`` could be written to
            ``C:/HelloWorld.txt``

            Mutually exclusive with the ``'dst_dir`` argument.

        Raises
        ------
        ValueError
            if neither dst_dir or dst_file is set
        ValueError
            if the HTTP status code is not 200 (and it wasn't raised by urllib)
        """
        if dst_dir:
            write_path = os.path.join(dst_dir, file_path)
        elif dst_file:
            write_path = dst_file
        else:
            raise ValueError('Either dst_dir or dst_file must be set')

        # Make any intermediate dirs to avoid errors
        os.makedirs(os.path.split(write_path)[0], exist_ok=True)

        # As per manual, writing should automatically find the optimal buffer
        with open(write_path, mode='wb') as f:
            f.write(self.download_raw(file_path))

    def download_raw(self, file_path):
        """
        Downloads the raw bytes.

        Parameters
        ----------
        file_path : str
            path of the file relative to the content.ggpk root directory

        Returns
        -------
        bytes
            the raw contents of the file in bytes

        Raises
        ------
        ValueError
            if the HTTP status code is not 200 (and it wasn't raised by urllib)
        """
        hosts = [self.patch_cdn_url, self.patch_url]
        for index, host in enumerate(hosts):
            try:
                with request.urlopen(
                    url="%s%s" % (host, file_path),
                ) as robj:
                    if robj.getcode() != 200:
                        raise ValueError('HTTP response code: %s' % robj.getcode())
                    return robj.read()
            except URLError as url_error:
                # try alternate patch url if connection refused
                if (not isinstance(url_error.reason, ConnectionRefusedError)
                    or not index < len(hosts)):
                    raise url_error

    @property
    def version(self):
        """
        Retrieves the game version from the url.

        Returns
        -------
        str
            The gama version in x.x.x.x format.

            The first 3 digits match the public known versions, the last is
            internal scheme for the a/b/c patches and hotfixes.
        """
        return self.patch_url.strip('/').rsplit('/', maxsplit=1)[-1]
