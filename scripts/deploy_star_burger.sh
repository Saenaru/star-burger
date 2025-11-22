#!/bin/bash
set -e

cd /opt/projects/star-burger

set -a
source .env
set +a

echo "🔄 Переключение на ветку server-config"
#git checkout server-config

echo "🔄 Обновление кода репозитория"
#git fetch origin
#git reset --hard origin/server-config

echo "📦 Установка Python библиотек"
source venv/bin/activate
pip install -r requirements.txt

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

echo "$COMMIT_HASH" > commit_hash.txt

if [ -n "$ROLLBAR_ACCESS_TOKEN" ]; then
    RESPONSE=$(curl -s -w "%{http_code}" -X POST https://api.rollbar.com/api/1/deploy/ \
      -H "Content-Type: application/json" \
      -d "{
        \"access_token\": \"$ROLLBAR_ACCESS_TOKEN\",
        \"environment\": \"production\",
        \"revision\": \"$COMMIT_HASH\",
        \"local_username\": \"deploy-script\",
        \"comment\": \"$COMMIT_MESSAGE\"
      }")

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ Уведомление Rollbar отправлено успешно"
    else
        echo "⚠️ Ошибка отправки уведомления Rollbar. Код: $HTTP_CODE"
    fi
else
    echo "⚠️ ROLLBAR_ACCESS_TOKEN не установлен, пропускаем уведомление Rollbar"
fi

echo "✅ Деплой успешно завершён"
echo "📝 Коммит: $COMMIT_HASH"
echo "🌿 Ветка: server-config"
