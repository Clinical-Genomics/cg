FROM python:3.7-slim

ENV GUNICORN_WORKERS=4
ENV GUNICORN_TREADS=4
ENV GUNICORN_BIND="0.0.0.0:5000"
ENV GUNICORN_TIMEOUT=400

WORKDIR /home/src/app
COPY . /home/src/app

RUN pip install -r requirements.txt
RUN pip install -e .


ENTRYPOINT ["gunicorn",  "cg.server.auto:app"]
CMD ["--workers=$GUNICORN_WORKERS", "--bind=$GUNICORN_BIND", "--threads=$GUNICORN_TREADS", "--timeout=$GUNICORN_TIMEOUT"]
