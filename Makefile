############
# COMMANDS #
############

lint: ## flake8 linting and black and isort code style for scripts
	 @echo ">>> lint scripts"
	 @echo ">>> black files"
	 black .
	 @echo ">>> isort files"
	 isort .
	 @echo ">>> flake8 files"
	 flake8 .
	 @echo ">>> mypy files"
	 mypy

# misc
help: ## show help on available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
