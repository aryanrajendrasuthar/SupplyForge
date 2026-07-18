FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5005
CMD ["gunicorn", "-b", "0.0.0.0:5005", "app:create_app()"]
