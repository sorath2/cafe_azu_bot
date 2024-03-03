WORKDIR = .

style:
	poetry run black -S -l 79 $(WORKDIR)
	poetry run isort $(WORKDIR)
	poetry run flake8 $(WORKDIR)
