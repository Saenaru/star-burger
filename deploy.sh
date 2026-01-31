#!/bin/bash

set -e


echo "⬇️  Скачиваем обновления из Git..."
git pull origin master

echo "🐳 Пересобираем и запускаем контейнеры..."
docker compose -f docker-compose.prod.yaml up -d --build

echo "🗄️  Накатываем миграции базы данных..."
docker compose -f docker-compose.prod.yaml exec -T backend python manage.py migrate

echo "🎨 Собираем статику (CSS, картинки)..."
docker compose -f docker-compose.prod.yaml exec -T backend python manage.py collectstatic --noinput

echo "🔄 Перезагружаем Nginx..."
docker compose -f docker-compose.prod.yaml exec -T nginx nginx -s reload

echo "🧹 Чистим старые Docker-образы..."
docker system prune -f

echo "✅ Деплой успешно завершен! Сайт обновлен."