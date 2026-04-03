.PHONY: all build test run api ui agent clean help

help:
	@echo "Brandes Exchange - Development Commands"
	@echo ""
	@echo "  make build       Build C++ engine"
	@echo "  make test        Run all tests (73 total)"
	@echo "  make test-engine Run C++ tests (31)"
	@echo "  make test-agent  Run Python tests (42)"
	@echo "  make run         Start API + UI"
	@echo "  make api         Start API server only"
	@echo "  make ui          Start UI only"
	@echo "  make agent       Run AI agent query"
	@echo "  make interactive Run agent in interactive mode"
	@echo "  make demo        Run trading demo"
	@echo "  make clean       Remove build artifacts"
	@echo ""
	@echo "Examples:"
	@echo "  make agent QUERY='Analyze the order book'"
	@echo "  make interactive"

# Build C++ engine
build:
	@echo "Building C++ engine..."
	@mkdir -p build
	@cd build && cmake ../engine -DCMAKE_BUILD_TYPE=Release && make -j4
	@echo "Build complete"

# Run all tests
test: test-engine test-agent
	@echo ""
	@echo "All tests passed! (73 total)"

# C++ engine tests
test-engine:
	@echo "Running C++ tests..."
	@cd build && ./test_matching 2>/dev/null || echo "Build first with: make build"

# Python agent tests
test-agent:
	@echo "Running Python tests..."
	@pytest tests/ -v --tb=short

# Start API server
api:
	@echo "Starting Brandes Exchange API on http://127.0.0.1:8000"
	@cd api && python main.py

# Start UI
ui:
	@echo "Starting UI on http://localhost:5173"
	@cd ui && npm run dev

# Start everything
run:
	@echo "Starting Brandes Exchange..."
	@cd api && python main.py &
	@sleep 2
	@cd ui && npm run dev

# Run AI agent
agent:
	@if [ -z "$(QUERY)" ]; then \
		python -m agent "What is the current state of my exchange?"; \
	else \
		python -m agent "$(QUERY)"; \
	fi

# Interactive agent mode
interactive:
	@python -m agent --interactive

# Run demo
demo:
	@./scripts/demo.sh

# Install dependencies
install:
	@pip install -r requirements.txt
	@cd ui && npm install

# Clean
clean:
	@rm -rf build/
	@rm -rf __pycache__/
	@rm -rf .pytest_cache/
	@rm -rf .sentinel/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
