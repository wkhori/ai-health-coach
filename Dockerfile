FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -e .
RUN python -m src.db.seed

ENV PORT=8000
EXPOSE 8000
CMD uvicorn src.main:app --host 0.0.0.0 --port $PORT
