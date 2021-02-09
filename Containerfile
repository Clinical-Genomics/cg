FROM python:3.7-slim

ENV GUNICORN_WORKERS=1
ENV GUNICORN_TREADS=1
ENV GUNICORN_BIND="0.0.0.0:5000"
ENV GUNICORN_TIMEOUT=400

ENV SECRET_KEY="thisIsNotASafeKey"
ENV TEMPLATES_AUTO_RELOAD=True

ENV SQLALCHEMY_DATABASE_URI="sqlite:///:memory:"
ENV CG_SQL_DATABASE_URI="sqlite:///:memory:"
ENV FLASK_DEBUG=True

ENV CG_ENABLE_ADMIN=1

ENV LIMS_HOST="mocklims.scilifelab.se"
ENV LIMS_USERNAME="limsadmin"
ENV LIMS_PASSWORD="limsadminpassword"

ENV OSTICKET_API_KEY=None
ENV OSTICKET_DOMAIN=None

ENV GOOGLE_OAUTH_CLIENT_ID=1
ENV GOOGLE_OAUTH_CLIENT_SECRET=1

EXPOSE 5000
WORKDIR /home/src/app
COPY . /home/src/app


RUN pip install -r requirements.txt
RUN pip install -e .

CMD gunicorn \
    --workers=$GUNICORN_WORKERS \
    --bind=$GUNICORN_BIND  \
    --threads=$GUNICORN_TREADS \
    --timeout=$GUNICORN_TIMEOUT \
    cg.server.auto:app
