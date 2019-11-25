VIRTUALENV=$(shell which virtualenv)

.PHONY: dev-init
dev-init:
	test -d venv || $(VIRTUALENV) --python=python3 venv
	. venv/bin/activate; pip install -Ur requirements.txt
