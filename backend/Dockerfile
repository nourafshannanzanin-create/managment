# syntax=docker/dockerfile:1.7

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Keep this layer stable. Changing PIP_* args/env below must NOT invalidate apt cache.
# BuildKit apt cache also keeps .deb files across rebuilds when the layer does invalidate.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    set -eux; \
    rm -f /etc/apt/apt.conf.d/docker-clean; \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        libfreetype6 \
        libjpeg62-turbo \
        libopenjp2-7 \
        libtiff6 \
        zlib1g; \
    if ! apt-get install -y --no-install-recommends libpng16-16t64; then \
      apt-get install -y --no-install-recommends libpng16-16; \
    fi

# Override at build time without busting the apt layer above:
#   --build-arg PIP_INDEX_URL=https://pypi.org/simple/ --build-arg PIP_TRUSTED_HOST=pypi.org
ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ARG PIP_TRUSTED_HOST=mirrors.aliyun.com

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_RETRIES=10 \
    PIP_INDEX_URL=${PIP_INDEX_URL} \
    PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST}

COPY requirements.txt .
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
CMD ["gunicorn", "-c", "gunicorn.conf.py", "config.wsgi:application"]
