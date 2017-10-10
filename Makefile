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
	rm -fr \
	    language-app/lib

.PHONY: help language-app clean
