.DEFAULT_GOAL := help


.PHONY: help
# See <https://gist.github.com/klmr/575726c7e05d8780505a> for explanation
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: server-start
server-start: ## Start FastAPI server
	uvicorn src.surrealdb_rag.app:app --reload

.PHONY: pycache-remove
pycache-remove:
	find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf

.PHONY: dsstore-remove
dsstore-remove:
	find . | grep -E ".DS_Store" | xargs rm -rf

.PHONY: cleanup
cleanup: pycache-remove dsstore-remove 