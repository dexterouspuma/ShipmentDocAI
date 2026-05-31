# Shipment Document AI — API service image
FROM python:3.12-slim

# ODBC Driver 18 for SQL Server (needed by pyodbc against Azure SQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl gnupg unixodbc-dev gcc g++ \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list \
        > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install deps first for better layer caching
COPY api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the shared package and the api app
COPY shared/ ./shared/
COPY api/app/ ./app/

ENV ENVIRONMENT=prod
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
