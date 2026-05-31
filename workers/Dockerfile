# Shipment Document AI — extraction worker image
FROM python:3.12-slim

# ODBC Driver 18 for SQL Server (pyodbc -> Azure SQL persistence)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl gnupg unixodbc-dev gcc g++ \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list \
        > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY workers/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Worker reuses shared models + the api app's repository/storage singletons.
COPY shared/ ./shared/
COPY api/app/ ./app/
COPY workers/ ./workers/

ENV ENVIRONMENT=prod
WORKDIR /app/workers
CMD ["python", "worker.py"]
