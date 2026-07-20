FROM python:3.12-slim

# Unbuffered stdout so `docker logs` shows print() output in real time
# instead of only after the buffer fills or the process exits.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser


EXPOSE 5002
CMD ["gunicorn", "-b", "0.0.0.0:5002", "app:create_app()"]
