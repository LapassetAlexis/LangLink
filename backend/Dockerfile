# syntax=docker/dockerfile:1

# --- Étape 1 : construction des wheels (aucun compilateur dans l'image finale)
FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir --upgrade pip \
    && pip wheel --no-deps --wheel-dir /wheels .

# --- Étape 2 : exécution
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Un compte réel : un UID sans entrée passwd casse OpenSSH, cron et certains outils
# (cf. github-auth, « No user exists for uid »). On ne reproduit pas ce piège ici.
RUN groupadd --gid 1001 langlink \
    && useradd --uid 1001 --gid 1001 --create-home --shell /usr/sbin/nologin langlink

WORKDIR /app
COPY --from=builder /wheels /wheels
COPY pyproject.toml ./
RUN pip install /wheels/*.whl && rm -rf /wheels

COPY --chown=langlink:langlink app ./app
RUN mkdir -p /data/uploads && chown -R langlink:langlink /data

USER langlink
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
