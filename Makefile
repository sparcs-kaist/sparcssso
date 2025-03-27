setup_local_cert:
	cd local-dev && ./setup-cert.sh

# mysql 5.6이 arm64 이미지가 없어 amd64 고정이 필요
compose_up: setup_local_cert
	cd local-dev && DOCKER_DEFAULT_PLATFORM=linux/amd64 docker compose up -d

test:
	pytest tests/

test_coverage:
	pytest --cov=. tests/

lint:
	flake8 .
