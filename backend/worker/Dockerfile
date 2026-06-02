FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir psycopg2-binary

COPY backend/ /app/backend/

WORKDIR /app/backend/worker

ENV PYTHONPATH=/app

CMD ["python", "main.py"]