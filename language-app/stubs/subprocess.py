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

"""Stub subprocess module.

For some reason, when ``multiprocessing.util`` calls::

    from subprocess import _args_from_interpreter_flags

there is an import failue.

We entirely skip the ``subprocess`` module by making it a
stub here that shadows the version in the standard library.
"""


def _args_from_interpreter_flags(*args, **kwargs):
    print(
        '_args_from_interpreter_flags stub called with {!r} {!r}'.format(
            args, kwargs))
    return None
