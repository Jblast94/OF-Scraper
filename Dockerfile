# syntax=docker/dockerfile:1.7

# Stage 1: Build the application artifact
FROM python:3.10-slim AS builder

ARG BUILD_VERSION
WORKDIR /app

# Install only essential build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy all source files first to ensure version determination works
COPY . .

# Install build dependencies
RUN \
    if [ -n "$BUILD_VERSION" ]; then \
      VERSION="$BUILD_VERSION"; \
    else \
      VERSION="0.0.0+docker"; \
    fi && \
    export HATCH_VCS_PRETEND_VERSION=$VERSION && \
    echo "Build OF-SCRAPER with ${VERSION}" && \
    pip install --no-cache-dir hatch && \
    uv lock && \
    uv sync && \
    hatch build

# Stage 2: Create the final, minimal production image
FROM python:3.10-slim

WORKDIR /app

ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gosu \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && python -m venv ${VIRTUAL_ENV}

# Create non-root user
RUN groupadd -r ofscraper && useradd -r -g ofscraper -u 1001 ofscraper

# Define environment variables
ENV OF_API_KEY=""
ENV OF_DOWNLOAD_PATH="/app/data"

COPY --from=builder /app/dist/*.whl .
RUN pip install --no-cache-dir *.whl && rm *.whl

COPY --chmod=755 ./scripts/entry/. /usr/local/bin/entry/

# Create necessary directories and set ownership
RUN mkdir -p /app/data /app/logs /home/ofscraper/.config/ofscraper && \
    chown -R ofscraper:ofscraper /app /home/ofscraper

# Run as root and let entrypoint handle privilege dropping
USER root
ENTRYPOINT ["/usr/local/bin/entry/entrypoint.sh"]
CMD ["ofscraper"]

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1