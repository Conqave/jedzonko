FROM python:3.14-slim-trixie AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential pkg-config libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/app
COPY pyproject.toml ./


FROM base AS tools

RUN pip install --no-cache-dir ".[dev]"
WORKDIR /src


FROM base AS runtime

RUN pip install --no-cache-dir ".[server]"
COPY . .

EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000"]
