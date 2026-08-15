# syntax=docker/dockerfile:1.7

FROM python:3.12-slim

# Primary index can be overridden at build time, e.g.:
#   --build-arg PIP_INDEX_URL=https://pypi.org/simple/ --build-arg PIP_TRUSTED_HOST=pypi.org
ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ARG PIP_TRUSTED_HOST=mirrors.aliyun.com

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_RETRIES=10 \
    PIP_INDEX_URL=${PIP_INDEX_URL} \
    PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST}

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libfreetype6 \
        libjpeg62-turbo-dev \
        libopenjp2-7 \
        libpng-dev \
        libtiff6 \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Slow/unstable mirrors often time out on large wheels (Pillow/PyMuPDF).
# Retry across several indexes before failing the build.
RUN --mount=type=cache,target=/root/.cache/pip \
    set -eu; \
    try_install() { \
      index_url="$1"; \
      trusted_host="$2"; \
      echo "pip install via ${index_url}"; \
      pip install \
        --default-timeout=300 \
        --retries=10 \
        --index-url "${index_url}" \
        --trusted-host "${trusted_host}" \
        -r requirements.txt; \
    }; \
    try_install "${PIP_INDEX_URL}" "${PIP_TRUSTED_HOST}" \
      || try_install "https://pypi.tuna.tsinghua.edu.cn/simple" "pypi.tuna.tsinghua.edu.cn" \
      || try_install "https://mirrors.cloud.tencent.com/pypi/simple" "mirrors.cloud.tencent.com" \
      || try_install "https://pypi.org/simple" "pypi.org"

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY . .

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "180", "--access-logfile", "-", "--error-logfile", "-"]
