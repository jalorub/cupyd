test:
	pytest cupyd/tests/ -v -ra --cov=cupyd/core

check-codestyle:
	flake8
	black . --check

style:
	flake8
	black .

check-types:
	mypy cupyd