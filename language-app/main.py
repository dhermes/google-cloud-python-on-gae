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

import sys

import boltons.tbutils
import flask


app = flask.Flask(__name__)


@app.route('/')
def main():
    import _multiprocessing
    import subprocess
    return '\n'.join([
        '<pre>',
        '>>> import sys',
        '>>> sys',
        flask.escape(repr(sys)),
        '>>> sys.executable',
        flask.escape(repr(sys.executable)),
        '>>> sys.prefix',
        flask.escape(repr(sys.prefix)),
        '>>> getattr(sys, \'real_prefix\', None)',
        flask.escape(repr(getattr(sys, 'real_prefix', None))),
        '>>> import subprocess',
        '>>> subprocess',
        flask.escape(repr(subprocess)),
        '>>> import _multiprocessing',
        '>>> _multiprocessing',
        flask.escape(repr(_multiprocessing)),
        '</pre>',
    ])


@app.route('/import')
def do_import_live():
    try:
        from google.cloud import language

        return '\n'.join([
            '<pre>',
            '>>> from google.cloud import language',
            '>>> language',
            flask.escape(repr(language)),
            '</pre>',
        ])
    except:
        exc_info = boltons.tbutils.ExceptionInfo.from_current()
        exc_str = exc_info.get_formatted()
        return '\n'.join([
            '<pre>',
            flask.escape(exc_str),
            '</pre>',
        ])
