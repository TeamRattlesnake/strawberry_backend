all:
	@echo "commands: format, lint, install_dependencies"

format:
	autopep8 --in-place src/*.py --max-line-length 80

lint:
	pylint src/*.py --extension-pkg-whitelist='pydantic' --disable='logging-fstring-interpolation'

install_dependencies:
	sudo pip install -r requirements.txt
