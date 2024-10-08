test:
	pytest cupyd/tests/ -v -ra

check-codestyle:
	flake8 --max-line-length 100
	black . --line-length 100 --check

style:
	flake8 --max-line-length 100
	black . --line-length 100
