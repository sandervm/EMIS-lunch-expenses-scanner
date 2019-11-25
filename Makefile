VIRTUALENV=$(shell which virtualenv)

.PHONY: dev-init
dev-init:
	test -d venv || $(VIRTUALENV) --python=python3 venv
	. venv/bin/activate; pip install -Ur requirements.txt
	echo "\e[31mPlease supply your EMIS API key:\e[0m"
	@read apikey; echo $$apikey | tr -d '\n' > emis.key
