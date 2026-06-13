# Convenience targets. Colab uses the pip path directly (see NOTEBOOK_GUIDE.md);
# these are for local/dev/CI.
.PHONY: setup data ingest serve test eval lint clean

setup:        ## Install deps + this package (editable)
	pip install -r requirements.txt

data:         ## Generate synthetic data into data/
	python scripts/generate_data.py

ingest:       ## Build the retrieval index (+ embedding cache) from data/
	python scripts/ingest.py

serve:        ## Run the API locally on :8000
	uvicorn app.main:app --reload --port 8000

test:         ## Run the test suite (mock LLM, no network)
	LLM_MODE=mock pytest

eval:         ## Run the offline eval harness and print the metrics table
	LLM_MODE=mock python -m app.eval.run_eval

lint:         ## Lint + import sort check
	ruff check src tests scripts

clean:
	rm -rf .pytest_cache .ruff_cache **/__pycache__ data/index
