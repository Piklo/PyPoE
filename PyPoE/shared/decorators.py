"""
Decorators

Overview
-------------------------------------------------------------------------------

+----------+------------------------------------------------------------------+
| Path     | PyPoE/shared/decorators.py                                       |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                                                             |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
-------------------------------------------------------------------------------

Utility decorators.

Agreement
-------------------------------------------------------------------------------

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import functools
import warnings

# 3rd-party

# self

# =============================================================================
# Globals
# =============================================================================

__all__ = ['deprecated', 'doc']


# =============================================================================
# Classes
# =============================================================================


class DeprecationDecorator(object):
    """
    Decorator for setting functions as deprecated.

    Applying this decorate will cause DeprecationWarnings to be emitted on
    function call and also adds the DEPRECATED

    """
    _default_message = 'Use of {func} is deprecated and will be removed in' \
                       ' PyPoE {version}'
    _default_doc_message = 'DEPRECATED. Will be removed in PyPoE {version}'

    def __init__(self, message=None, doc_message=None, version=None):
        """
        Settings for the decorator.

        Both message and doc_message argument accept the following message
        formatter strings:
        +---------+------------------------------------------------------------+
        | version | Version the function will be removed in                    |
        +---------+------------------------------------------------------------+

        Additionally, message accepts the following message formatter string:
        +------+---------------------------------------------------------------+
        | func | The name of the function                                      |
        +------+---------------------------------------------------------------+

        :param str message: Warning message on each call.
        :param str doc_message: Message to append to docstring
        :param str version: Version the function will be removed in
        """
        self.message = message or self._default_message
        self.doc_message = doc_message or self._default_doc_message
        self.version = version or 'unknown version'

    def __call__(self, function):
        message_kwargs = {
            'version': self.version,
        }

        if hasattr(function, '__func__'):
            function = function.__func__

        if function.__doc__ is None:
            function.__doc__ = self.doc_message.format(**message_kwargs)
        else:
            function.__doc__ = self.doc_message.format(**message_kwargs) + \
                               '\n' + function.__doc__

        @functools.wraps(function)
        def deprecated_function(*args, **kwargs):
            warnings.warn(
                self.message.format(
                    func=function.__name__,
                    **message_kwargs
                ), DeprecationWarning, stacklevel=2,
            )

            return function(*args, **kwargs)

        return deprecated_function


class DocStringDecorator(object):
    """
    Decorator for docstring modifications.

    It will modify the doc string of a given object, but will not actually
    wrap it. This is done so it can work with any type of object.
    """

    def __init__(self, prepend='', append='', doc=None):
        """
        :param prepend: String to prepend to the docstring
        :type prepend: str

        :param append: String to append to the docstring
        :type append: str

        :param doc: Docstring to use. If an object that doesn't inherit from str
        is supplied, use object's docstring.
        :type doc: None, str or object
        """
        self.append = append
        self.prepend = prepend
        self.doc = doc

    def __call__(self, function):
        if self.doc is None:
            docs = function.__doc__
        elif isinstance(self.doc, str):
            docs = self.doc
        else:
            docs = self.doc.__doc__

        if docs is None:
            docs = ''

        docs = self.prepend + docs + self.append

        if docs != '':
            if hasattr(function, '__func__'):
                function.__func__.__doc__ = docs
            else:
                function.__doc__ = docs

        return function


# =============================================================================
# Functions
# =============================================================================


def _make_callable(cls):
    @functools.wraps(cls)
    def call(*args, **kwargs):
        if len(args) == 1 and callable(args[0]):
            return cls()(args[0])
        else:
            return cls(*args, **kwargs)

    return call


# =============================================================================
# Init
# =============================================================================

deprecated = _make_callable(DeprecationDecorator)
doc = _make_callable(DocStringDecorator)
