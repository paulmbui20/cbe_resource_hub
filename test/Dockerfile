ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim-bookworm AS test
ARG PYTHON_VERSION

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps (curl useful for debugging inside container)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY ../requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install testing dependencies
RUN pip install \
    pytest \
    pytest-django \
    pytest-cov \
    pytest-xdist \
    coverage \
    factory-boy \
    faker \
    bc


# Copy application code into test image
COPY .. .
RUN chmod +x test/test.sh


# Create directories for coverage reports
RUN mkdir -p /app/coverage /app/htmlcov


# Default command
CMD ["./test/test.sh"]
