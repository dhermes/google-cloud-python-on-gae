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

-   Using a custom Python 2.7 `virtualenv` with the same (very old)
    versions provided as [libraries][6] in App Engine (set up via
    [`env-requirements.txt`][7]).
-   Had to [patch][12] the constructor for
    `google.appengine.tools.devappserver2.python.runtime.stubs.FakeFile`,
    it does not match the [builtin `file`][13] (uses `bufsize` instead
    of `buffering` as keyword). As of `gcloud 175.0.0`:

    ```
    $ cd ~/google-cloud-sdk/platform/google_appengine/google/appengine/
    $ cd tools/devappserver2/python/runtime/
    $ cat stubs.py | grep -n -B 10 -A 13 'def __init__.*filename'
    265-      if FakeFile._skip_files.match(relative_filename):
    266-        visibility = FakeFile.Visibility.SKIP_BLOCK
    267-      elif FakeFile._static_files.match(relative_filename):
    268-        visibility = FakeFile.Visibility.STATIC_BLOCK
    269-
    270-    with FakeFile._availability_cache_lock:
    271-      FakeFile._availability_cache[fixed_filename] = (
    272-          visibility == FakeFile.Visibility.OK)
    273-    return visibility
    274-
    275:  def __init__(self, filename, mode='r', bufsize=-1, **kwargs):
    276-    """Initializer. See file built-in documentation."""
    277-    if mode not in FakeFile.ALLOWED_MODES:
    278-      raise IOError(errno.EROFS, 'Read-only file system', filename)
    279-
    280-    visible = FakeFile.is_file_accessible(filename)
    281-    if visible != FakeFile.Visibility.OK:
    282-      log_access_check_fail(filename, visible)
    283-      raise IOError(errno.EACCES, 'file not accessible', filename)
    284-
    285-    super(FakeFile, self).__init__(filename, mode, bufsize, **kwargs)
    286-
    287-
    288-class RestrictedPathFunction(object):
    ```
-   Patch builtin `open` so that it can handle opening `/dev/null`. This
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

-   Some [libraries][6] in prod over-ride any vendored in equivalent (see e.g.
    `google.protobuf` in [`/info`][9]). This **does not** occur in dev.
-   `grpc` does not come with a `dist-info` directory.
-   Had to make sure to run `python2.7 $(which dev_appserver.py)` rather than
    just `dev_appservery.py` on a system where the bare `python` is not 2.7
    (though this is in violation of [PEP 394][10], so I deserve it).
-   Had to [HTML-escape][11] a hyphen in my `app.yaml` config (i.e.
    `clean&#2D;env/` instead of `clean-env/`). This actually blocks the
    `devappserver` from even starting.
-   Uploading the app includes **926 files** (at 41.2 MB)! This is because
    `lib/` is so **very big**.
-   On App Engine (prod) gRPC stalled the entire request for 30s and
    the page just came back with 500. Then after an hour or so, it just
    magically started working. [@jonparrott][14] experienced the same
    heisen-bug:

    ```
    Traceback (most recent call last):
      File "/base/data/home/runtimes/python27_experiment/python27_lib/versions/1/google/appengine/runtime/wsgi.py", line 267, in Handle
        result = handler(dict(self._environ), self._StartResponse)
      File "/base/data/home/apps/s~{APP}/{VERSION}/lib/flask/app.py", line 1997, in __call__
        return self.wsgi_app(environ, start_response)
      File "/base/data/home/apps/s~{APP}/{VERSION}/lib/flask/app.py", line 1982, in wsgi_app
        response = self.full_dispatch_request()
      File "/base/data/home/apps/s~{APP}/{VERSION}/lib/flask/app.py", line 1612, in full_dispatch_request
        rv = self.dispatch_request()
      File "/base/data/home/apps/s~{APP}/{VERSION}/lib/flask/app.py", line 1598, in dispatch_request
        return self.view_functions[rule.endpoint](**req.view_args)
      File "/base/data/home/apps/s~{APP}/{VERSION}/main.py", line 47, in index
        snippets.quickstart_add_data_one()
      File "/base/data/home/apps/s~{APP}/{VERSION}/snippets.py", line 38, in quickstart_add_data_one
        u'born': 1815
      File "/base/data/home/apps/s~{APP}/{VERSION}/lib/google/cloud/firestore_v1beta1/document.py", line 224, in set
        write_results = batch.commit()
      File "/base/data/home/apps/s~{APP}/{VERSION}/lib/google/cloud/firestore_v1beta1/batch.py", line 135, in commit
        transaction=None, options=self._client._call_options)
      File "/base/data/home/apps/s~{APP}/{VERSION}/lib/google/cloud/firestore_v1beta1/gapic/firestore_client.py", line 851, in commit
        return self._commit(request, options)
      File "/base/data/home/apps/s~{APP}/{VERSION}/lib/google/gax/api_callable.py", line 452, in inner
        return api_caller(api_call, this_settings, request)
      File "/base/data/home/apps/s~{APP}/{VERSION}/lib/google/gax/api_callable.py", line 438, in base_caller
        return api_call(*args)
      File "/base/data/home/apps/s~{APP}/{VERSION}/lib/google/gax/api_callable.py", line 376, in inner
        return a_func(*args, **kwargs)
      File "/base/data/home/apps/s~{APP}/{VERSION}/lib/google/gax/retry.py", line 68, in inner
        return a_func(*updated_args, **kwargs)
      File "/base/data/home/runtimes/python27_experiment/python27_lib/versions/third_party/grpcio-1.0.0/grpc/_channel.py", line 488, in __call__
        state, deadline, = self._blocking(request, timeout, metadata, credentials)
      File "/base/data/home/runtimes/python27_experiment/python27_lib/versions/third_party/grpcio-1.0.0/grpc/_channel.py", line 484, in _blocking
        _handle_event(completion_queue.poll(), state, self._response_deserializer)
      File "/base/data/home/runtimes/python27_experiment/python27_lib/versions/third_party/grpcio-1.0.0/grpc/_channel.py", line 144, in _handle_event
        state.due.remove(operation_type)
    DeadlineExceededError: The overall deadline for responding to the HTTP request was exceeded.
    ```

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
[12]: https://github.com/dhermes/google-cloud-python-on-gae/blob/a7b450a3428087e96db45885eaff08f7f2963f60/language-app/appengine_config.py#L128-L145
[13]: https://docs.python.org/2/library/functions.html#file
[14]: https://github.com/jonparrott
