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

import imp
import sys

from google.appengine.ext import vendor


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


def workaround_bad_subprocess_stub():
    """Unload the SDK/Rutime's subprocess module (it's empty).

    Load our stub which provides a dummy function that's
    """
    sys.modules.pop('subprocess', None)
    file_obj, filename, details = imp.find_module('subprocess', ['stubs'])
    sys.modules['subprocess'] = imp.load_module(
        'subprocess', file_obj, filename, details)


def all_updates():
    vendor.add('lib')
    stub_replace('subprocess')
    stub_replace('_multiprocessing')


all_updates()
