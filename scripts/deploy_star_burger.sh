#!/bin/bash
set -e

cd /opt/projects/star-burger

echo "🔄 Переключение на ветку server-config"
git checkout server-config

echo "🔄 Обновление кода репозитория"
git fetch origin
git reset --hard origin/server-config

echo "📦 Установка Python библиотек"
source /opt/venv/star-burger/bin/activate
pip install -r requirements.txt

echo "📦 Установка Node.js библиотек"
npm install

echo "🏗️ Пересборка JS-кода"
npm run build

echo "📁 Пересборка статики Django"
python manage.py collectstatic --noinput --clear

echo "🗃️ Накатывание миграций"
python manage.py migrate --noinput

echo "🔄 Перезапуск сервисов Systemd"
systemctl restart star-burger.service
systemctl reload nginx

echo "📡 Уведомление Rollbar о деплое"
COMMIT_HASH=$(git rev-parse HEAD)
COMMIT_MESSAGE=$(git log -1 --pretty=%B)

curl -X POST https://api.rollbar.com/api/1/deploy/ \
  -H "Content-Type: application/json" \
  -d "{
    \"access_token\": \"$ROLLBAR_ACCESS_TOKEN\",
    \"environment\": \"production\",
    \"revision\": \"$COMMIT_HASH\",
    \"local_username\": \"deploy-script\",
    \"comment\": \"$COMMIT_MESSAGE\"
  }" > /dev/null 2>&1 || echo "⚠️ Не удалось уведомить Rollbar"

echo "✅ Деплой успешно завершён"
echo "📝 Коммит: $COMMIT_HASH"
echo "🌿 Ветка: server-config"
