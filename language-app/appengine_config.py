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
import imp
import os
import sys

from google.appengine.ext import vendor


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

    Helper for :func:`workaround_dill_opening_os_devnull`.

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

    Helper for :func:`workaround_dill_opening_os_devnull`.

    Works exactly the same as ``_pyio.open`` unless ``filename`` is
    ``os.devnull`` (e.g. ``'/dev/null'``). In that case, just opens a
    dummy file (the ``requirements.txt`` in the current directory).
    """
    if filename == os.devnull:
        mode = 'r'
        filename = 'requirements.txt'

    return PYIO_OPEN(filename, mode, **kwargs)


def workaround_dill_opening_os_devnull():
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


def all_updates():
    vendor.add('lib')
    stub_replace('subprocess')
    stub_replace('_multiprocessing')
    workaround_dill_opening_os_devnull()


all_updates()
