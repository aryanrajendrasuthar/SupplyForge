FROM python:3.12-slim

# Unbuffered stdout so `docker logs` shows print() output in real time
# instead of only after the buffer fills or the process exits.
ENV PYTHONUNBUFFERED=1

# Build context is the repo root (not this directory) so shared/auth can be
# copied in alongside the service — the monorepo layout is preserved inside
# the image so requirements.txt's `-e ../../shared/auth` resolves exactly
# the same way it does in local dev.
WORKDIR /repo

COPY shared/auth shared/auth
COPY services/inventory-service services/inventory-service

WORKDIR /repo/services/inventory-service
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /repo
USER appuser

EXPOSE 5005
CMD ["gunicorn", "-b", "0.0.0.0:5005", "app:create_app()"]
