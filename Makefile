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

PY27?=python2.7
PIP?=pip
DEV_APPSERVER?=$(shell which dev_appserver.py)
GCLOUD?=gcloud

help:
	@echo 'Makefile for a google-cloud-python-on-gae  '
	@echo '                                           '
	@echo 'Usage:                                     '
	@echo '   make language-app  Run language app     '
	@echo '   make clean         Clean generated files'
	@echo '                                           '

language-app/lib: language-app/requirements.txt
	rm -fr language-app/lib
	cd language-app && \
	    $(PIP) install \
	        --target lib \
	        --requirement requirements.txt

language-app: language-app/lib language-app/app.yaml
	$(GCLOUD) components update
	cd language-app && \
	    $(PY27) $(DEV_APPSERVER) app.yaml

clean:
	rm -f \
	    language-app/*pyc
	rm -fr \
	    language-app/lib

.PHONY: help language-app clean
