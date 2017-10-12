# `google-cloud-python` on Google App Engine

Experiments getting [`google-cloud-python`][1] working on
[Google App Engine][2] (Python).

## `google-cloud-language`

I used an [old trick][3] to actually [run unit tests][5] by
collection them directly form imported unit test modules.

I wanted to gather all unit test modules the [same way][4]
we do for `datastore` doctests (via `pkgutil.iter_modules`).
But it turns out this only works for the imported modules.

Getting this to work on prod and dev took a number of workarounds:

### Dev

- Using a custom Python 2.7 `virtualenv` with the same (very old)
  versions provided as [libraries][6] in App Engine (set up via
  [`env-requirements.txt`][7]).
- Had to patch the constructor for
  `google.appengine.tools.devappserver2.python.runtime.stubs.FakeFile`,
  it does not match the builtin `file`.
- Patch builtin `open` so that it can handle opening `/dev/null`. This
  is because `dill` (a dependency of `google-gax`) uses `open` to
  alias the builtin `file` type (it's not so easy on Python 3).
  We will be dropping `dill` in the future (it is a more extreme
  version of `pickle`, it's not a great design choice to use object
  serialization).

### Prod

- Patch `_pyio.open` so that it can handle opening `/dev/null`.

### Both

- Having a meticulously pinned [`requirements.txt`][8] to set up vendored
  `lib/` (this is not a `grpc` / `google-cloud-language` workaround, it's
  standard).
- Removing `grpc` and `grpcio-1.4.0.dist-info` from vendored `lib/`
  so that we don't conflict with the environment.
- Adding a fake `grpcio-1.0.0.dist-info` to vendored `lib/` so that the
  distribution info is available. (It is needed for unit tests.)
- Had to "place" stubs `appengine_config.py` for standard library modules:
  `subprocess` (needed by ??), `_multiprocessing` (needed by ??) and
  `ctypes` (needed by `setuptools`, if not stubbed, the dev server won't
  even start).
- Had to clear existing imports from `sys.modules` in `appengine_config.py`
  so that our vendored packages could take precedence. This is true for
  `six`, `setuptools`, `pkg_resources` (from `setuptools`) and
  `google.protobuf`.

There are still some frustrating issues:

- The [libraries][6] in prod over-ride any vendored in equivalent (see e.g.
  `google.protobuf` in [`/info`][9]). This **does not** occur in dev.
- `grpc` does not come with a `dist-info` directory.
- Had to make sure to run `python2.7 $(which dev_appserver.py)` rather than
  just `dev_appservery.py` on a system where the bare `python` is not 2.7
  (though this is in violation of [PEP 394][10], so I deserve it).
- Had to [HTML-escape][11] a hyphen in my `app.yaml` config (i.e.
  `clean&#2D;env/` instead of `clean-env/`). This actually blocks the
  `devappserver` from even starting.

[1]: https://github.com/GoogleCloudPlatform/google-cloud-python
[2]: https://cloud.google.com/appengine/docs/python/
[3]: https://github.com/GoogleCloudPlatform/google-cloud-python/blob/8b9dda27d9da51276ccf7ffaad82e165d5a16450/system_tests/run_system_test.py#L78
[4]: https://github.com/GoogleCloudPlatform/google-cloud-python/blob/ce7afe633a32b0fbd021bc50db022d508acc851b/datastore/tests/doctests.py#L48
[5]: https://precise-truck-742.appspot.com/unit-tests
[6]: https://cloud.google.com/appengine/docs/standard/python/tools/built-in-libraries-27
[7]: https://github.com/dhermes/google-cloud-python-on-gae/blob/master/language-app/env-requirements.txt
[8]: https://github.com/dhermes/google-cloud-python-on-gae/blob/master/language-app/requirements.txt
[9]: https://precise-truck-742.appspot.com/info
[10]: https://www.python.org/dev/peps/pep-0394/
[11]: https://github.com/dhermes/google-cloud-python-on-gae/issues/1
