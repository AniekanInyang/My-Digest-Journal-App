FROM python:3.11-slim

WORKDIR /app

# Create /data directory for SQLite database persistence
RUN mkdir -p /data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app && chown -R appuser:appuser /data
USER appuser

EXPOSE 8080

# Railway sets $PORT environment variable, default to 8080 if not set
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8080} --timeout 120 --workers 2 --worker-class sync app:app"]
