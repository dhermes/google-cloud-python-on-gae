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
DEV_APPSERVER?=$(shell which dev_appserver.py)
GCLOUD?=gcloud
GAE_EMAIL=$(shell $(PY27) convert_key.py --email)
GAE_KEY=$(shell $(PY27) convert_key.py --pkcs1)

help:
	@echo 'Makefile for a google-cloud-python-on-gae'
	@echo ''
	@echo 'Usage:'
	@echo '   make language-app-run       Run language app'
	@echo '   make language-app-deploy    Deploy language app'
	@echo '   make clean                  Clean generated files'
	@echo ''

language-app/lib: language-app/requirements.txt
	rm -fr language-app/lib
	cd language-app && \
	    $(PY27) -m pip install \
	        --target lib \
	        --requirement requirements.txt
	# Icky ``grpcio`` hacks:
	cd language-app && rm -fr lib/grpc
	cd language-app && rm -fr lib/grpcio-1.4.0.dist-info
	cd language-app/lib && \
	    ln -s ../grpcio-1.0.0.dist-info grpcio-1.0.0.dist-info

language-app/clean-env:
	cd language-app && \
	    $(PY27) -m virtualenv --python=$(PY27) clean-env
	cd language-app && \
	    clean-env/bin/pip install \
	        --requirement env-requirements.txt

language-app-run: language-app/lib language-app/clean-env language-app/app.yaml
	# $(GCLOUD) components update
	cd language-app && \
	    clean-env/bin/python2.7 $(DEV_APPSERVER) app.yaml \
	        --appidentity_email_address $(GAE_EMAIL) \
	        --appidentity_private_key_path $(GAE_KEY)

language-app-deploy: language-app/lib language-app/app.yaml
	cd language-app && \
	    $(GCLOUD) app deploy app.yaml

clean:
	rm -f \
	    language-app/*pyc \
	    language-app/stubs/*pyc
	rm -fr \
	    language-app/clean-env \
	    language-app/lib
	$(PY27) convert_key.py --clean

.PHONY: help language-app-run language-app-deploy clean
