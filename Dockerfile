FROM python:3.11.8

# create user for celery workers to run on
RUN groupadd -g 1000 appuser \
    && useradd -r -u 1000 -g appuser appuser \
    && mkdir -p /app \
    && chown -R appuser:appuser /app

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
RUN uv pip install --system .

COPY . .