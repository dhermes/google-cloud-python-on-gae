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

import _multiprocessing
import os
import subprocess
import sys

import boltons.tbutils
import flask


app = flask.Flask(__name__)


def code_block(*lines):
    html_lines = ['<pre>']
    for line in lines:
        html_lines.append(flask.escape(line))
    html_lines.append('</pre>')
    return '\n'.join(html_lines)


@app.route('/')
def main():
    return code_block(
        '>>> import sys',
        '>>> sys',
        repr(sys),
        '>>> sys.executable',
        repr(sys.executable),
        '>>> sys.prefix',
        repr(sys.prefix),
        '>>> getattr(sys, \'real_prefix\', None)',
        repr(getattr(sys, 'real_prefix', None)),
        '>>> import subprocess',
        '>>> subprocess',
        repr(subprocess),
        '>>> import _multiprocessing',
        '>>> _multiprocessing',
        repr(_multiprocessing),
        '>>> import os',
        '>>> os',
        repr(os),
        '>>> os.devnull',
        repr(os.devnull),
        '>>> os.path.exists(os.devnull)',
        repr(os.path.exists(os.devnull)),
    )


@app.route('/import')
def do_import_live():
    try:
        from google.cloud import language

        return code_block(
            '>>> from google.cloud import language',
            '>>> language',
            repr(language),
        )
    except:
        exc_info = boltons.tbutils.ExceptionInfo.from_current()
        exc_str = exc_info.get_formatted()
        return code_block(exc_str)
