FROM python:3.8-slim

RUN apt-get update -q \
 && apt-get install -y -q \
     gcc \
     libssl-dev \
     curl \
     postgresql-client \
     gunicorn3
RUN useradd _gunicorn --no-create-home --user-group

COPY . /app/
WORKDIR /app

RUN chmod +x "/app/docker_run.sh" \
  && pip install pipenv \
  && pipenv install --dev --deploy --system --ignore-pipfile

ENTRYPOINT ["/app/docker_run.sh"]

