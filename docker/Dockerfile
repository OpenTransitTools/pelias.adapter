# ============================
# 1. Builder stage
# ============================
FROM python:3.12-slim AS builder

ENV POETRY_VERSION=2.2.1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

ENV PATH="/root/.local/bin:${POETRY_HOME}/bin:${PATH}"

WORKDIR /pelias_adapter

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -

COPY ./ /pelias_adapter/

COPY ./docker/entrypoint.sh /pelias_adapter/entrypoint.sh

# Make sure entrypoint is executable while still root
RUN chmod +x /pelias_adapter/entrypoint.sh


RUN poetry install --no-interaction --no-ansi --without dev


# ============================
# 2. Runtime stage
# ============================
FROM python:3.12-slim AS runtime

WORKDIR /pelias_adapter
ENV POETRY_VERSION=2.2.1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

ENV PATH="/root/.local/bin:${POETRY_HOME}/bin:${PATH}"

# Copy dependencies and app from builder
COPY --from=builder /usr/local /usr/local
COPY --from=builder /pelias_adapter /pelias_adapter

RUN chmod +x /pelias_adapter/entrypoint.sh
RUN ls -la /pelias_adapter

RUN useradd -m pelias_user && chown -R pelias_user:pelias_user /pelias_adapter
USER pelias_user


RUN rm -rf /pelias_adapter/docker

# Expose FastAPI port
EXPOSE 8000

ENTRYPOINT ["/pelias_adapter/entrypoint.sh"]
