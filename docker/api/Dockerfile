FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml .
COPY src ./src
RUN pip install --no-cache-dir --no-deps .

RUN python -m velov.data --out data/velov_history.csv \
 && python -m velov.train --data data/velov_history.csv --out models/

FROM python:3.12-slim AS runtime

WORKDIR /app

RUN useradd --system --uid 1001 app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY --from=builder --chown=app:app /app/models ./models

ENV MODEL_DIR=/app/models \
    PYTHONUNBUFFERED=1

USER app

EXPOSE 8069

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8069/ready', timeout=2).status == 200 else 1)"

CMD ["uvicorn", "velov.api.main:app", "--host", "0.0.0.0", "--port", "8069"]
