FROM node:16.16.0-slim AS frontend-builder
WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./

RUN npm install --include=dev

COPY frontend/ .

RUN ./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"


FROM python:3.10-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

COPY --from=frontend-builder /app/bundles ./bundles

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
