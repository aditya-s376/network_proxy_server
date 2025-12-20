PYTHON = python3
SERVER_SCRIPT = src/server.py
LOG_FILE = proxy.log
CONFIG_DIR = config
TEST_SCRIPT = tests/test_proxy.sh

all: run

run:
	@echo "Starting Proxy Server.."
	$(PYTHON) $(SERVER_SCRIPT)

clean:
	@echo "Cleaning up..."
	rm -f $(LOG_FILE)
	rm -rf __pycache__ src/__pycache__
	@echo "Clean complete."

test:
	@echo "Running automated test suite..."
	@chmod +x $(TEST_SCRIPT)
	./$(TEST_SCRIPT)

init:
	@mkdir -p $(CONFIG_DIR)
	@touch $(CONFIG_DIR)/blocked_domains.txt
	@echo "Project initialized. Add blocked domains to $(CONFIG_DIR)/blocked_domains.txt"

.PHONY: all run clean test init
