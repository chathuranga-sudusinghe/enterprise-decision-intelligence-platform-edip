FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

COPY app/ ./app/
COPY pipelines/runtime_paths.py ./pipelines/
COPY pipelines/models/favorita_bundle_inference.py ./pipelines/models/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir . && \
    rm -rf build *.egg-info

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
