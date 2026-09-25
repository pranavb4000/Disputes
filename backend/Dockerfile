# Backend image: FastAPI API + worker (same image, different command).
# All base images and package indexes can point at the bank's Artifactory via build args.
ARG PYTHON_IMAGE=python:3.12-slim
FROM ${PYTHON_IMAGE}

# Optional: pip index on Artifactory, e.g. https://artifactory.bank/artifactory/api/pypi/pypi-remote/simple
ARG PIP_INDEX_URL=""
ARG PIP_TRUSTED_HOST=""

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Optional: corporate root CA certificates (*.crt) so pip/requests trust internal TLS (Artifactory, proxies).
COPY certs/ /usr/local/share/ca-certificates/bank/
RUN if ls /usr/local/share/ca-certificates/bank/*.crt >/dev/null 2>&1; then update-ca-certificates; fi
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    PIP_CERT=/etc/ssl/certs/ca-certificates.crt

COPY requirements.txt requirements-ldap.txt ./
RUN set -eu; \
    [ -n "$PIP_INDEX_URL" ] && export PIP_INDEX_URL || unset PIP_INDEX_URL; \
    [ -n "$PIP_TRUSTED_HOST" ] && export PIP_TRUSTED_HOST || unset PIP_TRUSTED_HOST; \
    pip install -r requirements.txt

COPY . .
RUN groupadd --system app && useradd --system --gid app --home-dir /app app && chown -R app:app /app
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=4).status==200 else 1)"

# --proxy-headers: trust X-Forwarded-For from Nginx (FORWARDED_ALLOW_IPS limits which proxies are trusted).
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips=${FORWARDED_ALLOW_IPS:-127.0.0.1}"]
