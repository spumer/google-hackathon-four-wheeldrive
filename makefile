.PHONY: help

# if BIN not provided, try to detect the binary from the environment
PYTHON_INSTALL := $(shell python3 -c 'import sys;print(sys.executable)')
BIN ?= $(shell [ -e .venv/bin ] && echo '.venv/bin' || dirname $(PYTHON_INSTALL))/
CODE = ./app

help:  ## This help dialog.
	@IFS=$$'\n' ; \
	help_lines=(`fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##/:/'`); \
	printf "%-15s %s\n" "target" "help" ; \
	printf "%-15s %s\n" "------" "----" ; \
	for help_line in $${help_lines[@]}; do \
		IFS=$$':' ; \
		help_split=($$help_line) ; \
		help_command=`echo $${help_split[0]} | sed -e 's/^ *//' -e 's/ *$$//'` ; \
		help_info=`echo $${help_split[2]} | sed -e 's/^ *//' -e 's/ *$$//'` ; \
		printf '\033[36m'; \
		printf "%-15s %s" $$help_command ; \
		printf '\033[0m'; \
		printf "%s\n" $$help_info; \
	done

init:  ## Установка virtualenv и зависимостей
	python3 -m venv .venv
	chmod +x .venv/bin/activate
	source .venv/bin/activate
	pip3 install -r requirements-dev.txt

test:  ## Запуск тестов
	$(BIN)pytest $(args)

lint:  ## Проверка кода (linting)
	$(BIN)flake8 --jobs 4 --statistics --show-source $(CODE) $(CODE)/tests
	$(BIN)pytest --dead-fixtures --dup-fixtures

pretty:  ## Автоформатирование согласно code-style
	$(BIN)pre-commit run --all-files
	$(BIN)isort --apply --recursive $(CODE)
	$(BIN)autopep8 --in-place --recursive --max-line-length=120 $(CODE)
	$(BIN)unify --in-place --recursive $(CODE)

ci-check: lint  ## Проверка кода для CI
	app-tests-entrypoint $(args)

_run-pre-commit:
	$(BIN)pre-commit run --all-files

precommit_install:  ## Установка pre-commit хука с проверками code-style и мелкими авто-справлениеями
	echo '#!/bin/sh' >  .git/hooks/pre-commit
	echo "exec make lint _run-pre-commit BIN=$(BIN)" >> .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
