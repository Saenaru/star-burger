FROM node:16.16.0-slim AS frontend-builder
WORKDIR /app

COPY package.json package-lock.json ./

RUN npm install --include=dev

COPY . .
RUN ./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

FROM python:3.10-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY --from=frontend-builder /app/bundles ./bundles

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
