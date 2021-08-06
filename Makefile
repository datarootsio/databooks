############
# COMMANDS #
############

lint: ## flake8 linting and black and isort code style for scripts
	 @echo ">>> lint scripts"
	 @echo ">>> black files"
	 black nbhelp tests
	 @echo ">>> isort files"
	 isort nbhelp tests
	 @echo ">>> linting files"
	 flake8 nbhelp tests

# misc
help: ## show help on available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
