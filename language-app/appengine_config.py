# Copyright 2017 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import __builtin__
import _pyio
import errno
import imp
import os
import sys

from google.appengine.ext import vendor
try:
    from google.appengine.tools import devappserver2
    from google.appengine.tools.devappserver2.python.runtime import stubs
except ImportError:
    devappserver2 = None
    stubs = None


BUILTIN_OPEN = __builtin__.open
PYIO_OPEN = _pyio.open


def stub_replace(mod_name):
    """Replace a module from the SDK/Rutime.

    Replaces it with a stub provided in ``stubs/``.

    Used for

    * ``subprocess``: Needed by concurrency primitives. We don't actually
       use these primitives in most of our libraries, but we do use the
       interface.
    * ``_multiprocessing``: Imported un-protected in ``__init__.py`` for
      ``multiprocessing`` but not provided in GAE SDK.
    """
    sys.modules.pop(mod_name, None)
    file_obj, filename, details = imp.find_module(mod_name, ['stubs'])
    sys.modules[mod_name] = imp.load_module(
        mod_name, file_obj, filename, details)


def _open_avoid_devnull(filename, mode='r', **kwargs):
    """Replacement for the ``open`` builtin.

    Helper for :func:`patch_open_for_devnull`.

    Works exactly the same as ``open`` unless ``filename`` is ``os.devnull``
    (e.g. ``'/dev/null'``). In that case, just opens a dummy file (the
    ``requirements.txt`` in the current directory).
    """
    if filename == os.devnull:
        mode = 'r'
        filename = 'requirements.txt'

    return BUILTIN_OPEN(filename, mode, **kwargs)


def _io_open_avoid_devnull(filename, mode='r', **kwargs):
    """Replacement for the ``_pyio.open`` helper.

    Helper for :func:`patch_open_for_devnull`.

    Works exactly the same as ``_pyio.open`` unless ``filename`` is
    ``os.devnull`` (e.g. ``'/dev/null'``). In that case, just opens a
    dummy file (the ``requirements.txt`` in the current directory).
    """
    if filename == os.devnull:
        mode = 'r'
        filename = 'requirements.txt'

    return PYIO_OPEN(filename, mode, **kwargs)


def patch_open_for_devnull():
    """Patch the ``open`` builtin to avoid opening ``os.devnull``.

    On **import** ``dill`` calls::

        f = open(os.devnull, 'rb', buffering=0)
        FileType = type(f)
        f.close()

    so it has a type it can re-use. This is a problem on GAE, where the
    file pointed to by ``os.devnull`` cannot be accessed.
    """
    __builtin__.open = _open_avoid_devnull
    _pyio.open = _io_open_avoid_devnull



def _fake_file_init(self, filename, mode='r', buffering=-1, **kwargs):
    """Replacement for constructor in ``FakeFile`` class.

    Helper for :func:`patch_dev_fake_file`.

    Used as a stub because ``FakeFile`` incorrectly uses ``bufsize``.
    """
    if stubs is None:
        raise RuntimeError(
            'Expected stubs to import successfully on dev_appserver')

    if mode not in stubs.FakeFile.ALLOWED_MODES:
        raise IOError(errno.EROFS, 'Read-only file system', filename)

    visible = stubs.FakeFile.is_file_accessible(filename)
    if visible != stubs.FakeFile.Visibility.OK:
        stubs.log_access_check_fail(filename, visible)
        raise IOError(errno.EACCES, 'file not accessible', filename)

    super(stubs.FakeFile, self).__init__(
        filename, mode, buffering, **kwargs)


def patch_dev_fake_file():
    """Workaround for the ``devappserver`` file stub.

    .. _docs: https://docs.python.org/2/library/functions.html#file

    The ``FakeFile`` class (only present on ``dev``, not prod) incorrectly
    thinks that the third argument to file is ``bufsize``. The Python `docs`_
    note that this is ``buffering`` and ``dill`` (correctly) uses this as
    a keyword argument when determining the ``FileType``.

    See :func:`patch_open_for_devnull` for details on why
    ``FileType`` is used.
    """
    if devappserver2 is None:
        # NOTE: This means we are running in productions
        return

    stubs.FakeFile.__init__ = _fake_file_init



def clear_imports(mod_name):
    """Remove cached imports for a module.

    We may want to do this if we provide an over-ride in ``lib/`` for an
    out-of-date package that comes with the SDK (or accidentally comes
    in the environment running the ``dev_appserver``).
    """
    for key in sys.modules.keys():
        if key.startswith(mod_name):
            del sys.modules[key]


def all_updates():
    vendor.add('lib')
    stub_replace('subprocess')
    stub_replace('_multiprocessing')
    patch_open_for_devnull()
    patch_dev_fake_file()
    clear_imports('pkg_resources')
    clear_imports('six')


all_updates()
