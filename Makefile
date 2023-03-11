all:
	@echo "commands: format, lint, install_dependencies run_debug run"

format:
	autopep8 --in-place src/*.py --max-line-length 80

lint:
	pylint src/*.py --extension-pkg-whitelist='pydantic'

install_dependencies:
	sudo pip install -r requirements.txt

run_debug:
	uvicorn --app-dir src --host 0.0.0.0 --port 14565 server:app

run:
	sudo docker-compose up -d --build
