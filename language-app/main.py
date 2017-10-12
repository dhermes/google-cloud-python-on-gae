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
import functools
import imp
import io
import os
import subprocess
import sys
import unittest

import boltons.tbutils
import flask
import google.auth
import google.protobuf
try:
    import grpc
    grpc_info = None
except ImportError as exc:
    grpc = None
    grpc_info = sys.exc_info()
import pkg_resources
import setuptools
import six

from google.appengine.api import app_identity


app = flask.Flask(__name__)

MAIN_HTML = """\
<html>
  <ul>
    <li><a href="/info">Environment Info</a></li>
    <li><a href="/auth-check">Auth Info</a></li>
    <li><a href="/import">Package Import Check</a></li>
    <li><a href="/unit-tests">Unit Test Output</a></li>
    <li><a href="/system-tests">System Test Output</a></li>
  </ul>
</html>
"""


def code_block(*lines):
    html_lines = ['<pre>']
    for line in lines:
        html_lines.append(flask.escape(line))
    html_lines.append('</pre>')
    return '\n'.join(html_lines)


class PrettyErrors(object):

    def __init__(self, callable_):
        self.callable_ = callable_
        functools.update_wrapper(self, self.callable_)

    def __call__(self, *args, **kwargs):
        try:
            return self.callable_(*args, **kwargs)
        except:
            exc_info = boltons.tbutils.ExceptionInfo.from_current()
            exc_str = exc_info.get_formatted()
            return code_block(exc_str)


@app.route('/')
def main():
    return MAIN_HTML


@app.route('/info')
@PrettyErrors
def info():
    if grpc is None:
        exc_info = boltons.tbutils.ExceptionInfo.from_exc_info(*grpc_info)
        grpc_msg = exc_info.get_formatted()
    else:
        try:
            dist = pkg_resources.get_distribution('grpcio')
            grpc_msg = '\n'.join([
                '>>> grpc',
                repr(grpc),
                '>>> dist = pkg_resources.get_distribution(\'grpcio\')',
                '>>> dist',
                repr(dist),
            ])
        except pkg_resources.DistributionNotFound:
            exc_info = boltons.tbutils.ExceptionInfo.from_current()
            grpc_msg = '\n'.join([
                '>>> grpc',
                repr(grpc),
                '>>> dist = pkg_resources.get_distribution(\'grpcio\')',
                exc_info.get_formatted(),
            ])

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
        '>>> import six',
        '>>> six',
        repr(six),
        '>>> six.__version__',
        repr(six.__version__),
        '>>> import setuptools',
        '>>> setuptools',
        repr(setuptools),
        '>>> import pkg_resources',
        '>>> pkg_resources',
        repr(pkg_resources),
        '>>> import google.protobuf',
        '>>> google.protobuf',
        repr(google.protobuf),
        '>>> google.protobuf.__version__',
        repr(google.protobuf.__version__),
        '>>> import grpc',
        grpc_msg,
    )


def load_module(path):
    dirname, basename = os.path.split(path)
    mod_name, extension = os.path.splitext(basename)
    assert extension == '.py'
    file_obj, filename, details = imp.find_module(mod_name, [dirname])
    return imp.load_module(
        mod_name, file_obj, filename, details)


@app.route('/unit-tests')
@PrettyErrors
def unit_tests():
    test_mods = []
    for dirpath, _, filenames in os.walk('unit-tests'):
        for filename in filenames:
            if not filename.endswith('.py'):
                continue
            if filename == '__init__.py':
                continue
            test_mods.append(os.path.join(dirpath, filename))

    mod_objs = [load_module(path) for path in test_mods]
    suite = unittest.TestSuite()
    for mod_obj in mod_objs:
        tests = unittest.defaultTestLoader.loadTestsFromModule(mod_obj)
        suite.addTest(tests)

    stream = io.BytesIO()
    test_result = unittest.TextTestRunner(
        stream=stream, verbosity=2).run(suite)

    return code_block(
        '>>> import imp',
        '>>> import os',
        '>>> import unittest',
        '>>>',
        '>>> test_mods = []',
        '>>> for dirpath, _, filenames in os.walk(\'unit-tests\'):',
        '...     for filename in filenames:',
        '...         if not filename.endswith(\'.py\'):',
        '...             continue',
        '...         if filename == \'__init__.py\':',
        '...             continue',
        '...         test_mods.append(os.path.join(dirpath, filename))',
        '...',
        '>>> for path in test_mods:',
        '...     print(path)',
        '...',
        '\n'.join(test_mods),
        '>>>',
        '>>> def load_module(path):',
        '...     dirname, basename = os.path.split(path)',
        '...     mod_name, extension = os.path.splitext(basename)',
        '...     assert extension == \'.py\'',
        '...     file_obj, filename, details = imp.find_module(mod_name, [dirname])',
        '...     return imp.load_module(',
        '...         mod_name, file_obj, filename, details)',
        '...',
        '>>>',
        '>>> mod_objs = [load_module(path) for path in test_mods]',
        '>>>',
        '>>> suite = unittest.TestSuite()',
        '>>> for mod_obj in mod_objs:',
        '...     tests = unittest.defaultTestLoader.loadTestsFromModule(mod_obj)',
        '...     suite.addTest(tests)',
        '...',
        '>>> unittest.TextTestRunner(verbosity=2).run(suite)',
        stream.getvalue(),
    )


@app.route('/import')
@PrettyErrors
def import_():
    from google.cloud import language

    return code_block(
        '>>> from google.cloud import language',
        '>>> language',
        repr(language),
    )


@app.route('/auth-check')
@PrettyErrors
def auth_check():
    credentials, project = google.auth.default()
    key_name, signature = app_identity.sign_blob(b'abc')
    scope = 'https://www.googleapis.com/auth/userinfo.email'
    token, expiry = app_identity.get_access_token(scope)
    return code_block(
        '>>> import google.auth',
        '>>> credentials, project = google.auth.default()',
        '>>> credentials',
        repr(credentials),
        '>>> project',
        repr(project),
        '>>> credentials.__dict__',
        repr(credentials.__dict__),
        '>>> from google.appengine.api import app_identity',
        '>>> app_identity',
        repr(app_identity),
        # ALSO: get_access_token_uncached
        # (scopes, service_account_id=None)
        '>>> scope = \'https://www.googleapis.com/auth/userinfo.email\'',
        '>>> token, expiry = app_identity.get_access_token(scope)',
        '>>> token',
        repr(token[:6] + b'...'),
        '>>> expiry',
        repr(expiry),
        '>>> app_identity.get_application_id()',
        repr(app_identity.get_application_id()),
        '>>> app_identity.get_default_gcs_bucket_name()',
        repr(app_identity.get_default_gcs_bucket_name()),
        '>>> app_identity.get_default_version_hostname()',
        repr(app_identity.get_default_version_hostname()),
        '>>> app_identity.get_public_certificates()',
        repr(app_identity.get_public_certificates()),
        '>>> app_identity.get_service_account_name()',
        repr(app_identity.get_service_account_name()),
        '>>> key_name, signature = app_identity.sign_blob(b\'abc\')',
        '>>> key_name',
        repr(key_name),
        '>>> signature',
        repr(signature[:16] + b'...'),
    )


@app.route('/system-tests')
@PrettyErrors
def system_tests():
    # NOTE: We intentionally import at run-time.
    from google.cloud import language_v1
    from google.cloud.language_v1 import enums

    scopes = language_v1.LanguageServiceClient._ALL_SCOPES
    credentials, _ = google.auth.default(scopes=scopes)
    client = language_v1.LanguageServiceClient(credentials=credentials)
    content = 'Hello, world!'
    type_ = enums.Document.Type.PLAIN_TEXT
    document = {'content': content, 'type': type_}
    response = client.analyze_sentiment(document)

    return code_block(
        '>>> from google.cloud import language_v1',
        '>>> from google.cloud.language_v1 import enums',
        '>>>',
        '>>> scopes = language_v1.LanguageServiceClient._ALL_SCOPES',
        '>>> scopes',
        repr(scopes),
        '>>> credentials, _ = google.auth.default(scopes=scopes)',
        '>>> credentials',
        repr(credentials),
        '>>>',
        '>>> client = language_v1.LanguageServiceClient(credentials=credentials)',
        '>>> client',
        repr(client),
        '>>>',
        '>>> content = \'Hello, world!\'',
        '>>> type_ = enums.Document.Type.PLAIN_TEXT',
        '>>> document = {\'content\': content, \'type\': type_}',
        '>>> response = client.analyze_sentiment(document)',
        '>>>',
        '>>> response',
        repr(response)
    )
