FROM python:3.10-slim

WORKDIR /app

# install system deps for asyncpg build
RUN apt-get update && apt-get install -y gcc libpq-dev build-essential --no-install-recommends \
  && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy app code (we'll add app/ next)
COPY ./app /app/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
