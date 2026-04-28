# Stage 1: Export requirements from Poetry
FROM python:3.12-slim-bookworm AS builder

RUN pip install --no-cache-dir poetry==2.2.1 poetry-plugin-export==1.9.0

WORKDIR /build
COPY pyproject.toml poetry.lock* ./

RUN poetry export -f requirements.txt --without-hashes --without dev -o requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim-bookworm

# Install system dependencies for PDF processing and MIME detection
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        poppler-utils \
        libmagic1 \
        curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies (pip resolves transitive deps properly)
COPY --from=builder /build/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app
COPY app/ ./app/
RUN mkdir -p /app/data

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
