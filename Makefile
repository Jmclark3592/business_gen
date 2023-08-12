.PHONY: test
test:
	pytest .

.PHONY: format
format:
	black .

.PHONY: run
run:
	python3 business_gen.py