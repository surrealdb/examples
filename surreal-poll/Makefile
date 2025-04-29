# Include .env file
-include .env
# Make sure variables are exported
export

apply:
	@echo "Applying schema"
	$(eval MODIFIED_DB_HOST := $(subst wss://,https://,${VITE_DB_HOST}))
	for schema in $(wildcard schema/*.surql); do \
		echo "Applying schema: $$schema"; \
		surreal import $$schema --namespace surrealdb --database pollwebapp --endpoint ${MODIFIED_DB_HOST} --token ${DB_TOKEN};\
	done