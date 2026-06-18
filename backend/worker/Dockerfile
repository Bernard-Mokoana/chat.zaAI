FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ /app/backend/


WORKDIR /app/backend/worker

ENV PYTHONPATH=/app

RUN addgroup --system worker && adduser --system --ingroup worker worker
RUN chown -R worker:worker /app
USER worker

CMD ["python", "main.py"]
