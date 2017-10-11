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

"""Helper to convert a JSON key file into a  PEM PKCS#1 key."""

from __future__ import print_function

import argparse
import os
import json
import subprocess
import sys

try:
    import py
except ImportError:
    py = None


ENV_VAR = 'GOOGLE_APPLICATION_CREDENTIALS'


def _require_env():
    json_filename = os.environ.get(ENV_VAR)
    if json_filename is None:
        msg = '{} is unset'.format(ENV_VAR)
        print(msg, file=sys.stderr)
        sys.exit(1)

    return json_filename


def _require_file(json_filename):
    if not os.path.isfile(json_filename):
        msg = '{}={} is not a file.'.format(ENV_VAR, json_filename)
        print(msg, file=sys.stderr)
        sys.exit(1)


def _require_json(json_filename):
    with open(json_filename, 'r') as file_obj:
        try:
            return json.load(file_obj)
        except:
            msg = '{}={} does not contain valid JSON.'.format(
                ENV_VAR, json_filename)
            print(msg, file=sys.stderr)
            sys.exit(1)


def _require_private_key(key_json):
    pkcs8_pem = key_json.get('private_key')
    if pkcs8_pem is None:
        msg = '``private_key`` missing in JSON key file'
        print(msg, file=sys.stderr)
        sys.exit(1)

    return pkcs8_pem


def _require_email(key_json):
    client_email = key_json.get('client_email')
    if client_email is None:
        msg = '``client_email`` missing in JSON key file'
        print(msg, file=sys.stderr)
        sys.exit(1)

    return client_email


def get_key_json():
    json_filename = _require_env()
    _require_file(json_filename)
    key_json = _require_json(json_filename)
    return key_json, json_filename


def _require_py():
    if py is None:
        msg = 'py (https://pypi.org/project/py/) must be installed.'
        print(msg, file=sys.stderr)
        sys.exit(1)


def _require_openssl():
    """Check that ``openssl`` is on the PATH.

    Assumes :func:`_require_py` has been checked.
    """
    if py.path.local.sysfind('openssl') is None:
        msg = '``openssl`` command line tool must be installed.'
        print(msg, file=sys.stderr)
        sys.exit(1)


def _pkcs8_filename(pkcs8_pem, base):
    """Create / check a PKCS#8 file.

    Exits with 1 if the file already exists and differs from
    ``pkcs8_pem``. If the file does not exists, creates it with
    ``pkcs8_pem`` as contents and sets permissions to 0400.

    Args:
        pkcs8_pem (str): The contents to be stored (or checked).
        base (str): The base file path (without extension).

    Returns:
        str: The filename that was checked / created.
    """
    pkcs8_filename = '{}-PKCS8.pem'.format(base)
    if os.path.exists(pkcs8_filename):
        with open(pkcs8_filename, 'r') as file_obj:
            contents = file_obj.read()

        if contents != pkcs8_pem:
            msg = 'PKCS#8 file {} already exists.'.format(pkcs8_filename)
            print(msg, file=sys.stderr)
            sys.exit(1)
    else:
        with open(pkcs8_filename, 'w') as file_obj:
            file_obj.write(pkcs8_pem)
        # Protect the file from being read by other users..
        os.chmod(pkcs8_filename, 0o400)

    return pkcs8_filename


def _pkcs1_verify(pkcs8_filename, pkcs1_filename):
    """Verify the contents of an existing PKCS#1 file.

    Does so by using ``openssl rsa`` to print to stdout and
    then checking against contents.

    Exits with 1 if:

    * The ``openssl`` command fails
    * The ``pkcs1_filename`` contents differ from what was produced
      by ``openssl``

    Args:
        pkcs8_filename (str): The PKCS#8 file to be converted.
        pkcs1_filename (str): The PKCS#1 file to check against.
    """
    cmd = (
        'openssl',
        'rsa',
        '-in',
        pkcs8_filename,
    )
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return_code = process.wait()

    if return_code != 0:
        msg = 'Failed checking contents of {} against openssl.'.format(
            pkcs1_filename)
        print(msg, file=sys.stderr)
        sys.exit(1)

    cmd_output = process.stdout.read().decode('utf-8')
    with open(pkcs1_filename, 'r') as file_obj:
        expected_contents = file_obj.read()

    if cmd_output != expected_contents:
        msg = 'PKCS#1 file {} already exists.'.format(pkcs1_filename)
        print(msg, file=sys.stderr)
        sys.exit(1)


def _pkcs1_create(pkcs8_filename, pkcs1_filename):
    """Create a existing PKCS#1 file from a PKCS#8 file.

    Does so by using ``openssl rsa -in * -out *``.

    Exits with 1 if the ``openssl`` command fails.

    Args:
        pkcs8_filename (str): The PKCS#8 file to be converted.
        pkcs1_filename (str): The PKCS#1 file to be created.
    """
    cmd = (
        'openssl',
        'rsa',
        '-in',
        pkcs8_filename,
        '-out',
        pkcs1_filename,
    )
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return_code = process.wait()
    if return_code != 0:
        msg = 'Failed to convert {} to {} with openssl.'.format(
            pkcs8_filename, pkcs1_filename)
        print(msg, file=sys.stderr)
        sys.exit(1)


def convert_key(pkcs8_pem, json_filename):
    _require_py()
    _require_openssl()

    base, _ = os.path.splitext(json_filename)
    pkcs8_filename = _pkcs8_filename(pkcs8_pem, base)

    pkcs1_filename = '{}-PKCS1.pem'.format(base)
    if os.path.exists(pkcs1_filename):
        _pkcs1_verify(pkcs8_filename, pkcs1_filename)
    else:
        _pkcs1_create(pkcs8_filename, pkcs1_filename)

    return pkcs1_filename


def get_args():
    parser = argparse.ArgumentParser(
        description='Convert a JSON keyfile to dev_appserver values.')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--email', action='store_true',
        help='Requests that the email address be returned.')
    pkcs1_help = (
        'Requests that a filename for the converted PKCS#1 file be returned.')
    group.add_argument(
        '--pkcs1', action='store_true', help=pkcs1_help)
    group.add_argument(
        '--clean', action='store_true',
        help='Clean up any created files.')

    return parser.parse_args()


def _clean(json_filename):
    base, _ = os.path.splitext(json_filename)
    pkcs1_filename = '{}-PKCS1.pem'.format(base)
    pkcs8_filename = '{}-PKCS8.pem'.format(base)

    for filename in (pkcs1_filename, pkcs8_filename):
        try:
            os.remove(filename)
            print('Removed {}'.format(filename))
        except OSError:
            pass


def main():
    args = get_args()

    key_json, json_filename = get_key_json()
    if args.email:
        print(_require_email(key_json))
    elif args.pkcs1:
        pkcs8_pem = _require_private_key(key_json)
        pkcs1_filename = convert_key(pkcs8_pem, json_filename)
        print(pkcs1_filename)
    elif args.clean:
        _clean(json_filename)
    else:
        raise RuntimeError('Options not set', args)


if __name__ == '__main__':
    main()
