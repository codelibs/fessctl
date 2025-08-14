FROM python:3.13-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml ./
COPY src/ src/
RUN uv pip install . --system --target /build/python

COPY README.md ./

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN addgroup --system fessctl && adduser --system --group fessctl

WORKDIR /app

COPY --from=builder /build/python /app/

RUN chown -R fessctl:fessctl /app

USER fessctl

ENTRYPOINT ["python", "-m", "fessctl.cli"]
