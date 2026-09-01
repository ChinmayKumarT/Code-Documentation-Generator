FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# -w 1 is required, not a tuning choice: reports are written to temp/<uuid>/
# by one worker and fetched by a later /download request. Extra workers would
# serve 404s for reports they did not generate.
CMD gunicorn -w 1 -b 0.0.0.0:$PORT --timeout 120 app:app
