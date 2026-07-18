FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser


EXPOSE 5004
CMD ["gunicorn", "-b", "0.0.0.0:5004", "app:create_app()"]
