test:
	pytest tests/

test_coverage:
	pytest --cov=. tests/

lint:
	flake8 .
