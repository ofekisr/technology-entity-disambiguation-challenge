FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    IDX_SNAPSHOT=/app/index.sqlite

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install . && idx build

CMD ["idx", "resolve", "AWS"]
