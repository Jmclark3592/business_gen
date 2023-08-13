.PHONY: test
test:
	pytest .

.PHONY: format
format:
	black .

.PHONY: run
run:
	export ENVIRONMENT=local && python3 business_gen.py

.PHONY: docker-build
docker-build:
	docker build -t business-gen .

.PHONY: docker-run
docker-run:
	docker run -t business-gen .