FROM python:3.11-bookworm AS builder

ARG INCLUDE_EXAMPLES=false
ENV INCLUDE_EXAMPLES=${INCLUDE_EXAMPLES}

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Install libraries (pyaudio) required for the poetry build

RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y \
    build-essential \
    portaudio19-dev \
    libasound2-dev \
 && rm -rf /var/lib/apt/lists/*

RUN pip3 install poetry==1.7.1
WORKDIR /app
COPY pyproject.toml /app

# Install cached dependencies (with optionals)

RUN --mount=type=cache,target=/tmp/poetry_cache \
    set -eux; \
    OPTIONAL_INSTALLS=""; \
    if [ "$INCLUDE_EXAMPLES" = "true" ]; then OPTIONAL_INSTALLS="examples"; fi; \
    poetry install --no-root $(test -n "$OPTIONAL_INSTALLS" && echo "--with $OPTIONAL_INSTALLS")

FROM python:3.11-slim AS runner

COPY src /opt/streamvizzard/src
COPY --from=builder /app/.venv /opt/streamvizzard/.venv

# Install runtime libraries needed for pyaudio, OpenGL, etc.

RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y \
    libportaudio2 \
    libgl1 \
    libglib2.0-0 \
    libasound2 \
 && rm -rf /usr/share/doc/* /usr/share/man/* /usr/share/lintian/* /usr/share/locale/* /var/lib/apt/lists/*

# Prepare executable cli

RUN echo '#!/bin/bash\npython /opt/streamvizzard/src/cli.py "$@"' > /usr/local/bin/svcli && \
    chmod +x /usr/local/bin/svcli

# Finalize

ENV PATH="/opt/streamvizzard/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["/opt/streamvizzard/.venv/bin/python", "/opt/streamvizzard/src/main.py"]
