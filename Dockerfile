# Production image. NOT used inside Colab (Colab has no Docker daemon) — this is
# the deploy path documented in README.md and proven by CI building it.
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

COPY requirements.txt pyproject.toml ./
COPY src ./src
RUN pip install -r requirements.txt

COPY . .

# Build the index at image-build time so the container starts ready to serve.
RUN python scripts/generate_data.py && python scripts/ingest.py

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
