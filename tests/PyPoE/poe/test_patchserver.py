"""
Tests for PyPoE.poe.patchserver

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | tests/PyPoE/poe/test_patchserver.py                              |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                                                             |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Tests for patchserver.py

Agreement
===============================================================================

See PyPoE/LICENSE

TODO
===============================================================================
Testing on live data is difficult, since we can't verify it was downloaded
correctly as the contents of the files may change. Perhaps find a good
candidate for testing.
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import os
import re
from urllib.error import HTTPError
from socket import socket

# 3rd-party
import pytest

# self
from PyPoE.poe import patchserver

# =============================================================================
# Setup
# =============================================================================

_TEST_FILE = 'Data/Wordlists.dat'
_re_version = re.compile(r'[\d]+\.[\d]+\.[\d]+\.[\d]+', re.UNICODE)

# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope='module')
def patch():
    return patchserver.Patch()

@pytest.fixture(scope='function')
def patch_temp():
    return patchserver.Patch()

# =============================================================================
# Tests
# =============================================================================

def test_socket_fd_open_close(patch_temp):
    test_sock_from_fd = patchserver.socket_fd_open(patch_temp.sock_fd)
    assert isinstance(test_sock_from_fd, socket)
    sock_fd = test_sock_from_fd.detach()
    patchserver.socket_fd_close(sock_fd)

class TestPatch(object):
    def test_dst_file(self, patch, tmpdir):
        patch.download(
            file_path=_TEST_FILE,
            dst_file=os.path.join(str(tmpdir), 'test.txt'),
        )

    def test_dst_dir(self, patch, tmpdir):
        patch.download(
            file_path=_TEST_FILE,
            dst_dir=str(tmpdir),
        )

    def test_missing_dst_error(self, patch):
        with pytest.raises(ValueError):
            patch.download(
                file_path=_TEST_FILE,
            )

    def test_file_not_found(self, patch):
        with pytest.raises(HTTPError):
            patch.download_raw(
                file_path='THIS_SHOULD_NOT_EXIST.FILE',
            )

    def test_version(self, patch):
        assert _re_version.match(patch.version) is not None, 'patch.version ' \
            'result is expected to match the x.x.x.x format'

