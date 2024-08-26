.DEFAULT_GOAL := help
HOST := 0.0.0.0
PORT := 8080
ADDRESS := $(HOST):$(PORT)

.PHONY: help
# See <https://gist.github.com/klmr/575726c7e05d8780505a> for explanation
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: install
install: ## Install dependencies
	pip install -e .
	pip install ruff==0.3.0

.PHONY: fmt
fmt: ## Format code
	ruff format .
	ruff check . --fix

.PHONY: surreal-start
surreal-start: ## Start SurrealDB
	surreal start --auth --user root --pass root --strict --log debug file://data/srdb.db --bind $(ADDRESS) -A

.PHONY: surreal-init
surreal-init: ## Initialise SurrealDB to populate with data
	surreal import --conn http://$(ADDRESS) --user root --pass root --ns test --db test schema/define_ns_db.surql
	surreal import --conn http://$(ADDRESS) --user root --pass root --ns test --db test schema/chats.surql

.PHONY: surreal-remove
surreal-remove: ## Remove the SurealDB database
	rm -rf data/srdb.db

.PHONY: surreal-sql
surreal-sql: ## Surreal SQL
	surreal sql -e ws://$(ADDRESS) --hide-welcome --pretty --json -u root -p root

.PHONY: server-start
server-start: ## Start FastAPI server
	uvicorn src.surrealdb_openai.__main__:app --reload

.PHONY: pycache-remove
pycache-remove:
	find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf

.PHONY: dsstore-remove
dsstore-remove:
	find . | grep -E ".DS_Store" | xargs rm -rf

.PHONY: ruff-remove
ruff-remove:
	find . | grep -E ".ruff_cache" | xargs rm -rf

.PHONY: cleanup
cleanup: pycache-remove dsstore-remove ruff-remove ## Cleanup residual files.
