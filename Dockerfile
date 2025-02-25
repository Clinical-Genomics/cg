FROM docker.io/library/python:3.11-slim-bullseye

ENV CG_SQL_DATABASE_URI="sqlite:///:memory:"
ENV CG_SECRET_KEY="key"

ENV LIMS_HOST="mocklims.scilifelab.se"
ENV LIMS_USERNAME="limsadmin"
ENV LIMS_PASSWORD="limsadminpassword"

ENV MAIL_CONTAINER_URI="http://127.0.0.1:port/container"

ENV GOOGLE_OAUTH_CLIENT_ID="1"
ENV GOOGLE_OAUTH_CLIENT_SECRET="1"

ENV TRAILBLAZER_HOST="host"
ENV TRAILBLAZER_SERVICE_ACCOUNT="service_account"
ENV TRAILBLAZER_SERVICE_ACCOUNT_AUTH_FILE="auth_file"


WORKDIR /home/src/app
COPY pyproject.toml poetry.lock gunicorn.conf.py README.md ./

RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY cg ./cg

RUN poetry install --no-interaction --no-ansi

CMD gunicorn \
    --config gunicorn.conf.py \
    cg.server.auto:app