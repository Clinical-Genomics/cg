FROM docker.io/library/python:3.11-slim-bullseye

ENV GUNICORN_WORKERS=1
ENV GUNICORN_THREADS=1
ENV GUNICORN_BIND="0.0.0.0:8000"
ENV GUNICORN_TIMEOUT=400


ENV CG_SQL_DATABASE_URI="sqlite:///:memory:"
ENV CG_SECRET_KEY="key"

ENV LIMS_HOST="mocklims.scilifelab.se"
ENV LIMS_USERNAME="limsadmin"
ENV LIMS_PASSWORD="limsadminpassword"

ENV MAIL_CONTAINER_URI="http://127.0.0.1:port/container"

ENV OSTICKET_EMAIL="support@system.email"
ENV OSTICKET_API_KEY=None
ENV OSTICKET_DOMAIN=None
ENV OSTICKET_TIMEOUT="1"

ENV GOOGLE_OAUTH_CLIENT_ID="1"
ENV GOOGLE_OAUTH_CLIENT_SECRET="1"

ENV TRAILBLAZER_HOST="host"
ENV TRAILBLAZER_SERVICE_ACCOUNT="service_account"
ENV TRAILBLAZER_SERVICE_ACCOUNT_AUTH_FILE="auth_file"


WORKDIR /home/src/app
COPY pyproject.toml poetry.lock ./ 

RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY cg ./cg

CMD gunicorn \
    --workers=$GUNICORN_WORKERS \
    --bind=$GUNICORN_BIND  \
    --threads=$GUNICORN_THREADS \
    --timeout=$GUNICORN_TIMEOUT \
    --proxy-protocol \
    --forwarded-allow-ips="10.0.2.100,127.0.0.1" \
    --log-syslog \
    --access-logfile - \
    --error-logfile - \
    --log-level="debug" \
    cg.server.auto:app
